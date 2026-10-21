"""J-6 case leg (AEA-29): an escalated refund reaches the staff queue and opens as an eight-heading case view.

Level today: mock-tested (real services on a temp SQLite copy of the issued DB; no server, no model). Integrated level
blocked by AEA-30 (demo clock and DemoService), AEA-45 (getQueue/getCase routes) and AEA-52 (integrated staff side).
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any

import pytest
from starlette.datastructures import Headers

from meridian.domain.handoff import HandoffReason
from meridian.domain.staff import StaffRole, actor_for
from meridian.policy.handoff import PROMISE_TABLE
from tests.api.openapi_check import assert_response_matches
from tests.fixtures.sqlite import temp_sqlite
from tests.services._case_fixtures import (
    NOW,
    case_action,
    count,
    ctx,
    guidance,
    j,
    services,
    state_for,
    summary_of,
    wp7,
)

pytestmark = pytest.mark.journey

REP = StaffRole.REPRESENTATIVE
CUSTOMER_TEXT = (
    "I want a full refund on the repair. It didn't fix anything and I had to call another company."
)


@dataclasses.dataclass
class _Resp:
    status_code: int
    headers: Headers
    content: bytes

    def json(self) -> Any:
        return json.loads(self.content)


def _ok(body: Any) -> _Resp:
    headers = Headers({"content-type": "application/json", "X-Request-ID": "req-test"})
    return _Resp(200, headers, json.dumps(body).encode())


def test_j6_escalated_case_reaches_queue_and_case_view() -> None:
    from meridian.domain.handoff import BriefExtraction, Quote

    with temp_sqlite() as db:
        with db.uow(write=True) as tx:
            thread, req = wp7(tx)
            message_id = tx.core.messages.handoff_anchor(thread)
            tx.commit()
        cases, handoff, assembler, _ = services(
            db.uow, guidance_map={HandoffReason.REFUND: (guidance(HandoffReason.REFUND),)}
        )
        result = handoff.open(req, ctx(thread, req.turn_id))
        ref = result.case.case_ref
        with db.uow() as tx:
            brief = assembler.assemble(
                summary_of(tx, ref), state_for(tx, thread), tx.core.lookup_log.for_thread(thread)
            )
        extraction = BriefExtraction(
            needs=[Quote(message_id=message_id, text="I want a full refund on the repair.")],
            claims=[Quote(message_id=message_id, text="It didn't fix anything")],
            open_decision="",
        )
        done = assembler.attach_extraction(
            brief, extraction, None, customer_messages={message_id: CUSTOMER_TEXT}
        )
        cases.attach_brief(ref, done)

        queue = cases.queue(REP, NOW)
        assert str(ref) in [r.reference for r in queue.needs_my_action]
        detail = cases.detail(ref, REP, NOW)
        assert len(detail.brief.headings) == 8
        assert detail.promise.policy_row == "R26.refund"
        assert detail.promise.text == PROMISE_TABLE["R26.refund"]
        assert list(detail.case.allowed_actions) == ["claim", "flag"]
        known = {s.source_id for s in detail.sources}
        assert known and all(
            sid in known for h in detail.brief.headings for i in h.items for sid in i.source_ids
        )
        assert_response_matches(_ok(j(queue)), "getQueue")
        assert_response_matches(_ok(j(detail)), "getCase")

        claimed = cases.apply(
            ref, case_action("claim", detail.case.version), actor_for(REP), detail.case.version, NOW
        )
        assert not hasattr(claimed, "code")
        assert claimed.version == detail.case.version + 1

        with db.uow() as tx:
            t = str(thread)
            assert count(tx, "SELECT COUNT(*) FROM cases WHERE thread_id = ?", t) == 1
            assert (
                count(tx, "SELECT COUNT(*) FROM actions WHERE thread_id = ? AND kind = 'case_opened'", t) == 1
            )
            assert (
                count(
                    tx, "SELECT COUNT(*) FROM lookup_log WHERE thread_id = ? AND tool = 'staff_guidance'", t
                )
                == 1
            )
