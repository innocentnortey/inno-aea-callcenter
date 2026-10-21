"""AEA-22: `ToolDispatcher` (guard, guard order, one lookup row per call, safe errors). Frozen tests, written first.

Private-looking values are built at run time by `dispatch_doubles` makers, never literals. The module under test is
imported through a fixture so this file collects before `dispatch.py` exists.
"""

from __future__ import annotations

import ast
import importlib
import json
import logging
import re
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest

from meridian.domain.common import PassageId, ToolErrorCode
from meridian.domain.tools import ToolCallScope, ToolError, ToolKind
from meridian.ports.models import ToolCall
from meridian.ports.runtime import UnitOfWorkFactory
from tests.unit.agent.tools.dispatch_doubles import (
    MESSAGE_ID,
    OPEN_KINDS,
    WP2_INVOICE_FOR_MODEL,
    WP2_SNAPSHOT,
    WRITE_KINDS,
    Boom,
    EmptyArgs,
    ExecutorDouble,
    InvoiceArgs,
    KbArgs,
    NoteArgs,
    Recorder,
    RecordingUow,
    TitledArgs,
    card_like,
    foreign_customer_id,
    make_def,
    make_scope,
    private_values,
    property_names,
    six_digit_code,
    strip_titles,
)

LOGGER = "meridian.agent.tools.dispatch"
VERIFIED = "MHC-10002"


@pytest.fixture(scope="module")
def dispatch() -> ModuleType:
    return importlib.import_module("meridian.agent.tools.dispatch")


def _build(dispatch: ModuleType, defs: list[Any], uow: RecordingUow) -> Any:
    return dispatch.ToolDispatcher(dispatch.ToolRegistry(defs), cast(UnitOfWorkFactory, uow))


def _call(name: str, args: dict[str, Any] | None, call_id: str = "toolu_1") -> ToolCall:
    return ToolCall(id=call_id, name=name, args=args)


def _code(content: str) -> str:
    return str(json.loads(content)["error"]["code"])


# --- WP-2 --------------------------------------------------------------------------------------------------------
def test_wp2_invoice_read_before_and_after_code(dispatch: ModuleType) -> None:
    """regression (WP-2, US-8): refused before the code with no value leaked; runs and logs after the code."""
    uow = RecordingUow()
    ex = ExecutorDouble(
        "read_invoices",
        uow.recorder,
        uow,
        for_model=WP2_INVOICE_FOR_MODEL,
        record_ids=("INV-204411",),
        result_seen=WP2_SNAPSHOT,
    )
    d = _build(dispatch, [make_def("read_invoices", ToolKind.ACCOUNT_READ, InvoiceArgs, ex)], uow)
    kinds = frozenset({ToolKind.ACCOUNT_READ})
    call = _call("read_invoices", {"invoice_number": "INV-204411"}, "toolu_wp2_1")

    scope1 = make_scope(None)
    out = d.dispatch([call], kinds=kinds, scope=scope1)
    assert len(out) == 1
    assert out[0].tool_call_id == "toolu_wp2_1"
    err = json.loads(out[0].content)["error"]
    assert err["code"] == "not_verified"
    assert err["retryable"] is False
    assert isinstance(err["message"], str) and err["message"]
    assert "INV-204411" not in out[0].content and "478" not in out[0].content
    assert ex.calls == []
    assert len(uow.appended) == 1
    row = uow.appended[0]
    assert row.tool == "read_invoices"
    assert row.result_seen == "refused:not_verified"
    assert row.record_ids == () and row.passage_ids == ()
    assert row.message_id == MESSAGE_ID
    assert row.turn_id == scope1.ids.turn_id

    scope2 = make_scope(VERIFIED)
    out2 = d.dispatch([call], kinds=kinds, scope=scope2)
    assert len(ex.calls) == 1
    got_args, got_scope = ex.calls[0]
    assert cast(InvoiceArgs, got_args).invoice_number == "INV-204411"
    assert got_scope is scope2
    assert json.loads(out2[0].content) == WP2_INVOICE_FOR_MODEL
    assert len(uow.appended) == 2
    row2 = uow.appended[1]
    assert row2.record_ids == ("INV-204411",)
    assert row2.result_seen == WP2_SNAPSHOT
    assert row2.message_id == MESSAGE_ID
    assert row2.turn_id == scope2.ids.turn_id
    assert out2[0].record.outcome == "ok"
    assert out2[0].record.lookup_id == uow.returned_ids[-1]


