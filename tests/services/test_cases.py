"""AEA-29 frozen tests: CaseService (AC-8 to AC-16, AC-18 to AC-21, AC-23). Written from the acceptance criteria.

Labels: invariant, boundary, failure/refusal, negative, regression. Phone numbers and emails are read from the issued
data at run time; none is written in this file.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest

from meridian.adapters.sqlite.rows import case_stream, thread_stream
from meridian.domain.handoff import HandoffReason
from meridian.domain.staff import CUSTOMER_SPEAKER_NAME, StaffRole, actor_for
from meridian.domain.state import Controller
from meridian.policy.handoff import business_due, due_label, promise_for
from meridian.policy.texts import TEXTS, TextId
from meridian.services._case_rules import CON13_ACTIONS, LANE_ORDER, actions_for
from tests.fakes.clock import FixedClock
from tests.services._allowed_actions_table import REPRESENTATIVE_EXAMPLES, TABLE
from tests.services._case_fixtures import (
    CHI,
    DISPLAY_NOW,
    NOW,
    OMAR,
    OMAR_MESSAGE,
    STAFF_ROLES,
    BlockRecorder,
    activity_in,
    case_action,
    case_in_state,
    code_of,
    contact_of,
    ctx,
    display_case,
    followup_choice,
    guidance,
    is_rejected,
    j,
    jtext,
    new_thread,
    request,
    seed_shaped,
    services,
    set_identity,
    state_for,
    store,
    summary_of,
    thread_of,
    window_change,
    wp4,
    wp7,
)

REP, SUP, OWN = StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR, StaffRole.OWNER
ON_SHIFT, OFFLINE = "simulated_on_shift", "nobody_online"
LATER = NOW + dt.timedelta(hours=1)


def _version(s: Any, ref: Any) -> int:
    with s.uow() as tx:
        return int(tx.cases.cases.get(ref).version)


def _state(s: Any, ref: Any) -> tuple[Any, ...]:
    """Everything an unchanged case must keep: row, case events, case stream."""
    with s.uow() as tx:
        stream = tuple((e.id, e.type) for e in tx.core.events.after(case_stream(ref), 0))
        return tx.cases.cases.get(ref), tx.cases.case_events.list_for_case(ref), stream


def _made(s: Any, **kw: Any) -> Any:
    with s.uow(write=True) as tx:
        ref = case_in_state(tx, **kw)
        tx.commit()
    return ref


def _seeded(s: Any) -> dict[int, Any]:
    with s.uow(write=True) as tx:
        refs = seed_shaped(tx)
        tx.commit()
    return refs


def _keys(node: Any) -> set[str]:
    if isinstance(node, dict):
        return set(node) | {k for v in node.values() for k in _keys(v)}
    if isinstance(node, list):
        return {k for v in node for k in _keys(v)}
    return set()


def _values_of(node: Any, key: str) -> list[Any]:
    if isinstance(node, dict):
        found = [node[key]] if key in node else []
        return found + [x for v in node.values() for x in _values_of(v, key)]
    if isinstance(node, list):
        return [x for v in node for x in _values_of(v, key)]
    return []


# ---------------------------------------------------------------------------------------------------------- AC-8


def test_unstaffed_never_live_queued() -> None:
    """invariant (AC-8, R-30): with nobody online no reason yields a live-queued case."""
    with store() as s:
        _, handoff, _, _ = services(s.uow)
        for reason in HandoffReason:
            with s.uow(write=True) as tx:
                thread, _ = new_thread(tx, customer_text="I need a person.")
                tx.commit()
            req = request(
                thread,
                reason,
                change_request=window_change()
                if reason.value in ("fee_bearing_change", "burning_ruled_out")
                else None,
            )
            handoff.open(req, ctx(thread, req.turn_id))
        with s.uow() as tx:
            queued = tx.connection.execute(
                "SELECT COUNT(*) FROM cases WHERE lifecycle = 'live_queued'"
            ).fetchone()[0]  # type: ignore[attr-defined]
            live = tx.connection.execute(
                "SELECT COUNT(*) FROM conversations WHERE live_state = 'queued'"
            ).fetchone()[0]  # type: ignore[attr-defined]
        assert queued == 0 and live == 0


def _staged(s: Any, recorder: BlockRecorder | None = None) -> tuple[Any, list[Any], Any]:
    """One unassigned refund (opened offline) and two live-queued person requests (opened on shift)."""
    cases, handoff, _, _ = services(s.uow, handoff_block=recorder)
    with s.uow(write=True) as tx:
        tx.cases.demo_state.set_staffing(OFFLINE)
        t0, _ = new_thread(tx, customer_text="I want a refund.")
        tx.commit()
    r0 = request(t0, HandoffReason.REFUND)
    refund = handoff.open(r0, ctx(t0, r0.turn_id))
    queued = []
    for _ in range(2):
        with s.uow(write=True) as tx:
            tx.cases.demo_state.set_staffing(ON_SHIFT)
            t, _ = new_thread(tx, customer_text="I need a person.")
            tx.commit()
        r = request(t, HandoffReason.CUSTOMER_REQUESTED_PERSON)
        res = handoff.open(r, ctx(t, r.turn_id))
        assert res.case.state == "live_queued"
        queued.append(res.case)
    with s.uow(write=True) as tx:
        tx.cases.demo_state.set_staffing(OFFLINE)
        tx.commit()
    return cases, queued, refund.case


def test_convert_live_queued() -> None:
    """invariant (AC-8): a shift end converts every live-queued case in place; events, history and promise follow."""
    with store() as s:
        recorder = BlockRecorder()
        cases, queued, refund = _staged(s, recorder)
        assert cases.convert_live_queued(LATER) == 2
        with s.uow() as tx:
            for before in queued:
                row = tx.cases.cases.get(before.case_ref)
                assert row.lifecycle == "unassigned" and row.created_at == before.created_at
                assert row.version == before.version + 1
                current = tx.cases.promises.current(before.case_ref)
                assert current.promise.policy_row == "R26.unstaffed" and current.status == "changed"
                assert current.promise.due_at == business_due(LATER, 1)
                assert current.promise == promise_for(before.reason, "nobody_online", LATER)
                assert any(
                    p.promise.text == before.promise.text for p in tx.cases.promises.history(before.case_ref)
                )
                thread = row.thread_id
                assert tx.core.conversations.lookup(str(thread)).live_state == "not_live"
                shift = [e for e in tx.core.events.after(thread_stream(thread), 0) if e.type == "shift_ended"]
                assert len(shift) == 1 and shift[0].payload["line"] == TEXTS[TextId.SHIFT_ENDED]
                assert shift[0].payload["handoff"] in [b.model_dump(mode="json") for b in recorder.blocks]
                stream = tx.core.events.after(case_stream(before.case_ref), 0)
                closed = [e for e in stream if e.type == "chat_closed"]
                assert len(closed) == 1 and closed[0].payload["reason"] == "shift_ended"
                assert any(e.type == "case_changed" for e in stream)
            untouched = tx.cases.cases.get(refund.case_ref)
        assert untouched.version == refund.version and untouched.lifecycle == "unassigned"


def test_convert_joins_caller_transaction() -> None:
    """invariant (AC-8): with tx given the conversion lives and dies with the caller's transaction."""
    with store() as s:
        cases, queued, _ = _staged(s)
        with s.uow(write=True) as tx:
            assert cases.convert_live_queued(LATER, tx) == 2
        for q in queued:
            with s.uow() as tx:
                assert tx.cases.cases.get(q.case_ref).lifecycle == "live_queued"
        with s.uow(write=True) as tx:
            assert cases.convert_live_queued(LATER, tx) == 2
            tx.commit()
        for q in queued:
            with s.uow() as tx:
                assert tx.cases.cases.get(q.case_ref).lifecycle == "unassigned"


