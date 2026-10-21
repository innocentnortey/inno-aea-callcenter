"""AEA-14: the escalation decision (policy/escalation.py)."""

from __future__ import annotations

import ast
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from meridian.domain.common import Halt, HaltReason
from meridian.domain.handoff import HandoffReason, Priority
from meridian.domain.specialists import (
    AccountResult,
    ChangeRequestDraft,
    KnowledgeResult,
    MembershipView,
    SchedulingResult,
)
from meridian.domain.state import FailureCounters, IdentityState
from meridian.domain.turn import (
    EscalationDecision,
    EscalationInputs,
    GateDecision,
    GateKind,
    Plan,
    PlannedTask,
    RuleMatches,
    TaskIntent,
)
from meridian.policy.escalation import OFFER_AFTER, R24_REASONS, decide_escalation
from meridian.policy.handoff import business_due, priority_for, promise_for

CHI = ZoneInfo("America/Chicago")
ROOT = Path(__file__).resolve().parents[3]
R = HandoffReason


def at(y: int, mo: int, d: int, h: int = 10, mi: int = 0) -> datetime:
    return datetime(y, mo, d, h, mi, tzinfo=CHI)


FRI_10 = at(2026, 10, 16)


def _rules(**kw: Any) -> RuleMatches:
    base: dict[str, Any] = {
        "safety": None,
        "burning_unclear": False,
        "danger_words": False,
        "person": False,
        "policy_trigger": None,
        "rule_ids": (),
        "correction": False,
    }
    base.update(kw)
    return RuleMatches.model_validate(base)


def _gate(kind: GateKind = GateKind.FREE_TEXT, **rule_kw: Any) -> GateDecision:
    return GateDecision(kind=kind, rules=_rules(**rule_kw))


def _plan(
    handoff: HandoffReason | None = None, tasks: tuple[PlannedTask, ...] = (), planner_failed: bool = False
) -> Plan:
    return Plan(
        mode="act",
        tasks=tasks,
        handoff_request=handoff,
        topic="other",
        source="planner",
        planner_failed=planner_failed,
    )


def _task(needs_identity: bool = True) -> PlannedTask:
    return PlannedTask(
        order=1, specialist="account", intent=TaskIntent.READ_INVOICE, needs_identity=needs_identity
    )


def _identity(status: Any = "verified") -> IdentityState:
    return IdentityState(
        status=status,
        customer_id=None,
        masked_hint=None,
        code_expires_at=None,
        tries_left=3,
        codes_sent=0,
        verified_at=None,
    )


def _account(renewal: date | None, status: Any = "read") -> AccountResult:
    return AccountResult(
        status=status,
        membership=None if renewal is None else MembershipView(tier="standard", renewal_date=renewal),
        tools=(),
        calls=(),
    )


def _scheduling(status: Any) -> SchedulingResult:
    draft = (
        ChangeRequestDraft(
            appointment_id=1,
            change="move",
            wanted_text="Monday morning instead",
            windows_shown=(),
            hours_before=2.0,
            window_start=at(2026, 10, 16, 12),
        )
        if status == "staff_change_request"
        else None
    )
    return SchedulingResult(status=status, change_request=draft, tools=(), calls=())


def _knowledge(status: Any = "failed") -> KnowledgeResult:
    return KnowledgeResult(status=status, passages=(), points=(), tools=(), calls=())


def _halt() -> Halt:
    return Halt(reason=HaltReason.BRAKE_TASKS, node="act", elapsed_ms=1200)


def _inputs(**kw: Any) -> EscalationInputs:
    base: dict[str, Any] = {
        "gate": _gate(),
        "plan": None,
        "results": (),
        "counters": FailureCounters(),
        "identity": _identity(),
        "halt": None,
        "models_disabled": False,
        "now": FRI_10,
    }
    base.update(kw)
    return EscalationInputs.model_validate(base)


def _shape(d: EscalationDecision) -> tuple[Any, ...]:
    return (d.outcome, d.reason, d.priority, d.rule_id)


