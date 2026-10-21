"""AEA-28: SchedulingService over a temp working copy with the fixed WP-4 demo clock (AC-1..AC-13, AC-17, AC-18, PA-2)."""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, closing
from datetime import date, timedelta
from typing import Any, cast

import pytest

from meridian.adapters.sqlite.repos_booking import AppointmentsRepo
from meridian.agent.tools.scheduling import FindWindowsArgs, scheduling_tools
from meridian.domain.actions import ActionKind, CompletedAction
from meridian.domain.common import CustomerId, ThreadId
from meridian.domain.specialists import ChangeRequestDraft, SchedulingSliceInputs, WriteResult
from meridian.domain.tools import LookupEntry, LookupRow, ToolCallScope
from meridian.policy.booking import fee_note, zone_for
from meridian.policy.limits import Limits
from meridian.policy.texts import TextId, format_usd, render
from meridian.ports.runtime import UnitOfWork
from meridian.services.scheduling import (
    OutOfArea,
    Refused,
    SchedulingService,
    SlotTaken,
    WindowQuery,
    WindowsFound,
)
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.scheduling_helpers import (
    CHI,
    LINDA,
    MHC_57204,
    NOW,
    appt_row,
    count,
    entry,
    issued_sha256,
    key,
    raw,
    row_digest,
    scope,
    service,
    slot_row,
    thread,
    turn,
)

BOOKED, MOVED, CANCELLED, CHANGE = (
    ActionKind.BOOKED,
    ActionKind.MOVED,
    ActionKind.CANCELLED,
    ActionKind.CHANGE_REQUEST_SENT,
)
_FEE_49 = render(TextId.FEE_APPLIES, amount=format_usd(4900))


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


@pytest.fixture(scope="module", autouse=True)
def issued_unchanged() -> Iterator[None]:
    before = issued_sha256()
    yield
    assert issued_sha256() == before


def _book(
    svc: SchedulingService, store: TempStore, n: int, slot: int, shown: set[int], who: CustomerId = LINDA
) -> tuple[ToolCallScope, WriteResult | SlotTaken | Refused]:
    sc = scope(store, thread(n), turn(1), who, shown)
    return sc, svc.book(
        key(sc, BOOKED, str(slot)),
        sc,
        slot,
        "AC not cooling",
        entry(sc, "book_visit", (f"slot:{slot}",), "x"),
    )


def test_find_windows_wp3_offers_earliest_north_repair(store: TempStore) -> None:
    svc = service(store)
    terms = svc.customer_terms(LINDA)
    assert terms is not None
    assert (terms.location, terms.tier) == ("78664", "standard")
    q = WindowQuery(
        zone_hint=terms.location,
        service_type="hvac_repair",
        member_tier=terms.tier,
        wanted_text="This Saturday if possible, 4 to 7",
        earliest=date(2026, 10, 17),
        latest=date(2026, 10, 17),
        window="16:00-19:00",
    )
    r = svc.find_windows(q, NOW, shown_turn=turn(1))
    assert isinstance(r, WindowsFound)
    assert r.zone == "north"
    assert r.exact_fit is False
    assert [w.slot_id for w in r.windows] == [56, 42, 58]
    assert [w.window for w in r.windows] == ["08:00-12:00", "12:00-16:00", "13:00-17:00"]
    assert [w.technician for w in r.windows] == ["Marta Kowalski", "Ray Mendoza", "Marta Kowalski"]
    assert all(w.date == date(2026, 10, 19) for w in r.windows)
    assert not {w.date for w in r.windows} & {date(2026, 10, 17), date(2026, 10, 18)}
    ids = {w.slot_id for w in r.windows}
    assert 1 not in ids and 57 not in ids
    assert all(w.shown_turn == turn(1) for w in r.windows)


def _q(tier: Any) -> WindowQuery:
    d = date(2026, 10, 21)
    return WindowQuery(
        zone_hint="78664",
        service_type="hvac_repair",
        member_tier=tier,
        earliest=d,
        latest=d,
        window="12:00-16:00",
    )