# ---------------------------------------------------------------------------------------------------------- AC-9

_REJECTIONS = (
    ("stale_version", "unassigned", None, REP, "claim", {}, 1, "VERSION_CONFLICT"),
    ("already_claimed", "claimed", SUP, REP, "claim", {}, 3, "CASE_ALREADY_CLAIMED"),
    ("release_no_reason", "claimed", REP, REP, "release", {}, 3, "REASON_REQUIRED"),
    ("close_no_reason", "claimed", REP, REP, "close_unresolved", {}, 3, "REASON_REQUIRED"),
    ("assign_no_reason", "unassigned", None, SUP, "assign", {"assignee": "riley"}, 3, "REASON_REQUIRED"),
    (
        "priority_no_reason",
        "unassigned",
        None,
        SUP,
        "change_priority",
        {"priority": "P2"},
        3,
        "REASON_REQUIRED",
    ),
    ("wait_no_wake_up", "claimed", REP, REP, "wait", {}, 3, "WAKE_UP_REQUIRED"),
    ("resolve_no_outcome", "claimed", REP, REP, "resolve", {}, 3, "OUTCOME_REQUIRED"),
    (
        "resolve_unassigned",
        "unassigned",
        None,
        REP,
        "resolve",
        {"outcome": "Done"},
        3,
        "NOT_ALLOWED_IN_STATE",
    ),
    (
        "assign_by_rep",
        "unassigned",
        None,
        REP,
        "assign",
        {"assignee": "riley", "reason": "r"},
        3,
        "ROLE_NOT_ALLOWED",
    ),
    (
        "priority_by_rep",
        "unassigned",
        None,
        REP,
        "change_priority",
        {"priority": "P2", "reason": "r"},
        3,
        "ROLE_NOT_ALLOWED",
    ),
)


