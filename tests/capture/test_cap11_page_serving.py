"""AEA-49 CAP-11: page and asset requests leave one `request` record each, with templates, never raw paths."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from meridian.web.app import ContainerOverrides
from meridian.web.frontend import DistDirectory
from tests.api.frontend_support import FrontendApp, frontend_app, install_socket_guard
from tests.api.web_shell_support import (
    app_log_text,
    captured_log,
    cookie_header,
    make_client,
    records_of,
)
from tests.fakes.trace import InMemoryTraceSink

DEEP = "/staff/cases/MHC-C-0007?tab=brief"


def build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[FrontendApp, InMemoryTraceSink]:
    sink = InMemoryTraceSink()
    return frontend_app(monkeypatch, tmp_path, overrides=ContainerOverrides(trace=sink)), sink


def six_calls(client: Any, token: str) -> list[Any]:
    headers = cookie_header(token)
    return [
        client.get("/", headers=headers),
        client.get(DEEP, headers=headers),
        client.get("/assets/app.js", headers=headers),
        client.get("/"),
        client.get(DEEP),
        client.get("/assets/app.js"),
    ]


def test_page_requests_recorded(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    h, _ = build(monkeypatch, tmp_path)
    with make_client(h.app) as client, captured_log() as stream:
        responses = six_calls(client, h.store.issue())
    records = records_of(stream, "request")
    for record in records:
        print(record)
    assert len(records) == 6
    routes = [
        "spa_fallback",
        "spa_fallback",
        "/assets/{file}",
        "spa_fallback",
        "spa_fallback",
        "/assets/{file}",
    ]
    statuses = [200, 200, 200, 303, 303, 200]
    roles = ["customer", "customer", "anonymous", "anonymous", "anonymous", "anonymous"]
    for record, response, route, status, role in zip(
        records, responses, routes, statuses, roles, strict=True
    ):
        assert record["request_id"] == response.headers["X-Request-ID"]
        assert record["route"] == route
        assert record["status"] == status
        assert record["caller_role"] == role


def test_no_raw_path_query_or_cookie(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    h, sink = build(monkeypatch, tmp_path)
    token = h.store.issue()
    caplog.set_level(logging.DEBUG)
    with make_client(h.app) as client, captured_log() as stream:
        six_calls(client, token)
    haystack = "\n".join(
        [
            stream.getvalue(),
            app_log_text(caplog),
            *(repr(r.__dict__) for r in caplog.records if r.name.startswith("meridian")),
            repr(sink.turns),
        ]
    )
    for needle in ("/staff/cases/MHC-C-0007", "MHC-C-0007", "%2Fstaff%2Fcases", "tab=brief", token):
        hits = haystack.count(needle)
        print(needle if needle != token else "<token>", hits)
        assert hits == 0


def test_wf19_status_values_and_no_outbound(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    outbound = install_socket_guard(monkeypatch)
    h, _ = build(monkeypatch, tmp_path)
    token = h.store.issue()
    headers = cookie_header(token)
    with make_client(h.app) as client, captured_log() as stream:
        responses = [
            *six_calls(client, token),
            client.get("/staff/queue"),
            client.get("/assets/missing.js", headers=headers),
            client.get("/assets/missing.js"),
        ]
        records = records_of(stream, "request")
        assert len(records) == len(responses)
        for record, response in zip(records, responses, strict=True):
            print(response.status_code, record["status"], record.get("error_kind"))
            assert record["status"] == response.status_code
            assert "error_kind" not in record

        def raising(self: DistDirectory) -> bytes:
            raise OSError("zqreadfailure")

        monkeypatch.setattr(DistDirectory, "read_index", raising)
        failed = client.get("/", headers=headers)
        record = records_of(stream, "request")[-1]
        print(failed.status_code, record["status"], record.get("error_kind"))
        assert failed.status_code == 500
        assert failed.json() == {"request_id": failed.headers["X-Request-ID"]}
        assert "zqreadfailure" not in failed.text
        assert record["status"] == 500
        assert record["error_kind"]
    assert outbound == []
