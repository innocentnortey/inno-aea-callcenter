"""Builders shared by the AEA-10 storage tests. Synthetic values only; ids come from uuid4 at run time."""

from __future__ import annotations

from datetime import timedelta
from typing import Any
from uuid import uuid4

from pydantic import TypeAdapter

from meridian.adapters.sqlite.repos_cases import DEMO_START, CaseRow
from meridian.adapters.sqlite.rows import ConversationRow
from meridian.domain.common import CaseRef, CustomerId, InvoiceId, ThreadId, TurnId
from meridian.domain.turn import TurnIds, TurnRecord

_THREAD: TypeAdapter[ThreadId] = TypeAdapter(ThreadId)
_TURN: TypeAdapter[TurnId] = TypeAdapter(TurnId)
_CASE: TypeAdapter[CaseRef] = TypeAdapter(CaseRef)
_CUSTOMER: TypeAdapter[CustomerId] = TypeAdapter(CustomerId)
_INVOICE: TypeAdapter[InvoiceId] = TypeAdapter(InvoiceId)

NOW = DEMO_START + timedelta(minutes=5)


def new_thread() -> ThreadId:
    return _THREAD.validate_python(str(uuid4()))


def new_turn() -> TurnId:
    return _TURN.validate_python(str(uuid4()))


def case_ref(n: int) -> CaseRef:
    return _CASE.validate_python(f"MHC-C-{n:04d}")


def customer_id(text: str) -> CustomerId:
    return _CUSTOMER.validate_python(text)


def invoice_id(text: str) -> InvoiceId:
    return _INVOICE.validate_python(text)


def conversation(thread: ThreadId, **kw: Any) -> ConversationRow:
    data: dict[str, Any] = {
        "thread_id": str(thread),
        "demo_session": "sess-" + uuid4().hex[:8],
        "run_tag": "live",
        "agent_version": "test",
        "started_at": DEMO_START,
    }
    data.update(kw)
    return ConversationRow.model_validate(data)


def turn_ids(thread: ThreadId, turn: TurnId, **kw: Any) -> TurnIds:
    data: dict[str, Any] = {
        "thread_id": str(thread),
        "turn_id": str(turn),
        "request_id": str(uuid4()),
        "run_tag": "live",
        "run_id": None,
        "agent_version": "test",
    }
    data.update(kw)
    return TurnIds.model_validate(data)


def turn_record(
    status: str = "completed", *, degrade_reason: str | None = None, planner: bool = True
) -> TurnRecord:
    trace: dict[str, Any] = {
        "gate_result": "clear",
        "path": "talk",
        "outcome": "answered",
        "degrade_reason": degrade_reason,
        "planner": {
            "model": "test-planner",
            "fallback_used": False,
            "failure": None,
            "plan_mode": "talk",
            "plan_source": "planner",
            "intents": [],
            "handoff_request": None,
            "topic": "booking",
            "planner_failed": False,
        }
        if planner
        else None,
        "danger_raised": False,
        "specialists_run": ["knowledge"],
    }
    return TurnRecord.model_validate(
        {
            "status": status,
            "trace": trace,
            "replied_at": NOW,
            "server_ms": 1200,
            "model_calls": 2,
            "input_tokens": 100,
            "output_tokens": 40,
            "cost_usd": 0.0125,
            "tool_calls": 1,
            "trace_id": None,
            "trace_export": "off",
            "response": "synthetic reply " + uuid4().hex[:6],
        }
    )


def case_row(thread: ThreadId, ref: int = 9, **kw: Any) -> CaseRow:
    data: dict[str, Any] = {
        "case_ref": str(case_ref(ref)),
        "thread_id": str(thread),
        "reason": "fee_bearing_change",
        "priority": "P2",
        "rule_id": "D4.fee_bearing",
        "trigger": "escalation",
        "lifecycle": "unassigned",
        "due_at": NOW + timedelta(hours=1),
        "created_at": DEMO_START,
        "updated_at": DEMO_START,
    }
    data.update(kw)
    return CaseRow.model_validate(data)