def test_rule_order_first_match() -> None:
    decide = decide_escalation
    esc = "escalate"
    assert _shape(decide(_inputs(gate=_gate(GateKind.PERSON)))) == (
        esc,
        R.CUSTOMER_REQUESTED_PERSON,
        Priority.P3,
        "R2.person",
    )
    assert _shape(decide(_inputs(gate=_gate(GateKind.PERSON, policy_trigger=R.REFUND)))) == (
        esc,
        R.CUSTOMER_REQUESTED_PERSON,
        Priority.P3,
        "R2.person",
    )
    assert _shape(decide(_inputs(gate=_gate(policy_trigger=R.REFUND)))) == (
        esc,
        R.REFUND,
        Priority.P3,
        "R24.refund",
    )
    assert _shape(decide(_inputs(results=(_scheduling("staff_change_request"),)))) == (
        esc,
        R.FEE_BEARING_CHANGE,
        Priority.P2,
        "R21.fee_bearing",
    )
    assert _shape(
        decide(_inputs(plan=_plan(R.MEMBERSHIP_CANCEL), results=(_account(date(2026, 11, 3)),)))
    ) == (esc, R.MEMBERSHIP_CANCEL, Priority.P3, "D4.membership_cancel")
    assert _shape(decide(_inputs(plan=_plan(R.UNSUPPORTED_ACTION)))) == (
        esc,
        R.UNSUPPORTED_ACTION,
        Priority.P4,
        "D4.unsupported",
    )
    assert _shape(decide(_inputs(plan=_plan(R.LATE_TECHNICIAN)))) == (
        esc,
        R.LATE_TECHNICIAN,
        Priority.P2,
        "D4.late_technician",
    )
    assert _shape(decide(_inputs(counters=FailureCounters(failed_answers=2)))) == (
        "offer",
        None,
        None,
        "OD6.two_misses",
    )
    assert _shape(decide(_inputs(counters=FailureCounters(corrections=2)))) == (
        "offer",
        None,
        None,
        "OD6.two_misses",
    )
    assert decide(_inputs(counters=FailureCounters(failed_answers=1))).outcome == "none"
    nothing = decide(_inputs())
    assert _shape(nothing) == ("none", None, None, "none")
    assert nothing.degraded is False
    both = decide(
        _inputs(results=(_scheduling("staff_change_request"),), counters=FailureCounters(failed_answers=2))
    )
    assert both.rule_id == "R21.fee_bearing"

    for inputs in (
        _inputs(gate=_gate(GateKind.PERSON)),
        _inputs(gate=_gate(policy_trigger=R.REFUND)),
        _inputs(results=(_scheduling("staff_change_request"),)),
        _inputs(plan=_plan(R.UNSUPPORTED_ACTION)),
        _inputs(plan=_plan(R.LATE_TECHNICIAN)),
    ):
        d = decide(inputs)
        assert d.reason is not None
        assert d.priority == priority_for(d.reason)
        assert d.degraded is False


def test_rule7_two_timeouts() -> None:
    assert _shape(decide_escalation(_inputs(counters=FailureCounters(timeouts=2)))) == (
        "offer",
        None,
        None,
        "OD6.two_timeouts",
    )
    both = decide_escalation(_inputs(counters=FailureCounters(timeouts=2, failed_answers=2)))
    assert both.rule_id == "OD6.two_misses"
    assert decide_escalation(_inputs(counters=FailureCounters(timeouts=1))).outcome == "none"


def _degraded(d: EscalationDecision, rule_id: str) -> None:
    assert _shape(d) == ("escalate", R.AI_FAILURE, Priority.P3, rule_id)
    assert d.degraded is True


def test_rule6_single_failed_specialist() -> None:
    _degraded(decide_escalation(_inputs(results=(_knowledge("failed"),))), "AI.specialist_failed")
    _degraded(decide_escalation(_inputs(results=(_account(None, status="failed"),))), "AI.specialist_failed")


def test_rule6_models_disabled() -> None:
    _degraded(decide_escalation(_inputs(models_disabled=True)), "AI.models_disabled")


def test_rule6_halt_and_planner_failed() -> None:
    _degraded(decide_escalation(_inputs(halt=_halt())), "AI.halt")
    _degraded(decide_escalation(_inputs(plan=_plan(planner_failed=True))), "AI.planner_failed")
    assert (
        decide_escalation(_inputs(plan=_plan(planner_failed=True, tasks=(_task(False),)))).outcome == "none"
    )


