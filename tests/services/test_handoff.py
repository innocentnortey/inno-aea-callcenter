"""AEA-29 frozen tests: HandoffService.open (AC-1 to AC-7, AC-17). Written from the acceptance criteria, before the code.

Each test is labelled with the failure mode it guards: invariant, boundary, failure/refusal, negative, capture.
"""

from __future__ import annotations

import datetime as dt
import inspect

import pytest

from meridian.adapters.sqlite.rows import case_stream, thread_stream
from meridian.domain.common import SafetyKind
from meridian.domain.handoff import HandoffReason, Priority, Promise, SourceRef
from meridian.policy.handoff import PROMISE_TABLE, priority_for, promise_for
from meridian.services.cases import CaseService
from meridian.services.handoff import BriefAssembler, CaseWriteFailed, HandoffService
from tests.services._case_fixtures import (
    CHI,
    NOW,
    FlakyUow,
    ctx,
    guidance,
    new_thread,
    request,
    rows_for_thread,
    services,
    state_for,
    store,
    window_change,
    wp4,
    wp7,
)

ON_SHIFT = "simulated_on_shift"
OFFLINE = "nobody_online"
GUIDED = (
    HandoffReason.REFUND,
    HandoffReason.FEE_BEARING_CHANGE,
    HandoffReason.LATE_TECHNICIAN,
    HandoffReason.BILLING_DISPUTE,
    HandoffReason.COMPLAINT_OR_MANAGER,
)
WINDOWED = (HandoffReason.FEE_BEARING_CHANGE, HandoffReason.BURNING_RULED_OUT)


def _guidance_map(*reasons: HandoffReason) -> dict[HandoffReason, tuple[object, ...]]:
    return {r: (guidance(r),) for r in reasons}


def _req(tx, reason: HandoffReason, *, text: str | None = "I need help with this.", **kw):
    thread, _ = new_thread(tx, customer_text=text)
    cr = window_change() if reason in WINDOWED else None
    sk = SafetyKind.GAS if reason is HandoffReason.SAFETY else None
    return thread, request(thread, reason, change_request=cr, safety_kind=sk, **kw)


# ---------------------------------------------------------------------------------------------------------- AC-1


def test_open_writes_all_rows_in_one_transaction() -> None:
    """invariant (AC-1): cases, case_events, promises, actions, events and the guidance lookup commit together."""
    with store() as s:
        with s.uow(write=True) as tx:
            thread, req = wp7(tx)
            tx.commit()
        _, handoff, _, _ = services(s.uow, guidance_map=_guidance_map(HandoffReason.REFUND))
        handoff.open(req, ctx(thread, req.turn_id))
        with s.uow() as tx:
            assert rows_for_thread(tx, thread) == {
                "cases": 1,
                "case_events": 1,
                "promises": 1,
                "actions": 1,
                "events": 1,
                "lookup_log": 1,
            }
            events = tx.core.events.after(thread_stream(thread), 0)
            assert [e.type for e in events] == ["case_created"]
            assert tx.core.lookup_log.for_thread(thread)[0].tool == "staff_guidance"


def test_failure_after_case_row_leaves_no_rows() -> None:
    """failure/refusal (AC-1): when the write fails after the case row, nothing at all is left behind."""
    with store() as s:
        with s.uow(write=True) as tx:
            thread, req = wp7(tx)
            tx.commit()
        flaky = FlakyUow(s.uow, fail_writes=2)
        _, handoff, _, _ = services(flaky, guidance_map=_guidance_map(HandoffReason.REFUND))
        with pytest.raises(CaseWriteFailed):
            handoff.open(req, ctx(thread, req.turn_id))
        with s.uow() as tx:
            assert set(rows_for_thread(tx, thread).values()) == {0}


# ---------------------------------------------------------------------------------------------------------- AC-2


