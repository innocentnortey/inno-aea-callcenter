"""AEA-02 AC-7 and PA-3: every sketched bound holds on both sides."""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from pydantic import ValidationError

from meridian.domain.common import CallRecord, ToolCallRecord
from meridian.domain.handoff import BriefExtraction, Quote
from meridian.domain.identity import CodeExpired, CodeSent, CodeWrong, IdentityState
from meridian.domain.records import FeeNote
from meridian.domain.specialists import (
    AccountReport,
    KnowledgePoint,
    KnowledgeReport,
    SchedulingReport,
    StaffNote,
)
from meridian.domain.turn import CodePayload, DangerAssessment, Plan, PlannedTask, ResponderDraft, TextPayload

NOW = dt.datetime(2026, 10, 16, 10, 0, tzinfo=dt.UTC)
PASSAGE = "faq/customer_faq.md#1"

_IDENTITY: dict[str, Any] = {
    "status": "not_checked",
    "customer_id": None,
    "masked_hint": None,
    "code_expires_at": None,
    "tries_left": 3,
    "codes_sent": 0,
    "verified_at": None,
}
_PLAN: dict[str, Any] = {
    "mode": "act",
    "tasks": [],
    "handoff_request": None,
    "topic": "other",
    "source": "planner",
}
_TASK: dict[str, Any] = {
    "order": 1,
    "specialist": "knowledge",
    "intent": "answer_question",
    "needs_identity": False,
}
_EXTRACTION: dict[str, Any] = {
    "needs": [{"message_id": 1, "text": "x"}],
    "claims": [],
    "open_decision": "x",
}
_CALL: dict[str, Any] = {
    "provider": "anthropic",
    "model": "m",
    "latency_ms": 1,
    "input_tokens": 1,
    "output_tokens": 1,
    "cache_read_tokens": 0,
    "cache_write_tokens": 0,
    "thinking_tokens": 0,
    "cost_usd": 0.0,
    "cost_source": "reported",
    "status": "ok",
    "failure": None,
    "provider_request_id": None,
    "stop_reason": None,
    "role": "planner",
    "attempt": 1,
}
_FEE: dict[str, Any] = {
    "service_type": "plumbing",
    "tier": "none",
    "fee_row": None,
    "amount_cents": 0,
    "waived": False,
    "line": "x",
}
_TOOL_RECORD: dict[str, Any] = {
    "tool_call_id": "t1",
    "name": "x",
    "kind": None,
    "outcome": "ok",
    "error": None,
    "record_ids": [],
    "passage_ids": [],
    "lookup_id": None,
    "elapsed_ms": 1,
}
_QUOTE: dict[str, Any] = {"message_id": 1, "text": "x"}
_STAFF_NOTE: dict[str, Any] = {
    "kind": "billed_differs_from_schedule",
    "record_id": "INV-204411",
    "text": "x",
    "source_file": "faq/customer_faq.md",
}
_DANGER: dict[str, Any] = {"label": "normal", "raised": False, "failure": None}
_POINT: dict[str, Any] = {"text": "x", "passage_id": PASSAGE}


def _case(model: Any, base: dict[str, Any], field: str, ok: Any, bad: Any) -> tuple[Any, ...]:
    return (model, base, field, ok, bad)


CASES = [
    _case(IdentityState, _IDENTITY, "tries_left", 3, 4),
    _case(IdentityState, _IDENTITY, "tries_left", 0, -1),
    _case(IdentityState, _IDENTITY, "codes_sent", 3, 4),
    _case(IdentityState, _IDENTITY, "codes_sent", 0, -1),
    _case(Plan, _PLAN, "tasks", [_TASK] * 3, [_TASK] * 4),
    _case(PlannedTask, _TASK, "order", 3, 4),
    _case(PlannedTask, _TASK, "order", 1, 0),
    _case(ResponderDraft, {"text": "x"}, "text", "x" * 1200, "x" * 1201),
    _case(ResponderDraft, {"text": "x"}, "text", "x", ""),
    _case(KnowledgePoint, _POINT, "text", "x" * 500, "x" * 501),
    _case(Quote, _QUOTE, "text", "x" * 300, "x" * 301),
    _case(BriefExtraction, _EXTRACTION, "needs", [_QUOTE] * 2, [_QUOTE] * 3),
    _case(BriefExtraction, _EXTRACTION, "needs", [_QUOTE], []),
    _case(BriefExtraction, _EXTRACTION, "claims", [_QUOTE] * 5, [_QUOTE] * 6),
    _case(BriefExtraction, _EXTRACTION, "open_decision", "x" * 200, "x" * 201),
    _case(DangerAssessment, _DANGER, "confidence", 1.0, 1.01),
    _case(DangerAssessment, _DANGER, "confidence", 0.0, -0.01),
    _case(CallRecord, _CALL, "attempt", 2, 3),
    _case(CallRecord, _CALL, "attempt", 1, 0),
    _case(
        CodeSent,
        {"masked_hint": "x", "expires_at": NOW, "sends_left": 0},
        "sends_left",
        2,
        3,
    ),
    _case(CodeSent, {"masked_hint": "x", "expires_at": NOW, "sends_left": 0}, "sends_left", 0, -1),
    _case(CodeWrong, {"tries_left": 1}, "tries_left", 2, 3),
    _case(CodeWrong, {"tries_left": 1}, "tries_left", 1, 0),
    _case(CodeExpired, {"resend_offered": True, "sends_left": 0}, "sends_left", 2, 3),
    _case(CodeExpired, {"resend_offered": True, "sends_left": 0}, "sends_left", 0, -1),
    _case(StaffNote, _STAFF_NOTE, "text", "x" * 300, "x" * 301),
    _case(TextPayload, {"text": "x"}, "text", "x" * 2000, "x" * 2001),
    _case(TextPayload, {"text": "x"}, "text", "x", ""),
    _case(FeeNote, _FEE, "line", "x" * 120, "x" * 121),
    _case(FeeNote, _FEE, "line", "x", ""),
    _case(KnowledgeReport, {"points": [], "answered": True}, "points", [_POINT] * 5, [_POINT] * 6),
    _case(AccountReport, {"summary": "x"}, "summary", "x" * 300, "x" * 301),
    _case(
        SchedulingReport,
        {"appointment_id": 1, "wanted_time": "x", "note": "x"},
        "note",
        "x" * 200,
        "x" * 201,
    ),
    _case(ToolCallRecord, _TOOL_RECORD, "name", "x" * 64, "x" * 65),
    # PA-3: CodePayload.code is exactly six ASCII digits
    _case(CodePayload, {"card_id": "c", "code": "000000"}, "code", "123456", "12345"),
    _case(CodePayload, {"card_id": "c", "code": "000000"}, "code", "123456", "1234567"),
    _case(CodePayload, {"card_id": "c", "code": "000000"}, "code", "123456", "12345a"),
]


@pytest.mark.parametrize(("model", "base", "field", "ok", "bad"), CASES)
def test_bound(model: Any, base: dict[str, Any], field: str, ok: Any, bad: Any) -> None:
    assert model.model_validate({**base, field: ok})
    with pytest.raises(ValidationError) as caught:
        model.model_validate({**base, field: bad})
    if model is CodePayload:
        assert "12345" not in str(caught.value)
