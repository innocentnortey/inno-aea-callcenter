"""AEA-60 helper: the six drifted copies of AC-11. Each runs one real check on a monkeypatched copy and must raise
`Drift` with role, field and value. Nothing is written to the prompt modules outside `monkeypatch`."""

from __future__ import annotations

from typing import Any

import pytest

from meridian.agent.prompts import routing as routing_prompts
from meridian.agent.prompts import specialists as specialist_prompts
from meridian.agent.prompts.routing import DANGER_FIELD
from meridian.agent.tools.dispatch import ToolDispatcher
from meridian.domain.common import LLMFacing
from meridian.domain.turn import DangerAssessment, PlannerChoices
from tests.contract import _prompts_render as pr
from tests.contract._prompts_checks import (
    check_brief_ids,
    check_choice_fields,
    check_responder_request,
    check_specialist_request,
    parse_brief_lines,
)
from tests.fakes import FakeIndex
from tests.fixtures.sqlite import temp_sqlite


def _render_turn(name: str, k: int) -> list[Any]:
    return pr.RENDERERS[name](k)


def _planner_request(k: int = 0) -> Any:
    return _render_turn("planner", k)[0][1]


def _with_options(fields: Any, name: str, change: Any) -> tuple[Any, ...]:
    return tuple(
        f.model_copy(update={"options": change(dict(f.options))}) if f.name == name else f for f in fields
    )


class DriftedDraft(LLMFacing):
    text: str
    promise: str


def _drift_planner_added(mp: pytest.MonkeyPatch) -> str:
    fields = _with_options(
        routing_prompts.PLANNER_FIELDS, "handoff", lambda o: {**o, "cancel_membership": "Cancel it."}
    )
    mp.setattr(routing_prompts, "PLANNER_FIELDS", fields)
    check_choice_fields("routing.planner", _planner_request(), PlannerChoices)
    return ""


def _drift_planner_removed(mp: pytest.MonkeyPatch) -> str:
    fields = _with_options(
        routing_prompts.PLANNER_FIELDS,
        "handoff",
        lambda o: {k: v for k, v in o.items() if k != "late_technician"},
    )
    mp.setattr(routing_prompts, "PLANNER_FIELDS", fields)
    check_choice_fields("routing.planner", _planner_request(), PlannerChoices)
    return ""


def _drift_classifier(mp: pytest.MonkeyPatch) -> str:
    fields = _with_options(
        routing_prompts.CLASSIFIER_FIELDS, DANGER_FIELD, lambda o: {**o, "emergency": "Help."}
    )
    mp.setattr(routing_prompts, "CLASSIFIER_FIELDS", fields)
    request = _render_turn("classifier", 0)[0][1]
    check_choice_fields("routing.classifier", request, DangerAssessment, fields={DANGER_FIELD: "label"})
    return ""


def _drift_specialist(mp: pytest.MonkeyPatch) -> str:
    mp.setattr(
        specialist_prompts,
        "ACCOUNT_PREFIX",
        specialist_prompts.ACCOUNT_PREFIX + " Call refund_invoice when asked.",
    )
    with temp_sqlite() as store:
        registry = pr.build_registry(store, FakeIndex())
        request, task = pr.specialist_request("account", 0)
        check_specialist_request("account", request, registry, ToolDispatcher(registry, store.uow), task)
    return ""


def _drift_responder(mp: pytest.MonkeyPatch) -> str:
    request = _render_turn("responder", 0)[0][1]
    check_responder_request(request.model_copy(update={"output_model": DriftedDraft}))
    return ""


def _drift_brief(mp: pytest.MonkeyPatch) -> str:
    with temp_sqlite() as store:
        ids = pr.seed_conversation(store)
    rendered = parse_brief_lines(_render_turn("brief", 0)[0][1].user)
    staff = ids["representative"][0]
    check_brief_ids(
        {**rendered, staff: "A team member is checking the schedule."}, rendered, set(ids["customer"])
    )
    return ""


DRIFTS = {
    "planner-handoff-added": (
        _drift_planner_added,
        "routing.planner.handoff offers 'cancel_membership'; PlannerChoices.handoff does not accept it",
    ),
    "planner-late-technician-removed": (
        _drift_planner_removed,
        "routing.planner.handoff does not offer 'late_technician'; PlannerChoices.handoff accepts it",
    ),
    "classifier-emergency-added": (
        _drift_classifier,
        "routing.classifier.danger_level offers 'emergency'; DangerAssessment.label does not accept it",
    ),
    "specialist-refund-invoice": (
        _drift_specialist,
        "specialist.account wording names 'refund_invoice'; no tool sent with it",
    ),
    "responder-promise-field": (
        _drift_responder,
        "responder.output_model offers 'promise'; ResponderDraft does not accept it",
    ),
    "brief-staff-message": (
        _drift_brief,
        "brief.shown offers message ",
    ),
}