def test_second_open_returns_already_open() -> None:
    """invariant (AC-2): one open case per thread; a new reason adds one case_event and no second guidance row."""
    with store() as s:
        with s.uow(write=True) as tx:
            thread, req1 = _req(tx, HandoffReason.REFUND)
            tx.commit()
        req2 = request(thread, HandoffReason.BILLING_DISPUTE)
        _, handoff, _, _ = services(
            s.uow, guidance_map=_guidance_map(HandoffReason.REFUND, HandoffReason.BILLING_DISPUTE)
        )
        first = handoff.open(req1, ctx(thread, req1.turn_id))
        second = handoff.open(req2, ctx(thread, req2.turn_id))
        assert first.created is True and second.created is False
        assert second.case.case_ref == first.case.case_ref
        with s.uow() as tx:
            counts = rows_for_thread(tx, thread)
            kinds = [e.kind for e in tx.cases.case_events.list_for_case(first.case.case_ref)]
        assert counts["cases"] == 1 and counts["actions"] == 1 and counts["lookup_log"] == 1
        assert counts["case_events"] == 2 and kinds.count("reason_added") == 1


def test_repeat_turn_is_idempotent() -> None:
    """invariant (AC-2): the identical request (same turn_id) writes zero new rows."""
    with store() as s:
        with s.uow(write=True) as tx:
            thread, req = _req(tx, HandoffReason.REFUND)
            tx.commit()
        _, handoff, _, _ = services(s.uow, guidance_map=_guidance_map(HandoffReason.REFUND))
        first = handoff.open(req, ctx(thread, req.turn_id))
        with s.uow() as tx:
            before = rows_for_thread(tx, thread)
        again = handoff.open(req, ctx(thread, req.turn_id))
        with s.uow() as tx:
            after = rows_for_thread(tx, thread)
            version = tx.cases.cases.get(first.case.case_ref).version
        assert after == before
        assert again.case.case_ref == first.case.case_ref and version == first.case.version


def test_new_reason_raises_priority() -> None:
    """invariant (AC-2): a higher-priority second reason raises the priority, bumps the version once, alerts for P0."""
    with store() as s:
        with s.uow(write=True) as tx:
            thread, req1 = _req(tx, HandoffReason.REFUND)
            thread_b, req_b1 = _req(tx, HandoffReason.REFUND)
            tx.commit()
        _, handoff, _, _ = services(s.uow)
        first = handoff.open(req1, ctx(thread, req1.turn_id))
        with s.uow() as tx:
            changed_before = len(
                [
                    e
                    for e in tx.core.events.after(case_stream(first.case.case_ref), 0)
                    if e.type == "case_changed"
                ]
            )
        req2 = request(thread, HandoffReason.LATE_TECHNICIAN)
        assert req2.priority is Priority.P2
        second = handoff.open(req2, ctx(thread, req2.turn_id))
        assert second.case.priority is Priority.P2 and second.case.version == first.case.version + 1
        with s.uow() as tx:
            changed_after = len(
                [
                    e
                    for e in tx.core.events.after(case_stream(first.case.case_ref), 0)
                    if e.type == "case_changed"
                ]
            )
        assert changed_after == changed_before + 1
        opened = handoff.open(req_b1, ctx(thread_b, req_b1.turn_id))
        assert opened.case.priority is Priority.P3
        safety = request(thread_b, HandoffReason.SAFETY, safety_kind=SafetyKind.GAS)
        raised = handoff.open(safety, ctx(thread_b, safety.turn_id))
        assert raised.created is False and raised.case.case_ref == opened.case.case_ref
        assert raised.case.priority is Priority.P0 and raised.alert == "supervisor_now"
        with s.uow() as tx:
            assert rows_for_thread(tx, thread_b)["cases"] == 1


def test_con4_always_yields_case() -> None:
    """boundary (AC-2): the 'talk to a person' tap always yields a case, even on a greeting-only thread."""
    with store() as s:
        with s.uow(write=True) as tx:
            thread, _ = new_thread(tx)
            tx.commit()
        _, handoff, _, _ = services(s.uow)
        req1 = request(thread, HandoffReason.CUSTOMER_REQUESTED_PERSON, trigger="con4")
        first = handoff.open(req1, ctx(thread, req1.turn_id))
        req2 = request(thread, HandoffReason.CUSTOMER_REQUESTED_PERSON, trigger="con4")
        second = handoff.open(req2, ctx(thread, req2.turn_id))
        assert first.created is True
        assert second.created is False and second.case.case_ref == first.case.case_ref


