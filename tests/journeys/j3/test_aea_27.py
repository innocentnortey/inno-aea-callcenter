"""J-3 identity step (AEA-27; J-3's identity step is a proposed addition to the journey map, backend-amendments §3,
pattern A). API level on AEA-57's harness: the real app, container and DB copy, scripted model.

Step 0 runs today: the real app binds identity_service to the one IdentityService. Step 1 (code sent to SCR-2's
inbox via listDemoInbox, entered through submitTurn, verified; a restart on the same working copy reads the message
expired with no code; the stored row holds only the HMAC) is declared with its needs and stays blocked until
AEA-40 (startChatSession, submitTurn), AEA-43 (listDemoInbox) and AEA-51 (run_graph) land. Its body is written with
the graph's scripted outputs once AEA-51 lands (plan R-1).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from meridian.services.identity import IdentityService
from meridian.web.container import Key
from tests.journeys.support.run import JourneyRun

pytestmark = pytest.mark.journey

J3 = "J-3"
IDENTITY_TABLES = ("identity_threads", "identity_codes", "demo_inbox")
CODE_STEP_NEEDS = ("login_sessions", "session_service", "turn_service", "run_graph", "identity_service")
CODE_STEP_OPERATIONS = ("startChatSession", "submitTurn", "listDemoInbox")


def test_j3_identity_service_bound_in_real_app(journey: JourneyRun) -> None:
    with journey.step(J3, "identity 0 service bound", needs=("identity_service",)):
        key: Key[IdentityService] = Key("identity_service")
        svc = journey.container.get(key)
        assert isinstance(svc, IdentityService)
        assert svc is journey.container.get(key)
        assert uuid.UUID(svc.boot_id).version == 4
        assert svc.inbox(str(uuid.uuid4()), now=datetime.now(UTC)) == ()
        for table in IDENTITY_TABLES:
            assert journey.db.count(table) == 0, table


def test_j3_code_from_inbox_verifies_restart_reads_expired(journey: JourneyRun) -> None:
    with journey.step(
        J3,
        "identity 1 code from inbox verifies; restart reads expired",
        needs=CODE_STEP_NEEDS,
        operations=CODE_STEP_OPERATIONS,
    ):
        pytest.skip(
            "J-3 identity body not written yet: needs AEA-51's scripted graph outputs (AEA-27 plan R-1)"
        )
