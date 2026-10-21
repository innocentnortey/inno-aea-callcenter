"""Frozen tests for the front nodes: gates, safety, identity (AEA-36, risk::security; plan section 7.1).

Failure-mode labels follow the ticket's tags: [invariant], [failure/refusal], [negative], [boundary].
Synthetic ids and data only; no model call; identity and handoff services are injected doubles.
"""

from __future__ import annotations

import ast
import contextlib
import dataclasses
import datetime as dt
import json
import logging
import random
import sqlite3
import string
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from langgraph.runtime import Runtime
from pydantic import SecretStr, TypeAdapter

from meridian.adapters.sqlite.db import format_wall
from meridian.agent.context import GraphDeps
from meridian.agent.nodes import front
from meridian.domain.actions import ActionKey, ActionKind, CompletedAction
from meridian.domain.common import CaseRef, CustomerId, RequestId, ThreadId, TurnId
from meridian.domain.handoff import CaseSummary, HandoffReason, HandoffRequest, HandoffResult, Priority
from meridian.domain.identity import (
    CodeCapReached,
    CodeExpired,
    CodeLocked,
    CodeSent,
    CodeWrong,
    FormValues,
    IdentityState,
    Located,
    Locator,
    NotVerified,
    Verified,
)
from meridian.domain.state import Controller, ConversationState, OpenTask, TaskDetails
from meridian.domain.turn import (
    ChoicePayload,
    CodePayload,
    DangerAssessment,
    FormPayload,
    GateKind,
    Intake,
    Plan,
    PlannedTask,
    SafetyKind,
    SpanHandle,
    TaskIntent,
    TextPayload,
    TurnBudget,
    TurnContext,
    TurnIds,
    TurnInput,
)
from meridian.gates.gate import burning_card_id, decide_gate, flags_from_state, parse_intake
from meridian.policy.handoff import priority_for, promise_for
from tests.fixtures.sqlite import TempStore, temp_sqlite

THREAD = ThreadId("6a7b8c9d-0e1f-4a2b-8c3d-4e5f6a7b8c9d")
TURN = TurnId("7b8c9d0e-1f2a-4b3c-9d4e-5f6a7b8c9d0e")
TURN_PREV = TurnId("8c9d0e1f-2a3b-4c4d-ae5f-6a7b8c9d0e1f")
TURN_CODE = TurnId("9d0e1f2a-3b4c-4d5e-bf6a-7b8c9d0e1f2a")
REQ = RequestId("0e1f2a3b-4c5d-4e6f-8a7b-8c9d0e1f2a3b")
NOW = dt.datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))
DEMO_SESSION = "demo-session-36"
HINT = "the phone ending in 02"
REP = Controller(
    kind="human", representative_name="Riley (demo representative)", case_ref=CaseRef("MHC-C-0009")
)

WP5 = "My carbon monoxide detector is going off."
CO_TYPO = "my carbon monoxid alarm is going off"
WP6 = "I need to schedule a service call. I smell something burning from the vents."
DANGER_WORDS = "My son can't breathe"
DANGER_FREE = "my mother is 88 and it's 95 degrees in here"
PLAIN = "When will the technician arrive?"
NOT_SURE = "not sure"

NODE_STUB_MSG = "stub from AEA-21"  # a red test must fail on the stub, never on a typo in this file


# ---------------------------------------------------------------- builders


def _intake(payload: Any) -> Intake:
    return parse_intake(payload)


def _state(turn_id: TurnId, intake: Intake, **kw: Any) -> ConversationState:
    turn_input = TurnInput(
        turn_id=turn_id,
        message_id=1,
        kind=intake.kind,
        text_store=intake.text_store,
        card_id=intake.card_id,
        choice=intake.choice,
        card_number_seen=intake.card_number_seen,
        received_at=NOW,
    )
    return ConversationState(thread_id=THREAD, turn_input=turn_input, **kw)


def _ctx(turn_id: TurnId, intake: Intake) -> TurnContext:
    t0 = time.monotonic()
    return TurnContext(
        ids=TurnIds(
            thread_id=THREAD,
            turn_id=turn_id,
            request_id=REQ,
            run_tag="live",
            run_id=None,
            agent_version="test",
        ),
        budget=TurnBudget(started=t0, deadline=t0 + 60.0),
        now=NOW,
        demo_session=DEMO_SESSION,
        span=SpanHandle(turn_id=turn_id, trace_id=None),
        intake=intake,
    )


def _rt(ctx: TurnContext) -> Runtime[TurnContext]:
    return Runtime(context=ctx)


def _apply(state: ConversationState, update: Any) -> ConversationState:
    return state.model_copy(update=dict(update))


class _Rec:
    """Records every access to a GraphDeps field a test does not drive, and refuses its use."""

    def __init__(self, name: str, log: list[tuple[str, str]]) -> None:
        self._name = name
        self._log = log

    def __getattr__(self, attr: str) -> Callable[..., Any]:
        self._log.append((self._name, attr))

        def refuse(*_a: Any, **_k: Any) -> Any:
            self._log.append((self._name, f"{attr}()"))
            raise AssertionError(f"{self._name}.{attr} must not be used")

        return refuse

    def __call__(self, *_a: Any, **_k: Any) -> Any:
        self._log.append((self._name, "__call__"))
        raise AssertionError(f"{self._name} must not be used")


