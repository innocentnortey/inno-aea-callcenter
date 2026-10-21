"""AEA-43 plan-added test: register_demo_routes includes the demo router once, and only on a real web shell."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from meridian.policy.limits import Limits
from meridian.web.app import create_app
from meridian.web.container import Container, register_demo_routes
from tests.api.web_shell_support import effective_routes, make_settings

DEMO_ROUTES = {
    ("GET", "/api/demo/inbox", "listDemoInbox"),
    ("GET", "/api/demo/staffing", "getStaffing"),
    ("PUT", "/api/demo/staffing", "setStaffing"),
    ("GET", "/api/demo/clock", "getDemoClock"),
    ("POST", "/api/demo/reset", "resetDemo"),
}


def _demo_routes(app: FastAPI) -> list[tuple[str, str, str | None]]:
    return [
        (method, route.path, route.operation_id)
        for route in effective_routes(app)
        if route.path.startswith("/api/demo/")
        for method in sorted(route.methods)
    ]


def test_register_demo_routes_includes_router_once(tmp_path: Path) -> None:
    """invariant (plan-added): nothing on a bare app; exactly the five routes on a web app; a second call adds none."""
    settings = make_settings(tmp_path)
    limits = Limits()
    bare = FastAPI()
    register_demo_routes(Container(settings=settings, limits=limits), bare, settings=settings, limits=limits)
    assert _demo_routes(bare) == []

    app = create_app(settings)
    assert _demo_routes(app) == []  # create_app alone does not include them; the container hunk does
    register_demo_routes(Container(settings=settings, limits=limits), app, settings=settings, limits=limits)
    first = _demo_routes(app)
    assert set(first) == DEMO_ROUTES
    assert len(first) == len(DEMO_ROUTES)
    register_demo_routes(Container(settings=settings, limits=limits), app, settings=settings, limits=limits)
    assert sorted(_demo_routes(app), key=str) == sorted(first, key=str)
