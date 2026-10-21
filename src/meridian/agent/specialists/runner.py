"""The braked tool loop for one specialist task (AEA-35; DO-4 §5 runner rules; graph-tools §2, §6; R-G-17).

Never raises; emits no signal and no check event; logs no message text; the provider message list lives for one run
only.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final

from pydantic import ValidationError

from meridian.agent.gateway import ModelGateway
from meridian.agent.specialists.specs import (
    REPORT_FACTS_TOOL,
    TROUBLESHOOTING_FILE,
    RunOutcome,
    SpecialistSpec,
    report_facts_schema,
)
from meridian.agent.tools.dispatch import DispatchedCall, ToolDispatcher
from meridian.domain.common import HaltReason, LLMFacing, ProviderFailure
from meridian.domain.records import Passage
from meridian.domain.specialists import (
    AccountCapture,
    KnowledgeCapture,
    SchedulingCapture,
    SpecialistResult,
)
from meridian.domain.state import ConversationState
from meridian.domain.tools import SpecialistTask, ToolCallRecord, ToolCallScope, ToolKind
from meridian.domain.turn import SpecialistKind, TurnContext
from meridian.policy.limits import Brakes
from meridian.ports.models import CallRecord, Role, ToolCall, ToolStepRequest, ToolTranscript
from meridian.ports.runtime import TraceSink

__all__ = ["SpecialistRunner", "scope_for"]

_log = logging.getLogger(__name__)
_QC_PREFIX: Final = "qc-"
_QC_KINDS: Final = frozenset({ToolKind.KB_SEARCH})
_QC_QUERY_CHARS: Final = 300  # KbSearchArgs.query max_length (data.md §4)
_REQUEST_MAX_TOKENS: Final = 3_000  # placeholder: the gateway replaces it with RoleSpec.max_tokens
_REQUEST_EFFORT: Final = None  # and RoleSpec.effort (AEA-20 _redact_tool; PD-12)


def scope_for(state: ConversationState, ctx: TurnContext) -> ToolCallScope:
    return ToolCallScope(
        ids=ctx.ids,
        customer_id=state.identity.customer_id if state.identity.status == "verified" else None,
        shown_slot_ids=frozenset(s.slot_id for s in state.shown_slots),
        now=ctx.now,
        message_id=state.turn_input.message_id,
    )


def _span_name(record: ToolCallRecord) -> str:
    return "tool:" + record.name if record.kind is not None else "tool:unknown"


@dataclass
class _Run:
    captured: list[KnowledgeCapture | AccountCapture | SchedulingCapture] = field(default_factory=list)
    passages: dict[str, Passage] = field(default_factory=dict)
    quick_checks: list[Passage] = field(default_factory=list)
    tools: list[ToolCallRecord] = field(default_factory=list)
    calls: list[CallRecord] = field(default_factory=list)
    report: LLMFacing | None = None
    brake: HaltReason | None = None
    failure: ProviderFailure | None = None
    broken: bool = False  # an exception or an empty step: status "failed"

    def outcome(self, task: SpecialistTask) -> RunOutcome:
        return RunOutcome(
            task=task,
            captured=tuple(self.captured),
            passages_returned=tuple(self.passages.values()),
            report=self.report,
            quick_checks=tuple(self.quick_checks),
            tools=tuple(self.tools),
            calls=tuple(self.calls),
            brake=self.brake,
            failure=self.failure,
        )


class SpecialistRunner:
    def __init__(
        self,
        *,
        gateway: ModelGateway,
        transcript: ToolTranscript,
        dispatcher: ToolDispatcher,
        specs: Mapping[SpecialistKind, SpecialistSpec],
        brakes: Brakes,
        trace: TraceSink,
    ) -> None:
        # Public by convention: AEA-51 asserts `runner.transcript is` the gateway's SPECIALIST adapter and
        # `runner.trace is` the container's sink (PD-8).
        self.gateway = gateway
        self.transcript = transcript
        self.dispatcher = dispatcher
        self.specs = specs
        self.brakes = brakes
        self.trace = trace

    def run(self, task: SpecialistTask, scope: ToolCallScope, ctx: TurnContext) -> SpecialistResult:
        spec = self.specs[task.task.specialist]  # a lookup, never a branch on the kind (DO-3 §4.5)
        run = _Run()
        try:
            self._loop(spec, task, scope, ctx, run)
        except Exception as exc:
            run.broken = True
            # Never log str(exc), repr(exc) or exc_info: they may hold message text.
            _log.error(
                "specialist_run_error kind=%s error_type=%s turn_id=%s",
                spec.kind,
                type(exc).__name__,
                ctx.ids.turn_id,
            )
        result = spec.build_result(run.outcome(task))
        if run.broken:
            result = result.model_copy(update={"status": "failed"})
        return result

    def _loop(
        self, spec: SpecialistSpec, task: SpecialistTask, scope: ToolCallScope, ctx: TurnContext, run: _Run
    ) -> None:
        tools = (*self.dispatcher.schemas(spec.tool_kinds), report_facts_schema(spec))
        prefix, dynamic, user = spec.render(task, ctx)
        messages = self.transcript.start(user)  # local only: never stored, logged, traced or returned
        if task.offer_quick_checks:
            qc = ToolCall(
                id=f"{_QC_PREFIX}{ctx.ids.turn_id}",
                name="kb_search",
                args={"query": task.customer_text[:_QC_QUERY_CHARS]},
            )
            quick = self.dispatcher.dispatch((qc,), kinds=_QC_KINDS, scope=scope)
            self._take(quick, ctx, run, model_round=False)
            for d in quick:
                cap = d.result.captured
                if isinstance(cap, KnowledgeCapture) and not cap.result.below_floor:
                    run.quick_checks.extend(p for p in cap.result.passages if p.file == TROUBLESHOOTING_FILE)
        rounds = 0
        seen: set[tuple[str, str]] = set()
        for _ in range(self.brakes.tool_rounds + 1):
            out = self.gateway.tool_step(
                Role.SPECIALIST,
                ToolStepRequest(
                    system_prefix=prefix,
                    system_dynamic=dynamic,
                    messages=messages,
                    tools=tools,
                    max_tokens=_REQUEST_MAX_TOKENS,
                    effort=_REQUEST_EFFORT,
                ),
                ctx,
            )
            run.calls.extend(out.calls)
            if out.halt is not None:
                run.brake = out.halt.reason
            if out.failure is not None:
                run.failure = out.failure
            if out.halt is not None or out.failure is not None:
                return
            step = out.value
            if step is None:
                run.broken = True
                return
            reports = [c for c in step.tool_calls if c.name == REPORT_FACTS_TOOL]
            calls = [c for c in step.tool_calls if c.name != REPORT_FACTS_TOOL]
            if run.report is None:
                for c in reports:
                    if c.args is None:
                        continue
                    try:
                        run.report = spec.report_model.model_validate(c.args)
                    except ValidationError:
                        continue
                    break
            if not calls:
                return
            if rounds >= self.brakes.tool_rounds:
                run.brake = HaltReason.BRAKE_TOOL_ROUNDS
                return
            new: list[ToolCall] = []
            dup: list[ToolCall] = []
            for c in calls:
                key = (c.name, json.dumps(c.args, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
                if key in seen:
                    dup.append(c)
                else:
                    seen.add(key)
                    new.append(c)
            if new:
                dispatched = self.dispatcher.dispatch(tuple(new), kinds=spec.tool_kinds, scope=scope)
                self._take(dispatched, ctx, run, model_round=True)
                rounds += 1
                messages = self.transcript.append(
                    messages, step, [(d.tool_call_id, d.content) for d in dispatched]
                )
            if dup:
                run.brake = HaltReason.BRAKE_IDENTICAL_CALL
                return
            if reports:
                return

    def _take(
        self, dispatched: Sequence[DispatchedCall], ctx: TurnContext, run: _Run, *, model_round: bool
    ) -> None:
        for d in dispatched:
            run.tools.append(d.record)
            self.trace.node(ctx.span, _span_name(d.record), d.record.elapsed_ms, d.record.outcome)
            if model_round and d.result.captured is not None:
                run.captured.append(d.result.captured)
                if isinstance(d.result.captured, KnowledgeCapture):
                    for p in d.result.captured.result.passages:
                        run.passages.setdefault(str(p.passage_id), p)
