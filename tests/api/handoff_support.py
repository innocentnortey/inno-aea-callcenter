"""AEA-42 app harness: the real `create_app`, the real AEA-23 middleware and the real `register_person_request` hunk,
over a temp SQLite copy with recording doubles for HandoffService, ReplyComposer, CaseService and DemoService.

Synthetic data only. No `.env`, no model, no socket.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI

import meridian.web.app as app_module
from meridian.domain.common import ThreadId
from meridian.domain.staff import DemoRole
from meridian.domain.turn import ExportStatus
from meridian.policy.limits import Limits
from meridian.web.app import ContainerOverrides, create_app
from meridian.web.container import Container, Key, register_person_request, register_web
from meridian.web.deps import (
    CASE_SERVICE,
    DEMO_SERVICE,
    HANDOFF_SERVICE,
    REPLY_COMPOSER,
    UOW_FACTORY,
    get_heartbeat,
    get_login_sessions,
    get_rate_limiter,
    get_staff_access,
)
from meridian.web.middleware import RateLimiter
from tests.api.web_shell_support import (
    FakeHeartbeat,
    FakeSessionStore,
    MutableClock,
    make_settings,
    suppress_container_starters,
)
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import TempStore
from tests.services.person_request_support import (
    WALL_T0,
    FakeDemoService,
    RecordingCaseService,
    RecordingComposer,
    RecordingHandoffService,
    open_thread,
)


@dataclass
class HandoffHarness:
    app: FastAPI
    store: FakeSessionStore
    db: TempStore
    handoff: RecordingHandoffService
    composer: RecordingComposer
    cases: RecordingCaseService
    demo: FakeDemoService
    trace: Any
    wall: MutableClock
    limiter: RateLimiter | None


def handoff_app(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    db: TempStore,
    *,
    presence: Any = "nobody_online",
    handoff_fails: bool = False,
    trace: Any = None,
    limiter: RateLimiter | None = None,
) -> HandoffHarness:
    from tests.fakes.trace import InMemoryTraceSink

    suppress_container_starters(monkeypatch)
    sink = trace if trace is not None else InMemoryTraceSink(status=_status())
    clock = FixedClock()
    handoff = RecordingHandoffService(db.uow, presence=presence, fail=handoff_fails)
    composer = RecordingComposer()
    cases = RecordingCaseService(db.uow)
    demo = FakeDemoService(clock)
    wall = MutableClock(WALL_T0)
    settings = make_settings(tmp_path)

    def build(app: FastAPI, settings_: Any, *, overrides: Any = None) -> Container:
        limits = Limits()
        container = Container(settings=settings_, limits=limits)
        register_web(container, app, settings=settings_, limits=limits)
        container.provide(UOW_FACTORY, lambda _c: db.uow)
        container.provide(Key[Any]("trace"), lambda _c: sink)
        container.provide(Key[Any]("demo_clock"), lambda _c: clock)
        container.provide(HANDOFF_SERVICE, lambda _c: handoff)
        container.provide(REPLY_COMPOSER, lambda _c: composer)
        container.provide(CASE_SERVICE, lambda _c: cases)
        container.provide(DEMO_SERVICE, lambda _c: demo)
        register_person_request(container, app, settings=settings_, limits=limits)
        container.build()
        return container

    monkeypatch.setattr(app_module, "build_container", build)
    app = create_app(settings, overrides=ContainerOverrides(wall_clock=wall))
    store = FakeSessionStore()
    app.dependency_overrides[get_login_sessions] = lambda: store
    app.dependency_overrides[get_staff_access] = lambda: store
    app.dependency_overrides[get_heartbeat] = lambda: FakeHeartbeat()
    if limiter is not None:
        app.dependency_overrides[get_rate_limiter] = lambda: limiter
    return HandoffHarness(app, store, db, handoff, composer, cases, demo, sink, wall, limiter)


def _status() -> ExportStatus:
    return "sent"


def customer_token(h: HandoffHarness, role: DemoRole = DemoRole.CUSTOMER) -> str:
    return h.store.issue(role, now=WALL_T0)


def session_id_of(h: HandoffHarness, token: str) -> str:
    return str(h.store.session_of(token).session_id)


def thread_for(h: HandoffHarness, token: str) -> ThreadId:
    """A live conversation owned by this login session."""
    return open_thread(h.db, demo_session=session_id_of(h, token))


HANDOFF_PATH = "/api/chat/sessions/{thread_id}/handoff"
FOLLOW_UP_PATH = "/api/chat/sessions/{thread_id}/follow-up"


def request_example(path: str, method: str, name: str) -> dict[str, Any]:
    """A named request-body example from the OpenAPI (read only)."""
    from tests.api.openapi_check import load_document

    document = load_document()
    examples = document["paths"][path][method]["requestBody"]["content"]["application/json"]["examples"]
    value: dict[str, Any] = dict(examples[name]["value"])
    return value
