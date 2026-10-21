"""Harness self-checks (AEA-57, AC-1..AC-7, AC-14, AC-16, AC-17). Not marked `journey`."""

from __future__ import annotations

import ast
import json
import re
import socket
import sqlite3
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, get_args, get_origin

import httpx
import pytest
from fastapi import FastAPI

from meridian.adapters.sqlite.migrate import ISSUED_TABLES, schema_files
from meridian.config import ENV_NAMES, JEV_MODEL, SONNET_MODEL, ModelSettings, Settings
from meridian.domain.common import CallRecord, ProviderCall, ProviderFailureKind, ProviderName, Role
from meridian.domain.turn import ResponderDraft
from meridian.policy.limits import Limits
from meridian.ports.models import ChoiceField, ChoiceRequest, StructuredRequest, ToolStepRequest
from meridian.web.container import Container, Key
from meridian.web.deps import WALL_CLOCK, get_session_service, get_wall_clock, provided
from tests.api.openapi_check import load_contract
from tests.fixtures.sqlite import ISSUED_DB, temp_sqlite
from tests.journeys.support import plugin
from tests.journeys.support.client import JourneyClient
from tests.journeys.support.db import DbReader, issued_rows, sha256_file
from tests.journeys.support.env import REPO_ROOT, journey_environ, journey_environment
from tests.journeys.support.record import FIELDS, build_record_data, maybe_write_record, render_record
from tests.journeys.support.run import JourneyRun
from tests.journeys.support.scripted_model import (
    JourneyScript,
    RawToolCall,
    RawToolStep,
    ScriptedAnthropicModel,
    ScriptedJevModel,
    role_specs,
    scripted_overrides,
)
from tests.journeys.support.server import StepClock, launch_server, socket_guard
from tests.journeys.support.steps import (
    OPERATION_OWNERS,
    RunNote,
    StepCollector,
    StepResult,
    TestOutcome,
    convention_violations,
    missing_needs,
    stop_blocked,
)

SUPPORT = Path(__file__).resolve().parent


def test_disposable_copy_and_issued_untouched() -> None:
    with socket_guard(), journey_environment() as env:
        assert not env.db_path.exists()
        with launch_server(env.settings, overrides=None):
            assert env.db_path.exists()
            reader = DbReader(env.db_path)
            counts = {}
            for table in ISSUED_TABLES:
                assert reader.table_rows(table) == issued_rows(table), table
                counts[table] = len(reader.table_rows(table))
            with reader.connect() as conn:
                names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            for schema in schema_files():
                for table in re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", schema.read_text()):
                    assert table in names, table
        root = env.root
    after = sha256_file(ISSUED_DB)
    print(f"issued sha256 before={env.issued_sha256_before} after={after}")
    print(f"issued table rows: {counts}")
    print(f"temp root removed: {not root.exists()}")
    assert after == env.issued_sha256_before
    assert not root.exists()


