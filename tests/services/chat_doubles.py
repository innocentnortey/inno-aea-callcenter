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
import json
import pkgutil
import random
import re
import sqlite3
import threading
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from pydantic import TypeAdapter

import meridian.domain as domain_package
from meridian.adapters.sqlite.rows import ConversationRow
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction, Settled
from meridian.domain.blocks import (
    FailureOfferBlock,
    FollowUpOptions,
    HandoffBlock,
    LiveQueuedBlock,
    Notice,
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


# -- storage seeding and reading --------------------------------------------------------------------------------
def human_controller(case_ref: str = "MHC-C-0042", name: str = "Riley") -> Controller:
    return Controller.model_validate({"kind": "human", "representative_name": name, "case_ref": case_ref})


def seed_thread(
    uow: Any,
    demo_session: str = DEMO_SESSION,
    *,
    controller: Controller | None = None,
    outcome: str = "open",
    at: dt.datetime = WORKED_PAIRS_NOW,
    run_tag: str = "live",
) -> ThreadId:
    """A conversations row plus the greeting assistant message, in one write transaction (cases.md section 5)."""
    thread_id = new_thread_id()
    row = ConversationRow.model_validate(
        {
            "thread_id": str(thread_id),
            "demo_session": demo_session,
            "run_tag": run_tag,
            "agent_version": AGENT_VERSION,
            "started_at": at,
            "outcome": outcome,
            "controller": (controller or Controller(kind="ai")).model_dump(),
        }
    )
    with uow(write=True) as tx:
        tx.core.conversations.insert(row)
        tx.core.messages.append(thread_id, "assistant", render(TextId.GREETING), at)
        tx.commit()
    return thread_id


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


def conversation(store: TempStore, thread_id: ThreadId) -> Any:
    with store.uow() as tx:
        return tx.core.conversations.lookup(str(thread_id))


def messages_of(store: TempStore, thread_id: ThreadId) -> tuple[Any, ...]:
    with store.uow() as tx:
        return tuple(tx.core.messages.all_for_thread(thread_id))


def customer_messages(store: TempStore, thread_id: ThreadId, turn_id: TurnId | None = None) -> list[Any]:
    return [
        m
        for m in messages_of(store, thread_id)
        if m.role == "customer" and (turn_id is None or m.turn_id == turn_id)
    ]


def turn_row(store: TempStore, turn_id: TurnId) -> Any:
    with store.uow() as tx:
        return tx.core.turns.get(turn_id)


def count_rows(store: TempStore, table: str, where: str = "1=1", params: tuple[Any, ...] = ()) -> int:
    conn = sqlite3.connect(store.db_path)
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params).fetchone()[0])  # noqa: S608 - test-only constants
    finally:
        conn.close()


def raw_value(store: TempStore, sql: str, params: tuple[Any, ...] = ()) -> Any:
    conn = sqlite3.connect(store.db_path)
    try:
        row = conn.execute(sql, params).fetchone()
    finally:
        conn.close()
    return None if row is None else row[0]


_DUMPED_TABLES = ("messages", "turns", "conversations", "check_events", "events", "lookup_log")


def text_dump(store: TempStore) -> str:
    """Every row of every table a customer value could land in, as one string, with UUIDs removed (so a random id
    cannot hold a six-digit run by chance)."""
    conn = sqlite3.connect(store.db_path)
    try:
        parts = [repr(conn.execute(f"SELECT * FROM {table}").fetchall()) for table in _DUMPED_TABLES]  # noqa: S608 - test-only constants
    finally:
        conn.close()
    return UUID_RE.sub("", "\n".join(parts))


# -- hooks: count, guard and break the unit of work -------------------------------------------------------------
class _RepoProxy:
    def __init__(self, repo: Any, name: str, hooks: dict[str, Callable[..., Any]]) -> None:
        self._repo = repo
        self._name = name
        self._hooks = hooks

    def __getattr__(self, attr: str) -> Any:
        target = getattr(self._repo, attr)
        hook = self._hooks.get(f"{self._name}.{attr}")
        if hook is None or not callable(target):
            return target

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            return hook(target, *args, **kwargs)

        return wrapped