@pytest.mark.parametrize(
    ("name", "lifecycle", "owner", "role", "action", "extra", "sent", "code"),
    _REJECTIONS,
    ids=[r[0] for r in _REJECTIONS],
)
def test_apply_rejections(
    name: str,
    lifecycle: str,
    owner: Any,
    role: StaffRole,
    action: str,
    extra: dict[str, Any],
    sent: int,
    code: str,
) -> None:
    """failure/refusal (AC-9): each rule answers its named code and changes no row."""
    with store() as s:
        cases, _, _, _ = services(s.uow)
        ref = _made(
            s, lifecycle=lifecycle, owner_role=owner, live_state="not_live", staffing=OFFLINE, version=3
        )
        before = _state(s, ref)
        result = cases.apply(ref, case_action(action, sent, **extra), actor_for(role), sent, NOW)
        assert is_rejected(result) and code_of(result) == code
        body = j(result)
        if code == "VERSION_CONFLICT":
            assert {"changed_by", "changed_at", "current_version"} <= set(body["details"])
            assert body["details"]["current_version"] == 3
        if code == "CASE_ALREADY_CLAIMED":
            assert body["details"]["claimed_by"] == "Demo supervisor"
        if code == "NOT_ALLOWED_IN_STATE":
            assert body["details"] == {"state": "unassigned", "needs": "claimed"}
        assert _state(s, ref) == before


def test_apply_success_writes_event() -> None:
    """invariant (AC-9): a success bumps the version, writes one action event and one case_changed; names are personas."""
    with store() as s:
        cases, _, _, _ = services(s.uow)
        ref = _made(
            s, lifecycle="unassigned", owner_role=None, live_state="not_live", staffing=OFFLINE, version=3
        )
        _, events_before, stream_before = _state(s, ref)
        result = cases.apply(ref, case_action("claim", 3), actor_for(REP), 3, NOW)
        assert not is_rejected(result)
        assert j(result)["owner"] == "Riley" and j(result)["version"] == 4
        _, events, stream = _state(s, ref)
        claims = [e for e in events if e.kind == "action:claim"]
        assert len(claims) == 1 and claims[0].actor_role == "representative"
        assert [t for _, t in stream].count("case_changed") - [t for _, t in stream_before].count(
            "case_changed"
        ) == 1
        assert len(events) == len(events_before) + 1
        riley = _made(s, lifecycle="unassigned", owner_role=None, live_state="not_live", staffing=OFFLINE)
        boss = _made(s, lifecycle="unassigned", owner_role=None, live_state="not_live", staffing=OFFLINE)
        assigned = cases.apply(
            riley,
            case_action("assign", 3, assignee="riley", reason="Balance the load"),
            actor_for(SUP),
            3,
            NOW,
        )
        assert j(assigned)["owner"] == "Riley"
        assigned = cases.apply(
            boss, case_action("assign", 3, assignee="supervisor", reason="Mine"), actor_for(SUP), 3, NOW
        )
        assert j(assigned)["owner"] == "Demo supervisor"
        mine = _made(s, lifecycle="claimed", owner_role=REP, live_state="not_live", staffing=OFFLINE)
        with s.uow() as tx:
            phone, digits, _email = contact_of(tx)
        released = cases.apply(
            mine,
            case_action("release", 3, reason=f"Customer asked me to call {phone}"),
            actor_for(REP),
            3,
            NOW,
        )
        assert not is_rejected(released)
        with s.uow() as tx:
            text = " ".join(e.model_dump_json() for e in tx.cases.case_events.list_for_case(mine))
        assert phone not in text and digits not in text


# --------------------------------------------------------------------------------------------------------- AC-10


def test_promise_status_kept_and_missed() -> None:
    """invariant (AC-10): kept / missed / open follow the promise due on the demo clock; each change is an event."""
    after = FixedClock(NOW).advanced(dt.timedelta(days=4)).now()
    with store() as s:
        cases, _, _, _ = services(s.uow)

        def mk(**kw: Any) -> Any:
            return _made(
                s, lifecycle="claimed", owner_role=REP, live_state="not_live", staffing=OFFLINE, **kw
            )

        resolve_before, resolve_after, reached, left, no_answer = mk(), mk(), mk(), mk(), mk()
        safety = mk(reason=HandoffReason.SAFETY)
        rep = actor_for(REP)
        steps = (
            (
                resolve_before,
                lambda r: cases.apply(r, case_action("resolve", 3, outcome="Done"), rep, 3, NOW),
                "kept",
            ),
            (
                resolve_after,
                lambda r: cases.apply(r, case_action("resolve", 3, outcome="Done"), rep, 3, after),
                "missed",
            ),
            (
                reached,
                lambda r: cases.record_activity(r, activity_in("call", "reached", 3), rep, NOW),
                "kept",
            ),
            (
                left,
                lambda r: cases.record_activity(r, activity_in("email", "left_message", 3), rep, NOW),
                "kept",
            ),
            (
                no_answer,
                lambda r: cases.record_activity(r, activity_in("call", "no_answer", 3), rep, NOW),
                "open",
            ),
            (
                safety,
                lambda r: cases.apply(r, case_action("resolve", 3, outcome="Done"), rep, 3, NOW),
                "kept",
            ),
        )
        for ref, act, expected in steps:
            assert not is_rejected(act(ref)), expected
            with s.uow() as tx:
                status = tx.cases.promises.current(ref).status
                changes = [e.detail.get("promise_status_to") for e in tx.cases.case_events.list_for_case(ref)]
            assert status == expected
            if expected == "open":
                assert not [c for c in changes if c]
            else:
                assert expected in changes