def test_scripted_model_parses_like_adapters() -> None:
    script = JourneyScript()
    planner = ScriptedJevModel(script, role=Role.PLANNER, model=JEV_MODEL)
    request = ChoiceRequest(
        system="s",
        state={},
        fields=(
            ChoiceField(name="knowledge", instructions="i", options={"no": "n", "yes": "y"}),
            ChoiceField(name="topic", instructions="i", options={"other": "o", "billing": "b"}),
        ),
    )
    script.add(
        Role.PLANNER,
        '{"knowledge": "no", "topic": "other"}',
        '{"knowledge": "maybe", "topic": "other"}',
        '{"knowledge": "no"',
    )
    ok = planner.choose(request, timeout_s=1.0)
    assert ok.failure is None and ok.value is not None
    assert ok.value.choices == {"knowledge": "no", "topic": "other"} and ok.value.probabilities is None
    assert isinstance(ok.record, ProviderCall) and not isinstance(ok.record, CallRecord)
    assert ok.record.provider == "openrouter_jev" and ok.record.model == JEV_MODEL
    assert ok.record.cost_usd == 0.0 and ok.record.cost_source == "price_table" and ok.record.status == "ok"
    assert planner.provider == "openrouter_jev" and planner.model == JEV_MODEL
    kinds: list[str] = []
    for _ in range(2):
        bad = planner.choose(request, timeout_s=1.0)
        assert bad.value is None and bad.failure is not None and bad.failure.retryable is False
        assert bad.failure.kind is ProviderFailureKind.INVALID_OUTPUT and bad.record.status == "error"
        kinds.append(bad.failure.kind.value)

    responder = ScriptedAnthropicModel(script, role=Role.RESPONDER, model=SONNET_MODEL)
    structured = StructuredRequest(
        system_prefix="p",
        system_dynamic="d",
        user="u",
        output_model=ResponderDraft,
        max_tokens=10,
        effort=None,
    )
    script.add(Role.RESPONDER, '{"text": "hello"}', '{"text": ""}', "not json")
    good = responder.structured(structured, timeout_s=1.0)
    assert good.value is not None and good.value.text == "hello" and good.failure is None
    for _ in range(2):
        bad_draft = responder.structured(structured, timeout_s=1.0)
        assert bad_draft.value is None and bad_draft.failure is not None
        assert bad_draft.failure.kind is ProviderFailureKind.INVALID_OUTPUT
        kinds.append(bad_draft.failure.kind.value)

    specialist = ScriptedAnthropicModel(script, role=Role.SPECIALIST, model=SONNET_MODEL)
    script.add(
        Role.SPECIALIST,
        RawToolStep(
            text="",
            calls=(
                RawToolCall(id="call-a", name="read_invoices", arguments='{"invoice_id": "INV-A"}'),
                RawToolCall(id="call-b", name="read_invoices", arguments="{bad"),
            ),
            stop_reason="tool_use",
        ),
    )
    messages = specialist.start("u")
    step = specialist.tool_step(
        ToolStepRequest(
            system_prefix="p", system_dynamic="d", messages=messages, tools=(), max_tokens=10, effort=None
        ),
        timeout_s=1.0,
    )
    assert step.failure is None and step.value is not None
    assert step.value.tool_calls[0].args == {"invoice_id": "INV-A"} and step.value.tool_calls[1].args is None

    exhausted = planner.choose(request, timeout_s=1.0)
    assert exhausted.failure is not None and exhausted.failure.kind is ProviderFailureKind.INVALID_OUTPUT
    assert [c.result for c in script.problems()].count("exhausted") == 1
    assert len(script.calls) == 8
    with pytest.raises(TypeError):
        JourneyScript().add(Role.SPECIALIST, "text")

    settings = Settings.from_env(journey_environ(Path("/nonexistent-journey-root")))
    _, models = scripted_overrides(settings, JourneyScript(), wall_clock=None)
    configured = role_specs(settings)
    assert set(models) == set(configured)
    for role, (provider, spec) in configured.items():
        assert models[role].provider == provider and models[role].model == spec.model
    print(f"failure kinds: {kinds}; calls per role: {[(c.role.value, c.result) for c in script.calls]}")


def _literals(annotation: Any) -> set[Any]:
    if get_origin(annotation) is None:
        return set()
    found: set[Any] = set()
    if str(get_origin(annotation)).endswith("Literal"):
        return set(get_args(annotation))
    for arg in get_args(annotation):
        found |= _literals(arg)
    return found