def test_member_reserved_only_for_verified_members(store: TempStore) -> None:
    svc = service(store)
    for tier in ("standard", "plus"):
        r = svc.find_windows(_q(tier), NOW, shown_turn=turn(1))
        assert isinstance(r, WindowsFound)
        assert r.windows[0].slot_id == 110
        assert r.windows[0].member_reserved is True
    r = svc.find_windows(_q("none"), NOW, shown_turn=turn(1))
    assert isinstance(r, WindowsFound)
    assert not any(w.member_reserved for w in r.windows)
    assert r.windows[0].slot_id == 125
    tools = {d.name: d for d in scheduling_tools(svc)}
    sc = scope(store, thread(1), turn(1), None)
    res = tools["find_windows"].executor(
        FindWindowsArgs(
            service_type="hvac_repair",
            zone_hint="Round Rock",
            earliest=date(2026, 10, 21),
            latest=date(2026, 10, 21),
            window="12:00-16:00",
        ),
        sc,
    )
    assert res.ok
    assert isinstance(res.for_model, dict)
    windows = cast(list[dict[str, Any]], res.for_model["windows"])
    assert not any(w["member_reserved"] for w in windows)
    assert res.for_model["fee_line"] == fee_note("hvac_repair", "none").line


@pytest.mark.parametrize("hint", ["Lakeway", "Lakeway, TX", "78734", "78738"])
def test_out_of_area_not_served(store: TempStore, hint: str) -> None:
    svc = service(store)
    r = svc.find_windows(
        WindowQuery(zone_hint=hint, service_type="plumbing", member_tier="none"), NOW, shown_turn=turn(1)
    )
    assert r == OutOfArea(reason="not_served")
    assert r.model_dump() == {"reason": "not_served"}
    assert hint not in r.model_dump_json()


def test_out_of_area_and_zip_towns(store: TempStore) -> None:
    svc = service(store)
    hint = "Zyxwvut Hollow QX"  # synthetic unknown place
    r = svc.find_windows(
        WindowQuery(zone_hint=hint, service_type="plumbing", member_tier="none"), NOW, shown_turn=turn(1)
    )
    assert r == OutOfArea(reason="unknown_location")
    assert hint not in r.model_dump_json()
    for z in ("78620", "78653"):
        f = svc.find_windows(
            WindowQuery(zone_hint=z, service_type="plumbing", member_tier="none"), NOW, shown_turn=turn(1)
        )
        assert isinstance(f, WindowsFound)
        assert f.zone == zone_for(z) == "central"
        assert f.windows


def test_book_writes_four_rows_in_one_transaction(store: TempStore, monkeypatch: pytest.MonkeyPatch) -> None:
    svc = service(store)
    _, r = _book(svc, store, 1, 56, {56})
    assert isinstance(r, WriteResult)
    with closing(raw(store)) as c:
        assert c.execute("SELECT status FROM appointment_slots WHERE slot_id = 56").fetchone() == ("booked",)
        assert c.execute(
            "SELECT appointment_id, customer_id, status FROM appointments WHERE slot_id = 56"
        ).fetchall() == [(160, "MHC-10001", "scheduled")]
        assert c.execute("SELECT kind FROM actions").fetchall() == [("booked",)]
        assert c.execute("SELECT COUNT(*) FROM lookup_log").fetchone() == (1,)
    cf = r.confirmation
    assert (cf.date, cf.window, cf.technician) == (date(2026, 10, 19), "08:00-12:00", "Marta Kowalski")
    assert cf.fee_note.waived is True and cf.fee_note.fee_row == "Diagnostic visit"

    class _InjectedFault(Exception):
        pass

    original = AppointmentsRepo.insert

    def wrapper(self: AppointmentsRepo, *a: Any, **k: Any) -> int:
        original(self, *a, **k)
        raise _InjectedFault

    with temp_sqlite() as s2:
        monkeypatch.setattr(AppointmentsRepo, "insert", wrapper)
        with pytest.raises(_InjectedFault):
            _book(service(s2), s2, 1, 56, {56})
        with closing(raw(s2)) as c:
            assert c.execute("SELECT status FROM appointment_slots WHERE slot_id = 56").fetchone() == (
                "open",
            )
            assert c.execute("SELECT MAX(appointment_id) FROM appointments").fetchone() == (159,)
            assert c.execute("SELECT COUNT(*) FROM actions").fetchone() == (0,)
            assert c.execute("SELECT COUNT(*) FROM lookup_log").fetchone() == (0,)