# --- AC-1 --------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("kind", list(ToolKind), ids=lambda k: k.value)
def test_requires_verified_guard(dispatch: ModuleType, kind: ToolKind) -> None:
    """invariant (AC-1, R-14): every kind that requires verification refuses without a bound customer."""
    requires = kind not in OPEN_KINDS
    name = f"tool_{kind.value}"
    effect = "write" if kind in WRITE_KINDS else "read"
    kinds = frozenset(ToolKind)

    uow = RecordingUow()
    ex = ExecutorDouble(name, uow.recorder, uow)
    d = _build(
        dispatch, [make_def(name, kind, EmptyArgs, ex, requires_verified=requires, effect=effect)], uow
    )
    out = d.dispatch([_call(name, {})], kinds=kinds, scope=make_scope(None))[0]
    if requires:
        assert _code(out.content) == "not_verified"
        assert ex.calls == []
        assert out.record.outcome == "refused"
    else:
        assert len(ex.calls) == 1
        assert out.record.outcome == "ok"

    uow2 = RecordingUow()
    ex2 = ExecutorDouble(name, uow2.recorder, uow2)
    d2 = _build(
        dispatch, [make_def(name, kind, EmptyArgs, ex2, requires_verified=requires, effect=effect)], uow2
    )
    out2 = d2.dispatch([_call(name, {})], kinds=kinds, scope=make_scope(VERIFIED))[0]
    assert len(ex2.calls) == 1
    assert out2.record.outcome == "ok"


# --- AC-2 --------------------------------------------------------------------------------------------------------
GUARD_CASES = [
    pytest.param("no_such_tool", None, {ToolKind.ACCOUNT_READ}, "unknown_tool", id="unknown_with_bad_args"),
    pytest.param("read_invoices", None, {ToolKind.KB_SEARCH}, "not_allowed", id="not_allowed_beats_bad_args"),
    pytest.param(
        "read_invoices", None, {ToolKind.ACCOUNT_READ}, "bad_arguments", id="bad_args_none_beats_not_verified"
    ),
    pytest.param("kb_search", {"query": ""}, {ToolKind.KB_SEARCH}, "bad_arguments", id="bad_args_invalid"),
    pytest.param("read_invoices", {}, {ToolKind.ACCOUNT_READ}, "not_verified", id="not_verified"),
]


@pytest.mark.parametrize(("name", "args", "kinds", "expected"), GUARD_CASES)
def test_guard_order_and_codes(
    dispatch: ModuleType, name: str, args: dict[str, Any] | None, kinds: set[ToolKind], expected: str
) -> None:
    """invariant (AC-2): unknown, not_allowed, bad_arguments, then not_verified; an earlier code wins; no execution."""
    uow = RecordingUow()
    inv = ExecutorDouble("read_invoices", uow.recorder, uow)
    kb = ExecutorDouble("kb_search", uow.recorder, uow)
    d = _build(
        dispatch,
        [
            make_def("read_invoices", ToolKind.ACCOUNT_READ, InvoiceArgs, inv),
            make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, kb),
        ],
        uow,
    )
    call = _call(name, args, "toolu_guard")
    out = d.dispatch([call], kinds=frozenset(kinds), scope=make_scope(None))[0]
    parsed = json.loads(out.content)["error"]
    assert parsed["code"] == expected
    assert out.tool_call_id == call.id
    assert out.record.error == expected
    assert inv.calls == [] and kb.calls == []
    assert parsed["retryable"] is (expected == "bad_arguments")
    assert isinstance(out.result.for_model, ToolError)


