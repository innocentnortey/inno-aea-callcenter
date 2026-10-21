"""AEA-43 test support: doubles for IdentityService (AEA-27), DemoService (AEA-30) and ResetService (AEA-31), honouring
DO-4 section 14, cases.md sections 6-7 and graph-tools section 5, and an app builder that runs AEA-23's register_web
plus AEA-43's register_demo_routes. Not a conftest. Everything is synthetic and built at run time; codes come from
new_digits(), so no file holds a six-digit literal.

Frozen with the AEA-43 tests (security ticket): the implementer must not edit this file.
"""

from __future__ import annotations

import secrets
import string
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from pydantic import SecretStr

import meridian.web.app as app_module
from meridian.config import Settings
from meridian.domain.identity import InboxMessage
from meridian.domain.staff import DemoRole, LoginSession
from meridian.policy.limits import Limits
from meridian.services.reset_gate import ResetGate
from meridian.web.app import ContainerOverrides, create_app
from meridian.web.container import Container, Key, register_demo_routes, register_web
from meridian.web.deps import (
    get_demo_service,
    get_heartbeat,
    get_identity_service,
    get_login_sessions,
    get_rate_limiter,
    get_reset_service,
    get_staff_access,
)
from meridian.web.middleware import RateLimiter
from tests.api.web_shell_support import FakeHeartbeat, FakeSessionStore, MutableClock, cookie_header
from tests.fakes.clock import WORKED_PAIRS_NOW
from tests.fakes.trace import InMemoryTraceSink

DEMO_START = WORKED_PAIRS_NOW  # 2026-10-16 10:00 America/Chicago (cases.md section 1.1)
START_LABEL = "Fri Oct 16, 2026 · 10:00 am"  # format_clock(DEMO_START) (cases.md section 6)
START_DATE_LABEL = "Fri Oct 16, 2026 (demo date)"
WALL_START = datetime(2026, 10, 21, 15, 0, tzinfo=UTC)  # a wall time far from the demo clock
CODE_GONE = "·" * 6
OFF_LABEL = "Nobody online"
ON_LABEL = "Simulated staff on shift (demo)"
ON_BANNER = "Simulated staffing (demo). No Meridian employee is online."


def new_digits() -> str:
    """Six digits generated per call; never a literal."""
    return "".join(secrets.choice(string.digits) for _ in range(6))


@dataclass(frozen=True)
class ClockViewStub:
    now: datetime
    label: str
    date_label: str


START_CLOCK = ClockViewStub(DEMO_START, START_LABEL, START_DATE_LABEL)


@dataclass(frozen=True)
class StaffingViewStub:
    mode: str
    label: str
    banner: str | None


OFF = StaffingViewStub("nobody_online", OFF_LABEL, None)
ON = StaffingViewStub("simulated_on_shift", ON_LABEL, ON_BANNER)


@dataclass(frozen=True)
class StaffingChangeStub:
    mode: str
    label: str
    converted_cases: int


@dataclass(frozen=True)
class ResetDoneStub:
    open_chats_ended: int
    roles_reset: int
    clock: ClockViewStub
    ok: bool = True


@dataclass(frozen=True)
class ResetFailedStub:
    code: str = "RESET_FAILED"


def inbox_message(
    *,
    digits: str | None,
    status: str = "active",
    msg_id: str = "msg-1",
    at: datetime = DEMO_START,
    to_masked: str = "···02",
) -> InboxMessage:
    return InboxMessage.model_validate(
        {
            "id": msg_id,
            "at": at,
            "to_masked": to_masked,
            "code": SecretStr(digits) if digits is not None else None,
            "status": status,
            "expires_at": at + timedelta(minutes=10),
        }
    )


class FakeIdentityService:
    """inbox(demo_session, now) double: messages per demo_session; records (demo_session, now)."""

    def __init__(
        self,
        by_session: Mapping[str, Sequence[InboxMessage]] | None = None,
        *,
        raises: Exception | None = None,
    ) -> None:
        self.by_session: dict[str, tuple[InboxMessage, ...]] = {
            key: tuple(value) for key, value in (by_session or {}).items()
        }
        self.raises = raises
        self.calls: list[tuple[str, datetime]] = []

    def inbox(self, demo_session: str, now: datetime) -> tuple[InboxMessage, ...]:
        self.calls.append((demo_session, now))
        if self.raises is not None:
            raise self.raises
        return self.by_session.get(demo_session, ())


@dataclass(frozen=True)
class DemoCall:
    method: str
    at_mono: float  # time.monotonic() at the call
    kwargs: dict[str, object]