def test_slot_taken_refuses_and_writes_nothing(store: TempStore) -> None:
    svc = service(store)
    _, first = _book(svc, store, 2, 56, {56})
    assert isinstance(first, WriteResult)
    before = row_digest(store)
    sc = scope(store, thread(1), turn(1), LINDA, {56})
    r = svc.book(key(sc, BOOKED, "56"), sc, 56, "AC not cooling", entry(sc))
    assert isinstance(r, SlotTaken)
    assert r.slot_id == 56
    assert [a.slot_id for a in r.alternatives] == [42, 58, 91]
    assert all(a.shown_turn == turn(1) for a in r.alternatives)
    assert 56 not in [a.slot_id for a in r.alternatives]
    # the message row seeded by scope() is not part of the digest tables
    assert row_digest(store) == before


def test_book_idempotent_on_action_key(store: TempStore) -> None:
    svc = service(store)
    sc = scope(store, thread(1), turn(1), LINDA, {56})
    k = key(sc, BOOKED, "56")
    e = entry(sc, "book_visit", ("slot:56",), "booked slot:56")
    first = svc.book(k, sc, 56, "AC not cooling", e)
    second = svc.book(k, sc, 56, "AC not cooling", e)
    assert isinstance(first, WriteResult)
    assert first == second
    assert count(store, "SELECT COUNT(*) FROM appointments WHERE slot_id = 56") == 1
    assert count(store, "SELECT COUNT(*) FROM actions") == 1
    assert count(store, "SELECT COUNT(*) FROM lookup_log") == 1


class RecordingUow:
    calls: int = 0

    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]:
        self.calls += 1
        raise AssertionError("no unit of work expected")


@pytest.mark.parametrize(
    "code",
    ["not_shown", "outside_service_area", "wrong_service_type", "booking_cap", "not_owned", "unverified"],
)
def test_refusals_write_nothing(store: TempStore, code: str) -> None:
    svc = service(store)
    if code == "unverified":
        rec = RecordingUow()
        bad = SchedulingService(rec, Limits().booking)
        sc = scope(store, thread(1), turn(1), None, {56})
        e = entry(sc)
        assert bad.book(key(sc, BOOKED, "56"), sc, 56, "x", e) == Refused(code="not_owned")
        assert bad.move(key(sc, MOVED, "1"), sc, 1, 56, e) == Refused(code="not_owned")
        assert bad.cancel(key(sc, CANCELLED, "1"), sc, 1, e) == Refused(code="not_owned")
        assert bad.request_change(key(sc, CHANGE, "1"), sc, 1, "move", "w", e) == Refused(code="not_owned")
        assert rec.calls == 0
        return
    if code == "booking_cap":
        for i, slot in enumerate((56, 42, 58), start=1):
            sc = scope(store, thread(1), turn(i), LINDA, {56, 42, 58, 91})
            assert isinstance(svc.book(key(sc, BOOKED, str(slot)), sc, slot, "x", entry(sc)), WriteResult)
        before = row_digest(store)
        sc = scope(store, thread(1), turn(4), LINDA, {56, 42, 58, 91})
        assert svc.book(key(sc, BOOKED, "91"), sc, 91, "x", entry(sc)) == Refused(code="booking_cap")
        assert row_digest(store) == before
        capped = service(store, cap=1)
        sc = scope(store, thread(2), turn(1), LINDA, {91, 72})
        assert isinstance(capped.book(key(sc, BOOKED, "91"), sc, 91, "x", entry(sc)), WriteResult)
        sc2 = scope(store, thread(2), turn(2), LINDA, {91, 72})
        assert capped.book(key(sc2, BOOKED, "72"), sc2, 72, "x", entry(sc2)) == Refused(code="booking_cap")
        return
    cases: dict[str, tuple[CustomerId, set[int], Callable[[ToolCallScope, LookupEntry], object]]] = {
        "not_shown": (LINDA, set(), lambda sc, e: svc.book(key(sc, BOOKED, "56"), sc, 56, "x", e)),
        "outside_service_area": (
            MHC_57204,
            {56},
            lambda sc, e: svc.book(key(sc, BOOKED, "56"), sc, 56, "x", e),
        ),
        "wrong_service_type": (MHC_57204, {44}, lambda sc, e: svc.move(key(sc, MOVED, "94"), sc, 94, 44, e)),
        "not_owned": (LINDA, set(), lambda sc, e: svc.cancel(key(sc, CANCELLED, "94"), sc, 94, e)),
    }
    who, shown, call = cases[code]
    sc = scope(store, thread(1), turn(1), who, shown)
    before = row_digest(store)
    assert call(sc, entry(sc)) == Refused(code=code)  # type: ignore[arg-type]
    assert row_digest(store) == before


