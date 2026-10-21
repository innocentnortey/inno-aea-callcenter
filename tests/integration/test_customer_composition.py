"""AEA-51 composition tests: the real container binds the real objects, role maps are guarded, the login gate, the
run tag, concurrency, the real adapters behind CON-2 and the eval runner against the app.

Everything runs the real app over HTTP on loopback, a disposable DB copy and a scripted model at the provider boundary.
"""

from __future__ import annotations

import asyncio
import io
import json
import re
import secrets
import shutil
import threading
import uuid
from pathlib import Path
from typing import Any

import anthropic
import httpx
import httpx2
import pytest
from langgraph.checkpoint.sqlite import SqliteSaver
from pydantic import SecretStr, ValidationError

from meridian.adapters.models.anthropic import AnthropicAdapter
from meridian.adapters.models.openrouter_jev import JevAdapter
from meridian.adapters.retrieval_fastembed import FastembedIndex
from meridian.adapters.tracing_langfuse import NullTraceSink
from meridian.agent.specialists.specs import SPECS
from meridian.config import JEV_MODEL, SONNET_MODEL, Settings, default_model_settings
from meridian.domain.common import Role, SafeError
from meridian.privacy.redact import RedactionProfile, redact
from meridian.web import deps
from meridian.web.app import ContainerOverrides, create_app
from meridian.web.container import Key
from meridian.web.middleware import EVAL_KEY_HEADER, RUN_ID_HEADER
from tests.graph.worked_pair_scenarios import (
    CO_TEXT,
    NORMAL,
    TOOLS,
    WP1_QUERY,
    BookVisitArgs,
    FindWindowsArgs,
    kb_steps,
    planner,
    responder,
    scheduling_steps,
    tool,
    top_passage,
    verified_open,
    wp1,
)
from tests.integration.customer_api import blocks, login, open_chat, say
from tests.integration.customer_support import (
    REPO_ROOT,
    RunOptions,
    StepJevModel,
    StepScript,
    build_capture_sink,
    customer_environment,
    fastembed_offline,
    finished_spans,
    open_customer_run,
    request_text,
    require_index,
    span_meta,
)
from tests.journeys.support.client import JourneyClient
from tests.journeys.support.db import DbReader
from tests.journeys.support.env import letters
from tests.journeys.support.logtap import tap_logs
from tests.journeys.support.scripted_model import role_specs
from tests.journeys.support.server import launch_server, socket_guard
from tests.unit.adapters._tracing_doubles import close_all


def _maps(settings: Settings) -> dict[str, Any]:
    return {
        "choice": settings.models.choice,
        "structured": settings.models.structured,
        "tools": settings.models.tools,
    }


def test_real_objects_bound(request: pytest.FixtureRequest) -> None:
    """AC-1, PA-2, PA-3: every seam holds its real object; only the scripted adapter and the in-memory exporter are
    substitutes; run_graph is the compiled graph's, proven by a driven turn."""
    registry: list[Any] = []
    sink, _exporter = build_capture_sink(registry)
    try:
        _check_bound_with_override(request, sink)
    finally:
        close_all(registry)
    _check_deployed_shape()


def _check_bound_with_override(request: pytest.FixtureRequest, sink: Any) -> None:
    with open_customer_run(request, RunOptions(trace=sink)) as run:
        c = run.container
        assert callable(c.get(Key[Any]("run_graph")))
        driven = wp1(run)  # the graph ran: a stored plan_mode proves run_graph is the compiled graph's
        row = run.db.one("SELECT plan_mode, outcome FROM turns WHERE turn_id = ?", (driven.turn_ids[0],))
        assert row["plan_mode"] == "act" and row["outcome"] == "acted"
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
        assert runner.trace is c.get(Key[Any]("trace")) is sink
        assert c.get(Key[Any]("retrieval_readiness")).ok
        composer = c.get(deps.REPLY_COMPOSER)
        assert composer is c.get(deps.REPLY_COMPOSER)
        graph_deps = c.get(Key[Any]("graph_deps"))
        assert graph_deps.ledger is c.get(Key[Any]("ledger"))
        assert graph_deps.trace is sink
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


def _check_deployed_shape() -> None:
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