# --- AC-3 --------------------------------------------------------------------------------------------------------
def test_every_call_answered_in_order(dispatch: ModuleType, caplog: pytest.LogCaptureFixture) -> None:
    """boundary (AC-3): same length and order; never raises; an executor exception becomes tool_failed."""
    caplog.set_level(logging.DEBUG)
    uow = RecordingUow()
    kb = ExecutorDouble("kb_search", uow.recorder, uow)
    boom = ExecutorDouble("boom", uow.recorder, uow, raises=Boom())
    d = _build(
        dispatch,
        [
            make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, kb),
            make_def("boom", ToolKind.KB_SEARCH, KbArgs, boom),
        ],
        uow,
    )
    kinds = frozenset({ToolKind.KB_SEARCH})
    calls = [
        _call("kb_search", {"query": "filters"}, "c1"),
        _call("no_such_tool", {"query": "x"}, "c2"),
        _call("boom", {"query": "x"}, "c3"),
        _call("kb_search", {"query": "drain"}, "c4"),
    ]
    out = d.dispatch(calls, kinds=kinds, scope=make_scope(None))
    assert [x.tool_call_id for x in out] == ["c1", "c2", "c3", "c4"]
    assert _code(out[2].content) == "tool_failed"
    assert json.loads(out[2].content)["error"]["retryable"] is False
    assert out[2].record.outcome == "failed"
    failed = [r for r in caplog.records if r.getMessage().startswith("tool_failed ")]
    assert len(failed) == 1
    assert "Boom" in failed[0].getMessage()
    assert card_like() not in failed[0].getMessage()
    assert all(len(x.content) <= 4000 for x in out)
    assert d.dispatch([], kinds=kinds, scope=make_scope(None)) == ()


def test_executor_returning_non_result_is_tool_failed(dispatch: ModuleType) -> None:
    """boundary (AC-3, S-9): an executor that returns something else than a ToolResult does not crash dispatch."""
    uow = RecordingUow()
    odd = ExecutorDouble("kb_search", uow.recorder, uow, returns_raw="not a ToolResult")
    d = _build(dispatch, [make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, odd)], uow)
    out = d.dispatch(
        [_call("kb_search", {"query": "x"})], kinds=frozenset({ToolKind.KB_SEARCH}), scope=make_scope(None)
    )[0]
    assert _code(out.content) == "tool_failed"
    assert out.record.outcome == "failed"


def test_oversized_result_is_truncated_json(dispatch: ModuleType, caplog: pytest.LogCaptureFixture) -> None:
    """boundary (AC-3, S-4): an over-long result becomes valid truncated JSON and stays ok."""
    caplog.set_level(logging.DEBUG)
    uow = RecordingUow()
    big = ExecutorDouble("kb_search", uow.recorder, uow, for_model={"text": "x" * 10_000})
    d = _build(dispatch, [make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, big)], uow)
    out = d.dispatch(
        [_call("kb_search", {"query": "x"})], kinds=frozenset({ToolKind.KB_SEARCH}), scope=make_scope(None)
    )[0]
    assert len(out.content) <= 4000
    assert json.loads(out.content)["truncated"] is True
    assert out.record.outcome == "ok"
    truncated = [r for r in caplog.records if r.getMessage().startswith("tool_result_truncated ")]
    assert len(truncated) == 1


@pytest.mark.parametrize("case", ["read", "service_written_write"])
def test_unrenderable_result_is_tool_failed(
    dispatch: ModuleType, caplog: pytest.LogCaptureFixture, case: str
) -> None:
    """boundary (S-10): a result that cannot be rendered becomes tool_failed and still leaves exactly one row."""
    caplog.set_level(logging.DEBUG)
    uow = RecordingUow()
    if case == "read":
        ex = ExecutorDouble("kb_search", uow.recorder, uow, unrenderable=True)
        d = _build(dispatch, [make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, ex)], uow)
        out = d.dispatch(
            [_call("kb_search", {"query": "x"})],
            kinds=frozenset({ToolKind.KB_SEARCH}),
            scope=make_scope(None),
        )[0]
        assert len(uow.appended) == 1
        assert uow.appended[0].result_seen == "failed"
        assert uow.appended[0].record_ids == () and uow.appended[0].passage_ids == ()
        assert out.record.lookup_id == uow.returned_ids[0]
    else:
        ex = ExecutorDouble(
            "book_slot",
            uow.recorder,
            uow,
            record_ids=("slot-57204",),
            lookup_written=True,
            unrenderable=True,
        )
        d = _build(dispatch, [make_def("book_slot", ToolKind.BOOK, EmptyArgs, ex)], uow)
        out = d.dispatch(
            [_call("book_slot", {})], kinds=frozenset({ToolKind.BOOK}), scope=make_scope(VERIFIED)
        )[0]
        assert len(uow.appended) == 1
        assert out.record.lookup_id is None
        assert out.record.record_ids == ("slot-57204",)
    assert _code(out.content) == "tool_failed"
    assert out.record.outcome == "failed"
    failed = [r for r in caplog.records if r.getMessage().startswith("tool_failed ")]
    assert len(failed) == 1
    assert "error_type=bad_result" in failed[0].getMessage()


