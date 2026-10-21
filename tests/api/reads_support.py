"""AEA-48 test support: a MetricsReads double (web.md section 4), a refusing rate limiter, and an app builder that runs
AEA-23's register_web plus AEA-48's register_reads. Not a conftest. Synthetic values only (the OpenAPI examples)."""

from __future__ import annotations

import copy
import logging
import threading
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Literal, cast

import pytest
from fastapi import FastAPI

import meridian.web.app as app_module
from meridian.config import Settings
from meridian.domain.staff import DemoRole
from meridian.policy.limits import Limits, WebLimits
from meridian.web.app import create_app
from meridian.web.container import Container, register_reads, register_web
from meridian.web.deps import (
    get_heartbeat,
    get_login_sessions,
    get_metrics_reads,
    get_rate_limiter,
    get_staff_access,
)
from meridian.web.middleware import ALLOWED, LimitScope, LimitVerdict, RateLimiter
from meridian.web.routes.reads import (
    LATEST_EVAL_PATH,
    MONITORING_PATH,
    OWNER_METRICS_PATH,
    READS_LOGGER,
)
from tests.api.openapi_check import load_document
from tests.api.web_shell_support import FakeHeartbeat, FakeSessionStore, cookie_header, reset_gate_of

OPERATIONS: dict[str, str] = {  # operation id -> path, in this order everywhere
    "getOwnerMetrics": OWNER_METRICS_PATH,
    "getMonitoring": MONITORING_PATH,
    "getLatestEval": LATEST_EVAL_PATH,
}
EXAMPLE_NAMES: dict[str, tuple[str, ...]] = {
    "getOwnerMetrics": ("SEEDED", "EMPTY"),
    "getMonitoring": (
        "DEFAULT",
        "FIRING",
        "TOO_FEW_TURNS",
        "EMPTY",
        "ZERO_TRAFFIC_FIRING",
        "FAILURE_AND_TRACE_FIRING",
    ),
    "getLatestEval": ("BOTH_SPLITS", "DEV_ONLY", "STALE_RUN", "NO_RUN"),
}
DEFAULT_EXAMPLE: dict[str, str] = {
    "getOwnerMetrics": "SEEDED",
    "getMonitoring": "DEFAULT",
    "getLatestEval": "BOTH_SPLITS",
}
RETRY_AFTER_MS = 7000  # the refusing limiter's verdict


def _examples(operation_id: str) -> Mapping[str, Any]:
    document = load_document()
    node = document["paths"][OPERATIONS[operation_id]]["get"]["responses"]["200"]["content"][
        "application/json"
    ]
    examples: Mapping[str, Any] = node["examples"]
    return examples


def example_names(operation_id: str) -> tuple[str, ...]:
    """The 200 example names in the OpenAPI, in file order (drift guard for EXAMPLE_NAMES)."""
    return tuple(_examples(operation_id))


def example(operation_id: str, name: str) -> dict[str, Any]:
    """A deep copy of the named 200 example's value (so a test may mutate it)."""
    return cast(dict[str, Any], copy.deepcopy(_examples(operation_id)[name]["value"]))


class FakeMetricsReads:
    """MetricsReads double. `returns[op]` is what the matching method returns (default: DEFAULT_EXAMPLE per op, deep
    copies); `calls` lists operation ids in call order; when `probe` is set, `held_at_call` records probe() per call."""

    def __init__(self, returns: Mapping[str, object] | None = None) -> None:
        self.returns: dict[str, object] = (
            dict(returns)
            if returns is not None
            else {op: example(op, DEFAULT_EXAMPLE[op]) for op in OPERATIONS}
        )
        self.calls: list[str] = []
        self.probe: Callable[[], bool] | None = None
        self.held_at_call: list[bool] = []

    def _read(self, operation_id: str) -> Mapping[str, object]:
        self.calls.append(operation_id)
        if self.probe is not None:
            self.held_at_call.append(self.probe())
        return cast(Mapping[str, object], self.returns[operation_id])

    def owner_metrics(self) -> Mapping[str, object]:
        return self._read("getOwnerMetrics")

    def monitoring(self) -> Mapping[str, object]:
        return self._read("getMonitoring")

    def latest_eval(self) -> Mapping[str, object]:
        return self._read("getLatestEval")


