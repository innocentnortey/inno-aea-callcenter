"""Self-checks for the browser harness (AEA-58). No Chrome page is opened here."""

from __future__ import annotations

import re
import uuid
from collections import Counter
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, cast

import pytest
from fastapi import FastAPI

from meridian.config import Settings
from meridian.web.container import ContainerError
from tests.api.openapi_check import load_contract
from tests.journeys.browser import selectors as selectors_module
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
from tests.journeys.browser.pages import DESKTOP, BrowserPage, BrowserRun
from tests.journeys.browser.record import BrowserSession, browser_record_values
from tests.journeys.browser.selectors import (
    CONTRACT_ROWS,
    PARAMETRIC_KEYS,
    PLACEHOLDER,
    SELECTOR_KEYS,
    SELECTORS_REVISION,
    SELECTORS_SOURCE,
    SelectorRow,
    fill_row,
    locate,
    locate_by,
    locate_in,
    missing_selectors,
    placeholder_count,
)
from tests.journeys.browser.server import INDEX_DIR_ENV, browser_environ
from tests.journeys.j1.test_aea_57 import CHAT_NEEDS, TURN_NEEDS
from tests.journeys.support.env import REPO_ROOT, journey_environment
from tests.journeys.support.logtap import tap_logs
from tests.journeys.support.record import FIELDS, build_record_data
from tests.journeys.support.scripted_model import JourneyScript, scripted_overrides
from tests.journeys.support.server import StepClock, launch_server
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


AEA62_KEYS: tuple[str, ...] = (
    "screen.scr2",
    "screen.scr4",
    "screen.scr5",
    "screen.scr6",
    "login.message.expired",
    "chat.source",
    "chat.source.toggle",
    "chat.source.excerpt",
    "chat.block.locate_prompt",
    "chat.block.code_prompt",
    "chat.block.account_card",
    "chat.block.slot_card",
    "chat.block.confirmation",
    "chat.block.handoff",
    "card.locate.name",
    "card.locate.phone",
    "card.locate.submit",
    "card.code.input",
    "card.code.submit",
    "card.slot.window_by_id",
    "card.slot.continue",
    "settled.visit",
    "settled.request",
    "inbox.message.active",
    "inbox.code",
    "shell.role.customer",
    "shell.role.representative",
    "shell.role.supervisor",
    "shell.role.owner",
    "shell.header_name",
    "role.panel",
    "role.panel.wrong_role",
    "role.panel.role_reset",
    "queue.row",
    "queue.row_by_ref",
    "case.root",
    "case.owner",
    "case.promise",
    "case.promise.open",
    "brief.section_by_number",
    "brief.heading",
    "brief.item.tag",
    "case.sources_tab",
    "case.source_by_id",
    "demo.reset",
    "demo.reset_result",
)


@pytest.fixture
def production_build(tmp_path: Path) -> ProductionBuild:
    """Stand-in for the plugin's fixture in this module: a dist with only index.html (no npm, no Chrome)."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>self-check</title>", encoding="utf-8")
    return ProductionBuild(dist, "0" * 64, "self-check stand-in")


@pytest.fixture
def journey_chrome() -> Any:
    """Stand-in for the plugin's fixture in this module: no browser starts; these runs open no page."""
    return cast(Any, object())


class _Target:
    def locator(self, selector: str) -> tuple[str, ...]:
        return ("css", selector)

    def get_by_role(self, role: str, *, name: str | None, exact: bool) -> tuple[str, ...]:
        return ("role", role, str(name), str(exact))

    def get_by_label(self, text: str, *, exact: bool) -> tuple[str, ...]:
        return ("label", text, str(exact))


def _rows(*extra: SelectorRow) -> Any:
    rows = [
        SelectorRow("queue.row_by_ref", "css", '[data-case-ref="{value}"]', None, "self-check"),
        SelectorRow("case.source_by_id", "role", "link", "{value}", "self-check"),
        SelectorRow("brief.section_by_number", "label", "Brief section {value}", None, "self-check"),
        SelectorRow("case.root", "css", "[data-testid=case]", None, "self-check"),
        *extra,
    ]
    return MappingProxyType({r.key: r for r in rows})


def test_selector_keys_cover_aea62() -> None:
    assert len(AEA62_KEYS) == 46
    assert len(set(AEA62_KEYS)) == 46
    assert all(SELECTOR_KEYS.get(k) for k in AEA62_KEYS)
    assert len(SELECTOR_KEYS) == 62
    assert PARAMETRIC_KEYS == {
        "card.slot.window_by_id",
        "queue.row_by_ref",
        "brief.section_by_number",
        "case.source_by_id",
    }
    assert PARAMETRIC_KEYS <= set(SELECTOR_KEYS)
    found = missing_selectors(AEA62_KEYS)
    if not any(k in CONTRACT_ROWS for k in AEA62_KEYS):
        assert len(found) == 46
        assert all(m.owner == "UX session" for m in found)