def test_role_maps_bound_and_guarded(request: pytest.FixtureRequest) -> None:
    """AC-2 and PA-1: a Jev adapter in a structured role cannot be configured; an override with the wrong provider stops
    start-up by role; after a turn every ledger row names its role's configured provider and model."""
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

    # (c) after a driven turn, every spend_ledger row equals its role's configured (provider, model)
    with open_customer_run(request, RunOptions()) as run:
        driven = wp1(run)
        configured = {r: (p, spec.model) for r, (p, spec) in role_specs(run.settings).items()}
        rows = run.db.rows(
            "SELECT role, provider, model FROM spend_ledger WHERE turn_id = ?", (driven.turn_ids[0],)
        )
        assert {r["role"] for r in rows} == {"planner", "classifier", "specialist", "responder"}
        for row in rows:
            assert (row["provider"], row["model"]) == configured[Role(row["role"])], row["role"]
        by_role = {r["role"]: (r["provider"], r["model"]) for r in rows}
        assert by_role["planner"] == by_role["classifier"] == ("openrouter_jev", JEV_MODEL)
        assert by_role["responder"] == by_role["specialist"] == ("anthropic", SONNET_MODEL)


def test_run_id_honoured_only_with_eval_key(request: pytest.FixtureRequest) -> None:
    """AC-41: a run id header without the eval key is ignored (live, no run id); with the key it is honoured."""
    with open_customer_run(request, RunOptions(eval_key=True)) as run:
        client = login(run)
        keyless_id, keyed_id = str(uuid.uuid4()), str(uuid.uuid4())
        run.steps.set_step({})
        plain = open_chat(run, client, headers={RUN_ID_HEADER: keyless_id})
        say(plain, CO_TEXT, headers={RUN_ID_HEADER: keyless_id})
        keyed_headers = {EVAL_KEY_HEADER: str(run.eval_key), RUN_ID_HEADER: keyed_id}
        keyed = open_chat(run, client, headers=keyed_headers)
        say(keyed, CO_TEXT, headers=keyed_headers)
        for chat, tag, run_id in ((plain, "live", None), (keyed, "eval", keyed_id)):
            conversation = run.db.one(
                "SELECT run_tag, run_id FROM conversations WHERE thread_id = ?", (chat.thread_id,)
            )
            turn = run.db.one("SELECT run_tag, run_id FROM turns WHERE thread_id = ?", (chat.thread_id,))
            assert (conversation["run_tag"], conversation["run_id"]) == (tag, run_id)
            assert (turn["run_tag"], turn["run_id"]) == (tag, run_id)