# --- AC-4 --------------------------------------------------------------------------------------------------------
def test_schemas_generated_without_scope_fields(dispatch: ModuleType) -> None:
    """invariant (AC-4): schemas come from args_model, titles trimmed, strict, no scope field, by name, cached."""
    uow = RecordingUow()
    defs = [
        make_def("b_read", ToolKind.ACCOUNT_READ, InvoiceArgs, ExecutorDouble("b_read", uow.recorder)),
        make_def("a_read", ToolKind.ACCOUNT_READ, TitledArgs, ExecutorDouble("a_read", uow.recorder)),
        make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, ExecutorDouble("kb_search", uow.recorder)),
    ]
    d = _build(dispatch, defs, uow)
    s = d.schemas(frozenset({ToolKind.ACCOUNT_READ}))
    assert [x.name for x in s] == ["a_read", "b_read"]
    by_name = {x.name: x for x in defs}
    for schema in s:
        source = by_name[schema.name]
        assert schema.strict is True
        assert schema.description == source.description
        assert schema.input_schema == strip_titles(source.args_model.model_json_schema())
        assert not property_names(schema.input_schema) & set(ToolCallScope.model_fields)
    titled = next(x for x in s if x.name == "a_read")
    assert "title" in titled.input_schema["properties"]
    assert d.schemas(frozenset({ToolKind.ACCOUNT_READ})) is s
    assert [x.name for x in d.schemas(frozenset({ToolKind.KB_SEARCH}))] == ["kb_search"]


# --- AC-6 --------------------------------------------------------------------------------------------------------
def test_one_lookup_row_per_call(dispatch: ModuleType) -> None:
    """invariant (AC-6, R-29): every call, run or refused, leaves exactly one lookup_log row, stamped by code."""
    uow = RecordingUow()
    kb = ExecutorDouble("kb_search", uow.recorder, uow)
    boom = ExecutorDouble("boom", uow.recorder, uow, raises=Boom())
    book = ExecutorDouble("book_slot", uow.recorder, uow, lookup_written=True)
    d = _build(
        dispatch,
        [
            make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, kb),
            make_def("boom", ToolKind.KB_SEARCH, KbArgs, boom),
            make_def("book_slot", ToolKind.BOOK, EmptyArgs, book),
        ],
        uow,
    )
    scope = make_scope(VERIFIED)
    calls = [
        _call("kb_search", {"query": "filters"}, "r1"),
        _call("no_such_tool", {}, "r2"),
        _call("boom", {"query": "x"}, "r3"),
        _call("book_slot", {}, "r4"),
    ]
    out = d.dispatch(calls, kinds=frozenset(ToolKind), scope=scope)
    assert len(uow.appended) == 4 == len(calls)
    assert [e.tool for e in uow.appended].count("book_slot") == 1
    assert all(e.message_id == MESSAGE_ID and e.turn_id == scope.ids.turn_id for e in uow.appended)
    r1, r2, r3, _r4 = uow.appended
    assert r1.tool == "kb_search"
    assert r2.result_seen == "refused:unknown_tool" and r2.record_ids == () and r2.passage_ids == ()
    assert r3.result_seen == "failed" and r3.record_ids == () and r3.passage_ids == ()
    assert out[0].record.lookup_id == uow.returned_ids[0]
    assert out[1].record.lookup_id == uow.returned_ids[1]
    assert out[2].record.lookup_id == uow.returned_ids[2]
    assert out[3].record.lookup_id is None  # S-8: the service wrote that row; dispatch does not know its id