class _CoreProxy:
    def __init__(self, core: Any, hooks: dict[str, Callable[..., Any]]) -> None:
        self._core = core
        self._hooks = hooks

    def __getattr__(self, name: str) -> Any:
        target = getattr(self._core, name)
        if any(key.startswith(name + ".") for key in self._hooks):
            return _RepoProxy(target, name, self._hooks)
        hook = self._hooks.get(name)
        if hook is not None and callable(target):

            def wrapped(*args: Any, **kwargs: Any) -> Any:
                return hook(target, *args, **kwargs)

            return wrapped
        return target


class _TxProxy:
    def __init__(self, tx: Any, hooks: dict[str, Callable[..., Any]]) -> None:
        self._tx = tx
        self.core = _CoreProxy(tx.core, hooks) if hooks else tx.core

    def __getattr__(self, name: str) -> Any:
        return getattr(self._tx, name)

    def commit(self) -> None:
        self._tx.commit()


class HookedUow:
    """A `UnitOfWorkFactory` wrapper: counts entries and the open depth, and wraps named repository methods.

    `hooks` maps `"repo.method"` (or `"settled_for"`) to `hook(real_method, *args, **kwargs)`.
    `forbidden_while` is an optional callable; when it returns True at entry the entry is recorded in
    `entered_while_forbidden` and an AssertionError is raised (a unit of work opened while it must not be).
    """

    def __init__(self, real: Any, hooks: dict[str, Callable[..., Any]] | None = None) -> None:
        self._real = real
        self._hooks = hooks or {}
        self.depth = 0
        self.entries = 0
        self.forbidden_while: Callable[[], bool] | None = None
        self.entered_while_forbidden = 0
        self._lock = threading.Lock()

    @contextmanager
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> Iterator[Any]:
        if self.forbidden_while is not None and self.forbidden_while():
            self.entered_while_forbidden += 1
            raise AssertionError("a unit of work was entered while it must not be open")
        with self._lock:
            self.entries += 1
            self.depth += 1
        try:
            with self._real(write=write, exclusive=exclusive) as tx:
                yield _TxProxy(tx, self._hooks)
        finally:
            with self._lock:
                self.depth -= 1