def test_scripted_model_not_selectable_in_deploy() -> None:
    offenders: list[str] = []
    for path in sorted((REPO_ROOT / "src" / "meridian").rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            offenders += [f"{path}: {n}" for n in names if n == "tests" or n.startswith("tests.")]
    print(f"import scan: {len(offenders)} offenders")
    assert offenders == []
    banned = ("scripted", "journey", "fake")
    for name in [*Settings.model_fields, *ENV_NAMES.values()]:
        assert not any(b in name.lower() for b in banned), name
    allowed = {"anthropic", "openrouter_jev"}
    assert set(get_args(ProviderName)) == allowed
    for field in ModelSettings.model_fields.values():
        assert _literals(field.annotation) <= allowed | set(Role)
    assert {ScriptedAnthropicModel.provider, ScriptedJevModel.provider} <= allowed


def test_server_thread_ephemeral_port() -> None:
    with socket_guard(), journey_environment() as env:
        with launch_server(env.settings, overrides=None) as server:
            assert server.host == "127.0.0.1" and server.port > 0 and server.port not in {4019, 5184}
            assert server.container is server.app.state.container
            assert not isinstance(server.container.get(WALL_CLOCK), StepClock)
            assert server.thread.is_alive()
            print(f"host={server.host} port={server.port} thread alive={server.thread.is_alive()}")
        print(f"after: thread alive={server.thread.is_alive()} close_count={server.close_count}")
        assert not server.thread.is_alive()
        assert server.close_count == 1
        assert server.container.closed
        assert server.app.state.container is None


def test_client_validates_every_response() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        headers = {"X-Request-ID": "rid"}
        if request.url.path == "/api/session":
            body = {
                "error": {
                    "code": "UNAUTHENTICATED",
                    "field": None,
                    "constraint": None,
                    "details": {"reason": "none"},
                },
                "request_id": "rid",
            }
            return httpx.Response(401, json=body, headers=headers)
        if request.url.params.get("case") == "status":
            return httpx.Response(418, json={}, headers=headers)
        return httpx.Response(200, json={"now": 5}, headers=headers)

    client = JourneyClient("http://journey.test", transport=httpx.MockTransport(handler))
    assert client.call("GET", "/api/session", operation_id="getSession").status_code == 401
    with pytest.raises(AssertionError, match="getDemoClock") as status_error:
        client.call("GET", "/api/demo/clock?case=status", operation_id="getDemoClock")
    assert "418" in str(status_error.value)
    with pytest.raises(AssertionError, match="getDemoClock") as body_error:
        client.call("GET", "/api/demo/clock?case=body", operation_id="getDemoClock")
    assert "200" in str(body_error.value)
    sent = len(calls)
    with pytest.raises(AssertionError, match="must name its operationId"):
        client.call("GET", "/api/demo/clock", operation_id=None)
    assert len(calls) == sent
    print(f"failing assertions: {status_error.value!s} | {body_error.value!s}")


def test_db_reader_read_only() -> None:
    with temp_sqlite() as store:
        reader = DbReader(store.db_path)
        with reader.connect() as conn:
            with pytest.raises(sqlite3.OperationalError, match="readonly") as error:
                conn.execute(
                    "INSERT INTO demo_state (id, demo_now, staffing) VALUES (1, 'x', 'nobody_online')"
                )
            conn.execute("SELECT 1").fetchall()
            assert conn.in_transaction is False
        assert reader.count("conversations") >= 0
        print(f"write refused: {error.value}")


def test_unbound_provider_blocked_then_strict_fails() -> None:
    container = Container(settings=None, limits=Limits())
    container.provide(Key[object]("login_sessions"), lambda _c: object())
    container.build()
    app = FastAPI()
    app.state.container = container
    missing = missing_needs(container, app, ("login_sessions", "session_service"), ("startChatSession",))
    assert [m.owner for m in missing] == ["AEA-40", "AEA-40"]
    with pytest.raises(RuntimeError, match="not bound: get_session_service"):
        provided(app, get_session_service)
    with pytest.raises(pytest.skip.Exception, match="blocked-on AEA-40"):
        stop_blocked(missing, strict=False)
    with pytest.raises(pytest.fail.Exception, match="blocked-on AEA-40"):
        stop_blocked(missing, strict=True)
    collector = StepCollector()
    collector.add_step(
        StepResult(
            "J-1",
            "4 start session",
            "tests/journeys/j1/test_aea_57.py::x",
            "blocked",
            "blocked-on AEA-40: session_service not bound",
            ("AEA-40",),
            0.0,
        )
    )
    rendered = render_record(
        build_record_data(scope="AEA-57", collector=collector, root=REPO_ROOT, command="c")
    )
    blocked_by = next(line for line in rendered.splitlines() if line.startswith("| Blocked by |"))
    assert "AEA-40" in blocked_by and "blocked-on AEA-40" in rendered
    with pytest.raises(KeyError):
        missing_needs(container, app, ("not_a_need",), ())
    assert set(OPERATION_OWNERS) == set(load_contract().operations)
    print(blocked_by)


def _collector() -> StepCollector:
    node = "tests/journeys/j1/test_aea_57.py::test_x"
    collector = StepCollector()
    collector.add_step(StepResult("J-1", "1 signed out", node, "pass", "", (), 0.1))
    collector.add_step(StepResult("J-1", "2 wrong login", node, "fail", "boom", (), 0.1))
    collector.add_step(
        StepResult("J-1", "4 start", node, "blocked", "blocked-on AEA-40: x", ("AEA-40",), 0.0)
    )
    collector.add_test(TestOutcome(node, "passed", 1.0))
    collector.add_test(TestOutcome(node, "skipped", 0.5))
    collector.add_note(
        RunNote("127.0.0.1", 5000, "dev", {"planner": f"openrouter_jev/{JEV_MODEL}"}, "ab" * 32, 3, 0.0, 0)
    )
    return collector


def test_evidence_record_fields(tmp_path: Path) -> None:
    command = "uv run pytest -m journey tests/journeys/j1"
    data = build_record_data(scope="AEA-57", collector=_collector(), root=REPO_ROOT, command=command)
    text = render_record(data)
    positions = [text.index(f"| {name} |") for name in FIELDS]
    assert positions == sorted(positions) and len(FIELDS) == 9
    assert re.match(
        r"^([0-9a-f]{7,40}|uncommitted \(HEAD [0-9a-f]+\)|unknown \(git unavailable\)); agent_version ",
        data.values["Tested revision"],
    )
    env = data.values["Environment"]
    assert "127.0.0.1" in env and "none (API level)" in env and "ScriptedModel" in env and JEV_MODEL in env
    result = data.values["Result"]
    assert ": pass" in result and ": fail: " in result and "blocked-on" in result
    day = date(2026, 10, 21)
    assert maybe_write_record(None, root=tmp_path, collector=_collector(), command=command, day=day) is None
    assert not (tmp_path / "docs").exists()
    written = maybe_write_record("AEA-57", root=tmp_path, collector=_collector(), command=command, day=day)
    assert written == tmp_path / "docs/testing/journeys/2026-10-21-AEA-57.md" and written.exists()
    with pytest.raises(ValueError):
        maybe_write_record("../x", root=tmp_path, collector=_collector(), command=command, day=day)
    print("fields:", ", ".join(FIELDS))


def _bullets(readme: str, heading: str) -> set[str]:
    section = readme.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]
    return {m.group(1) for m in re.finditer(r"^- `(--?[\w-]+|\w+)", section, flags=re.MULTILINE)}