# --- AC-7 --------------------------------------------------------------------------------------------------------
def test_lookup_write_failure_does_not_change_result(
    dispatch: ModuleType, caplog: pytest.LogCaptureFixture
) -> None:
    """boundary (AC-7): a failed lookup write is logged by type, lookup_id is None, content is unchanged."""
    caplog.set_level(logging.DEBUG)
    kinds = frozenset({ToolKind.KB_SEARCH})
    a = _call("kb_search", {"query": "filters"}, "ca")
    b = _call("kb_search", {"query": "drain"}, "cb")

    healthy = RecordingUow()
    d0 = _build(
        dispatch,
        [make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, ExecutorDouble("kb_search", healthy.recorder))],
        healthy,
    )
    baseline = d0.dispatch([a], kinds=kinds, scope=make_scope(None))[0].content

    uow = RecordingUow(fail_on_appends=frozenset({1}))
    d = _build(
        dispatch,
        [make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, ExecutorDouble("kb_search", uow.recorder))],
        uow,
    )
    out = d.dispatch([a, b], kinds=kinds, scope=make_scope(None))
    assert out[0].content == baseline
    assert out[0].record.lookup_id is None
    assert len(uow.appended) == 1
    assert out[1].record.lookup_id == uow.returned_ids[-1]
    failed = [r for r in caplog.records if r.getMessage().startswith("lookup_write_failed ")]
    assert len(failed) == 1
    assert "OperationalError" in failed[0].getMessage()
    assert card_like() not in failed[0].getMessage()
    assert card_like() not in caplog.text


# --- AC-8 --------------------------------------------------------------------------------------------------------
def _record_case(dispatch: ModuleType, case: str) -> tuple[Any, RecordingUow, Any]:
    uow = RecordingUow()
    rec = uow.recorder
    kinds_scope = make_scope(VERIFIED)
    if case == "ok":
        ex = ExecutorDouble(
            "read_invoices", rec, uow, record_ids=("INV-204411",), passage_ids=(PassageId("faq/x.md#3"),)
        )
        d = _build(dispatch, [make_def("read_invoices", ToolKind.ACCOUNT_READ, InvoiceArgs, ex)], uow)
        return (
            d.dispatch([_call("read_invoices", {})], kinds=frozenset(ToolKind), scope=kinds_scope)[0],
            uow,
            ex,
        )
    if case == "guard_refused":
        ex = ExecutorDouble("read_invoices", rec, uow)
        d = _build(dispatch, [make_def("read_invoices", ToolKind.ACCOUNT_READ, InvoiceArgs, ex)], uow)
        return (
            d.dispatch([_call("read_invoices", {})], kinds=frozenset(ToolKind), scope=make_scope(None))[0],
            uow,
            ex,
        )
    if case in ("executor_refused", "executor_tool_failed"):
        code = ToolErrorCode.NOT_SHOWN if case == "executor_refused" else ToolErrorCode.TOOL_FAILED
        ex = ExecutorDouble(
            "read_invoices",
            rec,
            uow,
            for_model=ToolError(code=code, message="refused by the tool", retryable=False),
            record_ids=("57204",),
            result_seen=f"refused:{code.value}",
        )
        d = _build(dispatch, [make_def("read_invoices", ToolKind.ACCOUNT_READ, InvoiceArgs, ex)], uow)
        return (
            d.dispatch([_call("read_invoices", {})], kinds=frozenset(ToolKind), scope=kinds_scope)[0],
            uow,
            ex,
        )
    if case == "raised":
        ex = ExecutorDouble("read_invoices", rec, uow, raises=Boom())
        d = _build(dispatch, [make_def("read_invoices", ToolKind.ACCOUNT_READ, InvoiceArgs, ex)], uow)
        return (
            d.dispatch([_call("read_invoices", {})], kinds=frozenset(ToolKind), scope=kinds_scope)[0],
            uow,
            ex,
        )
    ex = ExecutorDouble("read_invoices", rec, uow)
    d = _build(dispatch, [make_def("read_invoices", ToolKind.ACCOUNT_READ, InvoiceArgs, ex)], uow)
    return d.dispatch([_call("z" * 100, {})], kinds=frozenset(ToolKind), scope=kinds_scope)[0], uow, ex