class RefusingLimiter(RateLimiter):
    """Refuses the SESSION and IP read buckets (the 429 path); allows LOGIN_IP, THREAD and RESET_IP, so login works."""

    def __init__(self) -> None:
        super().__init__(WebLimits())

    def _verdict(self, scope: LimitScope) -> LimitVerdict:
        if scope in (LimitScope.SESSION, LimitScope.IP):
            return LimitVerdict(allowed=False, scope=scope, retry_after_ms=RETRY_AFTER_MS)
        return ALLOWED

    def peek(
        self, scope: LimitScope, key: str, now: float, *, family: Literal["turn", "read"] = "read"
    ) -> LimitVerdict:
        return self._verdict(scope)

    def check(
        self, scope: LimitScope, key: str, now: float, *, family: Literal["turn", "read"] = "read"
    ) -> LimitVerdict:
        return self._verdict(scope)


@dataclass
class ReadsHarness:
    app: FastAPI
    settings: Settings
    store: FakeSessionStore
    reads: FakeMetricsReads


def reads_app(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    *,
    reads: FakeMetricsReads | None = None,
    store: FakeSessionStore | None = None,
    limiter: RateLimiter | None = None,
) -> ReadsHarness:
    def build(app: FastAPI, settings: Any, *, overrides: Any = None) -> Container:
        limits = Limits()
        container = Container(settings=settings, limits=limits)
        register_web(container, app, settings=settings, limits=limits)
        register_reads(container, app, settings=settings, limits=limits)
        container.build()
        return container

    monkeypatch.setattr(app_module, "build_container", build)
    app = create_app(settings)
    the_store = store if store is not None else FakeSessionStore()
    the_reads = reads if reads is not None else FakeMetricsReads()
    app.dependency_overrides[get_login_sessions] = lambda: the_store
    app.dependency_overrides[get_staff_access] = lambda: the_store
    app.dependency_overrides[get_heartbeat] = lambda: FakeHeartbeat()
    app.dependency_overrides[get_metrics_reads] = lambda: the_reads
    if limiter is not None:
        app.dependency_overrides[get_rate_limiter] = lambda: limiter
    return ReadsHarness(app=app, settings=settings, store=the_store, reads=the_reads)


def signed_in(h: ReadsHarness, role: DemoRole) -> dict[str, str]:
    return cookie_header(h.store.issue(role))


def get_read(client: Any, operation_id: str, headers: Mapping[str, str] | None = None) -> Any:
    return client.get(OPERATIONS[operation_id], headers=dict(headers or {}))


@contextmanager
def gate_held_for(app: FastAPI, seconds: float) -> Iterator[None]:
    """Hold the app's real ResetGate from a background thread for `seconds`; yields once it is held."""
    gate = reset_gate_of(app)
    held = threading.Event()

    def hold() -> None:
        with gate.hold():
            held.set()
            time.sleep(seconds)

    thread = threading.Thread(target=hold, daemon=True)
    thread.start()
    assert held.wait(5)
    try:
        yield
    finally:
        thread.join(5)


def reads_log(caplog: pytest.LogCaptureFixture, level: int) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == READS_LOGGER and r.levelno == level]


def all_measures(bodies: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Every Measure, Tile and EvalMeasure dict in the given bodies (keys: operation ids present)."""
    found: list[dict[str, Any]] = []
    if "getOwnerMetrics" in bodies:
        b = bodies["getOwnerMetrics"]
        found += [b["in_scope_correct_resolution"], b["promises_kept_on_time"], b["handoffs"]]
        found += [*b["outcomes"], *b["handoffs_by_reason"]]
    if "getMonitoring" in bodies:
        b = bodies["getMonitoring"]
        found += [*b["health"], b["correctness"]["containment_estimate"]]
        found += list(b["correctness"]["escalations_by_reason"])
    if "getLatestEval" in bodies:
        b = bodies["getLatestEval"]
        for run in (b["splits"]["dev"], b["splits"]["held_out"]):
            if run:
                found += list(run["measures"])
        if b["headline"]:
            found.append(b["headline"])
    return found
