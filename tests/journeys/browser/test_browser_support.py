"""Self-checks for the browser harness (AEA-58). No Chrome page is opened here."""

from __future__ import annotations

import re
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI

from meridian.config import Settings
from meridian.web.container import ContainerError
from tests.api.openapi_check import load_contract
from tests.journeys.browser.build import (
    BrowserPrerequisiteError,
    ProductionBuild,
    check_production_build,
    launch_chrome,
)
from tests.journeys.browser.network import (
    UNBOUND_500_NEEDS,
    ApiExchange,
    NetworkLog,
    SeenRequest,
    ValidationSummary,
    operation_for,
    teardown_failures,
    validate_exchanges,
)
from tests.journeys.browser.record import BrowserSession, browser_record_values
from tests.journeys.browser.selectors import (
    CONTRACT_ROWS,
    SELECTOR_KEYS,
    SELECTORS_REVISION,
    SELECTORS_SOURCE,
    missing_selectors,
)
from tests.journeys.browser.server import browser_environ
from tests.journeys.j1.test_aea_57 import CHAT_NEEDS, TURN_NEEDS
from tests.journeys.support.env import REPO_ROOT, journey_environment
from tests.journeys.support.logtap import tap_logs
from tests.journeys.support.record import FIELDS, build_record_data
from tests.journeys.support.server import launch_server
from tests.journeys.support.steps import NEED_OWNERS, RunNote, StepCollector, StepResult, blocked_message

pytestmark = pytest.mark.journey

pytest_plugins = ("tests.journeys.browser.plugin",)

BROWSER_DIR = Path(__file__).parent


def _exchange(op: str, status: int, body: str, *, request_id: str | None = None) -> ApiExchange:
    rid = request_id or str(uuid.uuid4())
    return ApiExchange(
        index=0,
        method="GET",
        url="http://127.0.0.1:1/api/x",
        path="/api/x",
        operation_id=op,
        status=status,
        headers=[("content-type", "application/json"), ("x-request-id", rid)],
        request_body=None,
        body=body.encode(),
    )


def _app_with(*operation_ids: str) -> FastAPI:
    app = FastAPI()
    for op in operation_ids:
        app.add_api_route(f"/api/{op}", lambda: None, methods=["GET"], operation_id=op)
    return app


class _Container:
    def __init__(self, absent: set[str]) -> None:
        self.absent = absent

    def get(self, key: Any) -> object:
        if key.name in self.absent:
            raise ContainerError(f"not provided: {key.name}")
        return object()


def _validate(app: FastAPI, container: Any, *exchanges: ApiExchange) -> ValidationSummary:
    return validate_exchanges(exchanges, container=container, app=app, contract=load_contract())


def test_operation_resolver_covers_every_operation() -> None:
    contract = load_contract()
    for spec in contract.operations.values():
        path = re.sub(r"\{([^}]*)\}", r"\1_1", spec.path_template)
        assert operation_for(spec.method.upper(), path, contract) == spec.operation_id
    assert operation_for("GET", "/api/nope", contract) is None
    assert operation_for("POST", "/api/chat/sessions/t1/turns", contract) == "submitTurn"


def test_validation_rejects_undocumented_status() -> None:
    app = _app_with("getSession")
    container = cast(Any, object())
    bad = _validate(app, container, _exchange("getSession", 418, '{"x": 1}'))
    assert len(bad.failures) == 1
    assert "getSession" in bad.failures[0]
    assert "418" in bad.failures[0]
    rid = str(uuid.uuid4())
    body = (
        '{"error": {"code": "UNAUTHENTICATED", "field": null, "constraint": null, "details": {"reason": "none"}}, '
        f'"request_id": "{rid}"}}'
    )
    good = _validate(app, container, _exchange("getSession", 401, body, request_id=rid))
    assert good.failures == []
    assert good.validated["getSession"] == 1


def test_unrouted_operations_counted_not_validated() -> None:
    summary = _validate(
        FastAPI(), cast(Any, object()), _exchange("startChatSession", 404, '{"detail": "Not Found"}')
    )
    assert summary.unrouted["startChatSession"] == 1
    assert summary.unrouted_owners["startChatSession"] == "AEA-40"
    assert summary.failures == []


def test_unbound_service_500_counted_not_validated() -> None:
    body = f'{{"request_id": "{uuid.uuid4()}"}}'
    summary = _validate(
        _app_with("startChatSession"),
        _Container({"reply_composer"}),
        _exchange("startChatSession", 500, body),
    )
    assert summary.unbound["startChatSession"] == 1
    assert summary.unbound_owners["startChatSession"] == "AEA-51"
    assert not summary.validated
    assert summary.failures == []


def test_mounted_500_with_bound_needs_fails() -> None:
    body = f'{{"request_id": "{uuid.uuid4()}"}}'
    bound = _validate(
        _app_with("startChatSession"), _Container(set()), _exchange("startChatSession", 500, body)
    )
    assert len(bound.failures) == 1
    assert "startChatSession" in bound.failures[0]
    assert "500" in bound.failures[0]
    other = _validate(
        _app_with("getSession"), _Container({"reply_composer"}), _exchange("getSession", 500, body)
    )
    assert len(other.failures) == 1


