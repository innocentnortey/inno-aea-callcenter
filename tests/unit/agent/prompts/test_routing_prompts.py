"""Planner and classifier wording and what crosses to the model (AEA-37 AC-8, PA-2, PA-3, PA-7, PA-8)."""

from __future__ import annotations

import ast
import json
import logging
import sys
import typing
from pathlib import Path

import pytest

from meridian.agent.nodes.plan import danger_classifier, planner
from meridian.agent.prompts.routing import (
    CLASSIFIER_FIELDS,
    CLASSIFIER_SYSTEM,
    DANGER_FIELD,
    PLANNER_FIELDS,
    PLANNER_SYSTEM,
)
from meridian.domain.common import CustomerId, ProviderFailureKind
from meridian.domain.identity import IdentityState
from meridian.domain.turn import DangerAssessment, PlannerChoices, StateFlags, Topic
from meridian.ports.models import Role
from meridian.privacy.redact import RedactionProfile, redact
from tests.graph._spine_doubles import make_ctx
from tests.unit.agent.nodes.plan_fixtures import (
    TURN_0,
    TURN_1,
    ScriptedGateway,
    choices,
    failed,
    line,
    make_deps,
    make_state,
    ok,
    open_task,
    runtime,
    seeded_card,
    seeded_code,
    seeded_phone,
)

SRC = Path(__file__).resolve().parents[4] / "src" / "meridian"
PLAN_PY = SRC / "agent" / "nodes" / "plan.py"
ROUTING_PY = SRC / "agent" / "prompts" / "routing.py"


