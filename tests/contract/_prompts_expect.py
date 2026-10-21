"""AEA-60 helper: the expected fallback of every malformed case (AC-7 to AC-9), asserted on a `CaseRun`."""

from __future__ import annotations

from typing import Any

import pytest

from meridian.domain.common import (
    HandoffReason,
    Priority,
    ProviderFailureKind,
    Role,
    ToolCallRecord,
    ToolErrorCode,
    ToolKind,
)
from meridian.domain.turn import CheckedReply, CheckEvent, Plan, PlannerChoices, TaskIntent
from tests.contract import _prompts_malformed as pm

K = ProviderFailureKind


def _only_signal(run: pm.CaseRun, name: str) -> dict[str, Any]:
    found = [s for s in run.signals if s["name"] == name]
    assert len(found) == 1, (name, run.signals)
    return found[0]


def check_routing(case_id: str, caplog: pytest.LogCaptureFixture) -> None:
    run = pm.run_routing_case(case_id, caplog)
    plan = run.results["plan_join"]["plan"]
    outcome = run.results["planner"]["planner"]
    if case_id[0] in "abc":
        assert run.requests == {"jev_planner": 1, "fallback": 1}
        assert outcome.fallback_used is True
        assert outcome.choices == PlannerChoices.model_validate(pm.BOOK)
        assert plan.source == "fallback_planner"
        assert [t.intent for t in plan.tasks] == [TaskIntent.BOOK_NEW]
        signal = _only_signal(run, "planner_fallback")
        assert {k: signal[k] for k in ("cause", "role", "node", "recovered")} == {
            "cause": "invalid_output",
            "role": "planner",
            "node": "planner",
            "recovered": True,
        }
        jev_call = next(c for c, _ in run.ledger.records if c.role is Role.PLANNER)
        assert jev_call.status == "error"
        assert jev_call.failure is not None and jev_call.failure.kind is K.INVALID_OUTPUT
        assert jev_call.attempt == 1
    elif case_id[0] == "d":
        assert run.requests == {"jev_planner": 1, "fallback": 1}
        assert outcome.choices is None and outcome.fallback_used is True
        assert outcome.failure is not None and outcome.failure.kind is K.INVALID_OUTPUT
        assert plan == Plan(
            mode="act",
            tasks=(),
            handoff_request=None,
            topic="other",
            source="rules_only",
            planner_failed=True,
        )
        assert _only_signal(run, "planner_fallback")["recovered"] is False
    else:
        assert run.requests["jev_classifier"] == 1
        danger = run.results["danger"]["danger"]
        assert (danger.label, danger.raised) == ("normal", False)
        assert danger.failure is not None and danger.failure.kind is K.INVALID_OUTPUT
        assert run.check_events == [
            CheckEvent(
                check="classifier",
                turn_id=run.ctx.ids.turn_id,
                result="fallback",
                codes=("fallback", "invalid_output"),
            )
        ]
        signal = _only_signal(run, "classifier_fallback")
        assert (signal["role"], signal["node"], signal["cause"]) == (
            "classifier",
            "danger_classifier",
            "invalid_output",
        )
        assert [t.intent for t in plan.tasks] == [TaskIntent.BOOK_NEW]
        assert "halt" not in run.results["plan_join"] or run.results["plan_join"]["halt"] is None
        assert run.results["route"] != "safety"


def _only_record(run: pm.CaseRun) -> ToolCallRecord:
    assert len(run.tool_records) == 1, run.tool_records
    return run.tool_records[0]