# ---------------------------------------------------------------------------------------------------------- AC-3


@pytest.mark.parametrize("presence", [OFFLINE, ON_SHIFT])
@pytest.mark.parametrize("reason", list(HandoffReason))
def test_promise_matches_table(reason: HandoffReason, presence: str) -> None:
    """invariant (AC-3): the stored promise equals promise_for for every reason and presence; live-queued is stored."""
    with store() as s:
        with s.uow(write=True) as tx:
            tx.cases.demo_state.set_staffing(presence)
            thread, req = _req(tx, reason)
            tx.commit()
        _, handoff, _, _ = services(s.uow)
        result = handoff.open(req, ctx(thread, req.turn_id))
        window = req.change_request.window_start if req.change_request else None
        expected = promise_for(reason, presence, NOW, window)  # type: ignore[arg-type]
        with s.uow() as tx:
            stored = tx.cases.promises.current(result.case.case_ref)
            row = tx.cases.cases.get(result.case.case_ref)
            live_state = tx.core.conversations.lookup(str(thread)).live_state
        assert stored is not None and stored.promise == expected
        assert row is not None
        if expected.live_queued:
            assert row.lifecycle == "live_queued" and live_state == "queued"
        else:
            assert row.lifecycle == "unassigned" and live_state == "not_live"


def test_promise_literal_rows() -> None:
    """invariant (AC-3): WP-7, WP-8, danger and safety land on the literal policy rows and due times."""
    mon = dt.datetime(2026, 10, 19, 19, 0, tzinfo=CHI)
    tue = dt.datetime(2026, 10, 20, 19, 0, tzinfo=CHI)
    cases = (
        (HandoffReason.REFUND, "R26.refund", tue),
        (HandoffReason.MEMBERSHIP_CANCEL, "R26.unstaffed", mon),
        (HandoffReason.DANGER, "OD4.danger_review", mon),
        (HandoffReason.BURNING_UNCLEAR, "OD4.danger_review", mon),
        (HandoffReason.SAFETY, "R26.safety_none", None),
    )
    with store() as s:
        _, handoff, _, _ = services(s.uow)
        for reason, row, due in cases:
            with s.uow(write=True) as tx:
                thread, req = _req(tx, reason)
                tx.commit()
            result = handoff.open(req, ctx(thread, req.turn_id))
            with s.uow() as tx:
                stored = tx.cases.promises.current(result.case.case_ref)
            assert stored is not None
            assert stored.promise.policy_row == row and stored.promise.due_at == due
            assert stored.promise.text == PROMISE_TABLE[row]  # type: ignore[index]


# ---------------------------------------------------------------------------------------------------------- AC-4


def test_fee_bearing_stores_both_dues() -> None:
    """invariant (AC-4, CAS-10): case due = window start, promise due = Monday 19:00; the alert is raised."""
    with store() as s:
        with s.uow(write=True) as tx:
            thread, req = wp4(tx)
            tx.commit()
        _, handoff, _, _ = services(s.uow)
        result = handoff.open(req, ctx(thread, req.turn_id))
        with s.uow() as tx:
            row = tx.cases.cases.get(result.case.case_ref)
            promise = tx.cases.promises.current(result.case.case_ref)
        assert row is not None and promise is not None
        assert row.priority is Priority.P2
        assert row.due_at == dt.datetime(2026, 10, 16, 12, 0, tzinfo=CHI)
        assert promise.promise.due_at == dt.datetime(2026, 10, 19, 19, 0, tzinfo=CHI)
        assert result.alert == "supervisor_now"


def test_alert_for_p0_p1_and_fee_bearing() -> None:
    """invariant (AC-4, R-21): the alert is raised for exactly P0, P1 and fee_bearing_change."""
    with store() as s:
        _, handoff, _, _ = services(s.uow)
        for reason in HandoffReason:
            with s.uow(write=True) as tx:
                thread, req = _req(tx, reason)
                tx.commit()
            result = handoff.open(req, ctx(thread, req.turn_id))
            expected = (
                priority_for(reason) in (Priority.P0, Priority.P1)
                or reason is HandoffReason.FEE_BEARING_CHANGE
            )
            assert (result.alert == "supervisor_now") is expected, reason


