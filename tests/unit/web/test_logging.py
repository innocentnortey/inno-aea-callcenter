"""AEA-23 AC-17: the allow-list log formatter and the `request` record's route template.

Failure mode guarded: negative (a value in a path parameter, a query string, a request body, an unlisted extra field or
a free-text log line never reaches the log; only web section 10's fields do).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi import Body

from meridian.web.logging import (
    ALLOWED_FIELDS,
    AUTH_LOGGER,
    RECORD_ATTR,
    REQUEST_LOGGER,
    SIGNAL_LOGGER,
    STREAM_LOGGER,
    auth_event,
    emit_record,
    request_record,
)
from tests.api.web_shell_support import (
    FakeSessionStore,
    add_test_route,
    captured_log,
    cookie_header,
    log_records,
    make_client,
    make_settings,
    rand_word,
    records_of,
    web_app,
)

REQUEST_FIELDS = {"record", "request_id", "route", "status", "duration_ms", "caller_role", "thread_id"}
SIGNAL_FIELDS = {
    "record", "name", "turn_id", "thread_id", "request_id", "run_tag", "node", "cause", "role", "specialist",
    "attempt", "recovered",
}  # fmt: skip


def echo_endpoint(item: str, payload: dict[str, Any] = Body(...)) -> dict[str, str]:  # noqa: B008
    return {"item": "ok"}


def test_allow_list_formatter_drops_raw_path_query_body_and_extras(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """negative (AC-17): only allow-listed scalar fields leave the process; each kind's key set matches web section 10."""
    assert set(ALLOWED_FIELDS) == {"request", "auth_event", "stream_reconnect", "signal"}
    assert ALLOWED_FIELDS["request"] == REQUEST_FIELDS | {"error_kind"}
    assert ALLOWED_FIELDS["auth_event"] == {"record", "request_id", "outcome", "session_id", "at"}
    assert ALLOWED_FIELDS["stream_reconnect"] == {
        "record",
        "request_id",
        "thread_id",
        "case_ref",
        "last_event_id",
        "replayed",
    }
    assert ALLOWED_FIELDS["signal"] == SIGNAL_FIELDS

    distinct = {
        kind: rand_word(14, kind) for kind in ("path", "query", "body", "extra", "freetext", "signalextra")
    }

    # Unit level: every kind, each with an extra unlisted field that must be dropped.
    with captured_log() as stream:
        stamp = datetime(2031, 1, 1, tzinfo=UTC)
        base_request = request_record(
            request_id="r-1",
            route="/x/{id}",
            status=200,
            duration_ms=3,
            caller_role="anonymous",
            thread_id=None,
            error_kind=None,
        )
        emit_record(REQUEST_LOGGER, {**base_request, "extra_field": distinct["extra"]})
        emit_record(
            AUTH_LOGGER,
            {
                **auth_event(request_id="r-2", outcome="ok", session_id="s-1", at=stamp),
                "password": distinct["extra"],
            },
        )
        emit_record(
            STREAM_LOGGER,
            {
                "record": "stream_reconnect",
                "request_id": "r-3",
                "thread_id": "t-1",
                "case_ref": None,
                "last_event_id": 4,
                "replayed": 2,
                "payload": distinct["extra"],
            },
        )
        logging.getLogger(REQUEST_LOGGER).info(
            "raw", extra={RECORD_ATTR: {"record": "request", "request_id": "r-4", "route": "/y", "status": 200, "duration_ms": 1,
                                        "caller_role": "anonymous", "thread_id": None, "extra_field": distinct["extra"]}}
        )  # fmt: skip
        signal_fields = {
            "record": "signal", "name": "classifier_fallback", "turn_id": "u-1", "thread_id": "t-1", "request_id": "r-5",
            "run_tag": "live", "node": "plan", "cause": "timeout", "role": "classifier", "specialist": None, "attempt": 1,
            "recovered": True,
        }  # fmt: skip
        logging.getLogger(SIGNAL_LOGGER).info(
            "signal", extra={"signal": {**signal_fields, "payload": distinct["signalextra"]}}
        )
        logging.getLogger("meridian.other").info("free text " + distinct["freetext"])
    lines = log_records(stream)
    for label in ("extra", "signalextra", "freetext"):
        assert distinct[label] not in stream.getvalue(), label
    assert len(lines) == 6
    for record in lines[:5]:
        kind = record["record"]
        assert set(record) <= ALLOWED_FIELDS[kind], (kind, set(record) - ALLOWED_FIELDS[kind])
    assert set(lines[4]) == SIGNAL_FIELDS
    assert set(lines[0]) == REQUEST_FIELDS

    # Request level: the record carries the route template, never the raw path, query or body.
    store = FakeSessionStore()
    app = web_app(monkeypatch, make_settings(tmp_path), store=store)
    add_test_route(app, "POST", "/api/test/echo/{item}", echo_endpoint)
    token = store.issue()
    with make_client(app) as client, captured_log() as http_stream:
        response = client.post(
            f"/api/test/echo/{distinct['path']}?q={distinct['query']}",
            json={"secret_field": distinct["body"]},
            headers=cookie_header(token),
        )
    assert response.status_code == 200
    requests = records_of(http_stream, "request")
    assert len(requests) == 1
    assert requests[0]["route"] == "/api/test/echo/{item}"
    assert set(requests[0]) == REQUEST_FIELDS
    for label in ("path", "query", "body"):
        assert distinct[label] not in http_stream.getvalue(), label
