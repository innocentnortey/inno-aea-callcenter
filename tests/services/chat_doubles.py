"""AEA-40 test support: doubles, seeders and builders for the customer API tests (frozen with the AEA-40 tests).

Not a conftest. Everything is synthetic and built at run time: no `.env`, no real secret, no paid call, no socket. The
verification code, card number and phone number are generated from a seeded `random.Random` (never typed as literals),
so no file in this ticket holds a code-, card- or phone-like value.

Two rules for this module (plan section 7.1):
* Part A tests (turns) import nothing Part B needs, so `ClockView` / `StaffingView` (AEA-02b) and the two new
  `TextId`s (AEA-03 follow-up) are resolved lazily, inside the helpers only Part B tests call.
* The production modules under test (`meridian.services.turn`, `meridian.services.session`, `meridian.web.routes.chat`)
  are imported inside helper functions, so this module imports while they do not exist yet.
"""

from __future__ import annotations

import datetime as dt
import importlib
import pkgutil
import random
import re
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest
from pydantic import TypeAdapter

import meridian.domain as domain_package
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction, Settled
from meridian.domain.blocks import (
    FailureOfferBlock,
    SettledIdentity,
    SettledReplying,
    SettledView,
    Speaker,
    TextBlock,
    Write,
)
from meridian.domain.common import Halt, HaltReason, RequestId, ThreadId, TurnId
from meridian.domain.state import Controller, IdentityState
from meridian.domain.turn import (
    CheckEvent,
    ComposedReply,
    GraphOutcome,
    PlannerTrace,
    TurnContext,
    TurnInput,
    TurnTrace,
)
from meridian.policy.limits import Limits
from meridian.policy.texts import TextId, render
from tests.fakes import WORKED_PAIRS_NOW, FixedClock, InMemoryTraceSink
from tests.fixtures.sqlite import TempStore

AGENT_VERSION = "test-agent-0"
DEMO_SESSION = "demo-session-test"
WALL_NOW = dt.datetime(2026, 10, 21, 15, 30, tzinfo=dt.UTC)
ASSISTANT_SPEAKER = Speaker(kind="assistant", display_name="Meridian assistant")
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

_THREAD = TypeAdapter(ThreadId)
_TURN = TypeAdapter(TurnId)
_REQUEST = TypeAdapter(RequestId)


def new_thread_id() -> ThreadId:
    return _THREAD.validate_python(str(uuid.uuid4()))


def new_turn_id() -> TurnId:
    return _TURN.validate_python(str(uuid.uuid4()))


def new_request_id() -> RequestId:
    return _REQUEST.validate_python(str(uuid.uuid4()))


def fixed_wall() -> dt.datetime:
    return WALL_NOW


# -- synthetic values -------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Synthetic:
    """A code, a card number and a phone number built from a seeded generator. Never typed as literals."""

    code: str
    card_digits: str
    card: str  # the same digits grouped by four, as a customer might type them
    phone: str

    def needles(self) -> tuple[str, ...]:
        """Every form of the three values that must never appear in stored rows, logs or traces."""
        return (self.code, self.card_digits, self.card, self.phone, self.phone.replace("-", ""))


def synthetic(seed: int = 4040) -> Synthetic:
    rng = random.Random(seed)
    code = "".join(str(rng.randint(0, 9)) for _ in range(6))
    digits = "".join(str(rng.randint(0, 9)) for _ in range(16))
    card = " ".join(digits[i : i + 4] for i in range(0, 16, 4))
    phone = f"{rng.randint(200, 999)}-{rng.randint(200, 999)}-{rng.randint(1000, 9999)}"
    return Synthetic(code=code, card_digits=digits, card=card, phone=phone)


# -- payload builders (plain dicts: the models validate them) ---------------------------------------------------
def text_payload(text: str) -> dict[str, Any]:
    return {"kind": "text", "text": text}


def code_payload(code: str, card_id: str = "code-card-1") -> dict[str, Any]:
    return {"kind": "code", "card_id": card_id, "code": code}