def _deps(log: list[tuple[str, str]] | None = None, **over: Any) -> GraphDeps:
    sink: list[tuple[str, str]] = [] if log is None else log
    fields: dict[str, Any] = {
        f.name: over.get(f.name, _Rec(f.name, sink)) for f in dataclasses.fields(GraphDeps)
    }
    return GraphDeps(**fields)


def _used(log: list[tuple[str, str]], *names: str) -> list[tuple[str, str]]:
    return [e for e in log if e[0] in names]


def _gated(payload: Any, *, turn_id: TurnId = TURN, **state_kw: Any) -> tuple[ConversationState, TurnContext]:
    intake = _intake(payload)
    state = _state(turn_id, intake, **state_kw)
    ctx = _ctx(turn_id, intake)
    update = front.gates(state, _rt(ctx), deps=_deps())
    return _apply(state, update), ctx


def _booking_task() -> OpenTask:
    return OpenTask(
        task_id="t-1",
        specialist="scheduling",
        intent=TaskIntent.BOOK_NEW,
        opened_turn=TURN_PREV,
        details=TaskDetails(),
        status="open",
    )


def _verified() -> IdentityState:
    return IdentityState(
        status="verified",
        customer_id=CustomerId("MHC-10002"),
        masked_hint=HINT,
        code_expires_at=None,
        tries_left=3,
        codes_sent=1,
        verified_at=NOW,
    )


def _code_sent_state() -> IdentityState:
    return IdentityState(
        status="code_sent",
        customer_id=CustomerId("MHC-10002"),
        masked_hint=HINT,
        code_expires_at=NOW + dt.timedelta(minutes=10),
        tries_left=3,
        codes_sent=1,
        verified_at=None,
    )


def _not_checked() -> IdentityState:
    return IdentityState(
        status="not_checked",
        customer_id=None,
        masked_hint=None,
        code_expires_at=None,
        tries_left=3,
        codes_sent=0,
        verified_at=None,
    )


def _handoff_result(
    reason: HandoffReason, *, created: bool = True, case_ref: str = "MHC-C-0009"
) -> HandoffResult:
    summary = CaseSummary(
        case_ref=CaseRef(case_ref),
        reason=reason,
        priority=priority_for(reason),
        state="unassigned",
        created_at=NOW,
        promise=promise_for(reason, "nobody_online", NOW),
        followup=None,
        version=1,
        due_at=None,
    )
    action = CompletedAction(
        key=ActionKey(thread_id=THREAD, turn_id=TURN, kind=ActionKind.CASE_OPENED, record_id=case_ref),
        kind=ActionKind.CASE_OPENED,
        records={"case": case_ref},
        at=NOW,
    )
    return HandoffResult(case=summary, created=created, action=action, alert="supervisor_now")


def _code_sent() -> CodeSent:
    return CodeSent(masked_hint=HINT, expires_at=NOW + dt.timedelta(minutes=10), sends_left=2)


def _verified_step(turn_id: TurnId = TURN_CODE) -> Verified:
    return Verified(
        customer_id=CustomerId("MHC-10002"),
        action=CompletedAction(
            key=ActionKey(thread_id=THREAD, turn_id=turn_id, kind=ActionKind.VERIFIED, record_id="MHC-10002"),
            kind=ActionKind.VERIFIED,
            records={"customer": "MHC-10002"},
            at=NOW,
        ),
    )


# ---------------------------------------------------------------- doubles


class _HandoffDouble:
    def __init__(self, outcomes: list[HandoffResult | Exception]) -> None:
        self._outcomes = list(outcomes)
        self.calls: list[HandoffRequest] = []

    def open(self, req: HandoffRequest, ctx: TurnContext) -> HandoffResult:
        self.calls.append(req)
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _resolve(value: Any) -> Any:
    return value() if callable(value) else value


class _IdentityDouble:
    def __init__(
        self,
        *,
        locate: Any = None,
        send: Any = None,
        verify: Any = None,
        writer: Callable[[str], None] | None = None,
    ) -> None:
        self._locate = locate
        self._send = send
        self._verify = verify
        self._writer = writer
        self.calls: list[str] = []
        self.args: list[tuple[Any, ...]] = []

    def _go(self, name: str, result: Any, args: tuple[Any, ...]) -> Any:
        self.calls.append(name)
        self.args.append(args)
        if self._writer is not None:
            self._writer(name)
        return _resolve(result)

    def locate(self, thread_id: ThreadId, locator: Locator, now: dt.datetime) -> Any:
        return self._go("locate", self._locate, (thread_id, locator, now))

    def send_code(self, thread_id: ThreadId, demo_session: str, now: dt.datetime) -> Any:
        return self._go("send_code", self._send, (thread_id, demo_session, now))

    def verify(self, ids: TurnIds, digits: SecretStr, now: dt.datetime) -> Any:
        return self._go("verify", self._verify, (ids, digits, now))


class _UowDouble:
    def __init__(self, state: IdentityState) -> None:
        self._state = state
        self.opened: list[tuple[bool, bool]] = []
        self.reads: list[ThreadId] = []

    def __call__(self, *, write: bool = False, exclusive: bool = False) -> Any:
        self.opened.append((write, exclusive))

        def identity_state(thread_id: ThreadId) -> IdentityState:
            self.reads.append(thread_id)
            return self._state

        tx = SimpleNamespace(core=SimpleNamespace(reads=SimpleNamespace(identity_state=identity_state)))
        return contextlib.nullcontext(tx)