# --------------------------------------------------------------------------------------------------------- AC-11


def test_queue_ordering() -> None:
    """invariant (AC-11): P0 first, then overdue, then by case due; no-due rows sit with their priority."""
    with store() as s:
        refs = _seeded(s)
        cases, _, _, _ = services(s.uow)
        view = j(cases.queue(REP, NOW))
        rows = view["needs_my_action"]
        assert [r["reference"] for r in rows] == [str(refs[n]) for n in (8, 5, 6, 7)]
        assert [r["due_state"] for r in rows] == ["no_due_time", "overdue", "on_time", "on_time"]
        assert view["live"] == []


def test_oversight_lanes_fixed_order() -> None:
    """invariant (AC-11): five lanes in fixed order, each case in the first lane it qualifies for, empty lanes kept."""
    with store() as s:
        refs = _seeded(s)
        cases, _, _, _ = services(s.uow)
        view = j(cases.oversight(NOW))
        assert list(view["lanes"]) == list(LANE_ORDER)
        names = {lane: [r["reference"] for r in body["rows"]] for lane, body in view["lanes"].items()}
        assert names == {
            "p0_p1": [str(refs[8])],
            "overdue": [str(refs[5])],
            "due_soon": [],
            "unowned": [str(refs[6]), str(refs[7])],
            "stuck_waiting": [],
        }
        assert all(body["count"] == len(body["rows"]) for body in view["lanes"].values())
        assert view["new_flags_count"] == 0


def test_detail_current_value_changed() -> None:
    """invariant (AC-11): a source shows the current value; a later change flags the source and the items citing it."""
    with store() as s:
        refs = _seeded(s)
        cases, _, _, _ = services(s.uow)
        with s.uow() as tx:
            row = next(
                r for r in tx.core.lookup_log.for_thread(thread_of(tx, refs[7])) if r.tool == "read_invoices"
            )

        def invoice_source() -> tuple[dict[str, Any], dict[str, Any]]:
            body = j(cases.detail(refs[7], REP, NOW))
            return next(x for x in body["sources"] if x["lookup_log_id"] == f"ll-{row.id}"), body

        source, _ = invoice_source()
        assert source["changed_since"] is False and source["current"] is not None
        with s.uow(write=True) as tx:
            tx.connection.execute("UPDATE invoices SET balance_cents = 0 WHERE invoice_id = 'INV-204411'")  # type: ignore[attr-defined]
            tx.commit()
        source, body = invoice_source()
        assert source["changed_since"] is True and source["changed_note"].startswith(
            "Changed since the AI saw it"
        )
        citing = [
            i for h in body["brief"]["headings"] for i in h["items"] if source["source_id"] in i["source_ids"]
        ]
        assert citing and all(i["changed"] for i in citing)


# --------------------------------------------------------------------------------------------------------- AC-12


def _verified_case(s: Any, handoff: Any, reason: HandoffReason = HandoffReason.REFUND) -> tuple[Any, Any]:
    with s.uow(write=True) as tx:
        thread, _ = new_thread(tx, customer_text="Please call me back.")
        set_identity(tx, thread, "verified", OMAR)
        tx.commit()
    req = request(thread, reason, verified_customer=OMAR)
    return thread, handoff.open(req, ctx(thread, req.turn_id)).case


