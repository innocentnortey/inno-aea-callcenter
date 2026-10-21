"""AEA-49 J-1 over HTTP: the login gate and the built app, served from one origin.

Level: `mock-tested` (real `create_app`, `build_container` and AEA-23 gate; doubles for the login session store and
heartbeat; fixture dist; TestClient, no server, no browser). Blocked by: AEA-57 (journey harness: real server,
disposable DB, scripted model), AEA-44 (real StaffSessionStore), AEA-58 (browser J-1).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.api.frontend_support import INDEX_HTML, INDEX_MARKER, frontend_app, login_redirect
from tests.api.web_shell_support import cookie_header, login, make_client, session_cookie_value

pytestmark = pytest.mark.journey


def test_j1_login_gate_and_built_app_over_http(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    h = frontend_app(monkeypatch, tmp_path)
    with make_client(h.app) as client:
        for path in ("/", "/staff/queue"):
            r = client.get(path)
            assert r.status_code == 303
            assert r.headers["location"] == login_redirect(path)
        page = client.get("/login")
        assert page.status_code == 200
        assert page.content == INDEX_HTML.encode()
        urls = re.findall(r'(?:src|href)="(/(?:assets|fonts)/[^"]+)"', INDEX_HTML)
        assert urls
        for url in urls:
            assert client.get(url).status_code == 200, url
        signed = login(client, h.settings)
        assert signed.status_code == 200
        token = session_cookie_value(signed)
        assert token
        client.cookies.clear()
        headers = cookie_header(token)
        deep = client.get("/staff/cases/MHC-C-0007", headers=headers)
        assert deep.status_code == 200
        assert deep.content == INDEX_HTML.encode()
        api = client.get("/api/chat/sessions", headers=headers)
        assert api.headers["content-type"].startswith("application/json")
        assert INDEX_MARKER not in api.text