class _SpyUow:
    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.opened: list[dict[str, Any]] = []

    def __call__(self, **kw: Any) -> Any:
        self.opened.append(dict(kw))
        return self._inner(**kw)


# ---------------------------------------------------------------- sentinels


def _constants_haystack() -> str:
    parts = [
        str(THREAD),
        str(TURN),
        str(TURN_PREV),
        str(TURN_CODE),
        str(REQ),
        NOW.isoformat(),
        format_wall(NOW),
        DEMO_SESSION,
        HINT,
        "MHC-10002",
        "MHC-C-0009",
    ]
    return "|".join(parts)


def _sentinels(seed: int = 36) -> dict[str, str]:
    rng = random.Random(seed)
    hay = _constants_haystack()
    while True:
        code = "".join(str(rng.randrange(10)) for _ in range(6))
        if code not in hay:
            break
    phone = f"512-555-01{rng.randrange(100):02d}"
    name = "Sentinelname " + "".join(rng.choice(string.ascii_lowercase) for _ in range(8))
    phrase = "zqsentinel" + "".join(rng.choice(string.ascii_lowercase) for _ in range(8))
    return {
        "code": code,
        "phone": phone,
        "phone_digits": "".join(c for c in phone if c.isdigit()),
        "name": name,
        "phrase": phrase,
    }


def _sig(record: logging.LogRecord) -> dict[str, Any]:
    signal: dict[str, Any] = record.__dict__["signal"]
    return signal