# ---------------------------------------------------------------------------------------------------------- AC-5


def test_no_promise_text_parameter() -> None:
    """negative (AC-5): no public signature takes promise text; promise parameters are typed Promise."""
    promise_params = 0
    for cls in (HandoffService, CaseService, BriefAssembler):
        members = [
            fn
            for name, fn in inspect.getmembers(cls, inspect.isfunction)
            if not name.startswith("_") or name == "__init__"
        ]
        for fn in members:
            for name, param in inspect.signature(fn).parameters.items():
                if name == "self":
                    continue
                assert "text" not in name, f"{cls.__name__}.{fn.__name__} takes {name}"
                if "promise" in name:
                    promise_params += 1
                    assert param.annotation in (Promise, "Promise"), f"{cls.__name__}.{fn.__name__}({name})"
    assert promise_params >= 1


# ---------------------------------------------------------------------------------------------------------- AC-6


def test_safety_write_retried_once() -> None:
    """failure/refusal (AC-6): one failed write is retried; two failures raise the typed error without values."""
    with store() as s:
        with s.uow(write=True) as tx:
            thread, req = _req(tx, HandoffReason.SAFETY)
            thread2, req2 = _req(tx, HandoffReason.SAFETY)
            tx.commit()
        once = FlakyUow(s.uow, fail_writes=1)
        _, handoff, _, _ = services(once)
        result = handoff.open(req, ctx(thread, req.turn_id))
        assert result.created is True and once.write_attempts == 2
        with s.uow() as tx:
            assert rows_for_thread(tx, thread)["cases"] == 1
        twice = FlakyUow(s.uow, fail_writes=2)
        _, handoff2, _, _ = services(twice)
        with pytest.raises(CaseWriteFailed) as caught:
            handoff2.open(req2, ctx(thread2, req2.turn_id))
        assert caught.value.attempts == 2
        text = str(caught.value)
        assert str(thread2) not in text and str(req2.turn_id) not in text and "injected" not in text


def test_safety_case_without_customer() -> None:
    """boundary (AC-6): a safety case opens with no customer on the thread: one P0 row with customer_id None."""
    with store() as s:
        with s.uow(write=True) as tx:
            thread, req = _req(tx, HandoffReason.SAFETY, text="I smell gas.")
            tx.commit()
        _, handoff, _, _ = services(s.uow)
        result = handoff.open(req, ctx(thread, req.turn_id))
        with s.uow() as tx:
            rows = tx.cases.cases.list_for_thread(thread)
        assert len(rows) == 1 and rows[0].priority is Priority.P0 and rows[0].customer_id is None
        assert result.case.priority is Priority.P0


# ---------------------------------------------------------------------------------------------------------- AC-7


@pytest.mark.parametrize("reason", GUIDED)
def test_staff_guidance_attached_not_responded(reason: HandoffReason) -> None:
    """negative/security (AC-7): guidance is logged for staff only; it never reaches responder inputs."""
    g = guidance(reason)
    with store() as s:
        with s.uow(write=True) as tx:
            thread, req = _req(tx, reason, verified_customer=None)
            other, other_req = _req(tx, HandoffReason.MEMBERSHIP_CANCEL)
            tx.commit()
        _, handoff, assembler, _ = services(s.uow, guidance_map=_guidance_map(*GUIDED))
        result = handoff.open(req, ctx(thread, req.turn_id))
        with s.uow() as tx:
            rows = tx.core.lookup_log.for_thread(thread)
            assert len(rows) == 1
            row = rows[0]
            assert row.tool == "staff_guidance" and row.passage_ids == (g.passage_id,)
            assert row.result_seen == g.text_sha256 and row.record_ids == ()
            assert row.message_id == tx.core.messages.handoff_anchor(thread)
            assert row.turn_id == req.turn_id
            brief = assembler.assemble(result.case, state_for(tx, thread), rows)
            responder_inputs = tx.core.settled_for(thread, NOW).model_dump_json()
            stored_json = row.model_dump_json()
        decide = brief.headings[6]
        matches = [i for i in decide.items if i.text == g.text]
        assert matches and matches[0].sources == (SourceRef(kind="lookup_log", ref=str(row.id)),)
        assert g.text not in result.model_dump_json()
        assert g.text not in responder_inputs
        assert g.text not in stored_json
        handoff.open(other_req, ctx(other, other_req.turn_id))
        with s.uow() as tx:
            assert tx.core.lookup_log.for_thread(other) == ()


