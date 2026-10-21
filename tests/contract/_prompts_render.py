"""AEA-60 helper: render every prompt the graph sends, through the real builders, nodes and runner (plan steps 1-2).

Private to `test_prompts_vs_consumers.py`. Synthetic text only; nothing here reaches a network or a held-out file.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import Any, cast

from meridian.adapters.models.anthropic import AnthropicAdapter
from meridian.agent.gateway import ModelGateway, ModelOutcome
from meridian.agent.nodes import reply
from meridian.agent.nodes.plan import danger_classifier, planner
from meridian.agent.specialists.runner import SpecialistRunner
from meridian.agent.specialists.specs import SPECS
from meridian.agent.tools.account import account_tools
from meridian.agent.tools.dispatch import ToolDispatcher, ToolRegistry
from meridian.agent.tools.knowledge import knowledge_tools
from meridian.agent.tools.scheduling import scheduling_tools
from meridian.domain.common import (
    ProviderFailure,
    ProviderFailureKind,
    ProviderName,
    RequestId,
    TurnId,
)
from meridian.domain.handoff import BriefExtraction, Quote
from meridian.domain.state import ConversationState
from meridian.domain.tools import SpecialistTask, ToolCallScope
from meridian.domain.turn import (
    ResponderDraft,
    SpanHandle,
    TaskIntent,
    TurnBudget,
    TurnContext,
    TurnIds,
)
from meridian.policy.limits import Brakes
from meridian.ports.models import (
    ChoiceAnswer,
    ChoiceRequest,
    Role,
    StructuredRequest,
    ToolStep,
    ToolStepRequest,
)
from meridian.services.handoff import BriefAssembler
from tests.contract._anthropic_fixtures import adapter_for
from tests.fakes import WORKED_PAIRS_NOW, FakeIndex, FixedClock, InMemoryTraceSink
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.unit.agent.nodes import plan_fixtures as pf
from tests.unit.agent.nodes import reply_fixtures as rf
from tests.unit.agent.specialists._doubles import (
    WP1_INCLUDES,
    WP1_MINIMUM,
    WP1_PRICE,
    make_task,
    scheduling_slice,
)

THREAD = rf.THREAD
NOW = FixedClock().now()
JEV_MODEL = "typesafe/jev-1.13"
assert NOW == WORKED_PAIRS_NOW

# (turn id, customer text, assistant reply): synthetic, from WP-3 / WP-4F.
CONVERSATION: tuple[tuple[TurnId, str, str], ...] = (
    (pf.TURN_1, pf.WP3, "I can help book a visit for that."),
    (pf.TURN_2, pf.WP3_PICK, "Saturday 16:00-19:00 is open."),
    (pf.TURN_3, "Saturday afternoon works best.", "Here are two windows."),
    (pf.TURN_4, "Yes, the 4 to 7 window.", "Shall I book it?"),
    (pf.TURN_5, pf.WP4F, ""),
)
RENDER_TURNS = (0, 1, 4)  # turns 1, 2 and 5
STAFF_LINE = "A team member is checking the schedule."

Request = ChoiceRequest | StructuredRequest[Any] | ToolStepRequest


@contextmanager
def case_ctx(sink: InMemoryTraceSink, turn_id: TurnId) -> Iterator[TurnContext]:
    """A turn context whose span was opened by `sink` (the sink refuses a foreign span handle)."""
    ids = TurnIds(
        thread_id=THREAD,
        turn_id=turn_id,
        request_id=RequestId(str(uuid.uuid4())),
        run_tag="live",
        run_id=None,
        agent_version="test",
    )
    with sink.turn(ids) as span:
        t = time.monotonic()
        yield TurnContext(
            ids=ids,
            budget=TurnBudget(started=t, deadline=t + 60.0),
            now=NOW,
            demo_session="demo-test",
            span=span,
        )


# --- a recording gateway (DO-4 section 12 signatures) -------------------------------------------------------------


def failed(kind: ProviderFailureKind, provider: ProviderName) -> ModelOutcome[Any]:
    f = ProviderFailure(
        kind=kind,
        provider=provider,
        http_status=None,
        retry_after_s=None,
        retryable=False,
        provider_request_id=None,
    )
    return ModelOutcome[Any](value=None, calls=(), failure=f, halt=None)


def ok_choice(picks: Mapping[str, str]) -> ModelOutcome[ChoiceAnswer]:
    return ModelOutcome[ChoiceAnswer](
        value=ChoiceAnswer(choices=dict(picks), probabilities=None), calls=(), failure=None, halt=None
    )


def ok_value(value: Any) -> ModelOutcome[Any]:
    return ModelOutcome[Any](value=value, calls=(), failure=None, halt=None)


def end_step() -> ModelOutcome[ToolStep]:
    return ModelOutcome[ToolStep](
        value=ToolStep(
            text="", tool_calls=(), raw={"role": "assistant", "content": []}, stop_reason="end_turn"
        ),
        calls=(),
        failure=None,
        halt=None,
    )


class RecordingGateway:
    """Records every request by role and answers from a per-role queue."""

    def __init__(self, outcomes: Mapping[Role, Sequence[ModelOutcome[Any]]]) -> None:
        self._queues = {role: list(items) for role, items in outcomes.items()}
        self.requests: list[tuple[Role, Request]] = []

    def _next(self, role: Role, req: Request) -> ModelOutcome[Any]:
        self.requests.append((role, req))
        queue = self._queues.get(role)
        if not queue:
            raise AssertionError(f"unexpected {role.value} call")
        return queue.pop(0)

    def choose(self, role: Role, req: ChoiceRequest, ctx: TurnContext) -> ModelOutcome[Any]:
        return self._next(role, req)

    def structured(self, role: Role, req: StructuredRequest[Any], ctx: TurnContext) -> ModelOutcome[Any]:
        return self._next(role, req)

    def tool_step(self, role: Role, req: ToolStepRequest, ctx: TurnContext) -> ModelOutcome[Any]:
        return self._next(role, req)

    def for_role(self, role: Role) -> list[Request]:
        return [r for who, r in self.requests if who is role]

    def as_gateway(self) -> ModelGateway:
        return cast("ModelGateway", self)


class NoScheduling:
    """AEA-60 never executes a scheduling tool; the registry only closes over this."""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError("AEA-60 never executes a scheduling tool")


def build_registry(store: TempStore, index: FakeIndex) -> ToolRegistry:
    return ToolRegistry(
        (*knowledge_tools(index), *account_tools(store.uow), *scheduling_tools(cast(Any, NoScheduling())))
    )


# --- the fixture conversation ----------------------------------------------------------------------------------


def _chat_lines(k: int) -> list[Any]:
    lines: list[Any] = []
    for turn_id, text, answer in CONVERSATION[:k]:
        lines.append(pf.line("customer", text, turn_id))
        if answer:
            lines.append(pf.line("assistant", answer, turn_id))
    return lines


def routing_state(k: int) -> ConversationState:
    turn_id, text, _ = CONVERSATION[k]
    tasks = [] if k == 0 else [pf.open_task("t-1", specialist="scheduling", intent=TaskIntent.BOOK_NEW)]
    state = pf.make_state(text, turn_id=turn_id, chat=_chat_lines(k), tasks=tasks)
    return state.model_copy(update={"thread_id": THREAD})


def seed_conversation(store: TempStore) -> dict[str, list[int]]:
    """Write every customer and assistant line plus one staff line; return message ids by role."""
    ids: dict[str, list[int]] = {"customer": [], "assistant": [], "representative": []}
    with store.uow(write=True) as tx:
        for turn_id, text, answer in CONVERSATION:
            ids["customer"].append(
                tx.core.messages.append(THREAD, "customer", text, NOW, turn_id=turn_id, kind="text")
            )
            if answer:
                ids["assistant"].append(
                    tx.core.messages.append(THREAD, "assistant", answer, NOW, turn_id=turn_id, kind="text")
                )
        ids["representative"].append(
            tx.core.messages.append(THREAD, "representative", STAFF_LINE, NOW, turn_id=pf.TURN_4, kind="text")
        )
        tx.commit()
    return ids


# --- render functions: each returns [(role, request)] for turn index k ------------------------------------------


def render_planner(k: int) -> list[tuple[Role, Request]]:
    sink = InMemoryTraceSink()
    gw = RecordingGateway(
        {
            Role.PLANNER: [failed(ProviderFailureKind.INVALID_OUTPUT, "openrouter_jev")],
            Role.PLANNER_FALLBACK: [ok_choice(pf.choices())],
        }
    )
    with case_ctx(sink, CONVERSATION[k][0]) as ctx:
        planner(routing_state(k), pf.runtime(ctx), deps=pf.make_deps(gw))
    return list(gw.requests)


def render_classifier(k: int) -> list[tuple[Role, Request]]:
    sink = InMemoryTraceSink()
    gw = RecordingGateway({Role.CLASSIFIER: [ok_choice({"danger_level": "normal"})]})
    with case_ctx(sink, CONVERSATION[k][0]) as ctx:
        danger_classifier(routing_state(k), pf.runtime(ctx), deps=pf.make_deps(gw))
    return list(gw.requests)


_INTENT: dict[str, TaskIntent] = {
    "knowledge": TaskIntent.ANSWER_QUESTION,
    "account": TaskIntent.READ_INVOICE,
    "scheduling": TaskIntent.BOOK_NEW,
}


def _raising_transcript() -> AnthropicAdapter:
    def handler(request: Any) -> Any:
        raise AssertionError("a rendering run never reaches the wire")

    return adapter_for(handler)[0]


def specialist_task(kind: str, k: int) -> SpecialistTask:
    text = CONVERSATION[k][1]
    earlier = tuple(t for _, t, _ in CONVERSATION[:k])
    return make_task(
        cast(Any, kind),
        _INTENT[kind],
        text,
        messages=earlier,
        slice_=scheduling_slice() if kind == "scheduling" else None,
    )


def render_specialist(kind: str, k: int) -> tuple[list[tuple[Role, Request]], SpecialistTask]:
    sink = InMemoryTraceSink()
    task = specialist_task(kind, k)
    with temp_sqlite() as store:
        ids = seed_conversation(store)
        registry = build_registry(store, FakeIndex(passages=(WP1_INCLUDES, WP1_PRICE, WP1_MINIMUM)))
        gw = RecordingGateway({Role.SPECIALIST: [end_step()]})
        runner = SpecialistRunner(
            gateway=gw.as_gateway(),
            transcript=_raising_transcript(),
            dispatcher=ToolDispatcher(registry, store.uow),
            specs=SPECS,
            brakes=Brakes(),
            trace=sink,
        )
        with case_ctx(sink, CONVERSATION[k][0]) as ctx:
            scope = ToolCallScope(
                ids=ctx.ids,
                customer_id=None,
                shown_slot_ids=frozenset(),
                now=ctx.now,
                message_id=ids["customer"][k],
            )
            runner.run(task, scope, ctx)
    return list(gw.requests), task


def specialist_request(kind: str, k: int) -> tuple[ToolStepRequest, SpecialistTask]:
    rendered, task = render_specialist(kind, k)
    request = rendered[0][1]
    assert isinstance(request, ToolStepRequest)
    return request, task


def render_responder(k: int) -> list[tuple[Role, Request]]:
    sink = InMemoryTraceSink()
    turn_id, text, _ = CONVERSATION[k]
    gw = RecordingGateway({Role.RESPONDER: [ok_value(ResponderDraft(text="I can help with that."))]})
    with temp_sqlite() as store, case_ctx(sink, turn_id) as ctx:
        ids = seed_conversation(store)
        state = rf.state(
            turn_input=rf.turn_input(turn=turn_id, message_id=ids["customer"][k], text=text),
            facts=rf.facts(turn_id=turn_id),
            chat_window=_chat_lines(k),
        )
        reply.responder(state, rf.run(ctx), deps=rf.deps(uow=store.uow, gw=gw.as_gateway()))
    return list(gw.requests)


def valid_extraction(message_id: int) -> BriefExtraction:
    quote = Quote(message_id=message_id, text="schedule a service call")
    return BriefExtraction(needs=[quote], claims=[], open_decision="Decide on the booking.")


def render_brief(k: int) -> list[tuple[Role, Request]]:
    sink = InMemoryTraceSink()
    turn_id, text, _ = CONVERSATION[k]
    with temp_sqlite() as store, case_ctx(sink, turn_id) as ctx:
        ids = seed_conversation(store)
        gw = RecordingGateway({Role.BRIEF: [ok_value(valid_extraction(ids["customer"][0]))]})
        state = rf.state(
            turn_input=rf.turn_input(turn=turn_id, message_id=ids["customer"][k], text=text),
            handoff=rf.handoff_result(rf.case_summary()),
            facts=rf.facts(turn_id=turn_id),
        )
        deps = rf.deps(
            uow=store.uow,
            gw=gw.as_gateway(),
            cases=rf.FakeCaseService(rf.case_summary()),
            brief=cast(Any, BriefAssembler()),
        )
        reply.brief(state, rf.run(ctx), deps=deps)
    return list(gw.requests)


Renderer = Callable[[int], list[tuple[Role, Request]]]


def _specialist_renderer(kind: str) -> Renderer:
    return lambda k: render_specialist(kind, k)[0]


def _only(role: Role, renderer: Renderer) -> Renderer:
    return lambda k: [(who, req) for who, req in renderer(k) if who is role]


RENDERERS: dict[str, Renderer] = {
    "planner": _only(Role.PLANNER, render_planner),
    "planner_fallback": _only(Role.PLANNER_FALLBACK, render_planner),
    "classifier": render_classifier,
    "responder": render_responder,
    "brief": render_brief,
    **{f"specialist:{kind}": _specialist_renderer(kind) for kind in SPECS},
}


def offered_set(role: str, request: Request) -> object:
    """What the prompt offers the model, in a comparable form."""
    if isinstance(request, ChoiceRequest):
        return {f.name: frozenset(f.options) for f in request.fields}
    if isinstance(request, ToolStepRequest):
        return tuple((t.name, json.dumps(t.input_schema, sort_keys=True), t.strict) for t in request.tools)
    return json.dumps(request.output_model.model_json_schema(), sort_keys=True)


__all__ = [
    "CONVERSATION",
    "JEV_MODEL",
    "NOW",
    "RENDERERS",
    "RENDER_TURNS",
    "THREAD",
    "NoScheduling",
    "RecordingGateway",
    "SpanHandle",
    "build_registry",
    "case_ctx",
    "end_step",
    "failed",
    "offered_set",
    "ok_choice",
    "ok_value",
    "render_brief",
    "render_classifier",
    "render_planner",
    "render_responder",
    "render_specialist",
    "routing_state",
    "seed_conversation",
    "specialist_request",
    "specialist_task",
    "valid_extraction",
]
