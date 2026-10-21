"""AEA-51 composition tests (pass 1): the real container binds the real objects, role maps are guarded, the login gate.

Pass 2 adds the driven-turn parts (run_graph, trace identities, AC-2 part c, AC-41, AC-43, AC-44, AC-49..51).
Everything runs the real app over HTTP on loopback, a disposable DB copy and a scripted model at the provider boundary.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver
from pydantic import ValidationError

from meridian.adapters.models.anthropic import AnthropicAdapter
from meridian.adapters.models.openrouter_jev import JevAdapter
from meridian.adapters.retrieval_fastembed import FastembedIndex
from meridian.adapters.tracing_langfuse import NullTraceSink
from meridian.agent.specialists.specs import SPECS
from meridian.config import JEV_MODEL, Settings, default_model_settings
from meridian.domain.common import Role, SafeError
from meridian.web import deps
from meridian.web.app import ContainerOverrides, create_app
from meridian.web.container import Key
from tests.integration.customer_support import (
    RunOptions,
    StepJevModel,
    StepScript,
    customer_environment,
    fastembed_offline,
    open_customer_run,
)
from tests.journeys.support.client import JourneyClient
from tests.journeys.support.db import DbReader
from tests.journeys.support.logtap import tap_logs
from tests.journeys.support.server import launch_server, socket_guard


def _maps(settings: Settings) -> dict[str, Any]:
    return {
        "choice": settings.models.choice,
        "structured": settings.models.structured,
        "tools": settings.models.tools,
    }


def test_real_objects_bound(request: pytest.FixtureRequest) -> None:
    """AC-1 (structural part), PA-2, PA-3. Pass 2 adds run_graph, the driven WP-1 turn and the trace identities."""
    with open_customer_run(request, RunOptions()) as run:
        c = run.container
        saver = c.get(Key[Any]("checkpointer"))
        assert isinstance(saver.saver, SqliteSaver)
        assert saver.path.name == "checkpoints.sqlite"
        assert c.get(Key[Any]("compiled_graph")).config["recursion_limit"] == 25
        registry = c.get(Key[Any]("tool_registry"))
        for spec in SPECS.values():
            registry.check_covers(spec.tool_kinds)  # raises when a kind has no tool
        runner = c.get(Key[Any]("specialist_runner"))
        ports = c.get(Key[Any]("model_ports"))
        assert runner.transcript is ports["tools"][Role.SPECIALIST][0]
        assert runner.trace is c.get(Key[Any]("trace"))
        assert c.get(Key[Any]("retrieval_readiness")).ok
        composer = c.get(deps.REPLY_COMPOSER)
        assert composer is c.get(deps.REPLY_COMPOSER)
        graph_deps = c.get(Key[Any]("graph_deps"))
        assert graph_deps.ledger is c.get(Key[Any]("ledger"))
        assert graph_deps.trace is c.get(Key[Any]("trace"))
        assert graph_deps.specialists is runner
        assert graph_deps.retrieval is c.get(Key[Any]("retrieval_index"))
        assert isinstance(graph_deps.retrieval, FastembedIndex)
        assert graph_deps.gateway is c.get(Key[Any]("model_gateway"))
        classes = {
            "identity": "IdentityService",
            "scheduling": "SchedulingService",
            "handoff": "HandoffService",
            "brief": "BriefAssembler",
            "cases": "CaseService",
            "demo": "DemoService",
            "uow": "SqliteUnitOfWorkFactory",
            "gateway": "ModelGateway",
        }
        for attribute, name in classes.items():
            assert type(getattr(graph_deps, attribute)).__name__ == name, attribute
        table = []
        for map_name, configured in _maps(run.settings).items():
            for role, (provider, spec) in configured.items():
                port, bound_spec = ports[map_name][role]
                assert port is run.models[role]
                assert bound_spec == spec
                table.append((role.value, type(port).__name__, provider, spec.model))
        print("role, port class, provider, model:", table)

    # (b) the deployed shape: no overrides, an empty index, no outbound connection (PA-1..PA-3)
    with socket_guard() as guard, tap_logs() as logs, fastembed_offline():
        with customer_environment(index_dir=None, eval_key=None) as env:
            with launch_server(env.settings, overrides=None) as server:
                c = server.container
                ports = c.get(Key[Any]("model_ports"))
                planner = ports["choice"][Role.PLANNER][0]
                specialist = ports["tools"][Role.SPECIALIST][0]
                assert isinstance(planner, JevAdapter) and planner.model == JEV_MODEL
                assert isinstance(specialist, AnthropicAdapter)
                assert ports["structured"][Role.RESPONDER][0] is specialist  # same model, same object
                assert isinstance(c.get(Key[Any]("trace")), NullTraceSink)
                assert c.get(Key[Any]("retrieval_readiness")).ok is False
                print(
                    "deployed shape:",
                    [
                        (m, r.value, type(p).__name__, s.model)
                        for m, per_role in ports.items()
                        for r, (p, s) in per_role.items()
                    ],
                )
            warnings = [r for r in logs._snapshot() if "retrieval_not_ready" in r.getMessage()]
            assert len(warnings) == 1
            assert warnings[0].levelname == "WARNING"
            assert warnings[0].name == "meridian.graph"
            assert DbReader(env.db_path).scalar("SELECT COUNT(*) FROM spend_ledger") == 0
    assert guard.blocked == []


def test_role_maps_bound_and_guarded() -> None:
    """AC-2 parts (a) and (b), PA-1. Part (c), the ledger models after a driven turn, is pass 2."""
    # (a) a Jev adapter in a structured role is refused when Settings is built, by field, never by value
    good = default_model_settings()
    jev_spec = good.choice[Role.PLANNER][1]
    with customer_environment(index_dir=None, eval_key=None) as env:
        fields = {name: getattr(env.settings, name) for name in type(env.settings).model_fields}
        bad_models = {
            "choice": dict(good.choice),
            "structured": {**good.structured, Role.RESPONDER: ("openrouter_jev", jev_spec)},
            "tools": dict(good.tools),
        }
        with pytest.raises(ValidationError) as caught:
            Settings.model_validate({**fields, "models": bad_models})
        problems = SafeError.from_validation_error(caught.value)
        assert any(p.field.startswith("models.structured") for p in problems)
        text = str(caught.value) + repr(problems)
        for secret in (*env.secret_values(), env.settings.anthropic_api_key.get_secret_value()):
            assert secret not in text

        # (b) an override whose provider differs from the configured one stops start-up, naming the role (PA-1)
        script = StepScript()
        mismatched = StepJevModel(script, role=Role.RESPONDER, model=JEV_MODEL)
        app = create_app(
            env.settings,
            overrides=ContainerOverrides(structured={Role.RESPONDER: mismatched}),
        )

        async def start() -> None:
            async with app.router.lifespan_context(app):
                pass

        with pytest.raises(ValueError, match=r"override for role responder has provider openrouter_jev"):
            asyncio.run(start())


def test_login_gate(request: pytest.FixtureRequest) -> None:
    """AC-4: no session cookie, no chat. Both responses are checked against the OpenAPI by the client."""
    with open_customer_run(request, RunOptions()) as run:
        anonymous = JourneyClient(run.base_url)
        try:
            for method, path, operation in (
                ("POST", "/api/chat/sessions", "startChatSession"),
                ("POST", f"/api/chat/sessions/{uuid.uuid4()}/turns", "submitTurn"),
            ):
                response = anonymous.call(
                    method,
                    path,
                    operation_id=operation,
                    body={"turn_id": str(uuid.uuid4()), "payload": {"kind": "text", "text": "hi"}}
                    if operation == "submitTurn"
                    else None,
                )
                body = response.json()
                assert response.status_code == 401
                assert body["error"]["code"] == "UNAUTHENTICATED"
                assert body["error"]["details"]["reason"] == "none"
        finally:
            anonymous.close()