def test_requests_cross_only_planner_input(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    latest = f"Hi, my name is Omar Patel. My number is {seeded_phone()} and my card is {seeded_card()}."
    chat = (
        line("customer", "my customer number is MHC-10002", TURN_0),
        line("customer", "it's about INV-204411", TURN_0),
        line("customer", f"the code is {seeded_code()}", TURN_0),
    )
    identity = IdentityState(
        status="located",
        customer_id=CustomerId("MHC-10002"),
        masked_hint="the phone ending in 02",
        code_expires_at=None,
        tries_left=3,
        codes_sent=1,
        verified_at=None,
    )
    state = make_state(latest, chat=chat, identity=identity, tasks=(open_task("t-1", specialist="account"),))
    ctx = make_ctx(TURN_1)
    gw = ScriptedGateway(
        {
            Role.PLANNER: [ok(Role.PLANNER, choices()), failed(Role.PLANNER, ProviderFailureKind.BODY_ERROR)],
            Role.PLANNER_FALLBACK: [ok(Role.PLANNER_FALLBACK, choices())],
            Role.CLASSIFIER: [failed(Role.CLASSIFIER, ProviderFailureKind.BODY_ERROR)],
        }
    )
    deps = make_deps(gw)
    planner(state, runtime(ctx), deps=deps)
    classified = danger_classifier(state, runtime(ctx), deps=deps)
    planner(state, runtime(ctx), deps=deps)

    planner_req = gw.calls[0][1]
    classifier_req = next(req for role, req in gw.calls if role is Role.CLASSIFIER)
    assert set(planner_req.state) == {"latest_message", "recent_chat", "flags"}
    flags = planner_req.state["flags"]
    assert isinstance(flags, dict)
    assert set(flags) == set(StateFlags.model_fields)
    assert all(v is None or isinstance(v, bool | int | str) for v in flags.values())
    assert set(classifier_req.state) == {"latest_message"}

    dumps = [planner_req.model_dump_json(), classifier_req.model_dump_json()]
    dumps += [e.model_dump_json() for e in classified["check_events"]]
    dumps += [json.dumps(r.signal) for r in caplog.records if r.name == "meridian.signal"]  # type: ignore[attr-defined]
    dumps.append(caplog.text)
    assert any(r.name == "meridian.signal" for r in caplog.records)
    for secret in ("Omar Patel", "MHC-10002", "INV-204411", seeded_phone(), seeded_card(), seeded_code()):
        for dump in dumps:
            assert secret not in dump
    for token in ("[name]", "[phone]", "[customer id]", "[invoice id]"):
        assert token in planner_req.model_dump_json()


def test_choice_fields_match_consumer_types() -> None:
    assert [f.name for f in PLANNER_FIELDS] == ["knowledge", "account", "scheduling", "handoff", "topic"]
    assert [f.name for f in PLANNER_FIELDS] == list(PlannerChoices.model_fields)
    for f in PLANNER_FIELDS:
        args = typing.get_args(PlannerChoices.model_fields[f.name].annotation)
        if f.name == "topic" and not args:
            args = typing.get_args(Topic)
        assert tuple(f.options) == args, f.name
    assert tuple(CLASSIFIER_FIELDS[0].options) == typing.get_args(
        DangerAssessment.model_fields["label"].annotation
    )
    assert CLASSIFIER_FIELDS[0].name == DANGER_FIELD


def test_sp1_wording_kept() -> None:
    assert PLANNER_SYSTEM == (
        "You are the planner for Meridian Home Comfort's customer chat (heating, cooling and plumbing in Austin, "
        "Texas). You never write to the customer. Read STATE: the recent chat, any open task and the customer's "
        "latest message. For each field choose the one option that fits the customer's latest message, using the "
        'open task and recent chat to understand short replies. Choose "none" or "no" when the message does not '
        "need that kind of help. Private account details and any booking or change need the account or "
        "scheduling fields; public company questions need knowledge."
    )
    assert CLASSIFIER_SYSTEM == (
        'You check one customer message sent to a home heating, cooling and plumbing company. Choose "normal" '
        "unless the message itself says or clearly implies someone is in danger or there is an unexplained "
        "burning smell. You never reply to the customer."
    )
    by_name = {f.name: f for f in PLANNER_FIELDS}
    assert by_name["knowledge"].instructions.startswith("Does the latest message ask about Meridian's public")
    assert by_name["knowledge"].options["no"] == "No company information is needed to answer."
    assert by_name["account"].instructions == "Does the customer need their own account records read?"
    assert by_name["account"].options["invoice"] == (
        "Their invoice or bill: what a charge is for, the balance, the due date."
    )
    assert by_name["scheduling"].instructions == (
        "Does the customer want to book a new visit or change an existing one?"
    )
    assert by_name["scheduling"].options["none"] == "No booking or change is requested."
    assert (
        by_name["handoff"].instructions
        == "Does the message ask for something that must go to a staff member?"
    )
    assert by_name["handoff"].options["refund"] == "Asks for money back."
    assert by_name["handoff"].options["billing_dispute"] == "Says a charge is wrong or disputes it."
    assert CLASSIFIER_FIELDS[0].instructions == (
        "Is anyone in danger because of conditions in the home, or is there a burning smell whose cause is "
        "unclear?"
    )
    assert CLASSIFIER_FIELDS[0].options["burning_unclear"] == (
        "Mentions a burning or electrical smell without saying whether a breaker tripped."
    )


def _scan(path: Path) -> list[tuple[str, bool]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    guarded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and ast.unparse(node.test) == "TYPE_CHECKING":
            guarded.update(id(inner) for stmt in node.body for inner in ast.walk(stmt))
    found: list[tuple[str, bool]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((alias.name, id(node) in guarded) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"relative import in {path.name}"
            found.append((node.module or "", id(node) in guarded))
    return found


def test_plan_modules_import_allowed_layers() -> None:
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    run_time_ok = {
        PLAN_PY: (
            "meridian.domain",
            "meridian.ports.models",
            "meridian.policy.limits",
            "meridian.privacy.redact",
            "meridian.agent.context",
            "meridian.agent.signals",
            "meridian.agent.prompts.routing",
        ),
        ROUTING_PY: ("meridian.domain.turn", "meridian.ports.models"),
    }
    never = (
        "meridian.agent.routers",
        "meridian.agent.graph",
        "meridian.gates",
        "meridian.services",
        "meridian.adapters",
        "meridian.agent.nodes",
    )
    for path, allowed in run_time_ok.items():
        imports = _scan(path)
        print(path.name, imports)
        for module, guarded in imports:
            top = module.split(".")[0]
            assert top in stdlib or top in {"pydantic", "langgraph", "meridian"}, module
            assert not module.startswith(never), f"{path.name} imports {module}"
            if top == "meridian" and not guarded:
                assert module.startswith(allowed), f"{path.name} run-time import {module}"
            if module == "meridian.agent.gateway":
                assert guarded, "meridian.agent.gateway must be imported under TYPE_CHECKING only"
    assert ("meridian.agent.gateway", True) in _scan(PLAN_PY)


def test_jev_leaves_wording_unchanged() -> None:
    strings = [PLANNER_SYSTEM, CLASSIFIER_SYSTEM]
    for f in (*PLANNER_FIELDS, *CLASSIFIER_FIELDS):
        strings.append(f.instructions)
        strings.extend(f.options.values())
    assert len(strings) == 35
    for s in strings:
        assert redact(s, RedactionProfile.JEV).text == s