def _signal_records(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [r.signal for r in caplog.records if r.name == "meridian.signal" and hasattr(r, "signal")]


def _locate_payload(name: str | None, phone: str | None) -> FormPayload:
    return FormPayload(
        card_id=f"locate-{TURN}",
        values=FormValues(name=name, phone=None if phone is None else SecretStr(phone)),
    )


def _code_payload(code: str, turn_id: TurnId = TURN_CODE) -> CodePayload:
    return CodePayload(card_id=f"code-{turn_id}", code=SecretStr(code))


# ---------------------------------------------------------------- gates


def test_gate_first_every_turn_mid_chat() -> None:
    """[invariant] AC-1: a typo'd CO phrase mid-chat is SAFETY, even with a task open, a card pending or a rep in charge."""
    base: dict[str, Any] = {"open_tasks": [_booking_task()], "identity": _verified()}
    cases = {
        "a_open_task": base,
        "b_burn_card_pending": {**base, "burning_card_id": burning_card_id(TURN_PREV)},
        "c_rep_owns_chat": {**base, "controller": REP},
    }
    for case_id, kw in cases.items():
        intake = _intake(TextPayload(text=CO_TYPO))
        state = _state(TURN, intake, **kw)
        ctx = _ctx(TURN, intake)
        update = front.gates(state, _rt(ctx), deps=_deps())
        gate = update["gate"]
        print(f"{case_id} -> {gate.kind.value} keys={sorted(update)}")
        assert gate.kind is GateKind.SAFETY, case_id
        assert gate.rules.safety is SafetyKind.CO, case_id
        assert gate.resume_task_id is None, case_id
        assert gate == decide_gate(intake, flags_from_state(state)), case_id
        assert set(update) <= {"gate", "check_events", "burning_card_id"}, case_id


def test_gate_event_and_burning_card_id() -> None:
    """[invariant] AC-2: one codes-only gate event per turn; the burn card id is set on BURNING_ASK, cleared otherwise."""
    prev_card = burning_card_id(TURN_PREV)
    cases: dict[str, tuple[Any, dict[str, Any]]] = {
        "wp5": (TextPayload(text=WP5), {}),
        "wp6": (TextPayload(text=WP6), {}),
        "plain": (TextPayload(text=PLAIN), {}),
        "burn_no": (ChoicePayload(card_id=prev_card, option="no"), {"burning_card_id": prev_card}),
    }
    for case_id, (payload, kw) in cases.items():
        intake = _intake(payload)
        state = _state(TURN, intake, **kw)
        update = front.gates(state, _rt(_ctx(TURN, intake)), deps=_deps())
        gate = update["gate"]
        events = update["check_events"]
        print(f"{case_id} -> {gate.kind.value} events={len(events)} card={update.get('burning_card_id')}")
        assert len(events) == 1, case_id
        ev = events[0]
        assert ev.check == "gate", case_id
        assert ev.turn_id == TURN, case_id
        assert ev.codes == (gate.kind.value, *gate.rules.rule_ids), case_id
        if case_id == "wp5":
            assert ev.result == "fired"
            assert ev.codes == ("safety", "R5.co")
            assert update["burning_card_id"] is None
        elif case_id == "wp6":
            assert ev.result == "fired"
            assert ev.codes[0] == "burning_ask"
            assert update["burning_card_id"] == f"burn-{TURN}"
        elif case_id == "plain":
            assert ev.result == "pass"
            assert ev.codes == ("free_text",)
            assert update["burning_card_id"] is None
        else:
            assert "burning_card_id" in update and update["burning_card_id"] is None, case_id


def test_burning_no_writes_code_built_plan() -> None:
    """[invariant] AC-3: only a burning 'no' writes plan, and it is the code-built booking plan."""
    prev_card = burning_card_id(TURN_PREV)
    pending = {"burning_card_id": prev_card}
    expected = Plan(
        mode="act",
        tasks=(
            PlannedTask(order=1, specialist="scheduling", intent=TaskIntent.BOOK_NEW, needs_identity=True),
        ),
        handoff_request=HandoffReason.BURNING_RULED_OUT,
        topic="booking",
        source="rules_only",
    )
    intake = _intake(ChoicePayload(card_id=prev_card, option="no"))
    state = _state(TURN, intake, **pending)
    update = front.gates(state, _rt(_ctx(TURN, intake)), deps=_deps())
    assert update["plan"] == expected
    assert update["plan"].planner_failed is False

    others: dict[str, tuple[Any, dict[str, Any]]] = {
        "wp5": (TextPayload(text=WP5), {}),
        "wp6": (TextPayload(text=WP6), {}),
        "plain": (TextPayload(text=PLAIN), {}),
        "danger_words": (TextPayload(text=DANGER_WORDS), {}),
        "burn_yes": (ChoicePayload(card_id=prev_card, option="yes"), pending),
        "burn_not_sure": (ChoicePayload(card_id=prev_card, option="not_sure"), pending),
        "burn_text_unsure": (TextPayload(text=NOT_SURE), pending),
        "locate_form": (_locate_payload("Omar Patel", "512-555-0100"), {}),
        "code": (_code_payload("123456"), {}),
    }
    for case_id, (payload, kw) in others.items():
        intake = _intake(payload)
        state = _state(TURN, intake, **kw)
        update = front.gates(state, _rt(_ctx(TURN, intake)), deps=_deps())
        print(f"{case_id} -> keys={sorted(update)}")
        assert "plan" not in update, case_id


# ---------------------------------------------------------------- safety


def test_wp5_safety_p0_no_model_no_identity() -> None:
    """[invariant] AC-4, PA-4 (WP-5): CO alarm opens one P0 case by code; no model, identity, retrieval or runner call."""
    state, ctx = _gated(TextPayload(text=WP5))
    log: list[tuple[str, str]] = []
    result = _handoff_result(HandoffReason.SAFETY)
    h = _HandoffDouble([result])
    update = front.safety(state, _rt(ctx), deps=_deps(log, handoff=h))
    assert len(h.calls) == 1
    req = h.calls[0]
    assert req.trigger == "safety"
    assert req.reason is HandoffReason.SAFETY
    assert req.priority is Priority.P0
    assert req.safety_kind is SafetyKind.CO
    assert req.rule_id == "R5.co"
    assert req.thread_id == THREAD
    assert req.turn_id == TURN
    assert req.identity == state.identity
    assert req.change_request is None
    assert update == {"handoff": result}
    assert log == []
    print("wp5 -> gateway=0 identity=0 retrieval=0 specialists=0 open=1")


_BURN_TABLE = {
    # case id -> (reason, priority literal, rule id, cause)
    "burn_yes": (HandoffReason.SAFETY, Priority.P0, "R7.burning_yes", "safety"),
    "burn_unsure": (HandoffReason.BURNING_UNCLEAR, Priority.P1, "R7.burning_unsure", "burning_unclear"),
    "burn_text_unsure": (HandoffReason.BURNING_UNCLEAR, Priority.P1, "R7.burning_unsure", "burning_unclear"),
    "danger_rule": (HandoffReason.DANGER, Priority.P1, "R8.danger_words", "danger"),
    "clf_danger": (HandoffReason.DANGER, Priority.P1, "R47.classifier_danger", "danger"),
    "clf_burning": (
        HandoffReason.BURNING_UNCLEAR,
        Priority.P1,
        "R47.classifier_burning_unclear",
        "burning_unclear",
    ),
}


def _burn_case(case_id: str) -> tuple[ConversationState, TurnContext]:
    prev_card = burning_card_id(TURN_PREV)
    pending: dict[str, Any] = {"burning_card_id": prev_card}
    if case_id == "burn_yes":
        return _gated(ChoicePayload(card_id=prev_card, option="yes"), **pending)
    if case_id == "burn_unsure":
        return _gated(ChoicePayload(card_id=prev_card, option="not_sure"), **pending)
    if case_id == "burn_text_unsure":
        return _gated(TextPayload(text=NOT_SURE), **pending)
    if case_id == "danger_rule":
        return _gated(TextPayload(text=DANGER_WORDS))
    if case_id in ("clf_danger", "clf_burning"):
        state, ctx = _gated(TextPayload(text=DANGER_FREE))
        label: Any = "danger" if case_id == "clf_danger" else "burning_unclear"
        danger = DangerAssessment(label=label, raised=True, confidence=0.9, failure=None)
        return _apply(state, {"danger": danger}), ctx
    raise AssertionError(case_id)


@pytest.mark.parametrize("case_id", list(_BURN_TABLE))
def test_burning_and_danger_paths(case_id: str, caplog: pytest.LogCaptureFixture) -> None:
    """[invariant] AC-5, PA-4 (WP-6): reason, priority and rule id come from code and policy, never a model."""
    caplog.set_level(logging.INFO, logger="meridian.signal")
    reason, priority, rule_id, cause = _BURN_TABLE[case_id]
    state, ctx = _burn_case(case_id)
    h = _HandoffDouble([_handoff_result(reason)])
    front.safety(state, _rt(ctx), deps=_deps(handoff=h))
    print(f"{case_id} -> {reason.value} {priority.value} {rule_id} {cause}")
    assert len(h.calls) == 1, case_id
    req = h.calls[0]
    assert req.reason is reason, case_id
    assert req.priority == priority_for(req.reason), case_id
    assert req.priority is priority, case_id
    assert req.rule_id == rule_id, case_id
    assert req.safety_kind is None, case_id
    assert req.trigger == "safety", case_id
    signals = [s for s in _signal_records(caplog) if s["name"] == "safety_reply_sent"]
    assert len(signals) == 1, case_id
    assert signals[0]["cause"] == cause, case_id


def test_burning_ask_opens_no_case(caplog: pytest.LogCaptureFixture) -> None:
    """[invariant] AC-5, PA-3: BURNING_ASK reaches safety but opens no case and sends no instruction signal."""
    caplog.set_level(logging.INFO, logger="meridian.signal")
    state, ctx = _gated(TextPayload(text=WP6))
    h = _HandoffDouble([])
    update = front.safety(state, _rt(ctx), deps=_deps(handoff=h))
    assert update == {}
    assert h.calls == []
    assert _signal_records(caplog) == []


def test_safety_case_write_retried_once_instruction_kept(caplog: pytest.LogCaptureFixture) -> None:
    """[failure/refusal] AC-6: one retry on a failed case write; the instruction signal exists whatever the write does."""
    caplog.set_level(logging.INFO, logger="meridian.signal")
    result = _handoff_result(HandoffReason.SAFETY)
    locked = "database is locked"

    # (a) first write fails, retry recovers
    state, ctx = _gated(TextPayload(text=WP5))
    caplog.clear()
    ha = _HandoffDouble([sqlite3.OperationalError(locked), result])
    update = front.safety(state, _rt(ctx), deps=_deps(handoff=ha))
    assert len(ha.calls) == 2
    assert update == {"handoff": result}
    recs = _signal_records(caplog)
    assert [r["name"] for r in recs] == ["safety_reply_sent", "case_write_failed"]
    assert recs[1]["attempt"] == 2
    assert recs[1]["recovered"] is True
    assert recs[1]["cause"] == "write_error"
    assert recs[1]["node"] == "safety"

    # (b) both writes fail: no exception, no handoff, no halt
    caplog.clear()
    hb = _HandoffDouble([sqlite3.OperationalError(locked), sqlite3.OperationalError(locked)])
    update = front.safety(state, _rt(ctx), deps=_deps(handoff=hb))
    assert len(hb.calls) == 2
    assert update == {}
    assert "handoff" not in update and "halt" not in update
    recs = _signal_records(caplog)
    assert [r["name"] for r in recs] == ["safety_reply_sent", "case_write_failed"]
    assert recs[1]["recovered"] is False

    # (c) first write succeeds: no failure signal
    caplog.clear()
    hc = _HandoffDouble([result])
    front.safety(state, _rt(ctx), deps=_deps(handoff=hc))
    assert len(hc.calls) == 1
    assert [r["name"] for r in _signal_records(caplog)] == ["safety_reply_sent"]


def test_safety_while_representative_owns_chat() -> None:
    """[invariant] AC-7 (GRC-3 A): a CO alarm beats AI-paused; the existing case comes back idempotently."""
    state, ctx = _gated(TextPayload(text=WP5), controller=REP)
    assert state.gate is not None
    assert state.gate.kind is GateKind.SAFETY
    existing = _handoff_result(HandoffReason.SAFETY, created=False, case_ref="MHC-C-0009")
    h = _HandoffDouble([existing])
    update = front.safety(state, _rt(ctx), deps=_deps(handoff=h))
    assert len(h.calls) == 1
    assert update["handoff"].created is False
    assert state.controller.case_ref is not None
    assert update["handoff"].case.case_ref == state.controller.case_ref


def test_safety_refuses_non_safety_paths(caplog: pytest.LogCaptureFixture) -> None:
    """[negative] PA-3: a router bug fails loudly; no case opens and no instruction signal is sent."""
    caplog.set_level(logging.INFO, logger="meridian.signal")
    normal = DangerAssessment(label="normal", raised=False, failure=None)
    prev_card = burning_card_id(TURN_PREV)
    cases: dict[str, tuple[ConversationState, TurnContext]] = {
        "free_text": _gated(TextPayload(text=PLAIN)),
        "classifier_normal": (lambda s_c: (_apply(s_c[0], {"danger": normal}), s_c[1]))(
            _gated(TextPayload(text=DANGER_FREE))
        ),
        "burn_no": _gated(ChoicePayload(card_id=prev_card, option="no"), burning_card_id=prev_card),
    }
    for case_id, (state, ctx) in cases.items():
        h = _HandoffDouble([])
        with pytest.raises(ValueError):
            front.safety(state, _rt(ctx), deps=_deps(handoff=h))
        assert h.calls == [], case_id
        assert _signal_records(caplog) == [], case_id


# ---------------------------------------------------------------- identity


def _ident_writer(store: TempStore) -> Callable[[str], None]:
    def write(method: str) -> None:
        conn = sqlite3.connect(store.db_path)
        try:
            tid = str(THREAD)
            now = format_wall(NOW)
            if method == "locate":
                conn.execute(
                    "INSERT OR REPLACE INTO identity_threads (thread_id, status, customer_id, masked_hint, "
                    "channel, verified_at, updated_at) VALUES (?, 'located', 'MHC-10002', ?, 'phone', NULL, ?)",
                    (tid, HINT, now),
                )
            elif method == "send_code":
                conn.execute(
                    "UPDATE identity_threads SET status='code_sent', updated_at=? WHERE thread_id=?",
                    (now, tid),
                )
                conn.execute(
                    "INSERT INTO identity_codes (thread_id, customer_id, code_hmac, held_by, sent_at, "
                    "expires_at, tries_left, used_at, inbox_message_id) "
                    "VALUES (?, 'MHC-10002', 'synthetic-hmac-36', 'test-boot', ?, ?, 3, NULL, 1)",
                    (tid, now, format_wall(NOW + dt.timedelta(minutes=10))),
                )
            elif method == "verify":
                conn.execute(
                    "UPDATE identity_threads SET status='verified', verified_at=?, updated_at=? "
                    "WHERE thread_id=?",
                    (now, now, tid),
                )
                conn.execute("UPDATE identity_codes SET used_at=? WHERE thread_id=?", (now, tid))
            conn.commit()
        finally:
            conn.close()

    return write


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def test_wp2_locate_send_verify(store: TempStore) -> None:
    """[invariant] AC-8 (WP-2): form -> locate -> send_code in one turn; code turn -> verify; identity re-read read-only."""
    conn = sqlite3.connect(store.db_path)
    try:
        phone = conn.execute("SELECT phone FROM customers WHERE customer_id = 'MHC-10002'").fetchone()[0]
    finally:
        conn.close()
    idd = _IdentityDouble(
        locate=Located(masked_hint=HINT),
        send=_code_sent(),
        verify=_verified_step(),
        writer=_ident_writer(store),
    )
    spy = _SpyUow(store.uow)
    deps = _deps(identity=idd, uow=spy)

    # turn 1
    state, ctx = _gated(
        FormPayload(
            card_id=f"locate-{TURN}",
            values=FormValues(name="Omar Patel", phone=SecretStr(str(phone))),
        )
    )
    update = front.identity(state, _rt(ctx), deps=deps)
    assert idd.calls == ["locate", "send_code"]
    locator = idd.args[0][1]
    assert isinstance(locator, Locator)
    assert locator.customer_id is None
    assert locator.invoice_number is None
    assert locator.name == "Omar Patel"
    assert idd.args[1] == (THREAD, DEMO_SESSION, NOW)
    assert isinstance(update["identity_step"], CodeSent)
    assert update["identity_step"].masked_hint == HINT
    with store.uow() as tx:
        fresh = tx.core.reads.identity_state(THREAD)
    assert update["identity"] == fresh
    assert fresh.status == "code_sent"
    assert fresh.codes_sent == 1
    assert fresh.customer_id == "MHC-10002"

    # turn 2
    code = _sentinels()["code"]
    state2, ctx2 = _gated(
        _code_payload(code),
        turn_id=TURN_CODE,
        identity=update["identity"],
    )
    update2 = front.identity(state2, _rt(ctx2), deps=deps)
    assert idd.calls[2:] == ["verify"]
    ids_arg, digits_arg, now_arg = idd.args[2]
    assert ids_arg == ctx2.ids
    assert isinstance(digits_arg, SecretStr)
    assert digits_arg.get_secret_value() == code
    assert now_arg == NOW
    assert isinstance(update2["identity_step"], Verified)
    assert update2["identity"].status == "verified"
    with store.uow() as tx:
        assert update2["identity"] == tx.core.reads.identity_state(THREAD)
    for opened in spy.opened:
        assert not opened.get("write", False)
        assert not opened.get("exclusive", False)


def test_identity_results_passed_through() -> None:
    """[failure/refusal] AC-9 (R-16): every not-verified cause is byte-identical; code results pass through unchanged."""
    prev_code_card = f"code-{TURN_PREV}"
    not_checked = _not_checked()
    # NotVerified causes
    dumps: list[str] = []
    for cause in ("no_match", "ambiguous", "no_contact"):
        idd = _IdentityDouble(locate=lambda: NotVerified())
        uow = _UowDouble(not_checked)
        state, ctx = _gated(_locate_payload("Omar Patel", "512-555-0100"))
        update = front.identity(state, _rt(ctx), deps=_deps(identity=idd, uow=uow))
        assert idd.calls == ["locate"], cause
        dumps.append(update["identity_step"].model_dump_json())
    idd = _IdentityDouble()
    uow = _UowDouble(not_checked)
    state, ctx = _gated(_locate_payload("Omar Patel", None))
    update = front.identity(state, _rt(ctx), deps=_deps(identity=idd, uow=uow))
    assert idd.calls == [], "incomplete"
    assert "identity" not in update, "incomplete"
    dumps.append(update["identity_step"].model_dump_json())
    assert len(set(dumps)) == 1
    assert dumps[0] == NotVerified().model_dump_json()

    # verify results
    for result in (CodeWrong(tries_left=2), CodeExpired(resend_offered=True, sends_left=1), CodeLocked()):
        idd = _IdentityDouble(verify=result)
        uow = _UowDouble(_code_sent_state())
        state, ctx = _gated(
            _code_payload("123456", TURN_CODE), turn_id=TURN_CODE, identity=_code_sent_state()
        )
        update = front.identity(state, _rt(ctx), deps=_deps(identity=idd, uow=uow))
        assert idd.calls == ["verify"], result.kind
        assert update["identity_step"] is result, result.kind

    # CodeCapReached after Located in the locate turn
    cap = CodeCapReached()
    idd = _IdentityDouble(locate=Located(masked_hint=HINT), send=cap)
    state, ctx = _gated(_locate_payload("Omar Patel", "512-555-0100"))
    update = front.identity(state, _rt(ctx), deps=_deps(identity=idd, uow=_UowDouble(not_checked)))
    assert idd.calls == ["locate", "send_code"]
    assert update["identity_step"] is cap

    # new_code choice: send_code, never verify
    cap2 = CodeCapReached()
    idd = _IdentityDouble(send=cap2)
    state, ctx = _gated(ChoicePayload(card_id=prev_code_card, option="new_code"), identity=_code_sent_state())
    update = front.identity(state, _rt(ctx), deps=_deps(identity=idd, uow=_UowDouble(_code_sent_state())))
    assert idd.calls == ["send_code"]
    assert update["identity_step"] is cap2


def test_code_and_form_values_never_leave_intake(caplog: pytest.LogCaptureFixture) -> None:
    """[negative] AC-10 (R-15): code digits and the form's phone and name never reach state, returns, logs or the model."""
    caplog.set_level(logging.DEBUG)
    s = _sentinels()
    log: list[tuple[str, str]] = []
    idd_locate = _IdentityDouble(locate=Located(masked_hint=HINT), send=_code_sent())
    idd_code = _IdentityDouble(verify=_verified_step())
    uow = _UowDouble(_verified())

    collected_states: list[ConversationState] = []
    collected_updates: list[Any] = []

    for payload, idd, turn_id, kw in (
        (_locate_payload(s["name"], s["phone"]), idd_locate, TURN, {}),
        (_code_payload(s["code"]), idd_code, TURN_CODE, {"identity": _code_sent_state()}),
    ):
        intake = _intake(payload)
        state = _state(turn_id, intake, **kw)
        ctx = _ctx(turn_id, intake)
        gate_update = front.gates(state, _rt(ctx), deps=_deps(log))
        state = _apply(state, gate_update)
        id_update = front.identity(state, _rt(ctx), deps=_deps(log, identity=idd, uow=uow))
        collected_updates.extend([gate_update, id_update])
        collected_states.extend([state, _apply(state, id_update)])

    assert len(collected_updates) == 4
    for needle in (s["code"], s["phone"], s["phone_digits"], s["name"]):
        for st in collected_states:
            assert needle not in st.model_dump_json()
        for up in collected_updates:
            assert needle not in TypeAdapter(Any).dump_json(up).decode()
            assert needle not in repr(up)
        for r in caplog.records:
            assert needle not in r.getMessage()
            assert needle not in repr(getattr(r, "signal", None))
            assert needle not in repr(r.args)
    assert _used(log, "gateway") == []


def test_front_nodes_write_only_own_keys(caplog: pytest.LogCaptureFixture) -> None:
    """[invariant] AC-11: gates, safety and identity write only their own state keys; none ever halts."""
    caplog.set_level(logging.INFO, logger="meridian.signal")
    prev_card = burning_card_id(TURN_PREV)
    pending = {"burning_card_id": prev_card}
    forbidden = {
        "halt", "planner", "reply", "open_tasks", "settled", "facts", "draft", "checked",
        "specialist_results", "escalation", "controller", "counters", "shown_slots", "chat_window",
        "brief_extraction", "danger", "turn_input", "thread_id",
    }  # fmt: skip

    gate_cases: dict[str, tuple[Any, dict[str, Any]]] = {
        "wp5": (TextPayload(text=WP5), {}),
        "wp6": (TextPayload(text=WP6), {}),
        "plain": (TextPayload(text=PLAIN), {}),
        "danger_words": (TextPayload(text=DANGER_WORDS), {}),
        "burn_no": (ChoicePayload(card_id=prev_card, option="no"), pending),
        "burn_yes": (ChoicePayload(card_id=prev_card, option="yes"), pending),
        "locate": (_locate_payload("Omar Patel", "512-555-0100"), {}),
        "code": (_code_payload("123456"), {}),
    }
    for case_id, (payload, kw) in gate_cases.items():
        intake = _intake(payload)
        state = _state(TURN, intake, **kw)
        u = front.gates(state, _rt(_ctx(TURN, intake)), deps=_deps())
        assert set(u) <= {"gate", "check_events", "burning_card_id", "plan"}, case_id
        assert ("plan" in u) == (case_id == "burn_no"), case_id
        assert not (set(u) & forbidden), case_id

    ok = _HandoffDouble([_handoff_result(HandoffReason.SAFETY)])
    bad = _HandoffDouble([RuntimeError("x"), RuntimeError("x")])
    wp5_state, wp5_ctx = _gated(TextPayload(text=WP5))
    ask_state, ask_ctx = _gated(TextPayload(text=WP6))
    for case_id, (st, cx, h) in {
        "safety_ok": (wp5_state, wp5_ctx, ok),
        "safety_both_fail": (wp5_state, wp5_ctx, bad),
        "burning_ask": (ask_state, ask_ctx, _HandoffDouble([])),
    }.items():
        su = front.safety(st, _rt(cx), deps=_deps(handoff=h))
        assert set(su) <= {"handoff"}, case_id
        assert not (set(su) & forbidden), case_id

    ident_cases: dict[str, tuple[Any, _IdentityDouble, dict[str, Any]]] = {
        "locate": (
            _locate_payload("Omar Patel", "512-555-0100"),
            _IdentityDouble(locate=Located(masked_hint=HINT), send=_code_sent()),
            {},
        ),
        "incomplete": (_locate_payload("Omar Patel", None), _IdentityDouble(), {}),
        "code_wrong": (
            _code_payload("123456"),
            _IdentityDouble(verify=CodeWrong(tries_left=2)),
            {"identity": _code_sent_state()},
        ),
        "free_text": (TextPayload(text=PLAIN), _IdentityDouble(), {}),
    }
    for case_id, (payload, idd, kw) in ident_cases.items():
        turn_id = TURN_CODE if case_id == "code_wrong" else TURN
        st, cx = _gated(payload, turn_id=turn_id, **kw)
        iu = front.identity(st, _rt(cx), deps=_deps(identity=idd, uow=_UowDouble(_code_sent_state())))
        assert set(iu) <= {"identity_step", "identity"}, case_id
        assert not (set(iu) & forbidden), case_id


def test_check_event_and_signal_records(caplog: pytest.LogCaptureFixture) -> None:
    """[invariant] AC-12: the gate event is codes-only; safety_reply_sent carries ids and cause, never the message."""
    caplog.set_level(logging.INFO, logger="meridian.signal")
    phrase = _sentinels()["phrase"]
    for text, codes, cause in (
        (f"{WP5} {phrase}", ("safety", "R5.co"), "safety"),
        (f"{DANGER_WORDS} {phrase}", ("danger_rule", "R8.danger_words"), "danger"),
    ):
        caplog.clear()
        intake = _intake(TextPayload(text=text))
        state = _state(TURN, intake)
        ctx = _ctx(TURN, intake)
        update = front.gates(state, _rt(ctx), deps=_deps())
        ev = update["check_events"][0]
        assert ev.codes == codes
        assert phrase not in ev.model_dump_json()
        state = _apply(state, update)
        reason = HandoffReason.SAFETY if cause == "safety" else HandoffReason.DANGER
        front.safety(state, _rt(ctx), deps=_deps(handoff=_HandoffDouble([_handoff_result(reason)])))
        sent = [
            r
            for r in caplog.records
            if r.name == "meridian.signal" and _sig(r)["name"] == "safety_reply_sent"
        ]
        assert len(sent) == 1
        rec = _sig(sent[0])
        assert rec["turn_id"] == str(TURN)
        assert rec["thread_id"] == str(THREAD)
        assert rec["request_id"] == str(REQ)
        assert rec["run_tag"] == "live"
        assert rec["node"] == "safety"
        assert rec["cause"] == cause
        assert phrase not in json.dumps(rec)
        assert phrase not in sent[0].getMessage()


def test_front_module_imports() -> None:
    """[invariant] PA-1: front.py reaches services only through deps and has no log or print path."""
    path = Path(__file__).resolve().parents[4] / "src/meridian/agent/nodes/front.py"
    tree = ast.parse(path.read_text())
    allowed = {
        "__future__", "dataclasses", "types", "typing", "langgraph.runtime", "meridian.agent.context",
        "meridian.agent.signals", "meridian.domain.handoff", "meridian.domain.identity",
        "meridian.domain.state", "meridian.domain.turn", "meridian.gates.gate", "meridian.policy.handoff",
    }  # fmt: skip
    forbidden_prefixes = (
        "logging", "sqlite3", "meridian.services", "meridian.adapters", "meridian.web", "meridian.agent.nodes",
    )  # fmt: skip
    modules: list[str] = []
    imported: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                modules.append(a.name)
                imported.setdefault(a.name, set())
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
            imported.setdefault(node.module, set()).update(a.name for a in node.names)

    def has(module_ok: Callable[[str], bool], name: str) -> bool:
        return any(module_ok(m) and name in names for m, names in imported.items())

    required = [
        ("decide_gate", lambda m: m == "meridian.gates.gate"),
        ("flags_from_state", lambda m: m == "meridian.gates.gate"),
        ("burning_card_id", lambda m: m == "meridian.gates.gate"),
        ("priority_for", lambda m: m == "meridian.policy.handoff"),
        ("emit_signal", lambda m: m == "meridian.agent.signals"),
        ("Locator", lambda m: m.startswith("meridian.domain.")),
    ]
    for name, ok in required:
        assert has(ok, name), f"required import missing: {name}"
    for m in modules:
        assert not m.startswith(forbidden_prefixes), f"forbidden import: {m}"
        assert m in allowed or m.startswith("meridian.domain."), f"import outside the allowed set: {m}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            assert not (isinstance(fn, ast.Name) and fn.id == "print"), "print call"
            assert not (isinstance(fn, ast.Attribute) and fn.attr == "get_secret_value"), "secret unwrapped"


def test_identity_without_form_or_code_calls_nothing() -> None:
    """[boundary] PA-2: with no locate form and no code the identity node calls no service and opens no transaction."""
    prev_code_card = f"code-{TURN_PREV}"
    prev_card = burning_card_id(TURN_PREV)
    cases: dict[str, tuple[Any, dict[str, Any]]] = {
        "free_text": (TextPayload(text=PLAIN), {}),
        "card_choice": (
            ChoicePayload(card_id="t-1.1", option="56"),
            {"open_tasks": [_booking_task()]},
        ),
        "burn_no": (ChoicePayload(card_id=prev_card, option="no"), {"burning_card_id": prev_card}),
        "code_card_something_else": (
            ChoicePayload(card_id=prev_code_card, option="something_else"),
            {"identity": _code_sent_state()},
        ),
    }
    for case_id, (payload, kw) in cases.items():
        idd = _IdentityDouble()
        uow = _UowDouble(_not_checked())
        state, ctx = _gated(payload, **kw)
        update = front.identity(state, _rt(ctx), deps=_deps(identity=idd, uow=uow))
        assert update == {}, case_id
        assert idd.calls == [], case_id
        assert uow.opened == [], case_id