def test_locate_by_fills_one_placeholder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(selectors_module, "CONTRACT_ROWS", _rows())
    t = cast(Any, _Target())
    got: Any = locate_by(t, "queue.row_by_ref", "MHC-C-0009")
    assert got == ("css", '[data-case-ref="MHC-C-0009"]')
    got = locate_by(t, "case.source_by_id", "src-12")
    assert got == ("role", "link", "src-12", "True")
    got = locate_by(t, "brief.section_by_number", "4")
    assert got == ("label", "Brief section 4", "True")
    got = locate(t, "case.root")
    assert got == ("css", "[data-testid=case]")
    got = locate_in(t, "case.root")
    assert got == ("css", "[data-testid=case]")
    row = SelectorRow("queue.row_by_ref", "css", '[data-case-ref="{value}"]', None, "self-check")
    filled = fill_row(row, "56")
    assert PLACEHOLDER not in filled.value
    assert PLACEHOLDER in row.value


def test_locate_by_refuses_misuse(monkeypatch: pytest.MonkeyPatch) -> None:
    two = SelectorRow(
        "card.slot.window_by_id", "css", "[data-a='{value}'][data-b='{value}']", None, "self-check"
    )
    monkeypatch.setattr(selectors_module, "CONTRACT_ROWS", _rows(two))
    t = cast(Any, _Target())
    with pytest.raises(ValueError):
        locate(t, "queue.row_by_ref")
    with pytest.raises(ValueError):
        locate_by(t, "case.root", "x")
    for bad in ('a"b', "", "a b", "x" * 65):
        with pytest.raises(ValueError):
            locate_by(t, "queue.row_by_ref", bad)
    with pytest.raises(ValueError):
        locate_by(t, "card.slot.window_by_id", "56")
    with pytest.raises(ValueError):
        fill_row(SelectorRow("queue.row_by_ref", "css", "[data-case-ref]", None, "self-check"), "1")
    with pytest.raises(KeyError):
        locate_by(t, "no.such.key", "1")


def test_contract_rows_parametric_placeholders() -> None:
    for key, row in CONTRACT_ROWS.items():
        assert placeholder_count(row) == (1 if key in PARAMETRIC_KEYS else 0), key


class _Shot:
    def __init__(self) -> None:
        self.paths: list[str] = []

    def screenshot(self, *, path: str) -> None:
        self.paths.append(path)
        Path(path).write_bytes(b"png")


def test_screenshot_element_shoots_only_the_target(tmp_path: Path) -> None:
    shot = _Shot()
    brun = BrowserRun(
        run=cast(Any, None),
        browser=cast(Any, None),
        channel="chrome",
        build=cast(Any, None),
        shots_dir=tmp_path / "shots",
        session=BrowserSession(),
        test_name="t",
    )
    bp = BrowserPage(DESKTOP, cast(Any, None), cast(Any, None), cast(Any, None))
    path = brun.screenshot_element(bp, cast(Any, shot), "account-card")
    assert path == tmp_path / "shots" / "t-chrome-desktop-account-card.png"
    assert shot.paths == [str(path)]
    assert path.is_file()
    assert brun.session.screenshots == [path]
    with pytest.raises(ValueError):
        brun.screenshot_element(bp, cast(Any, shot), "Account Card")
    assert len(shot.paths) == 1
    assert len(brun.session.screenshots) == 1


def test_browser_journey_factory_run_options(
    request: pytest.FixtureRequest,
    browser_journey_factory: Any,
    production_build: ProductionBuild,
    tmp_path: Path,
) -> None:
    idx = tmp_path / "idx"
    idx.mkdir()
    script = JourneyScript()
    seen: list[tuple[Any, ...]] = []

    def builder(settings: Settings, sc: JourneyScript, clock: Callable[[], datetime] | None) -> Any:
        seen.append((settings, sc, clock))
        return scripted_overrides(settings, sc, wall_clock=clock)

    with browser_journey_factory(
        index_dir=idx, with_clock=True, script=script, overrides_for=builder
    ) as brun:
        assert brun.run.script is script
        assert isinstance(brun.run.clock, StepClock)
        assert len(seen) == 1
        assert seen[0][0] is brun.run.settings
        assert seen[0][1] is script
        assert seen[0][2] is brun.run.clock
        assert brun.run.settings.index_dir == idx
        assert brun.run.settings.require_frontend is True
        assert brun.run.settings.web_dist_dir == production_build.dist_dir
        assert brun.build is production_build
        assert brun.pages == []
        assert brun.test_name == "test_browser_journey_factory_run_options"
        if not request.config.getoption("--journey-record"):
            assert brun.shots_dir == tmp_path / "shots"


def test_browser_journey_factory_defaults_match_browser_journey(
    browser_journey_factory: Any, tmp_path: Path
) -> None:
    with browser_journey_factory() as brun:
        assert type(brun.run.script) is JourneyScript
        assert brun.run.clock is None
        assert brun.run.settings.index_dir != tmp_path / "idx"
        assert brun.run.models


def test_index_dir_env_is_the_settings_name(tmp_path: Path) -> None:
    assert INDEX_DIR_ENV == "MERIDIAN_INDEX_DIR"
    with journey_environment() as base:
        environ = browser_environ(base.root, tmp_path / "dist")
        environ[INDEX_DIR_ENV] = str(tmp_path / "idx")
        assert Settings.from_env(environ).index_dir == tmp_path / "idx"
