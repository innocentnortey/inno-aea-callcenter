"""AEA-47 test support: a DemoService.advance_clock double (cases.md §6, MC-13) and an app builder that runs AEA-23's
register_web plus AEA-47's register_staff_clock. Not a conftest. Synthetic values only (OpenAPI examples)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest
from fastapi import FastAPI

import meridian.web.app as app_module
from meridian.config import Settings
from meridian.domain.staff import DemoRole, LoginSession, StaffActor
from meridian.policy.limits import Limits
from meridian.web.app import create_app
from meridian.web.container import Container, register_staff_clock, register_web
from meridian.web.deps import get_demo_service, get_heartbeat, get_login_sessions, get_staff_access
from tests.api.web_shell_support import FakeHeartbeat, FakeSessionStore, cookie_header
from tests.fakes.clock import CHICAGO

ADVANCE_PATH = "/api/demo/clock"


@dataclass(frozen=True)
class ClockAdvancedStub:
    """= ClockAdvanced's three fields (AEA-30 plan 4.3)."""

    now: datetime
    label: str
    became_overdue: int


@dataclass(frozen=True)
class ClockAdvancedWithDateLabel:
    """The pre-R-W-17 shape, to prove the route drops extra attributes."""

    now: datetime
    label: str
    became_overdue: int
    date_label: str


EXAMPLE_START = datetime(2026, 10, 16, 14, 20, tzinfo=CHICAGO)  # "Fri Oct 16, 2026 · 2:20 pm"
NEXT_MORNING = ClockAdvancedStub(
    datetime(2026, 10, 19, 7, 0, tzinfo=CHICAGO), "Mon Oct 19, 2026 · 7:00 am", 1
)
PLUS_1H = ClockAdvancedStub(datetime(2026, 10, 16, 15, 20, tzinfo=CHICAGO), "Fri Oct 16, 2026 · 3:20 pm", 0)
PLUS_4H = ClockAdvancedStub(datetime(2026, 10, 16, 18, 20, tzinfo=CHICAGO), "Fri Oct 16, 2026 · 6:20 pm", 0)


def default_results() -> dict[str, object]:
    return {"plus_1h": PLUS_1H, "plus_4h": PLUS_4H, "next_business_morning": NEXT_MORNING}


@dataclass(frozen=True)
class AdvanceCall:
    step: str
    actor: StaffActor
    request_id: str


class FakeClockAdvancer:
    """advance_clock(step, *, actor, request_id) double. Records every call; returns results[step] or raises."""

    def __init__(
        self, results: Mapping[str, object] | None = None, *, raises: Exception | None = None
    ) -> None:
        self.results: dict[str, object] = dict(results) if results is not None else default_results()
        self.raises = raises
        self.calls: list[AdvanceCall] = []

    def advance_clock(self, step: str, *, actor: StaffActor, request_id: str) -> object:
        self.calls.append(AdvanceCall(step=step, actor=actor, request_id=request_id))
        if self.raises is not None:
            raise self.raises
        return self.results[step]


@dataclass
class ClockHarness:
    app: FastAPI
    settings: Settings
    store: FakeSessionStore
    demo: Any  # FakeClockAdvancer or any object with advance_clock (the J-6 double)


def clock_app(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    *,
    demo: Any = None,
    store: FakeSessionStore | None = None,
) -> ClockHarness:
    """create_app over a container running register_web and register_staff_clock; doubles as dependency overrides."""

    def build(app: FastAPI, settings: Any, *, overrides: Any = None) -> Container:
        limits = Limits()
        container = Container(settings=settings, limits=limits)
        register_web(container, app, settings=settings, limits=limits)
        register_staff_clock(container, app, settings=settings, limits=limits)
        container.build()
        return container

    monkeypatch.setattr(app_module, "build_container", build)
    app = create_app(settings)
    the_store = store if store is not None else FakeSessionStore()
    the_demo = demo if demo is not None else FakeClockAdvancer()
    app.dependency_overrides[get_login_sessions] = lambda: the_store
    app.dependency_overrides[get_staff_access] = lambda: the_store
    app.dependency_overrides[get_heartbeat] = lambda: FakeHeartbeat()
    app.dependency_overrides[get_demo_service] = lambda: the_demo
    return ClockHarness(app=app, settings=settings, store=the_store, demo=the_demo)


def signed_in(h: ClockHarness, role: DemoRole) -> tuple[dict[str, str], LoginSession]:
    token = h.store.issue(role)
    return cookie_header(token), h.store.session_of(token)