def test_readme_lists_public_fixtures() -> None:
    readme = (SUPPORT / "README.md").read_text()
    assert _bullets(readme, "Public fixtures") == set(plugin.PUBLIC_FIXTURES)
    assert _bullets(readme, "Options") == set(plugin.OPTIONS)
    tree = ast.parse((SUPPORT / "plugin.py").read_text())
    fixtures = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            for deco in node.decorator_list:
                target = deco.func if isinstance(deco, ast.Call) else deco
                if isinstance(target, ast.Attribute) and target.attr == "fixture":
                    fixtures.add(node.name)
    assert set(plugin.PUBLIC_FIXTURES) <= fixtures
    print("listed:", sorted(plugin.PUBLIC_FIXTURES), sorted(plugin.OPTIONS))


def test_journey_file_convention(tmp_path: Path) -> None:
    assert convention_violations(REPO_ROOT) == []
    (tmp_path / "tests/journeys/j3").mkdir(parents=True)
    (tmp_path / "tests/journeys/j11").mkdir(parents=True)
    (tmp_path / "tests/journeys/j3/test_bad.py").write_text("")
    (tmp_path / "tests/journeys/j11/test_aea_99.py").write_text("")
    violations = convention_violations(tmp_path)
    assert len(violations) == 2  # the j11 folder and j3/test_bad.py
    print(violations)


def test_socket_guard_refuses_non_loopback() -> None:
    original = socket.socket.connect
    with socket_guard() as guard:
        with pytest.raises(OSError, match="journey socket guard"):
            socket.create_connection(("192.0.2.1", 9), timeout=0.2)
        assert guard.blocked == [("192.0.2.1", 9)]
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            with socket.create_connection(listener.getsockname(), timeout=1.0):
                pass
    assert socket.socket.connect is original


def test_wall_clock_control_moves_server_clock(journey: JourneyRun, journey_clock: StepClock) -> None:
    assert journey.container.get(WALL_CLOCK) is journey_clock
    real = datetime.now(UTC)
    journey_clock.advance(3600)
    seen = provided(journey.app, get_wall_clock)()
    assert seen.utcoffset() == timedelta(0)
    assert 3599 <= (seen - real).total_seconds() <= 3605
    print(f"offset seen: {(seen - real).total_seconds():.1f} s")


def test_wall_clock_control_expires_session(journey: JourneyRun, journey_clock: StepClock) -> None:
    lifetime = journey.container.limits.web.login_session_lifetime_s
    with journey.step(
        "harness",
        "wall clock expires a session",
        needs=("login_sessions", "demo_clock"),  # a successful login reads the demo clock (AEA-30)
        operations=("login", "getSession"),
    ):
        signed = journey.login()
        journey_clock.advance(lifetime - 1)
        alive = signed.client.call("GET", "/api/session", operation_id="getSession")
        assert alive.status_code == 200
        journey_clock.advance(1)
        gone = signed.client.call("GET", "/api/session", operation_id="getSession")
        body = json.loads(gone.text)
        assert gone.status_code == 401
        assert body["error"]["code"] == "UNAUTHENTICATED" and body["error"]["details"]["reason"] == "expired"
        print(
            f"before: {alive.status_code}; after: {gone.status_code} reason={body['error']['details']['reason']}"
        )


def test_wall_clock_control_leaves_demo_clock(journey: JourneyRun, journey_clock: StepClock) -> None:
    lifetime = journey.container.limits.web.login_session_lifetime_s
    with journey.step(
        "harness",
        "wall clock leaves the demo clock",
        needs=("login_sessions", "demo_service", "demo_clock"),
        operations=("login", "getDemoClock"),
    ):
        first = journey.login()
        before = first.client.call("GET", "/api/demo/clock", operation_id="getDemoClock").json()["now"]
        journey_clock.advance(lifetime)
        second = journey.login()
        after = second.client.call("GET", "/api/demo/clock", operation_id="getDemoClock").json()["now"]
        assert after == before
        print(f"demo clock before={before} after={after}")