def test_set_followup_rules() -> None:
    """failure/refusal + security (AC-12): refusals, the four stored fields, the masked label."""
    with store() as s:
        cases, handoff, _, _ = services(s.uow)
        choice = followup_choice("phone", "on_record", "morning")
        with s.uow(write=True) as tx:
            lone, _ = new_thread(tx, customer_text="Hello.")
            unverified, _ = new_thread(tx, customer_text="Call me.")
            tx.commit()
        refused = cases.set_followup(lone, choice, NOW)
        assert is_rejected(refused) and code_of(refused) == "NOT_ALLOWED_IN_STATE"
        assert j(refused)["details"] == {"state": "no_open_case"}
        req = request(unverified, HandoffReason.REFUND)
        opened = handoff.open(req, ctx(unverified, req.turn_id)).case
        refused = cases.set_followup(unverified, choice, NOW)
        assert is_rejected(refused) and code_of(refused) == "NOT_ALLOWED_IN_STATE"
        assert j(refused)["details"] == {"state": "not_verified"}
        with s.uow() as tx:
            assert tx.cases.followups.get(opened.case_ref) is None
        thread, case = _verified_case(s, handoff)
        saved = cases.set_followup(thread, choice, NOW)
        assert not is_rejected(saved)
        with s.uow() as tx:
            stored = tx.cases.followups.get(case.case_ref)
            phone, digits, email = contact_of(tx)
        assert (stored.channel, stored.destination, stored.on_record, stored.window) == (
            "phone",
            "on_record",
            True,
            "morning",
        )
        assert saved.destination_label == "the number ending in 02"
        assert saved.saved_line == "Follow-up saved: phone call, the number ending in 02, mornings."
        for blob in (jtext(saved), stored.model_dump_json()):
            assert phone not in blob and digits not in blob and email not in blob


# --------------------------------------------------------------------------------------------------------- AC-13


def test_no_contact_values_in_views() -> None:
    """negative + security (AC-13): no phone, email or address in any staff view or case_event."""
    with store() as s:
        refs = _seeded(s)
        cases, handoff, _, _ = services(
            s.uow, guidance_map={HandoffReason.BILLING_DISPUTE: (guidance(HandoffReason.BILLING_DISPUTE),)}
        )
        with s.uow(write=True) as tx:
            phone, digits, email = contact_of(tx)
            tx.core.messages.append(
                thread_of(tx, refs[7]), "customer", f"Reach me at {phone} or {email}", NOW
            )
            thread, _ = new_thread(tx, customer_text="I dispute this bill.")
            set_identity(tx, thread, "verified", OMAR)
            tx.commit()
        with s.uow() as tx:
            version = tx.cases.cases.get(refs[7]).version
        claimed = cases.apply(
            refs[7], case_action("claim", version, reason=f"Will call {phone}"), actor_for(REP), version, NOW
        )
        assert not is_rejected(claimed)
        req = request(thread, HandoffReason.BILLING_DISPUTE, verified_customer=OMAR)
        guided = handoff.open(req, ctx(thread, req.turn_id)).case
        views = {
            "queue": j(cases.queue(REP, NOW)),
            "oversight": j(cases.oversight(NOW)),
            "detail": j(cases.detail(refs[7], REP, NOW)),
            "guided": j(cases.detail(guided.case_ref, REP, NOW)),
        }
        with s.uow() as tx:
            events = " ".join(e.model_dump_json() for e in tx.cases.case_events.list_for_case(refs[7]))
            rows = {r.id: r for r in tx.core.lookup_log.for_thread(thread)}
        for blob in (*(jtext_of(v) for v in views.values()), events):
            assert phone not in blob and digits not in blob and email not in blob
        for name in ("queue", "oversight"):
            assert not ({"phone", "email", "address"} & _keys(views[name]))
        for source in views["detail"]["sources"]:
            assert source["audience"] == "customer"
        audiences = {src["lookup_log_id"]: src["audience"] for src in views["guided"]["sources"]}
        assert rows and all(
            audiences[f"ll-{i}"] == ("staff_only" if r.tool == "staff_guidance" else "customer")
            for i, r in rows.items()
        )
        assert any(a == "staff_only" for a in audiences.values())


def jtext_of(data: Any) -> str:
    import json

    return json.dumps(data, ensure_ascii=False)


# --------------------------------------------------------------------------------------------------------- AC-14


def test_activity_recorded_not_sent() -> None:
    """negative (AC-14): the fixed label everywhere; unclaimed refused; no wording that claims a send."""
    with store() as s:
        cases, handoff, _, _ = services(s.uow)
        open_ref = _made(s, lifecycle="unassigned", owner_role=None, live_state="not_live", staffing=OFFLINE)
        refused = cases.record_activity(open_ref, activity_in("call", "reached", 3), actor_for(REP), NOW)
        assert is_rejected(refused) and code_of(refused) == "NOT_ALLOWED_IN_STATE"
        claimed = _made(s, lifecycle="claimed", owner_role=REP, live_state="not_live", staffing=OFFLINE)
        done = cases.record_activity(
            claimed, activity_in("call", "reached", 3, "Explained the review"), actor_for(REP), NOW
        )
        assert not is_rejected(done)
        assert (
            j(done)["activity"]["label"] == "Demo: recorded, not sent"
            and j(done)["activity"]["by"] == "Riley (demo)"
        )
        detail = j(cases.detail(claimed, REP, NOW))
        assert detail["activities"] and all(
            a["label"] == "Demo: recorded, not sent" for a in detail["activities"]
        )
        thread, _case = _verified_case(s, handoff)
        saved = cases.set_followup(thread, followup_choice("phone", "on_record", "morning"), NOW)
        blob = (jtext(done) + jtext(saved)).lower()
        for phrase in ("sent you", "emailed you", "called you"):
            assert phrase not in blob