def locate_form_payload(name: str, phone: str, card_id: str = "locate-card-1") -> dict[str, Any]:
    return {"kind": "form", "card_id": card_id, "values": {"name": name, "phone": phone}}


def choice_payload(card_id: str, option: str) -> dict[str, Any]:
    return {"kind": "choice", "card_id": card_id, "option": option}


# -- doubles ----------------------------------------------------------------------------------------------------
class FakeSpendGuard:
    """SpendGuard (models.md section 6): `allow_turn()` answers `allow`. Counts calls."""

    def __init__(self, allow: bool = True) -> None:
        self.allow = allow
        self.calls = 0

    def allow_turn(self) -> bool:
        self.calls += 1
        return self.allow


def simple_settled_view(settled: Settled, identity: IdentityState, controller: Controller) -> SettledView:
    """The `ReplyComposer.settled_view` double (graph-core section 13): a pure function of its three inputs."""
    status = "not_checked" if identity.status == "located" else identity.status
    return SettledView(
        visit=None,
        request=None,
        identity=SettledIdentity(status=status, hint=None),
        replying=SettledReplying(kind=controller.kind, display_name=controller.representative_name),
        actions=tuple(
            Write(kind=a.kind.value, summary=a.kind.value, turn_id=str(a.key.turn_id), at=a.at)
            for a in settled.actions
        ),
    )


def empty_view() -> SettledView:
    return SettledView(
        visit=None,
        request=None,
        identity=SettledIdentity(status="not_checked", hint=None),
        replying=SettledReplying(kind="ai", display_name=None),
        actions=(),
    )


def _text_block(turn_id: TurnId, at: dt.datetime, text: str) -> TextBlock:
    return TextBlock(block_id=f"blk-{turn_id}-1", speaker=ASSISTANT_SPEAKER, at=at, text=text, sources=())


def answered_outcome(
    turn_id: TurnId,
    at: dt.datetime,
    *,
    text: str = "Here is what that invoice covers.",
    closed: bool = False,
    outcome: Any = "answered",
    events: bool = True,
) -> GraphOutcome:
    """A scripted `GraphOutcome`: a gate result, a planner decision, one specialist, two check events."""
    trace = TurnTrace(
        gate_result="clear",
        path="talk",
        outcome=outcome,
        planner=PlannerTrace(
            model="jev-test",
            fallback_used=False,
            failure=None,
            plan_mode="talk",
            plan_source="planner",
            topic="billing",
        ),
        specialists_run=("knowledge",),
    )
    reply = ComposedReply(
        blocks=(_text_block(turn_id, at, text),),
        settled_view=empty_view(),
        writes=(),
        notice=None,
        path="talk",
        outcome=outcome,
        degrade_reason=None,
    )
    checks = (
        (
            CheckEvent(check="gate", turn_id=turn_id, result="pass", codes=("free_text",)),
            CheckEvent(check="fact", turn_id=turn_id, result="pass"),
        )
        if events
        else ()
    )
    return GraphOutcome(
        reply=reply, turn_trace=trace, check_events=checks, halt=None, closed_every_open_task=closed
    )


def handed_off_outcome(turn_id: TurnId, at: dt.datetime, *, closed: bool = False) -> GraphOutcome:
    trace = TurnTrace(gate_result="clear", path="handoff", outcome="handed_off")
    reply = ComposedReply(
        blocks=(_text_block(turn_id, at, "A person will pick this up."),),
        settled_view=empty_view(),
        writes=(),
        notice=None,
        path="handoff",
        outcome="handed_off",
        degrade_reason=None,
    )
    return GraphOutcome(reply=reply, turn_trace=trace, closed_every_open_task=closed)


def degraded_outcome(turn_id: TurnId, at: dt.datetime) -> GraphOutcome:
    trace = TurnTrace(
        gate_result="clear", path="degraded", outcome="degraded_handoff", degrade_reason="model_error"
    )
    reply = ComposedReply(
        blocks=(
            FailureOfferBlock(
                block_id=f"blk-{turn_id}-1",
                speaker=ASSISTANT_SPEAKER,
                at=at,
                text=render(TextId.FAILURE_OFFER),
                person_key=True,
            ),
        ),
        settled_view=empty_view(),
        writes=(),
        notice=None,
        path="degraded",
        outcome="degraded_handoff",
        degrade_reason="model_error",
    )
    return GraphOutcome(reply=reply, turn_trace=trace)


