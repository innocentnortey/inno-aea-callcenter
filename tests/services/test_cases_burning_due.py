"""FU-identity-plan (AEA-51 finding F-2): CaseService.align_burning_due on a temp copy of the issued DB (CAS-16 A)."""

from __future__ import annotations

import datetime as dt

from meridian.domain.handoff import HandoffReason
from tests.services._case_fixtures import CHI, NOW, ctx, new_thread, new_turn, request, services, store, wp4

START = dt.datetime(2026, 10, 19, 8, 0, tzinfo=CHI)


def test_align_moves_due_once_to_the_window_start() -> None:
    with store() as s:
        cases, handoff, _, _ = services(s.uow)
        with s.uow(write=True) as tx:
            thread, _ = new_thread(tx, customer_text="I smell something burning from the vents")
            tx.commit()
        req = request(thread, HandoffReason.BURNING_RULED_OUT)
        opened = handoff.open(req, ctx(thread, req.turn_id))
        ref = opened.case.case_ref
        assert opened.case.due_at == opened.case.promise.due_at
        assert cases.align_burning_due(thread, START, new_turn(), NOW) is True
        with s.uow() as tx:
            row = tx.cases.cases.get(ref)
            events = tx.cases.case_events.list_for_case(ref)
        assert row is not None
        assert row.due_at == START
        assert row.version == opened.case.version + 1
        assert events[-1].kind == "due_moved"
        assert events[-1].detail["rule_id"] == "CAS16.booked_window"
        assert cases.align_burning_due(thread, START + dt.timedelta(days=1), new_turn(), NOW) is False
        with s.uow() as tx:
            again = tx.cases.cases.get(ref)
        assert again is not None
        assert (again.due_at, again.version) == (row.due_at, row.version)


def test_align_ignores_other_cases() -> None:
    with store() as s:
        cases, handoff, _, _ = services(s.uow)
        with s.uow(write=True) as tx:
            thread, req = wp4(tx)
            tx.commit()
        opened = handoff.open(req, ctx(thread, req.turn_id))
        assert cases.align_burning_due(thread, START, new_turn(), NOW) is False
        with s.uow() as tx:
            row = tx.cases.cases.get(opened.case.case_ref)
        assert row is not None
        assert row.due_at == opened.case.due_at
        with s.uow(write=True) as tx:
            empty, _ = new_thread(tx)
            tx.commit()
        assert cases.align_burning_due(empty, START, new_turn(), NOW) is False