def test_move_fee_free_wp4f(store: TempStore) -> None:
    svc = service(store)
    sc = scope(store, thread(1), turn(1), MHC_57204, {53})
    r = svc.move(key(sc, MOVED, "94"), sc, 94, 53, entry(sc))
    assert isinstance(r, WriteResult)
    assert slot_row(store, 189)[-1] == "open"
    assert slot_row(store, 53)[-1] == "booked"
    assert appt_row(store, 94)[1] == 53
    a = r.action
    assert a.records == {"appointment": "94", "slot": "53", "old_slot": "189"}
    assert a.before == {
        "date": "2026-10-23",
        "window": "08:00-12:00",
        "technician": "Devon Hale",
        "service_type": "plumbing",
    }
    assert a.after == {
        "date": "2026-10-19",
        "window": "08:00-12:00",
        "technician": "Devon Hale",
        "service_type": "plumbing",
        "fee_line": fee_note("plumbing", "none").line,
    }


def test_fee_bearing_move_and_cancel_never_write(store: TempStore) -> None:
    svc = service(store)
    sc = scope(store, thread(1), turn(1), MHC_57204, {44, 61})
    before = row_digest(store)
    a1, s2 = appt_row(store, 1), slot_row(store, 2)
    assert svc.move(key(sc, MOVED, "1"), sc, 1, 44, entry(sc)) == Refused(
        code="fee_bearing", hours_before=2.0
    )
    sc2 = scope(store, thread(1), turn(2), MHC_57204)
    assert svc.cancel(key(sc2, CANCELLED, "1"), sc2, 1, entry(sc2)) == Refused(
        code="fee_bearing", hours_before=2.0
    )
    assert (appt_row(store, 1), slot_row(store, 2), row_digest(store)) == (a1, s2, before)
    now24 = dt.datetime(2026, 10, 15, 12, 0, tzinfo=CHI)
    sc3 = scope(store, thread(3), turn(1), MHC_57204, now=now24)
    assert isinstance(svc.cancel(key(sc3, CANCELLED, "1"), sc3, 1, entry(sc3)), WriteResult)
    assert appt_row(store, 1)[5] == "cancelled"
    assert slot_row(store, 2)[-1] == "open"


def test_request_change_wp4_records_and_touches_nothing(store: TempStore) -> None:
    svc = service(store)
    snaps = (appt_row(store, 1), slot_row(store, 2), slot_row(store, 44), slot_row(store, 61))
    sc = scope(store, thread(1), turn(1), MHC_57204, {44, 61})
    d = svc.request_change(key(sc, CHANGE, "1"), sc, 1, "move", "Monday morning", entry(sc))
    assert isinstance(d, ChangeRequestDraft)
    assert d.change == "move" and d.hours_before == 2.0
    assert d.window_start == dt.datetime(2026, 10, 16, 12, 0, tzinfo=CHI)
    assert d.window_start.utcoffset() == timedelta(hours=-5)
    assert d.windows_shown == (44, 61)
    assert d.wanted_text == "Monday morning"
    assert snaps == (appt_row(store, 1), slot_row(store, 2), slot_row(store, 44), slot_row(store, 61))
    with store.uow() as tx:
        actions = tx.core.actions.for_thread(sc.ids.thread_id)
    assert len(actions) == 1 and actions[0].kind is CHANGE
    assert actions[0].after == {"change": "move", "wanted_text": "Monday morning", "fee_line": _FEE_49}
    assert count(store, "SELECT COUNT(*) FROM lookup_log") == 1


def test_cancel_fee_free(store: TempStore) -> None:
    svc = service(store)
    sc = scope(store, thread(1), turn(1), MHC_57204)
    r = svc.cancel(key(sc, CANCELLED, "94"), sc, 94, entry(sc))
    assert isinstance(r, WriteResult)
    assert appt_row(store, 94)[5] == "cancelled"
    assert slot_row(store, 189)[-1] == "open"
    with store.uow() as tx:
        (a,) = tx.core.actions.for_thread(sc.ids.thread_id)
    assert (
        a.kind is CANCELLED and a.before is not None and a.before["date"] == "2026-10-23" and a.after is None
    )