# --------------------------------------------------------------------------------------------------------- AC-15


def test_attach_brief_upserts() -> None:
    """invariant (AC-15): a second attach replaces the stored brief; one row per case."""
    with store() as s:
        cases, _, assembler, _ = services(s.uow)
        ref = _made(s, lifecycle="unassigned", owner_role=None, live_state="not_live", staffing=OFFLINE)
        with s.uow() as tx:
            thread = thread_of(tx, ref)
            draft = assembler.assemble(
                summary_of(tx, ref), state_for(tx, thread), tx.core.lookup_log.for_thread(thread)
            )
        assert draft.status == "being_written"
        cases.attach_brief(ref, draft)
        cases.attach_brief(ref, draft.model_copy(update={"status": "ready"}))
        with s.uow() as tx:
            assert tx.cases.briefs.get(ref).status == "ready"
            count = tx.connection.execute(
                "SELECT COUNT(*) FROM case_briefs WHERE case_ref = ?", (str(ref),)
            ).fetchone()[0]  # type: ignore[attr-defined]
        assert count == 1


# --------------------------------------------------------------------------------------------------------- AC-18


def _accepted(result: Any) -> bool:
    return not is_rejected(result)


def _arguments(action: str, now: dt.datetime) -> dict[str, Any]:
    return {
        "release": {"reason": "Handing it back"},
        "close_unresolved": {"reason": "Customer unreachable"},
        "assign": {"reason": "Balance the load", "assignee": "riley"},
        "change_priority": {"reason": "More urgent", "priority": "P2"},
        "wait": {"wake_up_at": (now + dt.timedelta(days=1)).isoformat()},
        "resolve": {"outcome": "Done"},
    }.get(action, {})


def _live_double(
    action: str, role: StaffRole, lifecycle: str, owner: StaffRole | None, live_state: str
) -> bool:
    """What LiveChatService accepts (staff.md section 5)."""
    if role is not REP:
        return False
    if action == "claim_and_join":
        return lifecycle == "live_queued" and owner is None and live_state == "queued"
    if action == "join_chat":
        return owner is REP and live_state == "queued"
    return owner is REP and live_state == "joined"  # send_live_message, hand_back, close_chat


def test_allowed_actions_listed_iff_accepted() -> None:
    """invariant (AC-18): an action is listed exactly when the server accepts it, for each role and state."""
    refusals = {"ROLE_NOT_ALLOWED", "NOT_ALLOWED_IN_STATE", "CASE_ALREADY_CLAIMED"}
    mismatches: list[str] = []
    live_keys = ("claim_and_join", "join_chat", "send_live_message", "hand_back", "close_chat")
    with store() as s:
        cases, _, _, _ = services(s.uow)
        for row, lifecycle, owner, live_state, staffing, rep_list, sup_list, own_list in TABLE:
            expected = {REP: rep_list, SUP: sup_list, OWN: own_list}
            for role in STAFF_ROLES:
                state = {
                    "lifecycle": lifecycle,
                    "owner_role": owner,
                    "live_state": live_state,
                    "staffing": staffing,
                }
                listed = list(actions_for(**state, actor_role=role))
                assert listed == expected[role], f"{row} {role}"
                ref = _made(s, **state)
                assert j(cases.detail(ref, role, NOW))["case"]["allowed_actions"] == listed, (
                    f"{row} {role} detail"
                )
                actor = actor_for(role)
                for action in CON13_ACTIONS:
                    target = _made(s, **state)
                    result = cases.apply(
                        target, case_action(action, 3, **_arguments(action, NOW)), actor, 3, NOW
                    )
                    if (action in listed) != _accepted(result):
                        mismatches.append(f"{row} {role.value} {action}")
                    if not _accepted(result):
                        assert code_of(result) in refusals, f"{row} {role.value} {action}: {code_of(result)}"
                for action in live_keys:
                    if (action in listed) != _live_double(action, role, lifecycle, owner, live_state):
                        mismatches.append(f"{row} {role.value} {action} (live)")
                for action, kind in (("log_call", "call"), ("log_email", "email")):
                    target = _made(s, **state)
                    result = cases.record_activity(target, activity_in(kind, "reached", 3), actor, NOW)
                    if (action in listed) != _accepted(result):
                        mismatches.append(f"{row} {role.value} {action}")
                if ("flag" in listed) != (role in (REP, SUP)):
                    mismatches.append(f"{row} {role.value} flag")
    assert mismatches == []


