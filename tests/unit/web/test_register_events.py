"""AEA-41 (PA-6): register_events includes the CON-3 route once and provides nothing."""

from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI

from meridian.policy.limits import Limits
from meridian.web.container import Container, register_events
from meridian.web.routes.events import EVENTS_PATH
from tests.api.web_shell_support import effective_routes


def test_register_events_includes_the_route_once() -> None:
    """invariant (PA-6): two calls leave one route and no provider."""
    app = FastAPI()
    container = Container(settings=SimpleNamespace(), limits=Limits())
    register_events(container, app, settings=SimpleNamespace(), limits=Limits())
    register_events(container, app, settings=SimpleNamespace(), limits=Limits())
    container.build()
    routes = [r for r in effective_routes(app) if r.path == EVENTS_PATH]
    assert len(routes) == 1
    assert routes[0].methods == frozenset({"GET"})
    assert routes[0].operation_id == "streamChatEvents"
    assert not container._factories
    doc = register_events.__doc__ or ""
    assert "AEA-41" in doc and "No-op until" not in doc
