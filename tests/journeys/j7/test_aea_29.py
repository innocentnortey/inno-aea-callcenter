"""J-7 case leg (AEA-29): a live takeover through the real LiveChatService leaves the case version and lifecycle alone.

Level today: mock-tested (real services on a temp SQLite copy of the issued DB; real LiveChatService; no server, no
model). Integrated level blocked by AEA-30 (demo clock and DemoService), AEA-45 (getQueue/getCase routes) and AEA-52
(integrated staff side).
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any

import pytest
from starlette.datastructures import Headers

from meridian.adapters.sqlite.rows import case_stream
from meridian.domain.handoff import HandoffReason
from meridian.domain.staff import StaffRole, actor_for
from meridian.services.live_chat import LiveView
from tests.api.openapi_check import assert_response_matches
from tests.fixtures.sqlite import temp_sqlite
from tests.services._case_fixtures import NOW, case_action, ctx, j, new_thread, request, services
from tests.services.live_chat_support import RILEY, new_service

pytestmark = pytest.mark.journey

REP = StaffRole.REPRESENTATIVE


@dataclasses.dataclass
class _Resp:
    status_code: int
    headers: Headers
    content: bytes

    def json(self) -> Any:
        return json.loads(self.content)


def test_j7_live_takeover_keeps_case_version() -> None:
    with temp_sqlite() as db:
        with db.uow(write=True) as tx:
            tx.cases.demo_state.set_staffing("simulated_on_shift")
            thread, _ = new_thread(tx, customer_text="I need to talk to a person.")
            tx.commit()
        cases, handoff, _, _ = services(db.uow)
        req = request(thread, HandoffReason.CUSTOMER_REQUESTED_PERSON, trigger="con4")
        opened = handoff.open(req, ctx(thread, req.turn_id))
        ref = opened.case.case_ref
        assert opened.case.state == "live_queued"
        with db.uow() as tx:
            conv = tx.core.conversations.lookup(str(thread))
        assert getattr(conv, "live_state", None) == "queued"

        claimed = cases.apply(ref, case_action("claim", 1), actor_for(REP), 1, NOW)
        assert not hasattr(claimed, "code")
        version = claimed.version
        with db.uow() as tx:
            before = [e.id for e in tx.core.events.after(case_stream(ref), 0) if e.type == "case_changed"]

        live = new_service(db.uow, at=NOW)
        for step in (
            live.join(ref, RILEY),
            live.send(ref, "Hello, this is Riley.", RILEY),
            live.hand_back(ref, RILEY),
        ):
            assert isinstance(step, LiveView)

        detail = cases.detail(ref, REP, NOW)
        assert detail.case.version == version and detail.case.lifecycle == "claimed"
        assert detail.live.state == "handed_back"
        rep_lines = [line for line in detail.conversation if line.speaker.kind == "representative"]
        assert [j(line.speaker) for line in rep_lines] == [
            {"kind": "representative", "display_name": "Riley"}
        ]
        headers = Headers({"content-type": "application/json", "X-Request-ID": "req-test"})
        assert_response_matches(_Resp(200, headers, json.dumps(j(detail)).encode()), "getCase")
        with db.uow() as tx:
            after = [e.id for e in tx.core.events.after(case_stream(ref), 0) if e.type == "case_changed"]
        assert after == before