def test_allowed_actions_match_representative_examples() -> None:
    """regression (AC-18): the four signed representative examples, in order."""
    for name, (lifecycle, owner, live_state, staffing, expected) in REPRESENTATIVE_EXAMPLES.items():
        got = actions_for(
            lifecycle=lifecycle, owner_role=owner, live_state=live_state, staffing=staffing, actor_role=REP
        )
        assert list(got) == expected, name


def test_allowed_actions_by_role() -> None:
    """invariant (AC-18, R-G-16): the owner gets nothing; the supervisor never chats or logs; the rep never assigns."""
    supervisor_never = {
        "claim_and_join",
        "join_chat",
        "send_live_message",
        "hand_back",
        "close_chat",
        "log_call",
        "log_email",
    }
    for row, lifecycle, owner, live_state, staffing, _r, _s, _o in TABLE:
        state = {"lifecycle": lifecycle, "owner_role": owner, "live_state": live_state, "staffing": staffing}
        assert list(actions_for(**state, actor_role=OWN)) == [], row
        assert not supervisor_never & set(actions_for(**state, actor_role=SUP)), row
        rep = set(actions_for(**state, actor_role=REP))
        assert not {"assign", "change_priority"} & rep, row
        assert ("claim_and_join" in rep) == (row == "T01"), row


# --------------------------------------------------------------------------------------------------------- AC-19

_EXAMPLE_CASE = {
    "reference": "MHC-C-0007",
    "reason": "Billing dispute",
    "priority": {"level": "P3", "word": "Standard"},
    "lifecycle": "unassigned",
    "owner": None,
    "created_at": "2026-10-16T14:14:00-05:00",
    "due_at": "2026-10-19T19:00:00-05:00",
    "due_label": "Mon Oct 19 · 7:00 pm",
    "due_state": "on_time",
    "wake_up_at": None,
    "promise_status": "open",
    "seed": True,
    "version": 3,
    "allowed_actions": ["claim", "flag"],
}
_EXAMPLE_PROMISE = {
    "due_at": "2026-10-19T19:00:00-05:00",
    "due_label": "Mon Oct 19 · 7:00 pm",
    "status": "open",
    "history": [],
    "text": "No representative is online right now. A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm. Your reference is MHC-C-0007.",
    "policy_row": "nobody_online_1_business_day",
}
# Listed differences, with the reason each differs (asserted exactly):
_DIFFERENCES = {
    "case.due_label",  # cases 3.1: policy/handoff.due_label is the producer; the example's short form is illustrative
    "case.version",  # STF-18: the example's version is illustrative
    "promise.due_label",  # same producer as case.due_label
    "promise.text",  # the example's wording is illustrative; ours is the policy table's
    "promise.policy_row",  # the example's row name is illustrative; ours is the table's
}


def _same(a: Any, b: Any) -> bool:
    if isinstance(a, str) and isinstance(b, str) and a != b:
        try:
            return dt.datetime.fromisoformat(a) == dt.datetime.fromisoformat(b)
        except ValueError:
            return False
    return bool(a == b)


def test_display_values_match_openapi_examples() -> None:
    """invariant (AC-19): one producer per display value; equal to the signed examples except the listed differences."""
    with store() as s:
        with s.uow(write=True) as tx:
            ref = display_case(tx)
            tx.commit()
        cases, handoff, _, _ = services(s.uow)
        body = j(cases.detail(ref, REP, DISPLAY_NOW))
        row = next(
            r for r in j(cases.queue(REP, DISPLAY_NOW))["needs_my_action"] if r["reference"] == str(ref)
        )
        differing = {f"case.{k}" for k, v in _EXAMPLE_CASE.items() if not _same(body["case"].get(k), v)}
        differing |= {
            f"promise.{k}" for k, v in _EXAMPLE_PROMISE.items() if not _same(body["promise"].get(k), v)
        }
        assert differing == _DIFFERENCES
        assert body["case"]["due_label"] == due_label(dt.datetime(2026, 10, 19, 19, 0, tzinfo=CHI))
        assert body["case"]["reason"] != "billing_dispute"
        assert row["customer_display_name"] == "Omar Patel" and row["follow_up_short"] == "Phone · mornings"
        assert (
            row["queued_at"] is None and row["age_label"] == "Open 6 min" and row["brief_status"] == "ready"
        )
        assert (row["reason"], row["priority"], row["due_state"], row["seed"]) == (
            "Billing dispute",
            {"level": "P3", "word": "Standard"},
            "on_time",
            True,
        )
        assert body["identity"]["demo_note"] == "Demo simulation" and body["identity"]["status"] == "verified"
        invoice = next(x for x in body["sources"] if x["ref"] == "invoices/INV-204411")
        assert invoice["version_label"] == "live record"
        assert (
            body["promise"]["follow_up"]["channel"] == "phone"
            and body["promise"]["follow_up"]["window"] == "morning"
        )
        assert body["promise"]["follow_up"]["on_record"] is True
        with s.uow(write=True) as tx:
            thread, req = wp4(tx)
            tx.commit()
        window_case = handoff.open(req, ctx(thread, req.turn_id)).case
        fee = j(cases.detail(window_case.case_ref, REP, NOW))["case"]
        assert (
            fee["due_label"] == due_label(dt.datetime(2026, 10, 16, 12, 0, tzinfo=CHI)) + ", the window start"
        )