@pytest.mark.parametrize(
    "case", ["ok", "guard_refused", "executor_refused", "executor_tool_failed", "raised", "unknown_long_name"]
)
def test_tool_call_records(dispatch: ModuleType, case: str) -> None:
    """invariant (AC-8): the ToolCallRecord carries outcome, error, ids and a non-negative elapsed_ms."""
    out, uow, _ = _record_case(dispatch, case)
    rec = out.record
    assert isinstance(rec.elapsed_ms, int) and rec.elapsed_ms >= 0
    assert (rec.error is None) == (rec.outcome == "ok")
    assert rec.tool_call_id == "toolu_1"
    if case == "ok":
        assert rec.outcome == "ok" and rec.error is None
        assert rec.kind == ToolKind.ACCOUNT_READ
        assert rec.record_ids == ("INV-204411",)
        assert rec.passage_ids == (PassageId("faq/x.md#3"),)
    elif case == "guard_refused":
        assert rec.outcome == "refused" and rec.error == ToolErrorCode.NOT_VERIFIED
    elif case == "executor_refused":
        assert rec.outcome == "refused" and rec.error == ToolErrorCode.NOT_SHOWN
        assert uow.appended[0].record_ids == ("57204",)
        assert rec.record_ids == ("57204",)
    elif case == "executor_tool_failed":
        assert rec.outcome == "failed" and rec.error == ToolErrorCode.TOOL_FAILED
    elif case == "raised":
        assert rec.outcome == "failed" and rec.error == ToolErrorCode.TOOL_FAILED
    else:
        assert rec.kind is None
        assert rec.name == "z" * 64
        assert rec.outcome == "refused" and rec.error == ToolErrorCode.UNKNOWN_TOOL


# --- AC-9 --------------------------------------------------------------------------------------------------------
def _assert_no_private_values(out: Any, uow: RecordingUow, caplog: pytest.LogCaptureFixture) -> None:
    for value in private_values():
        assert value not in json.loads(out.content).get("error", {}).get("message", "")
        assert value not in out.content
        assert value not in out.model_dump_json()
        assert all(value not in e.model_dump_json() for e in uow.appended)
        assert value not in caplog.text
        assert all(value not in r.getMessage() for r in caplog.records)


@pytest.mark.parametrize("case", ["unknown_tool", "bad_arguments", "executor_raises", "snapshot_store"])
def test_rejected_values_absent(dispatch: ModuleType, caplog: pytest.LogCaptureFixture, case: str) -> None:
    """invariant (AC-9, safe-validation-errors): rejected and private values appear nowhere we write or return."""
    caplog.set_level(logging.DEBUG)
    foreign, phone, card, code = private_values()
    uow = RecordingUow()
    scope = make_scope(VERIFIED)
    kinds = frozenset(ToolKind)
    if case == "unknown_tool":
        d = _build(
            dispatch,
            [make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, ExecutorDouble("kb_search", uow.recorder))],
            uow,
        )
        call = _call("no_such_tool", {"customer_id": foreign, "phone": phone, "card": card, "code": code})
    elif case == "bad_arguments":
        inv = ExecutorDouble("read_invoices", uow.recorder, uow)
        d = _build(dispatch, [make_def("read_invoices", ToolKind.ACCOUNT_READ, InvoiceArgs, inv)], uow)
        call = _call("read_invoices", {"customer_id": foreign, phone: "x", "invoice_number": card})
    elif case == "executor_raises":
        msg = f"{foreign} {phone} {card} {code}"
        ex = ExecutorDouble("kb_search", uow.recorder, uow, raises=RuntimeError(msg))
        d = _build(dispatch, [make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, ex)], uow)
        call = _call("kb_search", {"query": "filters"})
    else:
        ex = ExecutorDouble("kb_search", uow.recorder, uow, result_seen=f"ok {card} {code}")
        d = _build(dispatch, [make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, ex)], uow)
        call = _call("kb_search", {"query": "filters"})
    out = d.dispatch([call], kinds=kinds, scope=scope)[0]
    _assert_no_private_values(out, uow, caplog)
    assert len(uow.appended) == 1
    if case != "snapshot_store":
        assert re.fullmatch(r"refused:[a-z_]+|failed", uow.appended[0].result_seen)
        assert len(uow.appended[0].result_seen) <= 80
    if case == "bad_arguments":
        message = json.loads(out.content)["error"]["message"]
        assert "invoice_number: " in message
        assert "unexpected_field: extra_forbidden" in message
        assert _code(out.content) == "bad_arguments"
    if case == "snapshot_store":
        assert out.record.outcome == "ok"
        assert uow.appended[0].result_seen.startswith("ok")