def check_specialist(case_id: str, caplog: pytest.LogCaptureFixture) -> None:
    run = pm.run_specialist_case(case_id, caplog)
    result = run.results["specialist"]
    index = run.results["index"]
    lookups = [row.result_seen for row in run.lookup_rows]
    if case_id == "unknown-tool":
        record = _only_record(run)
        assert (record.name, record.kind, record.outcome) == ("issue_refund", None, "refused")
        assert record.error is ToolErrorCode.UNKNOWN_TOOL and record.lookup_id is not None
        assert [(r.tool, r.result_seen) for r in run.lookup_rows] == [
            ("issue_refund", "refused:unknown_tool")
        ]
        assert run.requests["specialist"] == 2 and index.searches == []
    elif case_id == "not-allowed":
        record = _only_record(run)
        assert record.kind is ToolKind.ACCOUNT_READ and record.error is ToolErrorCode.NOT_ALLOWED
        assert lookups == ["refused:not_allowed"]
    elif case_id in ("args-none", "extra-customer-id", "query-301"):
        assert _only_record(run).error is ToolErrorCode.BAD_ARGUMENTS
        assert lookups == ["refused:bad_arguments"]
        assert index.searches == [] and run.requests["specialist"] == 2
    elif case_id == "invoice-pattern":
        record = _only_record(run)
        assert record.name == "read_invoices" and record.error is ToolErrorCode.BAD_ARGUMENTS
        assert lookups == ["refused:bad_arguments"]
        assert result.status == "failed" and result.invoices == ()
    elif case_id == "report-6-points":
        assert run.outcome is not None and run.outcome.report is None
        assert result.status == "no_current_source" and result.points == ()
        assert len(index.searches) == 1
        assert [row.tool for row in run.lookup_rows] == ["kb_search"]
    else:
        assert run.outcome is not None and run.outcome.report is None
        assert result.status == "failed" and result.membership is None
        assert result.invoices == () and result.tools == () and run.lookup_rows == []


def check_act(case_id: str, caplog: pytest.LogCaptureFixture) -> None:
    run = pm.run_act_case(case_id, caplog)
    kind = {"step-unparseable": K.INVALID_OUTPUT, "step-max-tokens": K.MAX_TOKENS, "step-refusal": K.REFUSAL}[
        case_id
    ]
    result = run.results["update"]["specialist_results"][0]
    assert result.status == "failed" and result.failure is not None and result.failure.kind is kind
    assert run.requests["specialist"] == 1
    signal = _only_signal(run, "specialist_failed")
    assert {k: signal[k] for k in ("node", "role", "specialist", "cause")} == {
        "node": "run_specialist",
        "role": "specialist",
        "specialist": "knowledge",
        "cause": kind.value,
    }
    esc = run.results["escalation"]
    assert esc.outcome == "escalate" and esc.reason is HandoffReason.AI_FAILURE
    assert esc.priority is Priority.P3 and esc.rule_id == "AI.specialist_failed" and esc.degraded is True


def check_reply(case_id: str, caplog: pytest.LogCaptureFixture) -> None:
    if case_id.startswith("draft-"):
        run = pm.run_reply_case(case_id, caplog)
        assert run.results["update"] == {"draft": None}
        signal = _only_signal(run, "responder_fallback")
        cause = "refusal" if case_id == "draft-refusal" else "invalid_output"
        assert {k: signal[k] for k in ("role", "node", "cause", "attempt")} == {
            "role": "responder",
            "node": "responder",
            "cause": cause,
            "attempt": 1,
        }
        checked = run.results["checked"]
        assert checked.fallback_used is True and checked.text == ""
        composed = run.results["composed"]
        offers = [b for b in composed.blocks if b.type == "failure_offer"]
        assert len(offers) == 1 and offers[0].person_key is True
        assert composed.outcome == "degraded_handoff" and composed.degrade_reason == "model_error"
        assert run.requests["responder"] == 1
        return
    run = pm.run_brief_case(case_id, caplog)
    checked = run.results["checked"]
    assert isinstance(checked, CheckedReply)
    if case_id.startswith("brief-"):
        assert run.results["brief"] == {"brief_extraction": None}
        signal = _only_signal(run, "brief_failed")
        assert (signal["cause"], signal["role"]) == ("invalid_output", "brief")
        last = run.stored_briefs[-1]
        assert last.status == "failed"
        assert {h.number: h.not_generated for h in last.headings} == {n: n in (2, 4, 7) for n in range(1, 9)}
    else:
        assert run.results["brief"]["brief_extraction"] is not None
        quote = [e for e in checked.events if e.check == "brief_quote"]
        assert [(e.result, e.removed) for e in quote] == [("trimmed", 1)]
        assert not [s for s in run.signals if s["name"] == "brief_failed"]
        heading4 = next(h for h in run.stored_briefs[-1].headings if h.number == 4)
        assert all("money back" not in item.text for item in heading4.items)
