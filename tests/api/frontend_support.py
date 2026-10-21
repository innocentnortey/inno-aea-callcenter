"""AEA-49 test support: a fixture dist, an app builder, a raw-ASGI caller and an outbound-socket guard.

Everything is synthetic and built per test under `tmp_path`. The real `apps/web/dist` is never read. Distinctive
values are letters only, so none can look like a verification code, a card number or a phone number.
"""

from __future__ import annotations

import socket
import urllib.parse
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from meridian.config import Settings
from meridian.web.app import ContainerOverrides
from tests.api.web_shell_support import FakeHeartbeat, FakeSessionStore, full_app, make_settings

INDEX_MARKER = "zqfixtureindexpage"
HASHED_ASSET = "/assets/index-AbCdEf.js"
INDEX_HTML = (
    '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>' + INDEX_MARKER + "</title>"
    '<script type="module" crossorigin src="' + HASHED_ASSET + '"></script>'
    '<link rel="stylesheet" href="/assets/app.css"><link rel="preload" href="/fonts/f.woff2" as="font">'
    '</head><body><div id="root"></div></body></html>'
)
FILES: Mapping[str, bytes] = {
    "assets/app.js": b"console.log('zqappscript');\n",
    "assets/index-AbCdEf.js": b"export const zq = 'zqhashedscript';\n",
    "assets/app.css": b"body{margin:0}\n",
    "fonts/f.woff2": b"wOF2zqfixturefont",
    "assets/.env": b"ZQ_DOTFILE=zqdotfilesecret\n",
    ".env": b"ZQ_ROOT_DOTFILE=zqrootdotfile\n",
    "favicon.svg": b"<svg xmlns='http://www.w3.org/2000/svg'/>",
}
OUTSIDE_MARKER = "zqoutsidepyproject"
SCREEN_PATHS = (
    "/",
    "/demo",
    "/demo/inbox",
    "/role",
    "/staff/queue",
    "/staff/cases/MHC-C-0007",
    "/staff/oversight",
    "/staff/flags",
    "/staff/owner",
    "/monitoring",
    "/eval",
    "/login",
)


def build_fixture_dist(base: Path) -> Path:
    """Write base/dist (index.html + FILES) and base/pyproject.toml holding OUTSIDE_MARKER. Returns the dist path."""
    dist = base / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    for relative, content in FILES.items():
        target = dist / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    (base / "pyproject.toml").write_text(f"# {OUTSIDE_MARKER}\n", encoding="utf-8")
    return dist


@dataclass
class FrontendApp:
    app: FastAPI
    settings: Settings
    store: FakeSessionStore
    dist: Path | None


def frontend_app(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    with_dist: bool = True,
    require_frontend: bool = False,
    overrides: ContainerOverrides | None = None,
) -> FrontendApp:
    """The real `create_app` over the real container, with the fixture dist (or a missing folder) configured."""
    dist = build_fixture_dist(tmp_path) if with_dist else None
    settings = make_settings(
        tmp_path,
        web_dist_dir=dist if dist is not None else tmp_path / "no-dist",
        require_frontend=require_frontend,
    )
    store = FakeSessionStore()
    app = full_app(monkeypatch, settings, store=store, heartbeat=FakeHeartbeat(), overrides=overrides)
    return FrontendApp(app=app, settings=settings, store=store, dist=dist)


def login_redirect(path_and_query: str, reason: str = "none") -> str:
    """The gate's redirect target, e.g. '/staff/queue' -> '/login?return_to=%2Fstaff%2Fqueue&reason=none'."""
    return "/login?return_to=" + urllib.parse.quote(path_and_query, safe="") + "&reason=" + reason


@dataclass(frozen=True)
class RawResponse:
    status: int
    headers: dict[str, str]
    set_cookies: list[str]
    body: bytes


def raw_get(client: TestClient, raw_path: str, *, token: str | None = None) -> RawResponse:
    """Call the app's ASGI callable directly so dot segments reach the server un-normalised.

    The HTTP client rewrites '/assets/../../x' to '/x' before sending. The client must be entered (`with`).
    """
    path, _, query = raw_path.partition("?")
    headers: list[tuple[bytes, bytes]] = [(b"host", b"testserver")]
    if token is not None:
        headers.append((b"cookie", f"mhc_session={token}".encode()))
    scope: dict[str, Any] = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": query.encode(),
        "headers": headers,
        "client": ("198.51.100.7", 50000),
        "server": ("testserver", 80),
    }
    sent: list[MutableMapping[str, Any]] = []

    async def receive() -> MutableMapping[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: MutableMapping[str, Any]) -> None:
        sent.append(message)

    assert client.portal is not None
    client.portal.call(client.app, scope, receive, send)
    status = 0
    out_headers: dict[str, str] = {}
    cookies: list[str] = []
    body = b""
    for message in sent:
        if message["type"] == "http.response.start":
            status = message["status"]
            for name, value in message["headers"]:
                key = name.decode().lower()
                if key == "set-cookie":
                    cookies.append(value.decode())
                out_headers[key] = value.decode()
        elif message["type"] == "http.response.body":
            body += message.get("body", b"")
    return RawResponse(status=status, headers=out_headers, set_cookies=cookies, body=body)


def install_socket_guard(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """Refuse any non-loopback connect; the returned list holds the refused addresses (empty = none)."""
    outbound: list[Any] = []
    real_connect = socket.socket.connect
    real_create = socket.create_connection
    loopback = {"127.0.0.1", "::1", "localhost"}

    def guarded_connect(self: socket.socket, address: Any) -> Any:
        if isinstance(address, tuple) and address[0] not in loopback:
            outbound.append(address)
            raise AssertionError(f"outbound connect to {address[0]}")
        return real_connect(self, address)

    def guarded_create(address: Any, *args: Any, **kwargs: Any) -> Any:
        if address[0] not in loopback:
            outbound.append(address)
            raise AssertionError(f"outbound connect to {address[0]}")
        return real_create(address, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "create_connection", guarded_create)
    return outbound
