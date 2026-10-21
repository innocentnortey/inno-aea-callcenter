"""Structured log records through an allow-list formatter (web.md section 10, WEB-11).

Only allow-listed keys with scalar values leave the process; free text is reduced to its length by the LOG
redaction profile. No username, password, cookie, eval key, request body, raw path or query string is ever logged.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Literal

from meridian.privacy.redact import RedactionProfile, redact

REQUEST_LOGGER = "meridian.web.request"
AUTH_LOGGER = "meridian.web.auth"
STREAM_LOGGER = "meridian.web.stream"  # AEA-41 emits stream_reconnect through emit_record(STREAM_LOGGER, ...)
SIGNAL_LOGGER = "meridian.signal"  # AEA-21 emits with extra={"signal": record.model_dump(mode="json")}
RECORD_ATTR = "meridian_record"
ROOT_LOGGER = "meridian"
HANDLER_NAME = "meridian-allow-list"
ALLOWED_FIELDS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "request": frozenset(
            {
                "record",
                "request_id",
                "route",
                "status",
                "duration_ms",
                "caller_role",
                "thread_id",
                "error_kind",
            }
        ),
        "auth_event": frozenset({"record", "request_id", "outcome", "session_id", "at"}),
        "stream_reconnect": frozenset(
            {"record", "request_id", "thread_id", "case_ref", "last_event_id", "replayed"}
        ),
        "signal": frozenset(
            {
                "record",
                "name",
                "turn_id",
                "thread_id",
                "request_id",
                "run_tag",
                "node",
                "cause",
                "role",
                "specialist",
                "attempt",
                "recovered",
            }
        ),
    }
)
_SCALARS = (str, int, float, bool, type(None))


def emit_record(logger_name: str, fields: Mapping[str, object]) -> None:
    logging.getLogger(logger_name).info(str(fields["record"]), extra={RECORD_ATTR: dict(fields)})


def request_record(
    *,
    request_id: str,
    route: str,
    status: int,
    duration_ms: int,
    caller_role: str,
    thread_id: str | None,
    error_kind: str | None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "record": "request",
        "request_id": request_id,
        "route": route,
        "status": status,
        "duration_ms": duration_ms,
        "caller_role": caller_role,
        "thread_id": thread_id,
    }
    if status >= 500:
        record["error_kind"] = error_kind
    return record


def auth_event(
    *,
    request_id: str,
    outcome: Literal["ok", "rejected", "rate_limited", "logged_out"],
    session_id: str | None,
    at: datetime,
) -> dict[str, object]:
    return {
        "record": "auth_event",
        "request_id": request_id,
        "outcome": outcome,
        "session_id": session_id,
        "at": at.astimezone(UTC).isoformat(),
    }


class AllowListFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = record.__dict__.get(RECORD_ATTR)
        kind: object = None
        if isinstance(payload, Mapping):
            kind = payload.get("record")
        else:
            payload = record.__dict__.get("signal")
            if isinstance(payload, Mapping):
                kind = payload.get("record", "signal")
        out: dict[str, object]
        if isinstance(payload, Mapping) and isinstance(kind, str) and kind in ALLOWED_FIELDS:
            out = {
                key: payload[key]
                for key in sorted(ALLOWED_FIELDS[kind])
                if key in payload and isinstance(payload[key], _SCALARS)
            }
            if kind == "signal" and "record" not in out:
                out["record"] = "signal"
        else:
            out = {
                "record": "log",
                "logger": record.name,
                "level": record.levelname,
                "length": redact(record.getMessage(), RedactionProfile.LOG).length,
            }
            if record.exc_info and record.exc_info[0]:
                out["exc_type"] = record.exc_info[0].__name__
        return json.dumps(out, sort_keys=True, separators=(",", ":"))


def install_log_formatter() -> None:
    logger = logging.getLogger(ROOT_LOGGER)
    if any(handler.name == HANDLER_NAME for handler in logger.handlers):
        return
    handler = logging.StreamHandler()
    handler.set_name(HANDLER_NAME)
    handler.setFormatter(AllowListFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