def test_every_brief_source_id_resolves() -> None:
    """invariant (AC-19): every brief source id names a source of the same CaseDetail."""
    with store() as s:
        refs = _seeded(s)
        cases, handoff, assembler, _ = services(
            s.uow,
            guidance_map={
                HandoffReason.REFUND: (guidance(HandoffReason.REFUND),),
                HandoffReason.FEE_BEARING_CHANGE: (guidance(HandoffReason.FEE_BEARING_CHANGE),),
            },
        )
        wanted = list(refs.values())
        for make in (wp4, wp7):
            with s.uow(write=True) as tx:
                thread, req = make(tx)
                tx.commit()
            case = handoff.open(req, ctx(thread, req.turn_id)).case
            with s.uow() as tx:
                brief = assembler.assemble(case, state_for(tx, thread), tx.core.lookup_log.for_thread(thread))
            cases.attach_brief(case.case_ref, brief)
            wanted.append(case.case_ref)
        cited = 0
        for ref in wanted:
            body = j(cases.detail(ref, REP, NOW))
            known = {x["source_id"] for x in body["sources"]}
            ids = [i for h in body["brief"]["headings"] for item in h["items"] for i in item["source_ids"]]
            cited += len(ids)
            assert [i for i in ids if i not in known] == [], str(ref)
        assert cited >= 1


# --------------------------------------------------------------------------------------------------------- AC-20


def test_staff_conversation_customer_unnamed() -> None:
    """negative + security (AC-20): customer lines speak as 'Customer', never 'You'."""
    with store() as s:
        refs = _seeded(s)
        cases, _, _, _ = services(s.uow)
        lines = j(cases.detail(refs[7], REP, NOW))["conversation"]
        customer = [x for x in lines if x["speaker"]["kind"] == "customer"]
        assert customer and OMAR_MESSAGE in {x["text"] for x in customer}
        assert all(
            x["speaker"] == {"kind": "customer", "display_name": CUSTOMER_SPEAKER_NAME} for x in customer
        )


def test_customer_speaker_name() -> None:
    """negative + security (AC-20): no display_name in the whole CaseDetail is 'You', 'Omar' or 'Omar Patel'."""
    with store() as s:
        refs = _seeded(s)
        cases, _, _, _ = services(s.uow)
        names = _values_of(j(cases.detail(refs[7], REP, NOW)), "display_name")
        assert names and not {"You", "Omar", "Omar Patel"} & {n for n in names if n is not None}


# --------------------------------------------------------------------------------------------------------- AC-21


def test_conversation_writes_keep_case_version() -> None:
    """invariant (AC-21): live chat's conversation writes change neither version nor lifecycle, and add no case_changed."""
    with store() as s:
        cases, _, _, _ = services(s.uow)
        ref = _made(
            s, lifecycle="claimed", owner_role=REP, live_state="not_live", staffing=ON_SHIFT, version=5
        )
        before = [t for _, t in _state(s, ref)[2]].count("case_changed")
        with s.uow(write=True) as tx:
            thread = thread_of(tx, ref)
            convo = tx.core.conversations
            convo.set_controller(
                thread,
                Controller(kind="human", representative_name="Riley", case_ref=ref),
                live_state="joined",
                live_since=NOW,
            )
            tx.core.messages.append(thread, "representative", "Hello, this is Riley.", NOW)
            convo.set_controller(thread, Controller(kind="ai"), live_state="handed_back", live_since=NOW)
            convo.set_live_state(thread, "closed", NOW)
            tx.commit()
        case = j(cases.detail(ref, REP, NOW))["case"]
        assert case["version"] == 5 and case["lifecycle"] == "claimed"
        assert [t for _, t in _state(s, ref)[2]].count("case_changed") == before


# --------------------------------------------------------------------------------------------------------- AC-23


@pytest.mark.skip(
    reason="blocked-on UX session: OpenAPI amendment CaseDetail.events.last_event_id (and AEA-02b carrying it)"
)
def test_detail_last_event_id_same_snapshot() -> None:
    """invariant (AC-23): detail sets events.last_event_id in the same snapshot as the case it reads."""
    with store() as s:
        refs = _seeded(s)
        cases, _, _, _ = services(s.uow)
        body = j(cases.detail(refs[7], REP, NOW))
        with s.uow() as tx:
            newest = tx.core.events.latest_id(case_stream(refs[7]))
        assert body["events"]["last_event_id"] == newest