def test_estimate_books_estimate_slots_only(store: TempStore) -> None:
    svc = service(store)
    r = svc.find_windows(
        WindowQuery(zone_hint="78664", service_type="estimate", member_tier="standard"),
        NOW,
        shown_turn=turn(1),
    )
    assert isinstance(r, WindowsFound)
    assert all(w.service_type == "estimate" for w in r.windows)
    assert [w.slot_id for w in r.windows] == [27, 65, 66]
    _, b = _book(svc, store, 1, 65, {27, 65, 66})
    assert isinstance(b, WriteResult)
    assert b.confirmation.technician.startswith("Comfort Advisor")
    assert b.confirmation.fee_note.fee_row is None and b.confirmation.fee_note.amount_cents == 0


def test_write_records_carry_turn_and_message(store: TempStore) -> None:
    svc = service(store)

    def lookups(th: ThreadId) -> tuple[tuple[CompletedAction, ...], tuple[LookupRow, ...]]:
        with store.uow() as tx:
            return tx.core.actions.for_thread(th), tx.core.lookup_log.for_thread(th)

    sc = scope(store, thread(1), turn(1), LINDA, {56})
    assert isinstance(svc.book(key(sc, BOOKED, "56"), sc, 56, "x", entry(sc)), WriteResult)
    sc_m = scope(store, thread(2), turn(1), MHC_57204, {53})
    assert isinstance(svc.move(key(sc_m, MOVED, "94"), sc_m, 94, 53, entry(sc_m)), WriteResult)
    sc_c = scope(store, thread(2), turn(2), MHC_57204)
    assert isinstance(svc.cancel(key(sc_c, CANCELLED, "94"), sc_c, 94, entry(sc_c)), WriteResult)
    sc_r = scope(store, thread(3), turn(1), MHC_57204, {44})
    assert isinstance(
        svc.request_change(key(sc_r, CHANGE, "1"), sc_r, 1, "move", "w", entry(sc_r)), ChangeRequestDraft
    )

    shapes = {
        BOOKED: ({"appointment", "slot"}, None, 5),
        MOVED: ({"appointment", "slot", "old_slot"}, 4, 5),
        CANCELLED: ({"appointment", "slot"}, 4, None),
        CHANGE: ({"appointment", "slot"}, 4, 3),
    }
    for sc_x, kind in ((sc, BOOKED), (sc_m, MOVED), (sc_c, CANCELLED), (sc_r, CHANGE)):
        actions, rows = lookups(sc_x.ids.thread_id)
        a = next(x for x in actions if x.key.turn_id == sc_x.ids.turn_id)
        rec, nb, na = shapes[kind]
        assert a.kind is kind and set(a.records) == rec
        assert (None if a.before is None else len(a.before)) == nb
        assert (None if a.after is None else len(a.after)) == na
        assert a.at == NOW
        row = next(r for r in rows if r.turn_id == sc_x.ids.turn_id)
        assert (row.turn_id, row.message_id, row.thread_id) == (
            sc_x.ids.turn_id,
            sc_x.message_id,
            sc_x.ids.thread_id,
        )


def test_slice_inputs(store: TempStore) -> None:
    svc = service(store)
    s = svc.slice_inputs(MHC_57204)
    assert s.zone == "central" and s.member is False
    assert [a.appointment_id for a in s.appointments] == [1, 94]
    a1 = s.appointments[0]
    assert (a1.date, a1.window, a1.technician, a1.service_type) == (
        date(2026, 10, 16),
        "12:00-16:00",
        "Ray Mendoza",
        "hvac_tune_up",
    )
    for a in s.appointments:
        dumped = a.model_dump()
        assert "issue_description" not in dumped and "customer_id" not in dumped
    assert svc.slice_inputs(CustomerId("MHC-99999")) == SchedulingSliceInputs(
        zone=None, member=False, appointments=()
    )


def test_started_window_not_offered_or_booked(store: TempStore) -> None:
    svc = service(store)
    d = date(2026, 10, 16)
    r = svc.find_windows(
        WindowQuery(
            zone_hint="78664",
            service_type="hvac_repair",
            member_tier="standard",
            earliest=d,
            latest=d,
            window="08:00-12:00",
        ),
        NOW,
        shown_turn=turn(1),
    )
    assert isinstance(r, WindowsFound)
    assert 1 not in [w.slot_id for w in r.windows]
    before = row_digest(store)
    sc = scope(store, thread(1), turn(1), LINDA, {1})
    out = svc.book(key(sc, BOOKED, "1"), sc, 1, "x", entry(sc))
    assert isinstance(out, SlotTaken) and out.slot_id == 1
    assert row_digest(store) == before