def test_twenty_concurrent_conversations(request: pytest.FixtureRequest) -> None:
    """AC-43 (PD-13): 20 conversations at once never see BUSY or RATE_LIMITED; two racing for one slot give one
    booking and one SLOT_TAKEN."""
    plan = planner(scheduling="book_new", topic="booking")
    find = scheduling_steps(
        tool(TOOLS["find_windows"], FindWindowsArgs(service_type="hvac_repair").model_dump(mode="json"))
    )
    with open_customer_run(request, RunOptions()) as run:
        client = login(run)
        chats: list[Any] = []
        slot_x = 0
        for _ in range(20):
            chat = open_chat(run, client)
            responses = verified_open(
                run,
                chat,
                "MHC-10001",
                "I would like a repair visit on a teal day",
                first={
                    Role.CLASSIFIER: NORMAL,
                    Role.PLANNER: plan,
                    Role.RESPONDER: responder("I need your record first."),
                },
                after_code={
                    Role.CLASSIFIER: NORMAL,
                    Role.PLANNER: plan,
                    Role.SPECIALIST: find,
                    Role.RESPONDER: responder("Here are the windows."),
                },
            )
            chats.append(chat)
            shown = [
                int(w["slot_id"])
                for day in blocks(responses[-1], "slot_card")[0]["days"]
                for w in day["windows"]
            ]
            slot_x = slot_x or shown[0]
            assert shown[0] == slot_x  # every chat was shown the same windows
        book = scheduling_steps(
            tool(TOOLS["book"], BookVisitArgs(slot_id=slot_x, issue="AC not cooling").model_dump())
        )
        run.steps.set_step(
            {
                Role.CLASSIFIER: NORMAL,
                Role.PLANNER: plan,
                Role.RESPONDER: responder("Here is where things stand."),
            },
            by_marker={
                "teal": {Role.SPECIALIST: find},
                "amber": {Role.SPECIALIST: book},
            },
        )
        barrier = threading.Barrier(20)
        outcome: dict[int, Any] = {}

        def go(index: int) -> None:
            barrier.wait()
            text = "Book the amber window please" if index < 2 else "Which windows are open on teal days?"
            outcome[index] = say(chats[index], text)

        threads = [threading.Thread(target=go, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)
        assert len(outcome) == 20, "a conversation did not answer"
        notices = {r.json()["notice"]["code"] for r in outcome.values() if r.json()["notice"]}
        assert not notices & {"BUSY", "RATE_LIMITED"}, notices
        calls = [c for c in run.script.calls if c.role is Role.SPECIALIST]
        assert calls, "no specialist ran"
        racers = [c for c in calls if "amber" in request_text(c.request)]
        assert len(racers) >= 2, "marker not visible in specialist request"
        booked = run.db.rows("SELECT * FROM actions WHERE kind = 'booked'")
        assert len(booked) == 1
        assert run.db.count("appointments", "slot_id = ? AND status = 'scheduled'", (slot_x,)) == 1
        refusals = run.db.rows("SELECT * FROM lookup_log WHERE result_seen LIKE '%slot_taken%'")
        assert len(refusals) == 1, "exactly one racer is refused with SLOT_TAKEN"


class _Providers:
    """Recorded-shape provider responses behind the real adapters (models.md section 3). Modes are flipped per turn."""

    def __init__(self, passage_id: str) -> None:
        self.passage_id = passage_id
        self.jev_planner_error = False
        self.specialist_error = False
        self.jev_bodies: list[dict[str, Any]] = []
        self.anthropic_bodies: list[dict[str, Any]] = []

    # -- Jev (httpx) --
    def jev(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        self.jev_bodies.append(body)
        names = list(body["questions"])
        if "knowledge" in names and self.jev_planner_error:
            return httpx.Response(200, json={"error": {"code": 503, "message": "synthetic"}})
        choices = (
            {
                "knowledge": "yes",
                "account": "none",
                "scheduling": "none",
                "handoff": "none",
                "topic": "membership",
            }
            if "knowledge" in names
            else {"danger_level": "normal"}
        )
        answers = {
            n: {"type": "choice", "choice": choices[n], "probabilities": {choices[n]: 1.0}} for n in names
        }
        return httpx.Response(
            200,
            json={
                "model": "typesafe/jev-1.13-20260917",
                "id": "gen-test",
                "answers": answers,
                "usage": {"input_tokens": 100, "output_tokens": 10, "cost": 1e-05},
            },
        )

    # -- Anthropic (httpx2) --
    def anthropic(self, request: httpx2.Request) -> httpx2.Response:
        body = json.loads(request.content)
        self.anthropic_bodies.append(body)
        if "tools" in body:
            if self.specialist_error:
                return httpx2.Response(
                    500, json={"type": "error", "error": {"type": "api_error", "message": "synthetic"}}
                )
            first = len(body["messages"]) == 1
            block = (
                {"type": "tool_use", "id": "toolu_1", "name": "kb_search", "input": {"query": WP1_QUERY}}
                if first
                else {
                    "type": "tool_use",
                    "id": "toolu_2",
                    "name": "report_facts",
                    "input": {
                        "points": [{"text": "Members save 15% on repairs.", "passage_id": self.passage_id}],
                        "answered": True,
                    },
                }
            )
            return self._message([block], "tool_use")
        schema = body.get("output_config", {}).get("format", {}).get("schema", {})
        properties = set(schema.get("properties", {}))
        if "knowledge" in properties:  # the Sonnet planner fallback (a choice)
            text = json.dumps(
                {
                    "knowledge": "yes",
                    "account": "none",
                    "scheduling": "none",
                    "handoff": "none",
                    "topic": "membership",
                }
            )
        elif "text" in properties:
            text = json.dumps({"text": "Members save 15% on repairs."})
        else:  # the brief: one quote copied from the customer message it was shown
            shown = re.search(r"\[message (\d+)\] (.{1,30})", body["messages"][0]["content"])
            quote = {"message_id": int(shown.group(1)), "text": shown.group(2)} if shown else None
            text = json.dumps(
                {"needs": [quote] if quote else [], "claims": [], "open_decision": "Review the question."}
            )
        return self._message([{"type": "text", "text": text}], "end_turn")

    @staticmethod
    def _message(content: list[dict[str, Any]], stop_reason: str) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "model": SONNET_MODEL,
                "content": content,
                "stop_reason": stop_reason,
                "stop_sequence": None,
                "usage": {"input_tokens": 100, "output_tokens": 10},
            },
        )