def fail_after(message: str = "injected fault") -> Callable[..., Any]:
    """A hook that runs the real method and then raises, so only a rollback can undo what it wrote."""

    def hook(real: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        real(*args, **kwargs)
        raise RuntimeError(message)

    return hook


def fail_first_call(message: str = "injected fault") -> Callable[..., Any]:
    """A hook that raises on its first call (without running the real method) and passes later calls through."""
    state = {"calls": 0}

    def hook(real: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        state["calls"] += 1
        if state["calls"] == 1:
            raise RuntimeError(message)
        return real(*args, **kwargs)

    return hook


# -- blocks used by history tests -------------------------------------------------------------------------------
def handoff_block(
    reference: str = "MHC-C-0042", at: dt.datetime = WORKED_PAIRS_NOW, *, block_id: str = "blk-handoff"
) -> HandoffBlock:
    return HandoffBlock(
        block_id=block_id,
        speaker=ASSISTANT_SPEAKER,
        at=at,
        card_id=f"handoff-{reference}",
        options=(),
        answered=None,
        reference=reference,
        variant="nobody_online",
        promise_text="A person will reach out by tomorrow at noon.",
        due_at=None,
        due_label=None,
        extra_lines=(),
        followup_chooser=FollowUpOptions(
            legend="How should we reach you?", channels=(), windows=(), general_only=True
        ),
    )


def live_queued_block(
    reference: str = "MHC-C-0042", at: dt.datetime = WORKED_PAIRS_NOW, *, block_id: str = "blk-queued"
) -> LiveQueuedBlock:
    return LiveQueuedBlock(
        block_id=block_id,
        speaker=ASSISTANT_SPEAKER,
        at=at,
        reference=reference,
        promise_text="A representative is being asked to join.",
    )


def notice_codes(blocks: Any) -> list[str]:
    return [b.code for b in blocks if getattr(b, "type", None) == "notice"]


def has_person_key(blocks: Any) -> bool:
    return any(getattr(b, "person_key", False) for b in blocks)


@dataclass
class Collected:
    """Results of worker threads: either a response or the exception the call raised."""

    results: list[Any] = field(default_factory=list)
    errors: list[BaseException] = field(default_factory=list)

    def run(self, fn: Callable[[], Any]) -> None:
        try:
            self.results.append(fn())
        except BaseException as exc:
            self.errors.append(exc)


def turn_ids_of(cmd: Any) -> Any:
    """The `TurnIds` a command stands for (what `core.turns.begin` takes)."""
    from meridian.domain.turn import TurnIds

    return TurnIds.model_validate(
        {
            "thread_id": str(cmd.thread_id),
            "turn_id": str(cmd.turn_id),
            "request_id": str(cmd.request_id),
            "run_tag": cmd.run_tag,
            "run_id": cmd.run_id,
            "agent_version": AGENT_VERSION,
        }
    )


def records_of_kind(caplog: pytest.LogCaptureFixture, kind: str) -> list[dict[str, Any]]:
    """The `meridian_record` extras (web/logging.py RECORD_ATTR) with `record == kind`, from pytest's capture."""
    found: list[dict[str, Any]] = []
    for record in caplog.records:
        extra = record.__dict__.get("meridian_record")
        if isinstance(extra, dict) and extra.get("record") == kind:
            found.append(extra)
    return found


def log_blob(caplog: pytest.LogCaptureFixture) -> str:
    """Everything the loggers captured: messages, arguments, extras, exception text."""
    parts: list[str] = []
    for record in caplog.records:
        parts.append(record.getMessage())
        parts.append(repr(sorted((k, repr(v)) for k, v in record.__dict__.items() if k != "exc_info")))
        if record.exc_info:
            parts.append(repr(record.exc_info[1]))
        if record.exc_text:
            parts.append(record.exc_text)
    return "\n".join(parts)


def notice_of(response: Any) -> Notice | None:
    notice = response.notice
    assert notice is None or isinstance(notice, Notice)
    return notice


def dump_json(model: Any) -> str:
    return json.dumps(model.model_dump(mode="json"), sort_keys=True)


def data_dir_text(root: Path) -> str:
    """Every file under a directory, decoded leniently, for the 'nowhere in the working copy' checks."""
    parts: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            parts.append(path.read_bytes().decode("utf-8", errors="ignore"))
    return "\n".join(parts)


# -- history seeding (AC-16 to AC-18): rows in the shapes AEA-42 (web.md section 8) and AEA-46 (staff.md 5, 7) write ---
RILEY = "Riley"
_EVENT_SPEAKER: dict[str, Any] = {"kind": "event", "display_name": None}


@dataclass
class Takeover:
    """The ids and texts of one seeded representative takeover, in event-id order."""

    joined_id: int
    paused_id: int
    riley_message_id: int
    staff_event_id: int
    resumed_id: int
    riley_text: str
    lines: dict[str, str]
    staffing_id: int | None = None
    shift_end_id: int | None = None

    @property
    def newest_event_id(self) -> int:
        return max(
            i
            for i in (self.resumed_id, self.staff_event_id, self.staffing_id, self.shift_end_id)
            if i is not None
        )


def seed_case(
    uow: Any, thread_id: ThreadId, case_ref: str = "MHC-C-0042", at: dt.datetime = WORKED_PAIRS_NOW
) -> None:
    """A case row and its promise for the thread (an open case needs its promise: `settled_for` reads both)."""
    from meridian.adapters.sqlite.rows import CaseRow
    from meridian.domain.common import Promise

    row = CaseRow.model_validate(
        {
            "case_ref": case_ref,
            "thread_id": str(thread_id),
            "reason": "customer_requested_person",
            "priority": "P3",
            "rule_id": "R-TEST",
            "trigger": "customer",
            "lifecycle": "unassigned",
            "created_at": at,
            "updated_at": at,
        }
    )
    with uow(write=True) as tx:
        tx.cases.cases.insert(row)
        tx.cases.promises.insert(
            row.case_ref,
            Promise(policy_row="test", text="A person will reach out.", due_at=None, due_label=None),
            at,
        )
        tx.commit()


def seed_person_request_turn(
    uow: Any,
    thread_id: ThreadId,
    block: HandoffBlock | LiveQueuedBlock,
    at: dt.datetime = WORKED_PAIRS_NOW,
) -> TurnId:
    """A CON-4 turn row in web.md section 8's stored shape: completed, gate_result `person_requested`, no message."""
    from meridian.domain.turn import TurnIds, TurnRecord

    turn_id = new_turn_id()
    ids = TurnIds.model_validate(
        {
            "thread_id": str(thread_id),
            "turn_id": str(turn_id),
            "request_id": str(new_request_id()),
            "run_tag": "live",
            "run_id": None,
            "agent_version": AGENT_VERSION,
        }
    )
    stored = json.dumps(
        {
            "result": "case_created",
            "block": block.model_dump(mode="json"),
            "settled": empty_view().model_dump(mode="json"),
        }
    )
    record = TurnRecord(
        status="completed",
        trace=TurnTrace(gate_result="person_requested", path="handoff", outcome="handed_off"),
        replied_at=at,
        server_ms=5,
        model_calls=0,
        input_tokens=0,
        output_tokens=0,
        cost_usd=0.0,
        tool_calls=0,
        trace_id=None,
        trace_export="off",
        response=stored,
    )
    with uow(write=True) as tx:
        tx.core.turns.begin(ids, at)
        tx.core.turns.finish(turn_id, record)
        tx.commit()
    return turn_id


def seed_takeover(
    uow: Any,
    thread_id: ThreadId,
    at: dt.datetime = WORKED_PAIRS_NOW,
    *,
    riley_text: str = "Hi, this is Riley. I can see your request.",
    staffing_change: bool = False,
    shift_end: HandoffBlock | None = None,
    step: dt.timedelta = dt.timedelta(0),
) -> Takeover:
    """Riley joins, the AI pauses, Riley writes, hands back; optionally the staffing line and a shift end.

    Every row carries `at`; with a non-zero `step` the n-th row (joined 0, paused 1, Riley 2, resumed 3, staffing 4,
    shift end 5) is `n * step` later, so a test can ask for time order without depending on a tie-break.
    """
    from meridian.adapters.sqlite.rows import StreamEvent, thread_stream

    lines = {
        "joined": render(TextId.REP_JOINED, rep_name=RILEY),
        "paused": render(TextId.AI_PAUSED, rep_name=RILEY),
        "resumed": render(TextId.AI_RESUMED, rep_name=RILEY),
        "staffing": render(TextId.STAFFING_CHANGED_ON_SHIFT),
        "shift_ended": render(TextId.SHIFT_ENDED),
    }
    stream = thread_stream(thread_id)

    def event(tx: Any, kind: str, payload: dict[str, Any], n: int) -> int:
        return int(tx.core.events.append(stream, StreamEvent(type=kind, payload=payload, at=at + n * step)))

    with uow(write=True) as tx:
        joined = event(
            tx,
            "representative_joined",
            {"speaker": _EVENT_SPEAKER, "display_name": RILEY, "line": lines["joined"]},
            0,
        )
        paused = event(tx, "ai_paused", {"speaker": _EVENT_SPEAKER, "line": lines["paused"]}, 1)
        message_id = tx.core.messages.append(thread_id, "representative", riley_text, at + 2 * step)
        staff_event = event(
            tx,
            "staff_message",
            {
                "speaker": {"kind": "representative", "display_name": RILEY},
                "message_id": str(message_id),
                "text": riley_text,
            },
            2,
        )
        resumed = event(tx, "ai_resumed", {"speaker": _EVENT_SPEAKER, "line": lines["resumed"]}, 3)
        staffing_id = None
        if staffing_change:
            staffing_id = event(
                tx,
                "staffing_changed",
                {
                    "speaker": _EVENT_SPEAKER,
                    "staffing": {
                        "mode": "simulated_on_shift",
                        "label": "Simulated staff on shift (demo)",
                        "banner": None,
                    },
                    "line": lines["staffing"],
                },
                4,
            )
        shift_id = None
        if shift_end is not None:
            shift_id = event(
                tx,
                "shift_ended",
                {
                    "speaker": _EVENT_SPEAKER,
                    "line": lines["shift_ended"],
                    "handoff": shift_end.model_dump(mode="json"),
                    "settled": empty_view().model_dump(mode="json"),
                },
                5,
            )
        tx.commit()
    return Takeover(
        joined_id=joined,
        paused_id=paused,
        riley_message_id=message_id,
        staff_event_id=staff_event,
        resumed_id=resumed,
        riley_text=riley_text,
        lines=lines,
        staffing_id=staffing_id,
        shift_end_id=shift_id,
    )


def newest_event_id(store: TempStore, thread_id: ThreadId) -> int:
    from meridian.adapters.sqlite.rows import thread_stream

    with store.uow() as tx:
        return int(tx.core.events.latest_id(thread_stream(thread_id)))


def attr(obj: Any, name: str) -> Any:
    """Read a field of a union member without a type ignore (blocks are a discriminated union)."""
    return getattr(obj, name)
