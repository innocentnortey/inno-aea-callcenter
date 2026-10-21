"""AEA-29 Step 10: the real seed through the real assembler, views against the signed schemas, stored stream rows
against the signed event schemas. Temp SQLite copy of the issued database; no server, no model."""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
from typing import Any

from starlette.datastructures import Headers

from meridian.adapters.sqlite.rows import EventRow, case_stream, thread_stream
from meridian.agent.nodes.compose import ReplyComposer
from meridian.domain.handoff import HandoffReason
from meridian.domain.staff import StaffRole, actor_for
from meridian.services.cases import CaseService
from meridian.services.handoff import BriefAssembler, HandoffService
from meridian.services.reset import seed_demo
from meridian.web.schemas.events import CHAT_EVENT_TYPES
from meridian.web.schemas.staff_live import CASE_EVENT_TYPES
from tests.api.openapi_check import SseFrame, assert_response_matches, assert_sse_frames_match
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services._case_fixtures import (
    NOW,
    StaffingDemo,
    activity_in,
    case_action,
    ctx,
    j,
    new_thread,
    ref,
    request,
)

REP = StaffRole.REPRESENTATIVE
SUP = StaffRole.SUPERVISOR


@dataclasses.dataclass
class _Resp:
    status_code: int
    headers: Headers
    content: bytes

    def json(self) -> Any:
        return json.loads(self.content)


def _resp(status: int, body: Any) -> _Resp:
    return _Resp(
        status,
        Headers({"content-type": "application/json", "X-Request-ID": "req-test"}),
        json.dumps(body).encode(),
    )


def _seeded(db: TempStore) -> CaseService:
    with db.uow(write=True) as tx:
        assert seed_demo(tx, assembler=BriefAssembler()) == 4
        tx.commit()
    return CaseService(db.uow, FixedClock(NOW))


def test_seed_demo_with_real_assembler() -> None:
    with temp_sqlite() as db:
        cases = _seeded(db)
        with db.uow() as tx:
            for n in (5, 6, 7, 8):
                brief = tx.cases.briefs.get(ref(n))
                assert brief is not None and len(brief.headings) == 8 and brief.status == "ready"
            rows = tx.core.lookup_log.for_thread(tx.cases.cases.get(ref(7)).thread_id)  # type: ignore[union-attr]
            assert [r.tool for r in rows] == ["read_invoices"]
            heading5 = tx.cases.briefs.get(ref(7)).headings[4]  # type: ignore[union-attr]
            assert any(
                s.kind == "lookup_log" and s.ref == str(rows[0].id) for i in heading5.items for s in i.sources
            )
        queue = cases.queue(REP, NOW)
        assert [r.reference for r in queue.needs_my_action] == [
            "MHC-C-0008",
            "MHC-C-0005",
            "MHC-C-0006",
            "MHC-C-0007",
        ]
        assert [r.due_state for r in queue.needs_my_action] == [
            "no_due_time",
            "overdue",
            "on_time",
            "on_time",
        ]
        lanes = cases.oversight(NOW).lanes

        def refs(lane: Any) -> list[str]:
            return [r.reference for r in lane.rows]

        assert refs(lanes.p0_p1) == ["MHC-C-0008"]
        assert refs(lanes.overdue) == ["MHC-C-0005"]
        assert sorted(refs(lanes.unowned)) == ["MHC-C-0006", "MHC-C-0007"]
        source = cases.detail(ref(7), REP, NOW).sources[0]
        assert source.current is not None and source.changed_since is False
        with db.uow(write=True) as tx:
            tx.connection.execute("UPDATE invoices SET balance_cents = 0 WHERE invoice_id = 'INV-204411'")
            tx.commit()
        assert cases.detail(ref(7), REP, NOW).sources[0].changed_since is True


def test_views_match_openapi_schemas() -> None:
    with temp_sqlite() as db:
        cases = _seeded(db)
        for role in (REP, SUP):
            assert_response_matches(_resp(200, j(cases.queue(role, NOW))), "getQueue")
            for n in (5, 6, 7, 8):
                assert_response_matches(_resp(200, j(cases.detail(ref(n), role, NOW))), "getCase")
        assert_response_matches(_resp(200, j(cases.oversight(NOW))), "getOversight")
        rep = actor_for(REP)
        claimed = cases.apply(ref(6), case_action("claim", 1), rep, 1, NOW)
        assert not hasattr(claimed, "code")
        result = cases.record_activity(ref(6), activity_in("call", "reached", claimed.version), rep, NOW)
        assert not hasattr(result, "code")
        assert_response_matches(_resp(201, j(result)), "recordContactActivity")


def _frames(rows: list[EventRow]) -> list[SseFrame]:
    return [
        SseFrame(
            event=row.type,
            id=str(row.id),
            data=json.dumps({"event_id": row.id, "type": row.type, "at": row.at.isoformat(), **row.payload}),
        )
        for row in rows
    ]


def test_stream_rows_match_openapi_events() -> None:
    later = NOW + dt.timedelta(hours=2)
    composer = ReplyComposer()
    with temp_sqlite() as db:
        with db.uow(write=True) as tx:
            tx.cases.demo_state.set_staffing("simulated_on_shift")
            thread, _ = new_thread(tx, customer_text="I need to talk to a person.")
            other, _ = new_thread(tx, customer_text="Please call me back.")
            tx.commit()
        cases = CaseService(
            db.uow, FixedClock(NOW), handoff_block=composer.handoff_block, settled_view=composer.settled_view
        )
        handoff = HandoffService(db.uow, cases, StaffingDemo(), FixedClock(NOW))
        req = request(thread, HandoffReason.CUSTOMER_REQUESTED_PERSON, trigger="con4")
        first = handoff.open(req, ctx(thread, req.turn_id))
        assert first.case.promise.live_queued is True
        req2 = request(other, HandoffReason.CUSTOMER_REQUESTED_PERSON, trigger="con4")
        second = handoff.open(req2, ctx(other, req2.turn_id))
        claimed = cases.apply(second.case.case_ref, case_action("claim", 1), actor_for(REP), 1, NOW)
        assert not hasattr(claimed, "code")
        assert cases.convert_live_queued(later) == 1
        with db.uow() as tx:
            thread_rows = tx.core.events.after(thread_stream(thread), 0)
            case_rows = [
                *tx.core.events.after(case_stream(first.case.case_ref), 0),
                *tx.core.events.after(case_stream(second.case.case_ref), 0),
            ]
        assert "case_created" in [r.type for r in thread_rows]
        assert "case_created" not in CHAT_EVENT_TYPES
        chat = [r for r in thread_rows if r.type in CHAT_EVENT_TYPES]
        assert [r.type for r in chat] == ["shift_ended"]
        assert_sse_frames_match(_frames(chat), "streamChatEvents")
        assert set(chat[0].payload) == {"speaker", "line", "handoff", "settled"}
        staff = [r for r in case_rows if r.type in CASE_EVENT_TYPES]
        assert {r.type for r in staff} >= {"case_changed", "chat_closed"}
        assert_sse_frames_match(_frames(staff), "streamCaseEvents")
