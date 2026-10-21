"""AEA-48 router and source checks: three GETs, one registration, no storage and no clock in the route files."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute

import meridian.web.routes.reads as routes_module
import meridian.web.schemas.reads as schemas_module
from meridian.config import Settings
from meridian.policy.limits import Limits
from meridian.web.app import create_app
from meridian.web.container import Container, register_reads
from meridian.web.routes.reads import (
    LATEST_EVAL_PATH,
    MONITORING_PATH,
    OWNER_METRICS_PATH,
    build_router,
)
from tests.api.reads_support import reads_app
from tests.api.web_shell_support import effective_routes, make_client, make_settings

ALLOWED_IMPORTS = {
    "__future__", "datetime", "logging", "collections.abc", "typing", "fastapi", "fastapi.responses",
    "pydantic", "pydantic_core", "meridian.domain.staff", "meridian.web.deps", "meridian.web.errors",
    "meridian.web.middleware", "meridian.web.schemas.reads",
}  # fmt: skip


def test_router_declares_three_gets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant: exactly the three GETs with their operation ids; only getOwnerMetrics has a role dependency."""
    routes = build_router().routes
    assert len(routes) == 3
    assert all(isinstance(r, APIRoute) for r in routes)
    api_routes = [r for r in routes if isinstance(r, APIRoute)]
    assert {(r.path, frozenset(r.methods or ()), r.operation_id) for r in api_routes} == {
        (OWNER_METRICS_PATH, frozenset({"GET"}), "getOwnerMetrics"),
        (MONITORING_PATH, frozenset({"GET"}), "getMonitoring"),
        (LATEST_EVAL_PATH, frozenset({"GET"}), "getLatestEval"),
    }
    for r in api_routes:
        assert len(r.dependencies) == (1 if r.path == OWNER_METRICS_PATH else 0)
    h = reads_app(monkeypatch, make_settings(tmp_path))
    with make_client(h.app):
        paths = [i.path for i in effective_routes(h.app)]
    for path in (OWNER_METRICS_PATH, MONITORING_PATH, LATEST_EVAL_PATH):
        assert paths.count(path) == 1


def _reads_paths(app: FastAPI) -> list[str]:
    wanted = {OWNER_METRICS_PATH, MONITORING_PATH, LATEST_EVAL_PATH}
    return [i.path for i in effective_routes(app) if i.path in wanted]


def test_register_reads_includes_router_once(tmp_path: Path) -> None:
    """invariant: nothing on a bare app; one route per path after two calls on a web-shell app."""
    s: Settings = make_settings(tmp_path)
    bare = FastAPI()
    register_reads(Container(settings=s, limits=Limits()), bare, settings=s, limits=Limits())
    assert _reads_paths(bare) == []
    app = create_app(s)
    for _ in range(2):
        register_reads(Container(settings=s, limits=Limits()), app, settings=s, limits=Limits())
    assert sorted(_reads_paths(app)) == sorted([OWNER_METRICS_PATH, MONITORING_PATH, LATEST_EVAL_PATH])
    assert app.state.reads_routes_included is True


def test_reads_sources_touch_no_storage_or_clock() -> None:
    """invariant (AC-2): the route and schema files import no storage or service and read no clock."""
    for module in (routes_module, schemas_module):
        text = Path(module.__file__ or "").read_text("utf-8")
        assert re.search(r"uow|repos_|sqlite|UnitOfWork|datetime\.now|time\.time", text) is None
        names: set[str] = set()
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Import):
                names |= {a.name for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        assert names <= ALLOWED_IMPORTS, names - ALLOWED_IMPORTS