def test_unknown_tool_name_is_redacted_in_record_and_row(dispatch: ModuleType) -> None:
    """invariant (AC-8, S-5): a model-invented tool name holding a code is STORE-redacted before it is kept."""
    code = six_digit_code()
    uow = RecordingUow()
    d = _build(
        dispatch,
        [make_def("kb_search", ToolKind.KB_SEARCH, KbArgs, ExecutorDouble("kb_search", uow.recorder))],
        uow,
    )
    out = d.dispatch([_call(f"no_such_tool_{code}", {})], kinds=frozenset(ToolKind), scope=make_scope(None))[
        0
    ]
    assert code not in out.record.name
    assert len(out.record.name) <= 64
    assert code not in uow.appended[0].tool
    assert code not in out.model_dump_json()


# --- AC-10 -------------------------------------------------------------------------------------------------------
def test_scope_bound_by_code(dispatch: ModuleType) -> None:
    """invariant (AC-10): the executor gets the scope code bound, whatever the model put in its arguments."""
    uow = RecordingUow()
    ex = ExecutorDouble("note_read", uow.recorder, uow)
    d = _build(dispatch, [make_def("note_read", ToolKind.ACCOUNT_READ, NoteArgs, ex)], uow)
    scope = make_scope(VERIFIED)
    d.dispatch(
        [_call("note_read", {"note": f"use {foreign_customer_id()} instead"})],
        kinds=frozenset({ToolKind.ACCOUNT_READ}),
        scope=scope,
    )
    assert len(ex.calls) == 1
    _, got_scope = ex.calls[0]
    assert got_scope is scope
    assert got_scope.customer_id == VERIFIED


# --- AC-11 -------------------------------------------------------------------------------------------------------
def test_lookup_write_outside_executor(dispatch: ModuleType) -> None:
    """invariant (AC-11, DO-3 2.3 rule 1): no unit of work is open while an executor runs; one write per call."""
    rec = Recorder()
    uow = RecordingUow(rec)
    a = ExecutorDouble("a", rec, uow)
    b = ExecutorDouble("b", rec, uow)
    d = _build(
        dispatch,
        [make_def("a", ToolKind.KB_SEARCH, KbArgs, a), make_def("b", ToolKind.KB_SEARCH, KbArgs, b)],
        uow,
    )
    d.dispatch(
        [_call("a", {"query": "x"}, "ca"), _call("b", {"query": "y"}, "cb")],
        kinds=frozenset({ToolKind.KB_SEARCH}),
        scope=make_scope(None),
    )
    assert rec.events == [
        "execute:a", "enter:write", "append", "commit", "exit",
        "execute:b", "enter:write", "append", "commit", "exit",
    ]  # fmt: skip
    assert a.depths == [0] and b.depths == [0]


# --- S-7 ---------------------------------------------------------------------------------------------------------
def test_dispatch_imports_no_adapters(dispatch: ModuleType) -> None:
    """invariant (S-7, DO-3 2.1): dispatch reaches storage and models through ports only."""
    source = Path(str(dispatch.__file__)).read_text(encoding="utf-8")
    banned = (
        "meridian.adapters",
        "meridian.services",
        "meridian.web",
        "meridian.agent.specialists",
        "sqlite3",
        "anthropic",
        "httpx",
        "langfuse",
        "fastembed",
    )
    imported: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    bad = [m for m in imported if any(m == b or m.startswith(b + ".") for b in banned)]
    assert bad == []