def test_strict_fails_on_blocked_exchanges() -> None:
    summary = ValidationSummary(
        unrouted=Counter({"startChatSession": 1}),
        unrouted_owners={"startChatSession": "AEA-40"},
        unbound=Counter({"submitTurn": 1}),
        unbound_owners={"submitTurn": "AEA-51"},
    )
    assert teardown_failures(summary, strict=False) == []
    strict = teardown_failures(summary, strict=True)
    assert len(strict) == 2
    assert any("blocked-on AEA-40" in line for line in strict)
    assert any("blocked-on AEA-51" in line for line in strict)
    assert all("[--journeys-strict]" in line for line in strict)


def test_unbound_needs_match_aea57_scripts() -> None:
    assert UNBOUND_500_NEEDS["startChatSession"] == CHAT_NEEDS
    assert UNBOUND_500_NEEDS["getChatThread"] == CHAT_NEEDS
    assert UNBOUND_500_NEEDS["submitTurn"] == TURN_NEEDS
    assert set(UNBOUND_500_NEEDS) == {"startChatSession", "getChatThread", "submitTurn"}
    assert all(name in NEED_OWNERS for needs in UNBOUND_500_NEEDS.values() for name in needs)


def test_selector_rows_cite_contract() -> None:
    for key, row in CONTRACT_ROWS.items():
        assert key in SELECTOR_KEYS
        assert row.key == key
        assert row.row
    if CONTRACT_ROWS:
        assert SELECTORS_REVISION is not None
        assert re.fullmatch(r"[0-9a-f]{7,12}", SELECTORS_REVISION)
        assert (REPO_ROOT / SELECTORS_SOURCE).exists()
    if SELECTORS_REVISION is None:
        assert not CONTRACT_ROWS


def test_no_selector_strings_outside_module() -> None:
    pattern = re.compile("locator" + r"\(|get_" + "by_")
    root = REPO_ROOT / "tests" / "journeys"
    offenders = []
    for path in sorted(root.rglob("*.py")):
        if path == BROWSER_DIR / "selectors.py" or path == Path(__file__):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{number}")
    assert offenders == []


def test_missing_selector_reports_ux_owner() -> None:
    found = missing_selectors(("login.message.rate_limited",))
    assert (
        [m.owner for m in found] == ["UX session"]
        if "login.message.rate_limited" not in CONTRACT_ROWS
        else True
    )
    if found:
        assert blocked_message(found).startswith("blocked-on UX session")
    with pytest.raises(KeyError):
        missing_selectors(("no.such.key",))


def test_missing_build_message_names_build_command(tmp_path: Path) -> None:
    with pytest.raises(BrowserPrerequisiteError) as info:
        check_production_build(tmp_path)
    assert "npm --prefix apps/web run build" in str(info.value)
    assert "MERIDIAN_REQUIRE_FRONTEND" in str(info.value)


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_missing_build_refuses_server_start(tmp_path: Path) -> None:
    with tap_logs() as logs, journey_environment() as base:
        settings = Settings.from_env(browser_environ(base.root, tmp_path / "empty"))
        with pytest.raises(RuntimeError, match="stopped during start-up"):
            with launch_server(settings, overrides=None):
                pass
        assert "MERIDIAN_REQUIRE_FRONTEND" in logs.all_text()


def test_missing_chrome_channel_errors_with_flag_name() -> None:
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    try:
        with pytest.raises(BrowserPrerequisiteError) as info:
            launch_chrome(pw, {"channel": "msedge-canary"})
    finally:
        pw.stop()
    assert "--browser-channel msedge-canary" in str(info.value)


def test_browser_record_fields() -> None:
    nodeid = "tests/journeys/j1/test_aea_58.py::t"
    collector = StepCollector()
    collector.add_step(StepResult("J-1", "1a", nodeid, "pass", "", (), 0.1))
    collector.add_note(RunNote("127.0.0.1", 50000, "dev", {"planner": "scripted/x"}, "abc123", 0, 0.0, 0))
    session = BrowserSession(
        build=ProductionBuild(Path("/x/apps/web/dist"), "deadbeef", "dist is clean: no dev-layer markers"),
        channel="chrome",
        chrome_version="1.0",
    )
    base = build_record_data(scope="AEA-58", collector=collector, root=REPO_ROOT, command="cmd")
    values = browser_record_values(base, session, collector=collector, root=REPO_ROOT)
    assert all(name in values and values[name] for name in FIELDS)
    env = values["Environment"]
    assert "MERIDIAN_REQUIRE_FRONTEND=true" in env
    assert "deadbeef" in env
    assert "channel chrome" in env
    assert "version 1.0" in env
    assert "none (API level)" not in env


def test_no_held_out_paths_in_browser_files() -> None:
    needle = "held" + "out"
    files = [*BROWSER_DIR.glob("*.py"), *BROWSER_DIR.glob("*.md")]
    files += [REPO_ROOT / "tests/journeys/j1/test_aea_58.py", REPO_ROOT / "tests/journeys/j9/test_aea_58.py"]
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        assert needle not in text, path.name
        assert "key" + "_dir" not in text, path.name


def test_dev_params_and_origins_helpers() -> None:
    net = NetworkLog(load_contract())
    net.requests = [
        SeenRequest(0, "GET", "data:text/plain,hi", "other", False),
        SeenRequest(1, "GET", "http://127.0.0.1:9/?signedin=1&role=owner", "document", True),
        SeenRequest(2, "GET", "http://127.0.0.1:9/login?scenario=x", "document", True),
        SeenRequest(3, "GET", "http://127.0.0.1:9/assets/a.js", "script", False),
    ]
    assert net.origins() == {"http://127.0.0.1:9"}
    assert net.dev_param_hits(allowed_urls=("/?signedin=1&role=owner",)) == ["/login?scenario=x"]