def test_real_adapters_through_con2(request: pytest.FixtureRequest) -> None:
    """AC-44: the real JevAdapter and AnthropicAdapter (recorded-shape bodies on mock transports) carry a WP-1 turn;
    an error inside a Jev 200 makes the Sonnet planner answer; a specialist that always 5xx gives model_error; one HTTP
    request and one ledger row per attempt; no forced tool_choice; data collection denied on every Jev body."""
    from tests.integration.customer_support import serve_customer_run

    token = secrets.token_hex(8)
    with socket_guard() as guard, tap_logs() as logs, fastembed_offline():
        with customer_environment(index_dir=require_index(), eval_key=None) as env:
            providers = _Providers("placeholder")
            jev = JevAdapter(
                httpx.Client(transport=httpx.MockTransport(providers.jev)),
                api_key=SecretStr("test-or-" + token),
                model=JEV_MODEL,
            )
            sonnet = AnthropicAdapter(
                anthropic.Anthropic(
                    api_key="sk-test-" + token,
                    max_retries=0,
                    open_telemetry=False,
                    http_client=httpx2.Client(transport=httpx2.MockTransport(providers.anthropic)),
                ),
                model=SONNET_MODEL,
            )
            overrides = ContainerOverrides(
                choice={Role.PLANNER: jev, Role.CLASSIFIER: jev, Role.PLANNER_FALLBACK: sonnet},
                structured={Role.RESPONDER: sonnet, Role.BRIEF: sonnet},
                tools={Role.SPECIALIST: sonnet},
            )
            kwargs: dict[str, Any] = {"guard": guard, "logs": logs, "eval_key": None}
            with serve_customer_run(request, env, RunOptions(), overrides=overrides, **kwargs) as run:
                providers.passage_id = str(top_passage(run, WP1_QUERY).passage_id)
                chat = open_chat(run, login(run))
                turns = []
                for mode in ("ok", "jev_error", "specialist_error"):
                    providers.jev_planner_error = mode == "jev_error"
                    providers.specialist_error = mode == "specialist_error"
                    response = say(chat, "Do members get a discount on repairs?")
                    turns.append((mode, response.json()["turn_id"], response))
                for mode, turn_id, response in turns:
                    assert response.status_code == 200  # no exception reached the route
                    row = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (turn_id,))
                    if mode == "ok":
                        assert row["outcome"] == "acted" and row["planner_fallback_used"] == 0
                    elif mode == "jev_error":
                        assert row["outcome"] == "acted" and row["planner_fallback_used"] == 1
                    else:
                        assert (row["outcome"], row["degrade_reason"]) == ("degraded_handoff", "model_error")
                rows = run.db.rows("SELECT provider, role FROM spend_ledger")
                assert sum(r["provider"] == "openrouter_jev" for r in rows) == len(providers.jev_bodies)
                assert sum(r["provider"] == "anthropic" for r in rows) == len(providers.anthropic_bodies)
                fallback_rows = [r for r in rows if r["role"] == "planner_fallback"]
                assert fallback_rows, "the Sonnet planner answered after the Jev error"
                for body in providers.anthropic_bodies:
                    assert body.get("tool_choice", {"type": "auto"}) == {"type": "auto"}
                assert providers.jev_bodies and all(
                    b["provider"] == {"data_collection": "deny"} for b in providers.jev_bodies
                )
    assert guard.blocked == []


# -- the eval runner (AEA-24) against the app: WF-9, WF-10, WF-12 ---------------------------------------------------