class FakeDemoService:
    """staffing / set_staffing / clock_view double (cases.md section 6)."""

    def __init__(
        self,
        *,
        staffing: StaffingViewStub = OFF,
        clock: ClockViewStub = START_CLOCK,
        converted_on_change: int = 0,
        staffing_raises: Exception | None = None,
    ) -> None:
        self.current_mode: str = staffing.mode
        self.clock = clock
        self.converted_on_change = converted_on_change
        self.staffing_raises = staffing_raises
        self.calls: list[DemoCall] = []

    def _record(self, method: str, **kwargs: object) -> None:
        self.calls.append(DemoCall(method, time.monotonic(), dict(kwargs)))

    def staffing(self) -> StaffingViewStub:
        self._record("staffing")
        if self.staffing_raises is not None:
            raise self.staffing_raises
        return ON if self.current_mode == ON.mode else OFF

    def set_staffing(self, mode: str, *, request_id: object, role: object) -> StaffingChangeStub:
        self._record("set_staffing", mode=mode, request_id=request_id, role=role)
        label = ON_LABEL if mode == ON.mode else OFF_LABEL
        if mode == self.current_mode:
            return StaffingChangeStub(mode, label, 0)
        self.current_mode = mode
        return StaffingChangeStub(mode, label, self.converted_on_change)

    def clock_view(self) -> ClockViewStub:
        self._record("clock_view")
        return self.clock


_DEFAULT_DONE = ResetDoneStub(open_chats_ended=2, roles_reset=1, clock=START_CLOCK)


class FakeResetService:
    """reset(now, *, request_id, session_id, role) double (cases.md section 7). `outcomes` are used in order (an
    exception instance is raised, anything else returned); when they run out it returns `default`."""

    def __init__(self, *, outcomes: Sequence[object] = (), default: object = _DEFAULT_DONE) -> None:
        self.outcomes: list[object] = list(outcomes)
        self.default = default
        self.calls: list[tuple[datetime, dict[str, object]]] = []

    def reset(self, now: datetime, *, request_id: object, session_id: object, role: object) -> object:
        self.calls.append((now, {"request_id": request_id, "session_id": session_id, "role": role}))
        outcome = self.outcomes.pop(0) if self.outcomes else self.default
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@dataclass
class DemoHarness:
    app: FastAPI
    settings: Settings
    store: FakeSessionStore
    identity: FakeIdentityService
    demo: FakeDemoService
    resets: FakeResetService
    wall: MutableClock
    trace: InMemoryTraceSink


def demo_app(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    *,
    identity: FakeIdentityService | None = None,
    demo: FakeDemoService | None = None,
    resets: FakeResetService | None = None,
    store: FakeSessionStore | None = None,
    limiter: RateLimiter | None = None,
    wall: MutableClock | None = None,
) -> DemoHarness:
    """AEA-23's real app and middleware over a container that runs register_web and register_demo_routes only; the
    three services, the session store, the heartbeat and (optionally) the limiter are dependency overrides."""
    harness_trace = InMemoryTraceSink()

    def build(app: FastAPI, settings_: Any, *, overrides: Any = None) -> Container:
        limits = Limits()
        container = Container(settings=settings_, limits=limits)
        register_web(container, app, settings=settings_, limits=limits)
        register_demo_routes(container, app, settings=settings_, limits=limits)
        container.provide(Key[Any]("trace"), lambda _c: harness_trace)
        container.build()
        return container

    monkeypatch.setattr(app_module, "build_container", build)
    clock = wall if wall is not None else MutableClock(WALL_START)
    app = create_app(settings, overrides=ContainerOverrides(wall_clock=clock))
    store_ = store if store is not None else FakeSessionStore()
    identity_ = identity if identity is not None else FakeIdentityService()
    demo_ = demo if demo is not None else FakeDemoService()
    resets_ = resets if resets is not None else FakeResetService()
    heartbeat = FakeHeartbeat()
    app.dependency_overrides[get_login_sessions] = lambda: store_
    app.dependency_overrides[get_staff_access] = lambda: store_
    app.dependency_overrides[get_heartbeat] = lambda: heartbeat
    app.dependency_overrides[get_identity_service] = lambda: identity_
    app.dependency_overrides[get_demo_service] = lambda: demo_
    app.dependency_overrides[get_reset_service] = lambda: resets_
    if limiter is not None:
        app.dependency_overrides[get_rate_limiter] = lambda: limiter
    return DemoHarness(
        app=app,
        settings=settings,
        store=store_,
        identity=identity_,
        demo=demo_,
        resets=resets_,
        wall=clock,
        trace=harness_trace,
    )


def signed_in(h: DemoHarness, role: DemoRole = DemoRole.CUSTOMER) -> tuple[dict[str, str], LoginSession]:
    token = h.store.issue(role, now=WALL_START)
    return cookie_header(token), h.store.session_of(token)


@dataclass
class GateHold:
    thread: threading.Thread
    released_at: float | None = field(default=None)


def hold_gate_for(gate: ResetGate, seconds: float) -> GateHold:
    """Hold the reset gate on a background thread for `seconds`; returns once the hold has started. The monotonic
    time just before release is recorded in `released_at`."""
    entered = threading.Event()
    hold = GateHold(thread=threading.Thread(target=lambda: None))

    def run() -> None:
        with gate.hold():
            entered.set()
            time.sleep(seconds)
            hold.released_at = time.monotonic()

    hold.thread = threading.Thread(target=run, daemon=True)
    hold.thread.start()
    assert entered.wait(5), "the gate hold did not start"
    return hold
