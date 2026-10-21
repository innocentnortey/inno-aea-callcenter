"""Decide whether a turn becomes a handoff, an offer of a person, or neither (A7b; DO-4 §6 with cases §3.4).

Pure: first match wins; priority always from `policy/handoff.priority_for`.
"""

from __future__ import annotations

from datetime import date
from typing import Final

from meridian.domain.handoff import HandoffReason, Priority
from meridian.domain.specialists import AccountResult, SchedulingResult
from meridian.domain.turn import EscalationDecision, EscalationInputs, GateKind
from meridian.policy.handoff import business_due, priority_for

__all__ = ["OFFER_AFTER", "R24_REASONS", "decide_escalation"]

OFFER_AFTER: Final = 2  # [A: threshold 2, OD-6] rule 7; graph-core §8 keeps it here
R24_REASONS: Final[frozenset[HandoffReason]] = frozenset(
    {
        HandoffReason.REFUND,
        HandoffReason.BILLING_DISPUTE,
        HandoffReason.COMPLAINT_OR_MANAGER,
        HandoffReason.LEGAL_OR_CHARGEBACK,
        HandoffReason.COMMERCIAL,
    }
)


def _escalate(
    reason: HandoffReason,
    rule_id: str,
    priority: Priority | None = None,
    degraded: bool = False,
) -> EscalationDecision:
    return EscalationDecision(
        outcome="escalate",
        reason=reason,
        priority=priority if priority is not None else priority_for(reason),
        rule_id=rule_id,
        degraded=degraded,
    )


def _offer(rule_id: str) -> EscalationDecision:
    return EscalationDecision(outcome="offer", reason=None, priority=None, rule_id=rule_id)


def _renewal_date(inputs: EscalationInputs) -> date | None:
    for r in inputs.results:
        if isinstance(r, AccountResult) and r.membership is not None:
            return r.membership.renewal_date
    return None


def _private_task_open(inputs: EscalationInputs) -> bool:
    if inputs.plan is not None and any(t.needs_identity for t in inputs.plan.tasks):
        return True
    return any(
        isinstance(r, AccountResult | SchedulingResult) and r.status == "not_verified" for r in inputs.results
    )


def _degraded_rule(inputs: EscalationInputs) -> str | None:
    if inputs.halt is not None:
        return "AI.halt"
    if any(r.status == "failed" for r in inputs.results):
        return "AI.specialist_failed"
    if inputs.models_disabled:
        return "AI.models_disabled"
    plan = inputs.plan
    if plan is not None and plan.planner_failed and not plan.tasks:
        return "AI.planner_failed"
    return None


def _plan_request(inputs: EscalationInputs, reason: HandoffReason) -> EscalationDecision:
    if reason is HandoffReason.MEMBERSHIP_CANCEL:
        return _escalate(
            reason,
            "D4.membership_cancel",
            priority=priority_for(
                reason,
                promise_due=business_due(inputs.now, 1),
                renewal_date=_renewal_date(inputs),
            ),
        )
    if reason is HandoffReason.UNSUPPORTED_ACTION:
        return _escalate(reason, "D4.unsupported")
    if reason is HandoffReason.LATE_TECHNICIAN:
        return _escalate(reason, "D4.late_technician")
    if reason is HandoffReason.BURNING_RULED_OUT:
        return _escalate(reason, "R7.burning_ruled_out")
    return _escalate(reason, f"PLAN.{reason.value}")


def decide_escalation(inputs: EscalationInputs) -> EscalationDecision:
    if inputs.gate.kind == GateKind.PERSON:
        return _escalate(HandoffReason.CUSTOMER_REQUESTED_PERSON, "R2.person")

    trigger = inputs.gate.rules.policy_trigger
    if trigger is not None and trigger in R24_REASONS:
        return _escalate(trigger, f"R24.{trigger.value}")
    plan = inputs.plan
    requested = None if plan is None else plan.handoff_request
    if requested is not None and requested in R24_REASONS:
        return _escalate(requested, f"R24.{requested.value}")

    if any(isinstance(r, SchedulingResult) and r.status == "staff_change_request" for r in inputs.results):
        return _escalate(HandoffReason.FEE_BEARING_CHANGE, "R21.fee_bearing")

    if plan is not None and plan.handoff_request is not None:
        return _plan_request(inputs, plan.handoff_request)

    if inputs.identity.status in ("not_verified", "locked") and _private_task_open(inputs):
        return _escalate(HandoffReason.IDENTITY_UNVERIFIED, "R16.identity_unverified")

    degraded = _degraded_rule(inputs)
    if degraded is not None:
        return _escalate(HandoffReason.AI_FAILURE, degraded, degraded=True)

    c = inputs.counters
    if c.failed_answers >= OFFER_AFTER or c.corrections >= OFFER_AFTER:
        return _offer("OD6.two_misses")
    if c.timeouts >= OFFER_AFTER:
        return _offer("OD6.two_timeouts")

    return EscalationDecision(outcome="none", reason=None, priority=None, rule_id="none")
