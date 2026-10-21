"""AEA-49: serving the built frontend (stage7/web.md §12): SPA fallback, assets, public paths, traversal, cache."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from meridian.web.frontend import FrontendMissingError
from tests.api.frontend_support import (
    FILES,
    HASHED_ASSET,
    INDEX_HTML,
    INDEX_MARKER,
    OUTSIDE_MARKER,
    SCREEN_PATHS,
    frontend_app,
    login_redirect,
    raw_get,
)
from tests.api.web_shell_support import (
    add_test_route,
    assert_matches,
    cookie_header,
    effective_routes,
    error_body,
    login,
    make_client,
    session_cookie_value,
    set_cookie_lines,
)

SECRETS = (OUTSIDE_MARKER, "zqdotfilesecret", "zqrootdotfile")


def snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_spa_fallback_and_assets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    h = frontend_app(monkeypatch, tmp_path)
    assert h.dist is not None
    before = snapshot(h.dist)
    headers = cookie_header(h.store.issue())
    with make_client(h.app) as client:
        for path in SCREEN_PATHS:
            r = client.get(path, headers=headers)
            assert r.status_code == 200, path
            assert r.headers["content-type"].startswith("text/html"), path
            assert r.content == INDEX_HTML.encode(), path
            assert r.headers["cache-control"] == "no-cache", path
        js = client.get("/assets/app.js", headers=headers)
        assert js.status_code == 200
        assert js.content == FILES["assets/app.js"]
        assert js.headers["content-type"].split(";")[0] == "text/javascript"
        font = client.get("/fonts/f.woff2", headers=headers)
        assert font.status_code == 200
        assert font.content == FILES["fonts/f.woff2"]
        assert font.headers["content-type"].split(";")[0] == "font/woff2"
    assert snapshot(h.dist) == before
    print("12 paths + 2 files")


def test_api_and_healthz_not_shadowed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    h = frontend_app(monkeypatch, tmp_path)
    add_test_route(h.app, "GET", "/api/test/ping", lambda: {"pong": True})
    headers = cookie_header(h.store.issue())
    with make_client(h.app) as client:
        ping = client.get("/api/test/ping", headers=headers)
        assert ping.status_code == 200
        assert ping.json() == {"pong": True}
        for path in ("/api/no-such-route", "/api"):
            r = client.get(path, headers=headers)
            print(path, r.headers["content-type"], r.text)
            assert r.status_code == 404
            assert r.headers["content-type"].startswith("application/json")
            assert r.json() == {"detail": "Not Found"}
            assert INDEX_MARKER not in r.text
        health = client.get("/healthz")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}
        posted = client.post("/staff/queue", headers=headers)
        assert posted.status_code != 200
        assert INDEX_MARKER not in posted.text


def test_pages_behind_login(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    h = frontend_app(monkeypatch, tmp_path)
    with make_client(h.app) as client:
        for path in SCREEN_PATHS:
            r = client.get(path)
            print(path, r.status_code, r.headers.get("location"))
            if path == "/login":
                assert r.status_code == 200
                continue
            assert r.status_code == 303, path
            assert r.headers["location"] == login_redirect(path)
            assert INDEX_MARKER not in r.text
        assert client.get("/assets/app.js").status_code == 200
        assert client.get("/fonts/f.woff2").status_code == 200
        query = "/staff/cases/MHC-C-0007?tab=brief"
        q = client.get(query)
        assert q.status_code == 303
        assert q.headers["location"] == login_redirect(query)
        expired = h.store.issue()
        h.store.expire(expired)
        e = client.get("/staff/queue", headers=cookie_header(expired))
        assert e.status_code == 303
        assert e.headers["location"] == login_redirect("/staff/queue", "expired")
        cookies = set_cookie_lines(e)
        assert len(cookies) == 1
        assert cookies[0].startswith("mhc_session=;")
        assert "Max-Age=0" in cookies[0]
        api = client.get("/api/staff/queue")
        body = error_body(api, 401, "UNAUTHENTICATED")
        assert body["error"]["details"] == {"reason": "none"}
        assert_matches(api, "getQueue")
    entries = h.app.state.web_shell.public_paths.entries()
    assert {
        ("exact", "GET", "/login"),
        ("prefix", "GET", "/assets/"),
        ("prefix", "GET", "/fonts/"),
    } <= entries
    extra = {e for e in entries if e[1] == "GET"} - {
        ("exact", "GET", "/login"),
        ("prefix", "GET", "/assets/"),
        ("prefix", "GET", "/fonts/"),
        ("exact", "GET", "/healthz"),
    }
    assert extra == set()


def test_no_path_traversal_or_open_redirect(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    h = frontend_app(monkeypatch, tmp_path)
    token = h.store.issue()
    asset_like = (
        "/assets/../../pyproject.toml",
        "/assets/.env",
        "/fonts/../index.html",
    )
    page_like = ("/.env", "/../pyproject.toml")
    locations: list[str] = []
    with make_client(h.app) as client:
        for tok in (token, None):
            for path in (*asset_like, *page_like):
                r = raw_get(client, path, token=tok)
                print(tok is not None, path, r.status)
                body = r.body.decode(errors="replace")
                assert not any(s in body for s in SECRETS), path
                if tok is not None or path in asset_like:
                    assert r.status == 404, path
                else:
                    assert r.status == 303, path
                if "location" in r.headers:
                    locations.append(r.headers["location"])
        encoded = "/assets/%2e%2e/%2e%2e/pyproject.toml"
        for headers in (cookie_header(token), {}):
            r2 = client.get(encoded, headers=headers)
            print(encoded, r2.status_code)
            assert r2.status_code == 404
            assert not any(s in r2.text for s in SECRETS)
        login_page = client.get("/login?return_to=//evil.example")
        assert login_page.status_code == 200
        assert "location" not in login_page.headers
        for evil in ("//evil.example", "/\\evil.example"):
            r3 = raw_get(client, evil)
            assert r3.status == 303, evil
            assert r3.headers["location"].startswith("/login")
            assert "evil.example" not in r3.headers["location"]
            locations.append(r3.headers["location"])
    assert all(loc.startswith("/") and not loc.startswith("//") for loc in locations)


def test_missing_dist(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    h = frontend_app(monkeypatch, tmp_path / "a", with_dist=False)
    add_test_route(h.app, "GET", "/api/test/ping", lambda: {"pong": True})
    caplog.set_level(logging.WARNING, logger="meridian.web.frontend")
    with make_client(h.app) as client:
        records = [r for r in caplog.records if r.name == "meridian.web.frontend"]
        assert len(records) == 1
        assert records[0].levelno == logging.WARNING
        assert records[0].getMessage() == "frontend_dist_missing"
        headers = cookie_header(h.store.issue())
        assert client.get("/api/test/ping", headers=headers).status_code == 200
        nf = client.get("/staff/queue", headers=headers)
        print(nf.status_code, nf.text)
        assert nf.status_code == 404
        assert nf.json() == {"detail": "Not Found"}
        assert client.get("/staff/queue").status_code == 303
        login_page = client.get("/login")
        assert login_page.status_code == 404
        assert login_page.json() == {"detail": "Not Found"}
    paths = {r.path for r in effective_routes(h.app)}
    assert not paths & {"spa_fallback", "/assets/{file}", "/fonts/{file}"}

    # (b) assets but no index.html
    caplog.clear()
    h2 = frontend_app(monkeypatch, tmp_path / "b", with_dist=True)
    assert h2.dist is not None
    (h2.dist / "index.html").unlink()
    with make_client(h2.app):
        pass
    records = [r for r in caplog.records if r.name == "meridian.web.frontend"]
    assert [r.getMessage() for r in records] == ["frontend_dist_missing"]
    assert not {r.path for r in effective_routes(h2.app)} & {"spa_fallback", "/assets/{file}"}

    # (c) required
    h3 = frontend_app(monkeypatch, tmp_path / "c", with_dist=False, require_frontend=True)
    with pytest.raises(FrontendMissingError) as err, make_client(h3.app):
        pass
    print(err.value)
    assert "MERIDIAN_REQUIRE_FRONTEND" in str(err.value)
    assert str(tmp_path / "c" / "no-dist") in str(err.value)


def test_cache_headers_and_missing_asset_404(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    h = frontend_app(monkeypatch, tmp_path)
    headers = cookie_header(h.store.issue())
    immutable = "public, max-age=31536000, immutable"
    with make_client(h.app) as client:
        for hdrs in ({}, headers):
            assert client.get("/login", headers=hdrs).headers["cache-control"] == "no-cache"
            assert client.get("/assets/app.js", headers=hdrs).headers["cache-control"] == immutable
            assert client.get(HASHED_ASSET, headers=hdrs).headers["cache-control"] == immutable
            for missing in ("/assets/missing.js", "/fonts/missing.woff2"):
                r = client.get(missing, headers=hdrs)
                print(missing, r.status_code, dict(r.headers))
                assert r.status_code == 404
                assert r.headers["content-type"].startswith("application/json")
                assert INDEX_MARKER not in r.text
        for path in ("/", "/staff/queue"):
            assert client.get(path, headers=headers).headers["cache-control"] == "no-cache"


def test_example_pair(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    h = frontend_app(monkeypatch, tmp_path)
    with make_client(h.app) as client:
        r = client.get("/staff/queue")
        assert r.status_code == 303
        assert r.headers["location"] == "/login?return_to=%2Fstaff%2Fqueue&reason=none"
        assert client.get("/login").content == INDEX_HTML.encode()
        assert client.get(HASHED_ASSET).status_code == 200
        assert client.get("/fonts/f.woff2").status_code == 200
        signed = login(client, h.settings)
        assert signed.status_code == 200
        token = session_cookie_value(signed)
        assert token
        client.cookies.clear()
        headers = cookie_header(token)
        deep = client.get("/staff/cases/MHC-C-0007", headers=headers)
        assert deep.status_code == 200
        assert deep.content == INDEX_HTML.encode()
        api = client.get("/api/staff/cases/MHC-C-0007", headers=headers)
        assert api.headers["content-type"].startswith("application/json")
        assert INDEX_MARKER not in api.text
        nf = client.get("/api/no-such-route", headers=headers)
        assert nf.status_code == 404
        assert nf.headers["content-type"].startswith("application/json")
