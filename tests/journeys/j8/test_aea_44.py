"""J-8 (slice plan section 0a): role switch and session.

Level today: mock-tested (in-process app with AEA-23's real middleware and this ticket's real store over a temp SQLite
copy; not AEA-57's harness). Integrated level blocked by AEA-57 and AEA-52.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.api.staff_session_support import login_token, run_reset, staff_app, staff_rows, switch, tab
from tests.api.web_shell_support import make_client
from tests.fixtures.sqlite import temp_sqlite

pytestmark = pytest.mark.journey


def test_j8_role_switch_seen_by_second_tab_and_refusal_names_role(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    steps: list[str] = []

    def say(tab_name: str, method: str, path: str, response: object) -> None:
        body = response.json()  # type: ignore[attr-defined]
        detail = body.get("role") or body.get("error", {}).get("details", {}).get("reason")
        steps.append(f"{tab_name} {method} {path} {response.status_code} {detail}")  # type: ignore[attr-defined]

    with temp_sqlite() as db:
        h = staff_app(monkeypatch, tmp_path, db)
        with make_client(h.app) as client:
            token = login_token(client, h.settings)
            switched = switch(client, token, "representative")  # tab B
            say("B", "PUT", "/api/session/role", switched)
            assert switched.status_code == 200

            seen = client.get("/api/session", headers=tab(token))  # tab A
            say("A", "GET", "/api/session", seen)
            assert seen.json()["role"] == "representative"
            assert seen.json()["display_name"] == "Riley, demo representative"
            before = staff_rows(db.uow)
            assert before[0]["role"] == "representative"

            queue = client.get("/api/staff/queue", headers=tab(token))
            say("A", "GET", "/api/staff/queue", queue)
            assert queue.status_code == 200 and queue.json()["name"] == "Riley"

            run_reset(db.uow)
            refused = client.get("/api/staff/queue", headers=tab(token))
            say("A", "GET", "/api/staff/queue", refused)
            assert refused.status_code == 403
            assert refused.json()["error"]["details"] == {
                "role": "customer",
                "needs": ["representative", "supervisor"],
                "reason": "role_reset",
            }
            after = staff_rows(db.uow)[0]
            assert after["role"] == "customer" and after["role_reset_pending"] == 1
            assert after["session_id"] == before[0]["session_id"]

            again = client.get("/api/session", headers=tab(token))
            say("A", "GET", "/api/session", again)
            assert again.status_code == 200 and again.json()["role"] == "customer"
    print("\n".join(steps))


@pytest.mark.skip(
    reason="blocked: integrated level needs AEA-57 (journey harness) and AEA-52 (staff routes wired); "
    "see docs/testing/journeys/2026-10-21-AEA-44.md"
)
def test_j8_on_harness() -> None:
    """Same steps on AEA-57's harness with the production build: login, switch in tab B, getSession in tab A, a
    refused staff call that names the role and reason, reset, role_reset refusal, getSession still 200 as customer."""