def test_unverified_private_task_escalates() -> None:
    want = ("escalate", R.IDENTITY_UNVERIFIED, Priority.P3, "R16.identity_unverified")
    for status in ("not_verified", "locked"):
        got = decide_escalation(_inputs(identity=_identity(status), plan=_plan(tasks=(_task(True),))))
        assert _shape(got) == want
    got = decide_escalation(
        _inputs(identity=_identity("not_verified"), results=(_account(None, status="not_verified"),))
    )
    assert _shape(got) == want
    assert decide_escalation(_inputs(identity=_identity("not_verified"))).outcome == "none"


def test_membership_cancel_priority_uses_business_due() -> None:
    for renewal, prio in (
        (date(2026, 11, 3), Priority.P3),
        (date(2026, 10, 19), Priority.P2),
        (None, Priority.P3),
    ):
        results = () if renewal is None else (_account(renewal),)
        d = decide_escalation(_inputs(plan=_plan(R.MEMBERSHIP_CANCEL), results=results))
        assert d.priority is prio
        assert d.rule_id == "D4.membership_cancel"
        assert d.priority == priority_for(
            R.MEMBERSHIP_CANCEL, promise_due=business_due(FRI_10, 1), renewal_date=renewal
        )
    assert "presence" not in EscalationInputs.model_fields


def test_rule2_ids_for_every_policy_reason() -> None:
    assert len(R24_REASONS) == 5
    for reason in R24_REASONS:
        for inputs in (_inputs(gate=_gate(policy_trigger=reason)), _inputs(plan=_plan(reason))):
            assert _shape(decide_escalation(inputs)) == (
                "escalate",
                reason,
                Priority.P3,
                f"R24.{reason.value}",
            )


def test_rule4_burning_ruled_out_and_unexpected_reason() -> None:
    assert _shape(decide_escalation(_inputs(plan=_plan(R.BURNING_RULED_OUT)))) == (
        "escalate",
        R.BURNING_RULED_OUT,
        Priority.P2,
        "R7.burning_ruled_out",
    )
    assert _shape(decide_escalation(_inputs(plan=_plan(R.CUSTOMER_REQUESTED_PERSON)))) == (
        "escalate",
        R.CUSTOMER_REQUESTED_PERSON,
        Priority.P3,
        "PLAN.customer_requested_person",
    )


def test_rule3_needs_a_scheduling_change_request() -> None:
    assert decide_escalation(_inputs(results=(_scheduling("windows_shown"),))).outcome == "none"
    assert decide_escalation(_inputs(results=(_scheduling("failed"),))).rule_id == "AI.specialist_failed"


_ALLOWED_PREFIXES = ("meridian.domain", "meridian.policy.texts", "meridian.policy.handoff")
_BANNED_CALLS = {"now", "today", "utcnow", "monotonic", "perf_counter"}


def test_policy_modules_are_pure() -> None:
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    for name in ("handoff.py", "escalation.py"):
        tree = ast.parse((ROOT / "src/meridian/policy" / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            mods: list[str] = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""]
            for mod in mods:
                assert mod.split(".")[0] in stdlib or mod.startswith(_ALLOWED_PREFIXES), mod
            if isinstance(node, ast.Call):
                f = node.func
                assert not (isinstance(f, ast.Name) and f.id == "open")
                if isinstance(f, ast.Attribute):
                    assert f.attr not in _BANNED_CALLS
                    assert not (f.attr == "time" and isinstance(f.value, ast.Name) and f.value.id == "time")
    assert promise_for(R.REFUND, "nobody_online", FRI_10) == promise_for(R.REFUND, "nobody_online", FRI_10)
    i = _inputs(plan=_plan(R.LATE_TECHNICIAN))
    assert decide_escalation(i) == decide_escalation(i)


def test_offer_after_is_two() -> None:
    assert OFFER_AFTER == 2


def test_decision_shape_for_none_and_offer() -> None:
    for d in (decide_escalation(_inputs()), decide_escalation(_inputs(counters=FailureCounters(timeouts=2)))):
        assert d.reason is None
        assert d.priority is None
        assert d.degraded is False
