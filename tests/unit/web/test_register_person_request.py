"""AEA-42 PA-2: the register_person_request hunk binds the service, tolerates unbound siblings, includes routes once."""

from __future__ import annotations

import types
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI

from meridian.policy.limits import Limits
from meridian.services.person_request import PersonRequestService
from meridian.web.container import Container, Key, register_person_request
from meridian.web.deps import PERSON_REQUESTS
from meridian.web.middleware import PublicPaths, WebShellState
from tests.api.web_shell_support import effective_routes, make_settings
from tests.fakes.clock import FixedClock
from tests.fakes.trace import InMemoryTraceSink


def _wall() -> datetime:
    return datetime(2026, 10, 21, tzinfo=UTC)


def _app(tmp_path: Any) -> FastAPI:
    app = FastAPI()
    app.state.web_shell = WebShellState(
        settings=make_settings(tmp_path), wall_clock=_wall, public_paths=PublicPaths()
    )
    return app


def _handoff_paths(app: FastAPI) -> list[str]:
    return [r.path for r in effective_routes(app) if r.path.endswith(("/handoff", "/follow-up"))]


def test_register_binds_service_and_routes(tmp_path: Any) -> None:
    """All dependency keys provided: a real PersonRequestService, routes included once even if run twice."""
    limits = Limits()
    app = _app(tmp_path)
    c = Container(settings=types.SimpleNamespace(), limits=limits)
    for name, obj in (
        ("uow_factory", object()),
        ("handoff_service", object()),
        ("reply_composer", object()),
        ("trace", InMemoryTraceSink()),
        ("demo_clock", FixedClock()),
        ("wall_clock", _wall),
    ):
        c.provide(Key[Any](name), lambda _c, o=obj: o)  # type: ignore[misc]
    register_person_request(c, app, settings=c.settings, limits=limits)
    c.build()
    service = c.get(PERSON_REQUESTS)
    assert isinstance(service, PersonRequestService)
    assert service is c.get(PERSON_REQUESTS)
    assert sorted(_handoff_paths(app)) == [
        "/api/chat/sessions/{thread_id}/follow-up",
        "/api/chat/sessions/{thread_id}/handoff",
    ]
    c2 = Container(settings=types.SimpleNamespace(), limits=limits)
    register_person_request(c2, app, settings=c2.settings, limits=limits)
    assert len(_handoff_paths(app)) == 2  # not included a second time
    doc = register_person_request.__doc__ or ""
    assert "AEA-42" in doc and "No-op until" not in doc


def test_register_unbound_raises_at_call(tmp_path: Any) -> None:
    """A missing sibling key: the build still succeeds; calling request() names what is missing."""
    limits = Limits()
    app = _app(tmp_path)
    c = Container(settings=types.SimpleNamespace(), limits=limits)
    c.provide(Key[Any]("uow_factory"), lambda _c: object())
    register_person_request(c, app, settings=c.settings, limits=limits)
    c.build()
    bound = c.get(PERSON_REQUESTS)
    with pytest.raises(RuntimeError, match=r"not bound: .*handoff_service.*reply_composer"):
        bound.request(object())


def test_register_ignores_app_without_web_shell() -> None:
    """An app create_app did not build gets no provider and no routes."""
    limits = Limits()
    app = FastAPI()
    c = Container(settings=types.SimpleNamespace(), limits=limits)
    register_person_request(c, app, settings=c.settings, limits=limits)
    c.build()
    assert _handoff_paths(app) == []
    with pytest.raises(Exception, match="not provided"):
        c.get(PERSON_REQUESTS)
