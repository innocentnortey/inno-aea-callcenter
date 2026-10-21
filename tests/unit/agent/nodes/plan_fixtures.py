"""Plain helpers shared by AEA-37's tests: a scripted gateway double, state and outcome builders (plan section 6).

Every sensitive-looking value (phone, code, card) is assembled at run time from parts; nothing here is real.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal, cast

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.agent.gateway import ModelOutcome
from meridian.domain.actions import Settled
from meridian.domain.common import (
    CallRecord,
    Halt,
    HaltReason,
    ProviderFailure,
    ProviderFailureKind,
    ProviderName,
    TurnId,
)
from meridian.domain.identity import IdentityState
from meridian.domain.records import ShownSlot
from meridian.domain.state import ChatLine, ConversationState, OpenTask, TaskDetails
from meridian.domain.turn import (
    DangerAssessment,
    GateDecision,
    GateKind,
    PlannerOutcome,
    RuleMatches,
    SpecialistKind,
    TaskIntent,
    TurnContext,
)
from meridian.policy.limits import Limits
from meridian.ports.models import ChoiceAnswer, ChoiceRequest, Role
from tests.fakes import provider_call
from tests.graph._spine_doubles import DEMO_NOW, THREAD, RecordingSink, make_input, no_rules
from tests.graph._spine_doubles import make_deps as spine_deps

if TYPE_CHECKING:
    from meridian.agent.gateway import ModelGateway

TURN_0 = TurnId("0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d")
TURN_1 = TurnId("1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d")
TURN_2 = TurnId("2b3c4d5e-6f7a-4b8c-9d0e-1f2a3b4c5d6e")
TURN_3 = TurnId("3c4d5e6f-7a8b-4c9d-8e0f-1a2b3c4d5e6f")
TURN_4 = TurnId("4d5e6f7a-8b9c-4d0e-9f1a-2b3c4d5e6f7a")
TURN_5 = TurnId("5e6f7a8b-9c0d-4e1f-8a2b-3c4d5e6f7a8b")
JEV_MODEL = "jev-test-model"
SONNET_MODEL = "sonnet-test-model"

WP3 = "I need to schedule a service call. My AC isn't cooling."
WP3_PICK = "This Saturday if possible, 4 to 7, after work."
DANGER = "my mother is 88 and it's 95 degrees in here"
NODANGER = "my AC isn't cooling"
WP1 = "What does the Comfort Club membership actually include?"
WP4F = "Yes, please."
WP7 = "I want a full refund on the repair. It didn't fix anything and I had to call another company."
WP8 = "I want to cancel my Comfort Club membership."
LATE_TECH = "The technician was supposed to be here this morning and nobody has shown up."  # synthetic

_RETRYABLE = {
    ProviderFailureKind.TIMEOUT,
    ProviderFailureKind.CONNECTION,
    ProviderFailureKind.RATE_LIMITED,
    ProviderFailureKind.OVERLOADED,
    ProviderFailureKind.SERVER,
}


def seeded_phone() -> str:
    return "-".join(["512", "555", "01" + "02"])


def seeded_code() -> str:
    return "".join(["91", "42", "76"])


def seeded_card() -> str:
    return " ".join(["4000", "1234", "5678", "9010"])


def runtime(ctx: TurnContext) -> Runtime[TurnContext]:
    return Runtime(context=ctx)


def rules(**kw: Any) -> RuleMatches:
    return no_rules().model_copy(update=kw)


def free_text_gate(**rule_kw: Any) -> GateDecision:
    return GateDecision(kind=GateKind.FREE_TEXT, rules=rules(**rule_kw))


def open_task(
    task_id: str = "t-1",
    *,
    specialist: SpecialistKind = "scheduling",
    intent: TaskIntent = TaskIntent.RESCHEDULE,
    status: Literal["open", "waiting_identity", "done"] = "open",
) -> OpenTask:
    return OpenTask(
        task_id=task_id,
        specialist=specialist,
        intent=intent,
        opened_turn=TURN_0,
        details=TaskDetails(),
        status=status,
    )


def line(
    speaker: Literal["customer", "assistant", "representative", "event"], text: str, turn_id: TurnId | None
) -> ChatLine:
    return ChatLine(speaker=speaker, text=text, turn_id=turn_id, at=DEMO_NOW)


def make_state(
    text: str,
    *,
    turn_id: TurnId = TURN_1,
    gate: GateDecision | None = None,
    chat: Sequence[ChatLine] = (),
    tasks: Sequence[OpenTask] = (),
    identity: IdentityState | None = None,
    settled: Settled | None = None,
    planner: PlannerOutcome | None = None,
    danger: DangerAssessment | None = None,
    halt: Halt | None = None,
    shown_slots: Sequence[ShownSlot] = (),
) -> ConversationState:
    extra: dict[str, Any] = {"identity": identity} if identity is not None else {}
    return ConversationState(
        thread_id=THREAD,
        turn_input=make_input(turn_id, text),
        gate=gate or free_text_gate(),
        settled=settled or Settled(actions=(), open_case=None, read_at=DEMO_NOW),
        chat_window=list(chat),
        open_tasks=list(tasks),
        shown_slots=list(shown_slots),
        planner=planner,
        danger=danger,
        halt=halt,
        **extra,
    )


def merged(state: ConversationState, *updates: Mapping[str, Any]) -> ConversationState:
    """Apply node updates in order; check_events concatenate and halt keeps the first non-None value."""
    for update in updates:
        change = dict(update)
        if "check_events" in change:
            change["check_events"] = (*state.check_events, *change["check_events"])
        if "halt" in change and state.halt is not None:
            change["halt"] = state.halt
        state = state.model_copy(update=change)
    return state


def choices(**kw: str) -> dict[str, str]:
    base = {"knowledge": "no", "account": "none", "scheduling": "none", "handoff": "none", "topic": "other"}
    return base | kw


def failure(kind: ProviderFailureKind, provider: ProviderName = "openrouter_jev") -> ProviderFailure:
    return ProviderFailure(
        kind=kind,
        provider=provider,
        http_status=None,
        retry_after_s=None,
        retryable=kind in _RETRYABLE,
        provider_request_id=None,
    )


def _provider_of(role: Role) -> ProviderName:
    return "anthropic" if role is Role.PLANNER_FALLBACK else "openrouter_jev"


def record(role: Role, fail: ProviderFailure | None = None) -> CallRecord:
    provider = _provider_of(role)
    model = SONNET_MODEL if role is Role.PLANNER_FALLBACK else JEV_MODEL
    return CallRecord.from_provider(
        provider_call(provider=provider, model=model, failure=fail), role=role, attempt=1
    )


def ok(
    role: Role, picks: dict[str, str], *, probabilities: dict[str, dict[str, float]] | None = None
) -> ModelOutcome[ChoiceAnswer]:
    return ModelOutcome[ChoiceAnswer](
        value=ChoiceAnswer(choices=picks, probabilities=probabilities),
        calls=(record(role),),
        failure=None,
        halt=None,
    )


def failed(role: Role, kind: ProviderFailureKind) -> ModelOutcome[ChoiceAnswer]:
    f = failure(kind, _provider_of(role))
    return ModelOutcome[ChoiceAnswer](value=None, calls=(record(role, f),), failure=f, halt=None)


def halted(role: Role, reason: HaltReason) -> ModelOutcome[ChoiceAnswer]:
    return ModelOutcome[ChoiceAnswer](
        value=None, calls=(), failure=None, halt=Halt(reason=reason, node=role.value, elapsed_ms=0)
    )


class ScriptedGateway:
    """The gateway double (DO-4 section 12 `choose` signature): one queue of outcomes per role."""

    def __init__(self, script: Mapping[Role, Sequence[ModelOutcome[ChoiceAnswer]]]) -> None:
        self._queues = {role: list(outcomes) for role, outcomes in script.items()}
        self.calls: list[tuple[Role, ChoiceRequest]] = []

    def choose(self, role: Role, req: ChoiceRequest, ctx: TurnContext) -> ModelOutcome[ChoiceAnswer]:
        self.calls.append((role, req))
        queue = self._queues.get(role)
        if not queue:
            raise AssertionError(f"unexpected {role.value} call")
        return queue.pop(0)


def make_deps(gateway: object, *, limits: Limits | None = None) -> GraphDeps:
    return dataclasses.replace(
        spine_deps(RecordingSink()), gateway=cast("ModelGateway", gateway), limits=limits or Limits()
    )
