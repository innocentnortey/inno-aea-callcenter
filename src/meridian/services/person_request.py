"""PersonRequestService: CON-4 "Talk to a person" (AEA-42; stage7/web.md section 8, MC-17, MC-18, MC-27).

No model, no spend guard, no rate limit. The service claims the turn id, asks HandoffService to open the case, takes the
card from the ReplyComposer, reads the "What's settled" panel from stored rows and stores the whole answer on the turn
row, so a second press with the same turn id returns the same body and the history can show the card (R-W-6).

The two Protocols are typing only: `services/` may not import `agent/` (DO-3 section 2.1), and the real HandoffService
and ReplyComposer satisfy them structurally.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Annotated, Final, Literal, Protocol

from pydantic import Field

from meridian.adapters.sqlite.rows import ConversationRow
from meridian.domain.actions import Settled
from meridian.domain.blocks import HandoffBlock, LiveQueuedBlock, SettledView
from meridian.domain.common import MeridianModel, RequestId, ThreadId, TurnId
from meridian.domain.handoff import HandoffReason, HandoffRequest, HandoffResult
from meridian.domain.identity import IdentityState
from meridian.domain.state import Controller
from meridian.domain.turn import TurnBudget, TurnContext, TurnIds, TurnRecord, TurnTrace
from meridian.policy.handoff import priority_for
from meridian.policy.limits import TurnLimits
from meridian.ports.runtime import Clock, TraceSink, UnitOfWorkFactory

RUNNING_WAIT_S: Final = 3.0  # [A] web.md section 8 step 1; replaced by a measured CON-4 p99 at Stage 9
RUNNING_POLL_S: Final = 0.1  # poll interval while a duplicate press is running
CON4_RULE_ID: Final = "CON4.person"


class HandoffOpener(Protocol):
    def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult: ...


class HandoffComposer(Protocol):
    def handoff_block(self, result: HandoffResult) -> HandoffBlock | LiveQueuedBlock: ...

    def settled_view(
        self, settled: Settled, identity: IdentityState, controller: Controller
    ) -> SettledView: ...


class PersonRequest(MeridianModel):
    thread_id: ThreadId
    turn_id: TurnId
    request_id: RequestId
    demo_session: str
    run_tag: Literal["live", "eval", "load"]
    run_id: str | None


class PersonRequestOutcome(MeridianModel):
    result: Literal["case_created", "live_queued", "already_open"]
    block: Annotated[HandoffBlock | LiveQueuedBlock, Field(discriminator="type")]
    settled: SettledView


class HandoffWriteFailed(Exception):
    """The case could not be written, or a duplicate press never finished. The message carries no value."""


def read_identity(uow: UnitOfWorkFactory, thread_id: ThreadId) -> IdentityState:
    with uow() as tx:
        return tx.core.reads.identity_state(thread_id)


def settled_view_for(
    uow: UnitOfWorkFactory, composer: HandoffComposer, thread_id: ThreadId, read_at: datetime
) -> SettledView:
    """The one builder of the "What's settled" panel for CON-4 and CON-5 (WEB-20); it reads stored rows only."""
    with uow() as tx:
        settled = tx.core.settled_for(thread_id, read_at)
        identity = tx.core.reads.identity_state(thread_id)
        row = tx.core.conversations.lookup(str(thread_id))
    controller = row.controller if isinstance(row, ConversationRow) else Controller(kind="ai")
    return composer.settled_view(settled, identity, controller)


class PersonRequestService:
    def __init__(
        self,
        uow: UnitOfWorkFactory,
        handoff: HandoffOpener,
        composer: HandoffComposer,
        trace: TraceSink,
        demo_clock: Clock,
        wall_clock: Callable[[], datetime],
    ) -> None:
        self._uow = uow
        self._handoff = handoff
        self._composer = composer
        self._trace = trace
        self._demo_clock = demo_clock
        self._wall_clock = wall_clock

    def request(self, cmd: PersonRequest) -> PersonRequestOutcome:
        now = self._demo_clock.now()  # the one demo reading: received_at, ctx.now, settled and replied_at
        mono = time.monotonic()

        with self._uow(write=True) as tx:
            row = tx.core.conversations.lookup(str(cmd.thread_id))
            if not isinstance(row, ConversationRow):
                raise HandoffWriteFailed("thread is not open")  # a reset ended it after owned_thread
            ids = TurnIds(
                thread_id=cmd.thread_id,
                turn_id=cmd.turn_id,
                request_id=cmd.request_id,
                run_tag=cmd.run_tag,
                run_id=cmd.run_id,
                agent_version=row.agent_version,
            )
            begin = tx.core.turns.begin(ids, now)
            identity = tx.core.reads.identity_state(cmd.thread_id)
            tx.commit()

        if begin.status == "completed":
            if begin.response is None:
                raise HandoffWriteFailed("stored outcome is missing")
            return PersonRequestOutcome.model_validate_json(begin.response)
        if begin.status == "running":
            return self._await_stored(cmd)

        failure: Exception | None = None
        result: HandoffResult | None = None
        outcome: PersonRequestOutcome | None = None
        kind: Literal["case_created", "live_queued", "already_open"] = "already_open"
        with self._trace.turn(ids) as span:
            ctx = TurnContext(
                ids=ids,
                budget=TurnBudget(started=mono, deadline=mono + TurnLimits().deadline_s),
                now=now,
                demo_session=cmd.demo_session,
                span=span,
                intake=None,
            )
            reason = HandoffReason.CUSTOMER_REQUESTED_PERSON
            req = HandoffRequest(
                thread_id=cmd.thread_id,
                turn_id=cmd.turn_id,
                reason=reason,
                priority=priority_for(reason),
                rule_id=CON4_RULE_ID,
                trigger="con4",
                identity=identity,
            )
            try:
                result = self._handoff.open(req, ctx)
            except Exception as exc:
                # CaseWriteFailed (AEA-29) is the documented failure after its one retry and is not importable here;
                # any failure must still leave the turn row failed so the next tap re-runs.
                failure = exc
            if result is not None:
                first = result.created or result.action.key.turn_id == cmd.turn_id
                if first:
                    kind = "live_queued" if result.case.promise.live_queued else "case_created"
                block = self._composer.handoff_block(result)
                view = settled_view_for(self._uow, self._composer, cmd.thread_id, now)
                outcome = PersonRequestOutcome(result=kind, block=block, settled=view)

        trace_id = span.trace_id
        export = self._trace.export_status(span)
        server_ms = int((time.monotonic() - mono) * 1000)

        if outcome is None:
            with self._uow(write=True) as tx:
                tx.core.turns.finish(
                    cmd.turn_id,
                    TurnRecord(
                        status="failed",
                        trace=TurnTrace(
                            gate_result="person_requested",
                            path="handoff",
                            outcome="degraded_handoff",
                            degrade_reason="tool_error",
                        ),
                        replied_at=now,
                        server_ms=server_ms,
                        model_calls=0,
                        input_tokens=0,
                        output_tokens=0,
                        cost_usd=0.0,
                        tool_calls=0,
                        trace_id=trace_id,
                        trace_export=export,
                        response="",
                    ),
                )
                tx.commit()
            raise HandoffWriteFailed("case write failed") from failure

        with self._uow(write=True) as tx:
            tx.core.turns.finish(
                cmd.turn_id,
                TurnRecord(
                    status="completed",
                    trace=TurnTrace(gate_result="person_requested", path="handoff", outcome="handed_off"),
                    replied_at=now,
                    server_ms=server_ms,
                    model_calls=0,
                    input_tokens=0,
                    output_tokens=0,
                    cost_usd=0.0,
                    tool_calls=0,
                    trace_id=trace_id,
                    trace_export=export,
                    response=outcome.model_dump_json(),
                ),
            )
            if kind in ("case_created", "live_queued"):
                tx.core.conversations.set_outcome(
                    cmd.thread_id, "handed_off", ended_wall_at=self._wall_clock()
                )
            tx.commit()
        return outcome

    def _await_stored(self, cmd: PersonRequest) -> PersonRequestOutcome:
        deadline = self._wall_clock() + timedelta(seconds=RUNNING_WAIT_S)
        for _ in range(int(RUNNING_WAIT_S / RUNNING_POLL_S)):  # bounded even if a test freezes the wall clock
            with self._uow() as tx:
                row = tx.core.turns.get(cmd.turn_id)
            if row is None or str(row.thread_id) != str(cmd.thread_id) or row.status == "failed":
                raise HandoffWriteFailed("person request did not finish")
            if row.status == "completed" and row.response:
                return PersonRequestOutcome.model_validate_json(row.response)
            if self._wall_clock() >= deadline:
                break
            time.sleep(RUNNING_POLL_S)
        raise HandoffWriteFailed("person request still running")