def _wp1_script(run: Any) -> None:
    """The permissive step for WP-1's three turns (no $149): planner, classifier, specialist and responder."""
    first, second = kb_steps(run, WP1_QUERY, "Members save 15% on repairs.")
    run.steps.set_step(
        {
            Role.PLANNER: planner(knowledge="yes", topic="membership"),
            Role.CLASSIFIER: NORMAL,
            Role.SPECIALIST: (first, second),
            Role.RESPONDER: responder("Members save 15% on repairs."),
        }
    )


def _run_eval(run: Any, tmp: Path, argv: list[str], *, key: str) -> tuple[int, dict[str, Any], str, Path]:
    """AEA-24's runner in this process through its documented seam; nothing under the repo's eval/ is written."""
    from eval.harness.cli import main
    from eval.harness.deps import HarnessDeps
    from eval.harness.freeze import write_freeze

    cases = tmp / "cases"
    if not cases.exists():
        (cases / "dev").mkdir(parents=True)
        for name in ("WP-1.case.json", "WP-1.key.json"):
            shutil.copy2(REPO_ROOT / "eval" / "cases" / "dev" / name, cases / "dev" / name)
    reports = tmp / f"reports-{secrets.token_hex(3)}"
    freeze_file = tmp / f"freeze-{secrets.token_hex(3)}.json"
    write_freeze(freeze_file)
    log = io.StringIO()
    deps = HarnessDeps(
        env={
            "MERIDIAN_EVAL_KEY": key,
            "MERIDIAN_DEMO_USERNAME": run.demo_username,
            "MERIDIAN_DEMO_PASSWORD": run.settings.demo_password.get_secret_value(),
        },
        freeze_file=freeze_file,
        log_stream=log,
        ledger_dir=tmp / "ledger",
    )
    full = [
        *argv,
        "--base-url",
        run.base_url,
        "--db-copy",
        str(run.env.db_path),
        "--cases-dir",
        str(cases),
        "--reports-dir",
        str(reports),
    ]
    code = main(full, deps=deps)
    files = sorted(reports.glob("*.json")) if reports.is_dir() else []
    assert code in (0, 4), f"the runner refused or failed (exit {code}); its log: {log.getvalue()[-800:]}"
    assert len(files) == 1, f"expected one report, found {len(files)}"
    return code, json.loads(files[0].read_text(encoding="utf-8")), log.getvalue(), reports


def _rows_of_run(run: Any, run_id: str) -> dict[str, list[dict[str, Any]]]:
    return {
        table: run.db.rows(f"SELECT * FROM {table} WHERE run_id = ?", (run_id,))  # noqa: S608
        for table in ("conversations", "turns", "spend_ledger")
    }


def _check_tagged_records(run: Any, rows: dict[str, list[dict[str, Any]]], tag: str) -> None:
    assert rows["conversations"] and rows["turns"] and rows["spend_ledger"]
    for table in rows.values():
        assert {r["run_tag"] for r in table} == {tag}
    for turn in rows["turns"]:
        events = {
            e["check_kind"]
            for e in run.db.rows("SELECT * FROM check_events WHERE turn_id = ?", (turn["turn_id"],))
        }
        assert {"gate", "classifier"} <= events and events & {"fact", "completion"}, events


def _turn_spans(spans: list[Any], run_id: str, tag: str) -> list[Any]:
    masked = redact(run_id, RedactionProfile.TRACE).text
    found = [s for s in spans if s.name == "turn" and span_meta(s, "run_id") == masked]
    assert found, "no turn span carries the run id"
    assert {span_meta(s, "run_tag") for s in found} == {tag}
    return found


