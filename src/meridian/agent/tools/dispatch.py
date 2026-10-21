"""Tool dispatch: schemas for the model, the guard, execution, and one lookup-log row per call.

A specialist model may ask for a tool; this module decides whether it runs (stage7/graph-tools.md
section 1, GRT-1; DO-4 section 5). Every request is checked in a fixed order (known tool, allowed
kind, valid arguments, verified customer) before the executor the owning area supplied is called.
The model always gets JSON back, never an exception, and every call leaves exactly one lookup row.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
import types
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final, Protocol, cast

from pydantic import JsonValue, ValidationError

from meridian.domain.common import LLMFacing, MeridianModel, ToolErrorCode
from meridian.domain.tools import (
    LookupEntry,
    ToolCallRecord,
    ToolCallScope,
    ToolDef,
    ToolError,
    ToolKind,
    ToolResult,
)
from meridian.ports.models import ToolCall, ToolSchema
from meridian.ports.runtime import UnitOfWorkFactory
from meridian.privacy.redact import RedactionProfile, redact

__all__ = ["MAX_CONTENT_CHARS", "DispatchedCall", "ToolDispatcher", "ToolRegistry"]

_log = logging.getLogger(__name__)
MAX_CONTENT_CHARS: Final = 4_000
_NAME_RE: Final = re.compile(r"[a-z_]{1,64}")
_MUST_VERIFY: Final = frozenset(
    {
        ToolKind.ACCOUNT_READ,
        ToolKind.BOOK,
        ToolKind.MOVE,
        ToolKind.CANCEL,
        ToolKind.CHANGE_REQUEST,
    }
)
_SCOPE_FIELDS: Final = frozenset(ToolCallScope.model_fields)
_NO_RECURSE: Final = frozenset({"default", "examples", "const", "enum"})
_MESSAGES: Final[Mapping[ToolErrorCode, str]] = types.MappingProxyType(
    {
        ToolErrorCode.UNKNOWN_TOOL: "No tool with that name is available. Use only the tools you were given.",
        ToolErrorCode.NOT_ALLOWED: "That tool is not available for this task.",
        ToolErrorCode.BAD_ARGUMENTS: "The arguments did not match the tool's input schema.",
        ToolErrorCode.NOT_VERIFIED: (
            "The customer has not been verified yet. Account tools work only after the "
            "one-time code is entered."
        ),
        ToolErrorCode.TOOL_FAILED: "The tool could not complete this request.",
    }
)


class _LookupLogAppend(Protocol):
    def append(self, entry: LookupEntry) -> int: ...


class _HasLookupLog(Protocol):
    lookup_log: _LookupLogAppend


def _elapsed_ms(t0: float) -> int:
    return max(0, int((time.perf_counter() - t0) * 1000))


def _strip_titles(node: Any) -> Any:
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for key, value in node.items():
            if key == "title" and isinstance(value, str):
                continue
            if key in ("properties", "$defs") and isinstance(value, dict):
                out[key] = {name: _strip_titles(sub) for name, sub in value.items()}
            elif key in _NO_RECURSE:
                out[key] = value
            else:
                out[key] = _strip_titles(value)
        return out
    if isinstance(node, list):
        return [_strip_titles(v) for v in node]
    return node


def _trimmed_schema(args_model: type[LLMFacing]) -> dict[str, JsonValue]:
    return cast(dict[str, JsonValue], _strip_titles(args_model.model_json_schema()))


def _property_names(schema: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key == "properties" and isinstance(value, dict):
                names.update(str(n) for n in value)
            names |= _property_names(value)
    elif isinstance(schema, list):
        for item in schema:
            names |= _property_names(item)
    return names


def _unknown_name(name: str) -> str:
    return redact(name, RedactionProfile.STORE).text[:64]


def _bad_args_message(exc: ValidationError | None, args_model: type[LLMFacing]) -> str:
    base = _MESSAGES[ToolErrorCode.BAD_ARGUMENTS]
    if exc is None:
        return base + " The arguments could not be read as JSON."
    parts: list[str] = []
    for err in exc.errors(include_url=False, include_context=False, include_input=False)[:5]:
        loc = err["loc"]
        first = loc[0] if loc else ""
        if isinstance(first, str) and first in args_model.model_fields:
            field = first
        elif err["type"] == "extra_forbidden":
            field = "unexpected_field"
        else:
            field = "arguments"
        parts.append(f"{field}: {err['type']}")
    return base + " Problems: " + "; ".join(parts) + "."


def _stamped(entry: LookupEntry, tool: str, scope: ToolCallScope) -> LookupEntry:
    return LookupEntry(
        tool=tool,
        record_ids=entry.record_ids,
        passage_ids=entry.passage_ids,
        result_seen=redact(entry.result_seen, RedactionProfile.STORE).text,
        message_id=scope.message_id,
        turn_id=scope.ids.turn_id,
    )


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _render(for_model: ToolError | JsonValue) -> tuple[str, int]:
    if isinstance(for_model, ToolError):
        text = _dumps({"error": for_model.model_dump(mode="json")})
    else:
        text = _dumps(for_model)
    if len(text) <= MAX_CONTENT_CHARS:
        return text, len(text)
    keep = MAX_CONTENT_CHARS - 64
    while True:
        candidate = _dumps({"truncated": True, "partial": text[:keep]})
        if len(candidate) <= MAX_CONTENT_CHARS:
            return candidate, len(text)
        keep = max(0, keep - (len(candidate) - MAX_CONTENT_CHARS))


def _append_lookup(uow: UnitOfWorkFactory, entry: LookupEntry) -> int:
    # CoreRepos.lookup_log is AEA-10's (cases.md 1.2); typed structurally so this module builds before it lands.
    with uow(write=True) as tx:
        row_id = cast(_HasLookupLog, tx.core).lookup_log.append(entry)
        tx.commit()
    return row_id


class ToolRegistry:
    """The tools a deployment offers, checked once at start-up."""

    def __init__(self, defs: Iterable[ToolDef]) -> None:
        defs = tuple(defs)
        self._by_name: dict[str, ToolDef] = {}
        for d in defs:
            if not _NAME_RE.fullmatch(d.name):
                raise ValueError(f"tool name must match [a-z_]{{1,64}}: {d.name!r}")
            if d.name in self._by_name:
                raise ValueError(f"duplicate tool name: {d.name}")
            if d.kind in _MUST_VERIFY and not d.requires_verified:
                raise ValueError(f"tool {d.name}: kind {d.kind.value} must set requires_verified (R-14)")
            try:
                schema = _trimmed_schema(d.args_model)
            except Exception as exc:
                raise ValueError(f"tool {d.name}: args_model has no JSON schema") from exc
            bad = _property_names(schema) & _SCOPE_FIELDS
            if bad:
                raise ValueError(
                    f"tool {d.name}: arguments may not include scope fields: {', '.join(sorted(bad))}"
                )
            self._by_name[d.name] = d
        self._kinds = frozenset(d.kind for d in defs)

    def get(self, name: str) -> ToolDef | None:
        return self._by_name.get(name)

    def for_kinds(self, kinds: frozenset[ToolKind]) -> tuple[ToolDef, ...]:
        return tuple(sorted((d for d in self._by_name.values() if d.kind in kinds), key=lambda d: d.name))

    def check_covers(self, kinds: frozenset[ToolKind]) -> None:
        missing = sorted(k.value for k in kinds if k not in self._kinds)
        if missing:
            raise ValueError("no tool registered for kinds: " + ", ".join(missing))


class DispatchedCall(MeridianModel):
    tool_call_id: str
    content: str
    result: ToolResult
    record: ToolCallRecord


class ToolDispatcher:
    """Guards, runs and logs every tool call; never raises."""

    def __init__(self, registry: ToolRegistry, uow: UnitOfWorkFactory) -> None:
        self._registry = registry
        self._uow = uow
        self._schema_cache: dict[frozenset[ToolKind], tuple[ToolSchema, ...]] = {}
        self._lock = threading.Lock()

    def schemas(self, kinds: frozenset[ToolKind]) -> tuple[ToolSchema, ...]:
        key = frozenset(kinds)
        with self._lock:
            cached = self._schema_cache.get(key)
            if cached is None:
                cached = tuple(
                    ToolSchema(
                        name=d.name,
                        description=d.description,
                        input_schema=_trimmed_schema(d.args_model),
                        strict=True,
                    )
                    for d in self._registry.for_kinds(key)
                )
                self._schema_cache[key] = cached
            return cached

    def dispatch(
        self,
        calls: Sequence[ToolCall],
        *,
        kinds: frozenset[ToolKind],
        scope: ToolCallScope,
    ) -> tuple[DispatchedCall, ...]:
        return tuple(self._dispatch_one(c, kinds, scope) for c in calls)

    def _write_lookup(self, entry: LookupEntry, log_tool: str, scope: ToolCallScope) -> int | None:
        try:
            return _append_lookup(self._uow, entry)
        except Exception as exc:
            _log.error(
                "lookup_write_failed tool=%s error_type=%s turn_id=%s",
                log_tool,
                type(exc).__name__,
                scope.ids.turn_id,
            )
            return None

    def _dispatch_one(
        self, call: ToolCall, kinds: frozenset[ToolKind], scope: ToolCallScope
    ) -> DispatchedCall:
        t0 = time.perf_counter()
        try:
            return self._run(call, kinds, scope, t0)
        except Exception as exc:
            defn = self._registry.get(call.name)
            _log.error(
                "dispatch_internal_error tool=%s error_type=%s turn_id=%s",
                defn.name if defn else "unknown",
                type(exc).__name__,
                scope.ids.turn_id,
            )
            return self._refuse(call, defn, ToolErrorCode.TOOL_FAILED, scope, t0)

    def _run(
        self, call: ToolCall, kinds: frozenset[ToolKind], scope: ToolCallScope, t0: float
    ) -> DispatchedCall:
        defn = self._registry.get(call.name)
        if defn is None:
            return self._refuse(call, None, ToolErrorCode.UNKNOWN_TOOL, scope, t0)
        if defn.kind not in kinds:
            return self._refuse(call, defn, ToolErrorCode.NOT_ALLOWED, scope, t0)
        if call.args is None:
            return self._refuse(
                call,
                defn,
                ToolErrorCode.BAD_ARGUMENTS,
                scope,
                t0,
                message=_bad_args_message(None, defn.args_model),
            )
        try:
            args = defn.args_model.model_validate(call.args)
        except ValidationError as exc:
            return self._refuse(
                call,
                defn,
                ToolErrorCode.BAD_ARGUMENTS,
                scope,
                t0,
                message=_bad_args_message(exc, defn.args_model),
            )
        except Exception as exc:
            self._log_failed(defn, type(exc).__name__, scope)
            return self._refuse(call, defn, ToolErrorCode.TOOL_FAILED, scope, t0)
        if defn.requires_verified and scope.customer_id is None:
            return self._refuse(call, defn, ToolErrorCode.NOT_VERIFIED, scope, t0)

        try:
            result = defn.executor(args, scope)
        except Exception as exc:
            self._log_failed(defn, type(exc).__name__, scope)
            return self._refuse(call, defn, ToolErrorCode.TOOL_FAILED, scope, t0)
        if not isinstance(result, ToolResult):
            self._log_failed(defn, "bad_result", scope)
            return self._refuse(call, defn, ToolErrorCode.TOOL_FAILED, scope, t0)

        service_wrote = defn.effect == "write" and result.lookup_written
        try:
            content, full_len = _render(result.for_model)
        except Exception:
            self._log_failed(defn, "bad_result", scope)
            return self._refuse(
                call,
                defn,
                ToolErrorCode.TOOL_FAILED,
                scope,
                t0,
                existing=result.lookup if service_wrote else None,
            )
        if full_len > MAX_CONTENT_CHARS:
            _log.warning(
                "tool_result_truncated tool=%s chars=%d turn_id=%s",
                defn.name,
                full_len,
                scope.ids.turn_id,
            )

        if service_wrote:
            stored = result.lookup
            lookup_id = None
        else:
            stored = _stamped(result.lookup, defn.name, scope)
            lookup_id = self._write_lookup(stored, defn.name, scope)

        outcome: Any
        error: ToolErrorCode | None
        if isinstance(result.for_model, ToolError):
            error = result.for_model.code
            outcome = "failed" if error is ToolErrorCode.TOOL_FAILED else "refused"
        else:
            outcome, error = "ok", None
        record = ToolCallRecord(
            tool_call_id=call.id,
            name=defn.name,
            kind=defn.kind,
            outcome=outcome,
            error=error,
            record_ids=stored.record_ids,
            passage_ids=stored.passage_ids,
            lookup_id=lookup_id,
            elapsed_ms=_elapsed_ms(t0),
        )
        return DispatchedCall(
            tool_call_id=call.id,
            content=content,
            result=result.model_copy(update={"lookup": stored}),
            record=record,
        )

    @staticmethod
    def _log_failed(defn: ToolDef, error_type: str, scope: ToolCallScope) -> None:
        _log.warning(
            "tool_failed tool=%s error_type=%s turn_id=%s",
            defn.name,
            error_type,
            scope.ids.turn_id,
        )

    def _refuse(
        self,
        call: ToolCall,
        defn: ToolDef | None,
        code: ToolErrorCode,
        scope: ToolCallScope,
        t0: float,
        *,
        message: str | None = None,
        existing: LookupEntry | None = None,
    ) -> DispatchedCall:
        name = defn.name if defn is not None else _unknown_name(call.name)
        log_tool = defn.name if defn is not None else "unknown"
        failed = code is ToolErrorCode.TOOL_FAILED
        if not failed:
            _log.info("tool_refused tool=%s code=%s turn_id=%s", log_tool, code.value, scope.ids.turn_id)
        err = ToolError(
            code=code,
            message=message or _MESSAGES[code],
            retryable=code is ToolErrorCode.BAD_ARGUMENTS,
        )
        if existing is not None:
            entry = existing
            lookup_id = None
        else:
            entry = LookupEntry(
                tool=name,
                record_ids=(),
                passage_ids=(),
                result_seen="failed" if failed else f"refused:{code.value}",
                message_id=scope.message_id,
                turn_id=scope.ids.turn_id,
            )
            lookup_id = self._write_lookup(entry, log_tool, scope)
        content, _ = _render(err)
        record = ToolCallRecord(
            tool_call_id=call.id,
            name=name,
            kind=defn.kind if defn is not None else None,
            outcome="failed" if failed else "refused",
            error=code,
            record_ids=entry.record_ids,
            passage_ids=entry.passage_ids,
            lookup_id=lookup_id,
            elapsed_ms=_elapsed_ms(t0),
        )
        result = ToolResult(ok=False, for_model=err, captured=None, lookup=entry, lookup_written=False)
        return DispatchedCall(tool_call_id=call.id, content=content, result=result, record=record)
