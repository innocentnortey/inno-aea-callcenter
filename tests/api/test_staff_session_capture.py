"""AEA-44 AC-16: the three CON-10 entry points through the app the real container builds leave one ``request`` record
each, with the caller's role (WF-4: "staff role on every action").

Failure mode guarded: invariant (record per call; role resolved before the route runs). Temp SQLite via the container.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.api.staff_session_support import container_app, login_token, switch, tab
from tests.api.web_shell_support import captured_log, make_client, records_of


def test_wf4_session_entry_points_emit_records(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    h = container_app(monkeypatch, tmp_path)
    with captured_log() as stream, make_client(h.app) as client:
        token = login_token(client, h.settings)
        calls = [
            ("GET /api/session", client.get("/api/session", headers=tab(token)), "customer"),
            ("GET /api/session/roles", client.get("/api/session/roles", headers=tab(token)), "customer"),
            ("PUT /api/session/role", switch(client, token, "representative"), "customer"),
            ("GET /api/staff/queue", client.get("/api/staff/queue", headers=tab(token)), "representative"),
        ]
        records = records_of(stream, "request")
    for label, response, role in calls:
        assert response.status_code == 200, f"{label}: {response.text}"
        request_id = response.headers["X-Request-ID"]
        mine = [r for r in records if r.get("request_id") == request_id]
        assert len(mine) == 1, f"{label}: {len(mine)} request records"
        record = mine[0]
        assert record["route"] == label.split(" ", 1)[1]
        assert record["status"] == 200
        assert record["caller_role"] == role
        print(label, record)