@dataclass
class Call:
    turn_input: TurnInput
    context: TurnContext
    input_json: str  # `TurnInput.model_dump_json()` taken at call time


class ScriptedRunGraph:
    """`run_graph` double (graph-core section 2). Returns the scripted outcomes in order, then `answered_outcome`.

    An item is a `GraphOutcome` or a callable `(TurnInput, TurnContext) -> GraphOutcome`. Records every call.
    """

    def __init__(self, *items: GraphOutcome | Callable[[TurnInput, TurnContext], GraphOutcome]) -> None:
        self._items = list(items)
        self.calls: list[Call] = []
        self._lock = threading.Lock()

    def __call__(self, turn_input: TurnInput, context: TurnContext) -> GraphOutcome:
        with self._lock:
            index = len(self.calls)
            self.calls.append(Call(turn_input, context, turn_input.model_dump_json()))
        if index < len(self._items):
            item = self._items[index]
            return item if isinstance(item, GraphOutcome) else item(turn_input, context)
        return answered_outcome(turn_input.turn_id, context.now)


class BlockingRunGraph:
    """Blocks every call until `release` is set; `entered` is released once per call that has started."""

    def __init__(self) -> None:
        self.release = threading.Event()
        self.entered = threading.Semaphore(0)
        self.calls = 0
        self._lock = threading.Lock()

    def __call__(self, turn_input: TurnInput, context: TurnContext) -> GraphOutcome:
        with self._lock:
            self.calls += 1
        self.entered.release()
        assert self.release.wait(10), "the blocking graph double was never released"
        return answered_outcome(turn_input.turn_id, context.now)


class RaisingRunGraph:
    """`run_graph` that raises. The message carries a letters-only marker no log or body may contain."""

    MARKER = "qxzmarkerboom"

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, turn_input: TurnInput, context: TurnContext) -> GraphOutcome:
        self.calls += 1
        raise RuntimeError("scripted graph failure " + self.MARKER)


class DeadlineRunGraph:
    """Commits one BOOKED action for this turn in its own write transaction, then reports a DEADLINE halt."""

    def __init__(self, uow: Any, *, write_action: bool = True) -> None:
        self._uow = uow
        self._write_action = write_action
        self.calls: list[Call] = []

    def __call__(self, turn_input: TurnInput, context: TurnContext) -> GraphOutcome:
        self.calls.append(Call(turn_input, context, turn_input.model_dump_json()))
        if self._write_action:
            action = CompletedAction(
                key=ActionKey(
                    thread_id=context.ids.thread_id,
                    turn_id=context.ids.turn_id,
                    kind=ActionKind.BOOKED,
                    record_id="9001",
                ),
                kind=ActionKind.BOOKED,
                records={"appointment": "9001"},
                before=None,
                after={"date": "2026-10-19"},
                at=context.now,
            )
            with self._uow(write=True) as tx:
                tx.core.actions.record(action)
                tx.commit()
        trace = TurnTrace(gate_result="clear", path="act", outcome="acted")
        reply = ComposedReply(
            blocks=(_text_block(context.ids.turn_id, context.now, "Working on it."),),
            settled_view=empty_view(),
            writes=(),
            notice=None,
            path="act",
            outcome="acted",
            degrade_reason=None,
        )
        return GraphOutcome(
            reply=reply,
            turn_trace=trace,
            halt=Halt(reason=HaltReason.DEADLINE, node="act", elapsed_ms=60_000),
        )


class FakeComposer:
    """Stands in for `ReplyComposer` (AEA-21): only `settled_view` is read by AEA-40."""

    settled_view = staticmethod(simple_settled_view)