def test_staff_guidance_anchor_without_customer_text() -> None:
    """boundary/security (AC-7): with no customer message yet, the guidance row anchors on the greeting message."""
    with store() as s:
        with s.uow(write=True) as tx:
            thread, greeting = new_thread(tx)
            tx.commit()
        _, handoff, _, _ = services(s.uow, guidance_map=_guidance_map(HandoffReason.REFUND))
        req = request(thread, HandoffReason.REFUND, trigger="con4")
        handoff.open(req, ctx(thread, req.turn_id))
        with s.uow() as tx:
            rows = tx.core.lookup_log.for_thread(thread)
        assert len(rows) == 1 and rows[0].message_id == greeting


# --------------------------------------------------------------------------------------------------------- AC-17


def test_wf2_records_present() -> None:
    """capture (AC-17): every WF-2 record carries thread_id and turn_id; 'a handoff left no case' counts 0."""
    with store() as s:
        with s.uow(write=True) as tx:
            thread, req = wp7(tx)
            context = ctx(thread, req.turn_id)
            tx.core.turns.begin(context.ids, NOW)
            tx.commit()
        _, handoff, _, _ = services(s.uow, guidance_map=_guidance_map(HandoffReason.REFUND))
        result = handoff.open(req, context)
        ref = result.case.case_ref
        with s.uow(write=True) as tx:
            case = tx.cases.cases.get(ref)
            events = tx.cases.case_events.list_for_case(ref)
            promise = tx.cases.promises.current(ref)
            actions = tx.core.actions.for_thread(thread)
            stream = tx.core.events.after(thread_stream(thread), 0)
            tx.connection.execute(
                "UPDATE turns SET outcome = 'handed_off' WHERE turn_id = ?", (str(req.turn_id),)
            )
            orphans = tx.connection.execute(
                "SELECT COUNT(*) FROM turns t WHERE t.outcome = 'handed_off' "
                "AND NOT EXISTS (SELECT 1 FROM cases c WHERE c.turn_id = t.turn_id)"
            ).fetchone()[0]
        assert case is not None and case.thread_id == thread and case.turn_id == req.turn_id
        opened = [e for e in events if e.kind == "case_opened"]
        assert len(opened) == 1
        assert opened[0].detail.get("thread_id") == str(thread) and opened[0].detail.get("turn_id") == str(
            req.turn_id
        )
        assert promise is not None and promise.promise.text and promise.promise.policy_row
        assert promise.promise.due_at is not None
        assert len(actions) == 1
        key = actions[0].key
        assert (key.thread_id, key.turn_id, key.record_id) == (thread, req.turn_id, str(ref))
        assert actions[0].kind.value == "case_opened"
        created = [e for e in stream if e.type == "case_created"]
        assert len(created) == 1
        assert created[0].payload.get("thread_id") == str(thread) and created[0].payload.get(
            "turn_id"
        ) == str(req.turn_id)
        assert orphans == 0


def test_presence_read_inside_transaction() -> None:
    """invariant (plan-added): presence is read through the one write unit of work, which then commits."""
    with store() as s:
        with s.uow(write=True) as tx:
            thread, req = _req(tx, HandoffReason.REFUND)
            tx.commit()
        _, handoff, _, demo = services(s.uow)
        handoff.open(req, ctx(thread, req.turn_id))
        assert len(demo.seen) == 1
        assert demo.seen[0].committed is True  # type: ignore[attr-defined]
