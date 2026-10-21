"""The front nodes of the turn graph (AEA-36; graph-nodes section 9.3).

`gates` decides what kind of turn this is, first on every turn; `safety` opens the P0/P1 case by code with no model,
identity or lookup call; `identity` turns a locate form or a code entry into identity-service calls and passes the
result through. The code digits and the form values are read only from `ctx.intake` and never copied anywhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.agent.signals import emit_signal
from meridian.domain.handoff import HandoffReason, HandoffRequest, HandoffResult
from meridian.domain.identity import (
    CodeCapReached,
    CodeExpired,
    CodeLocked,
    CodeSent,
    CodeWrong,
    IdentityStep,
    Located,
    Locator,
    NotVerified,
    Verified,
)
from meridian.domain.state import ConversationState, GatesUpdate, IdentityNodeUpdate, SafetyUpdate
from meridian.domain.turn import (
    CheckEvent,
    DangerAssessment,
    GateDecision,
    GateKind,
    Plan,
    PlannedTask,
    SignalName,
    SignalRecord,
    TaskIntent,
    TurnContext,
)
from meridian.gates.gate import burning_card_id, decide_gate, flags_from_state
from meridian.policy.handoff import priority_for

__all__ = ["gates", "identity", "safety"]

_SAFETY_NODE: Final = "safety"
_RULE_SAFETY_FALLBACK: Final = "R5.safety"
_RULE_DANGER_FALLBACK: Final = "R8.danger_words"
_RULE_BURNING_YES: Final = "R7.burning_yes"
_RULE_BURNING_UNSURE: Final = "R7.burning_unsure"
_RULE_CLASSIFIER: Final = MappingProxyType(
    {"danger": "R47.classifier_danger", "burning_unclear": "R47.classifier_burning_unclear"}
)
_CAUSE_WRITE_ERROR: Final = "write_error"

_NEW_CODE: Final = "new_code"
_LOCATE_RESULTS: Final = (Located, NotVerified)
_SEND_RESULTS: Final = (CodeSent, NotVerified, CodeCapReached)
_VERIFY_RESULTS: Final = (Verified, CodeWrong, CodeExpired, CodeLocked)


def _burning_ruled_out_plan() -> Plan:
    """graph-nodes section 6 (GRN-6), CAS-16 option A: both dangers ruled out, so the booking task, identity first."""
    return Plan(
        mode="act",
        tasks=(
            PlannedTask(order=1, specialist="scheduling", intent=TaskIntent.BOOK_NEW, needs_identity=True),
        ),
        handoff_request=HandoffReason.BURNING_RULED_OUT,
        topic="booking",
        source="rules_only",
    )


def gates(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> GatesUpdate:
    ctx = runtime.context
    if ctx.intake is None:
        raise ValueError("gates node needs this turn's intake")
    gate = decide_gate(ctx.intake, flags_from_state(state))
    event = CheckEvent.from_gate(ctx.ids.turn_id, gate)
    card = burning_card_id(ctx.ids.turn_id) if gate.kind is GateKind.BURNING_ASK else None
    update: GatesUpdate = {"gate": gate, "check_events": (event,), "burning_card_id": card}
    if gate.kind is GateKind.BURNING_ANSWER and gate.burning_answer == "no":
        update["plan"] = _burning_ruled_out_plan()
    return update


@dataclass(frozen=True)
class _SafetyPath:
    reason: HandoffReason
    cause: str
    rule_id: str


def _first_rule(gate: GateDecision, fallback: str) -> str:
    return gate.rules.rule_ids[0] if gate.rules.rule_ids else fallback


def _safety_path(gate: GateDecision, danger: DangerAssessment | None) -> _SafetyPath | None:
    if gate.kind is GateKind.SAFETY:
        return _SafetyPath(HandoffReason.SAFETY, gate.gate_result(), _first_rule(gate, _RULE_SAFETY_FALLBACK))
    if gate.kind is GateKind.BURNING_ANSWER:
        if gate.burning_answer == "yes":
            return _SafetyPath(HandoffReason.SAFETY, gate.gate_result(), _RULE_BURNING_YES)
        if gate.burning_answer == "unsure":
            return _SafetyPath(HandoffReason.BURNING_UNCLEAR, gate.gate_result(), _RULE_BURNING_UNSURE)
        raise ValueError("safety node: a burning 'no' routes to booking")
    if gate.kind is GateKind.DANGER_RULE:
        return _SafetyPath(HandoffReason.DANGER, gate.gate_result(), _first_rule(gate, _RULE_DANGER_FALLBACK))
    if gate.kind is GateKind.BURNING_ASK:
        return None
    if (
        gate.kind is GateKind.FREE_TEXT
        and danger is not None
        and danger.raised
        and danger.label in _RULE_CLASSIFIER
    ):
        return _SafetyPath(HandoffReason(danger.label), danger.label, _RULE_CLASSIFIER[danger.label])
    raise ValueError("safety node reached without a safety path")


def _signal(ctx: TurnContext, name: SignalName, **extra: object) -> SignalRecord:
    return SignalRecord.model_validate(
        {
            "name": name,
            "turn_id": ctx.ids.turn_id,
            "thread_id": ctx.ids.thread_id,
            "request_id": ctx.ids.request_id,
            "run_tag": ctx.ids.run_tag,
            "node": _SAFETY_NODE,
            **extra,
        }
    )


def _open_case(deps: GraphDeps, request: HandoffRequest, ctx: TurnContext) -> HandoffResult | None:
    try:
        first: HandoffResult = deps.handoff.open(request, ctx)
    except Exception:
        failed = True
    else:
        return first
    retried: HandoffResult | None = None
    if failed:
        try:
            retried = deps.handoff.open(request, ctx)
        except Exception:
            retried = None
    emit_signal(
        ctx.ids,
        _signal(
            ctx,
            SignalName.CASE_WRITE_FAILED,
            cause=_CAUSE_WRITE_ERROR,
            attempt=2,
            recovered=retried is not None,
        ),
    )
    return retried


def safety(state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps) -> SafetyUpdate:
    ctx = runtime.context
    gate = state.gate
    if gate is None:
        raise ValueError("safety node: no gate decision")
    path = _safety_path(gate, state.danger)
    if path is None:
        return {}
    emit_signal(ctx.ids, _signal(ctx, SignalName.SAFETY_REPLY_SENT, cause=path.cause))
    request = HandoffRequest(
        thread_id=ctx.ids.thread_id,
        turn_id=ctx.ids.turn_id,
        reason=path.reason,
        priority=priority_for(path.reason),
        rule_id=path.rule_id,
        trigger="safety",
        identity=state.identity,
        safety_kind=gate.rules.safety,
    )
    result = _open_case(deps, request, ctx)
    return {"handoff": result} if result is not None else {}


def _as_locate(result: object) -> Located | NotVerified:
    if isinstance(result, _LOCATE_RESULTS):
        return result
    raise TypeError("identity service returned an unexpected result type")


def _as_send(result: object) -> CodeSent | NotVerified | CodeCapReached:
    if isinstance(result, _SEND_RESULTS):
        return result
    raise TypeError("identity service returned an unexpected result type")


def _as_verify(result: object) -> Verified | CodeWrong | CodeExpired | CodeLocked:
    if isinstance(result, _VERIFY_RESULTS):
        return result
    raise TypeError("identity service returned an unexpected result type")


def identity(
    state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps
) -> IdentityNodeUpdate:
    ctx = runtime.context
    gate = state.gate
    if gate is None:
        raise ValueError("identity node: no gate decision")
    intake = ctx.intake
    if intake is None:
        raise ValueError("identity node needs this turn's intake")
    thread_id = ctx.ids.thread_id
    step: IdentityStep | None = None
    called = False
    if gate.kind is GateKind.LOCATE:
        locator = Locator.from_form(intake.form) if intake.form is not None else None
        if locator is None:
            step = NotVerified()
        else:
            found = _as_locate(deps.identity.locate(thread_id, locator, ctx.now))
            called = True
            if isinstance(found, Located):
                step = _as_send(deps.identity.send_code(thread_id, ctx.demo_session, ctx.now))
            else:
                step = found
    elif gate.kind is GateKind.CODE_ENTRY:
        if intake.code_digits is not None:
            step = _as_verify(deps.identity.verify(ctx.ids, intake.code_digits, ctx.now))
            called = True
        elif intake.choice is not None and intake.choice.option == _NEW_CODE:
            step = _as_send(deps.identity.send_code(thread_id, ctx.demo_session, ctx.now))
            called = True
    if called:
        with deps.uow() as tx:
            fresh = tx.core.reads.identity_state(thread_id)
        if step is None:
            return {"identity": fresh}
        return {"identity_step": step, "identity": fresh}
    if step is not None:
        return {"identity_step": step}
    return {}