# -- Part B doubles: resolved lazily (AEA-02b and AEA-03 follow-up are not on main yet) -----------------------------
def resolve_domain_class(name: str) -> Any:
    """Find `ClockView` / `StaffingView` wherever AEA-02b put them under `meridian.domain` (proposed: `views`)."""
    for module_info in pkgutil.iter_modules(domain_package.__path__):
        module = importlib.import_module(f"meridian.domain.{module_info.name}")
        found = module.__dict__.get(name)
        if isinstance(found, type) and found.__module__ == module.__name__:
            return found
    pytest.fail(f"{name} is not defined under meridian.domain: blocked-on AEA-02b (cases.md A-2)")


def history_text_id(name: str) -> TextId:
    """`TextId.HISTORY_CODE_ENTERED` / `HISTORY_DETAILS_SENT` (AEA-03 follow-up, plan section 8 R-4)."""
    found = getattr(TextId, name, None)
    if found is None:
        pytest.fail(f"TextId.{name} is missing: blocked-on the AEA-03 follow-up (plan section 8 R-4)")
    assert isinstance(found, TextId)
    return found


class FakeDemo:
    """`DemoReads` double (plan 4.6): the OpenAPI STARTED example values."""

    def __init__(self) -> None:
        clock_view = resolve_domain_class("ClockView")
        staffing_view = resolve_domain_class("StaffingView")
        self._clock = clock_view(
            now=WORKED_PAIRS_NOW,
            label="Fri Oct 16, 2026 · 10:00 am",
            date_label="Fri Oct 16, 2026 (demo date)",
        )
        self._staffing = staffing_view(mode="nobody_online", label="Nobody online", banner=None)
        self.staffing_reads = 0
        self.clock_reads = 0

    def staffing(self) -> Any:
        self.staffing_reads += 1
        return self._staffing

    def clock_view(self) -> Any:
        self.clock_reads += 1
        return self._clock


def make_cmd(
    thread_id: ThreadId | str,
    payload: dict[str, Any],
    *,
    turn_id: TurnId | None = None,
    demo_session: str = DEMO_SESSION,
    run_tag: str = "live",
    run_id: str | None = None,
) -> Any:
    from meridian.services.turn import RunTurn

    return RunTurn.model_validate(
        {
            "thread_id": str(thread_id),
            "turn_id": str(turn_id or new_turn_id()),
            "request_id": str(new_request_id()),
            "demo_session": demo_session,
            "payload": payload,
            "run_tag": run_tag,
            "run_id": run_id,
        }
    )


def make_turn_service(
    store: TempStore,
    *,
    run_graph: Callable[[TurnInput, TurnContext], GraphOutcome] | None = None,
    spend: FakeSpendGuard | None = None,
    clock: Any = None,
    wall: Callable[[], dt.datetime] | None = None,
    trace: Any = None,
    monotonic: Callable[[], float] | None = None,
    uow: Any = None,
    limits: Limits | None = None,
) -> Any:
    """A real `TurnService` over the temp working copy with every sibling doubled (plan 4.6 constructor)."""
    from meridian.services.turn import TurnService

    extra: dict[str, Any] = {} if monotonic is None else {"monotonic": monotonic}
    return TurnService(
        uow if uow is not None else store.uow,
        clock if clock is not None else FixedClock(),
        wall if wall is not None else fixed_wall,
        spend if spend is not None else FakeSpendGuard(True),
        trace if trace is not None else InMemoryTraceSink(),
        run_graph if run_graph is not None else ScriptedRunGraph(),
        simple_settled_view,
        limits if limits is not None else Limits(),
        AGENT_VERSION,
        **extra,
    )


def make_session_service(
    store: TempStore,
    *,
    demo: FakeDemo | None = None,
    wall: Callable[[], dt.datetime] | None = None,
    uow: Any = None,
) -> Any:
    from meridian.services.session import SessionService

    return SessionService(
        uow if uow is not None else store.uow,
        FixedClock(),
        demo if demo is not None else FakeDemo(),
        Limits(),
        simple_settled_view,
        AGENT_VERSION,
        wall_clock=wall if wall is not None else fixed_wall,
    )