def test_eval_runner_against_app_wf9(request: pytest.FixtureRequest, tmp_path: Path) -> None:
    """AC-49: AEA-24's runner plays one dev case against the app with the eval key: WF-1 records are tagged eval + run
    id, the report has one case result, the DB-copy check ran; a run without the key is tagged live."""
    registry: list[Any] = []
    sink, exporter = build_capture_sink(registry)
    try:
        with open_customer_run(request, RunOptions(eval_key=True, trace=sink)) as run:
            _wp1_script(run)
            code, report, _log, _ = _run_eval(
                run, tmp_path, ["run", "--suite", "worked-pairs", "--repeats", "1"], key=str(run.eval_key)
            )
            run_id = report["run"]["run_id"]
            rows = _rows_of_run(run, run_id)
            _check_tagged_records(run, rows, "eval")
            assert len(report["results"]) == 1
            assert (
                report["summary"]["db_check"]["status"] == "ran"
            )  # the DB-copy check ran on the working copy
            assert not {r["thread_id"] for r in rows["turns"]} & {
                r["thread_id"] for r in run.db.rows("SELECT thread_id FROM turns WHERE run_id IS NULL")
            }
            spans = finished_spans(sink, exporter)
            for span in _turn_spans(spans, run_id, "eval"):
                names = {s.name for s in spans if s.context.trace_id == span.context.trace_id}
                assert any(n.startswith("model_call:") for n in names)
            # the keyless contrast: the runner holds a key the app does not, so the app tags its rows live
            existing = {r["turn_id"] for r in run.db.rows("SELECT turn_id FROM turns")}
            _wp1_script(run)
            _, report2, _, _ = _run_eval(
                run, tmp_path, ["run", "--suite", "worked-pairs", "--repeats", "1"], key=letters(40)
            )
            fresh = [
                r
                for r in run.db.rows("SELECT turn_id, run_tag, run_id FROM turns")
                if r["turn_id"] not in existing
            ]
            assert (
                fresh and {r["run_tag"] for r in fresh} == {"live"} and {r["run_id"] for r in fresh} == {None}
            )
            assert code in (0, 4) and report2["run"]["run_id"]
    finally:
        close_all(registry)


def test_load_runner_against_app_wf10(request: pytest.FixtureRequest, tmp_path: Path) -> None:
    """AC-50: AEA-24's load suite with two conversations: one timing line per CON-2 call, records tagged load, and the
    DB-copy check reports no violations."""
    registry: list[Any] = []
    sink, exporter = build_capture_sink(registry)
    try:
        with open_customer_run(request, RunOptions(eval_key=True, trace=sink)) as run:
            _wp1_script(run)
            _, report, _, reports = _run_eval(
                run,
                tmp_path,
                ["run", "--suite", "load", "--split", "dev", "--conversations", "2"],
                key=str(run.eval_key),
            )
            run_id = report["run"]["run_id"]
            rows = _rows_of_run(run, run_id)
            assert rows["turns"] and {r["run_tag"] for r in rows["turns"]} == {"load"}
            assert {r["run_tag"] for r in rows["conversations"]} == {"load"}
            timing_files = sorted(reports.glob("*.client_side_turn_timings.jsonl"))
            assert len(timing_files) == 1
            lines = timing_files[0].read_text(encoding="utf-8").splitlines()
            assert len(lines) == len(rows["turns"])
            db_check = report["summary"]["db_check"]
            assert (
                db_check["status"] == "ran"
                and db_check["findings"] == []
                and db_check["double_bookings"] == 0
            )
            assert _turn_spans(finished_spans(sink, exporter), run_id, "load")
    finally:
        close_all(registry)


def test_experiment_run_spend_wf12(request: pytest.FixtureRequest, tmp_path: Path) -> None:
    """AC-51: a dev run with --experiment XP-1: the ledger rows carry eval + run id and count in spend_today()."""
    with open_customer_run(request, RunOptions(eval_key=True)) as run:
        ledger = run.container.get(Key[Any]("ledger"))
        before = ledger.spend_today()
        _wp1_script(run)
        _, report, _, _ = _run_eval(
            run,
            tmp_path,
            ["run", "--suite", "worked-pairs", "--repeats", "1", "--experiment", "XP-1"],
            key=str(run.eval_key),
        )
        assert report["run"]["experiment_id"] == "XP-1"
        run_id = report["run"]["run_id"]
        rows = run.db.rows("SELECT * FROM spend_ledger WHERE run_id = ?", (run_id,))
        assert rows and {r["run_tag"] for r in rows} == {"eval"}
        spent = sum(float(r["cost_usd"]) for r in rows)
        assert ledger.spend_today() - before == pytest.approx(spent)
        print(f"scripted calls cost 0.0, so the spend delta is {spent}: the rows still exist and are counted")
