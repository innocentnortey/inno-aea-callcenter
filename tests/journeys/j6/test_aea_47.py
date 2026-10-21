"""J-6 clock leg (AEA-47). **Level today: mock-tested** - the real AEA-23 app and middleware in process with AEA-47's
router, a session-store double and a demo-service double over one open WP-4 case; no server, no browser, no DB copy.
Blocked steps: the `getQueue` read showing `due_state: overdue` (AEA-45 route; AEA-30 + AEA-52 real DemoService and
CaseService on the DB copy) and the integrated run (AEA-57 harness). Stored side at this level: the double's
demo-event list only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from meridian.domain.staff import DemoRole, StaffActor
from tests.api.staff_clock_support import ADVANCE_PATH, ClockAdvancedStub, clock_app
from tests.api.web_shell_support import (
    assert_matches,
    cookie_header,
    login,
    make_client,
    make_settings,
    session_cookie_value,
)
from tests.fakes.clock import CHICAGO, WORKED_PAIRS_NOW

pytestmark = pytest.mark.journey

WP4_CASE_DUE = datetime(
    2026, 10, 16, 12, 0, tzinfo=CHICAGO
)  # WP-4 step 5: P2 change request, due 12:00 today (Fri)
AFTER_PLUS_4H_LABEL = "Fri Oct 16, 2026 · 2:00 pm"


@dataclass
class OneCaseDemo:
    """Stands in for AEA-30's DemoService over one open WP-4 case. became_overdue follows cases.md 6:
    open cases whose case due d satisfies old_now <= d < new_now."""

    now: datetime = WORKED_PAIRS_NOW  # Fri Oct 16 10:00 (DEMO_START)
    case_due: datetime = WP4_CASE_DUE
    demo_events: list[dict[str, object]] = field(default_factory=list)

    def advance_clock(self, step: str, *, actor: StaffActor, request_id: str) -> ClockAdvancedStub:
        assert step == "plus_4h", step  # the only step this journey sends
        new = self.now + timedelta(hours=4)
        became = 1 if self.now <= self.case_due < new else 0
        self.demo_events.append(
            {
                "kind": "clock_advanced",
                "step": step,
                "role": actor.role.value,
                "request_id": str(request_id),
                "became_overdue": became,
            }
        )
        self.now = new
        return ClockAdvancedStub(now=new, label=AFTER_PLUS_4H_LABEL, became_overdue=became)


def test_j6_supervisor_advance_turns_wp4_case_overdue(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    demo = OneCaseDemo()
    settings = make_settings(tmp_path)
    h = clock_app(monkeypatch, settings, demo=demo)
    with make_client(h.app) as client:
        token = session_cookie_value(login(client, settings))
        assert token
        h.store.set_role(token, DemoRole.SUPERVISOR)
        r = client.post(ADVANCE_PATH, headers=cookie_header(token), json={"step": "plus_4h"})
    assert r.status_code == 200, r.text
    assert_matches(r, "advanceDemoClock")
    assert r.json() == {
        "now": "2026-10-16T14:00:00-05:00",
        "label": "Fri Oct 16, 2026 · 2:00 pm",
        "became_overdue": 1,
    }
    assert demo.demo_events == [
        {
            "kind": "clock_advanced",
            "step": "plus_4h",
            "role": "supervisor",
            "request_id": r.headers["X-Request-ID"],
            "became_overdue": 1,
        }
    ]
    print(r.json(), demo.demo_events[0])


def test_j6_queue_shows_wp4_case_overdue_after_advance() -> None:
    pytest.skip(
        "blocked: getQueue route (AEA-45); real DemoService and CaseService on the DB copy (AEA-30, AEA-52); "
        "journey harness (AEA-57)"
    )
