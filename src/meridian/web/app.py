"""The app factory (web.md section 15). Routers come from each area's own `register_<area>()` hunk.

`create_app` takes the settings and, in tests only, `ContainerOverrides` (R-W-8). The deployed factory call passes
nothing: no env name, Settings field, header or flag can build an override, and none shifts the wall clock (D-13).
"""

from __future__ import annotations

import os
import time
from collections.abc import AsyncIterator, Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from meridian.config import Settings
from meridian.ports.models import (
    ChoiceModel,
    ChoiceRole,
    StructuredModel,
    StructuredRole,
    ToolCallingModel,
    ToolRole,
)
from meridian.ports.runtime import TraceSink
from meridian.web.container import build_container
from meridian.web.deps import (
    get_heartbeat,
    get_login_sessions,
    get_rate_limiter,
    get_reset_gate,
    get_wall_clock,
    provided,
)
from meridian.web.errors import ApiProblem, handle_api_problem, handle_validation_error
from meridian.web.logging import install_log_formatter
from meridian.web.middleware import HEALTHZ_PATH, GateBindings, GateMiddleware, PublicPaths, WebShellState
from meridian.web.routes.auth import build_router


@dataclass(frozen=True)
class ContainerOverrides:
    """Test-only substitutes. Only the lifespan reads this, and hands it once to the container builder."""

    choice: Mapping[ChoiceRole, ChoiceModel] | None = None
    structured: Mapping[StructuredRole, StructuredModel] | None = None
    tools: Mapping[ToolRole, ToolCallingModel] | None = None
    trace: TraceSink | None = None
    wall_clock: Callable[[], datetime] | None = None


def _utc_now() -> datetime:
    return datetime.now(UTC)


async def healthz(request: Request) -> JSONResponse:
    """Async, from the in-memory heartbeat: never the worker pool, SQLite or a reset wait (DO-3 section 2.3 rule 3)."""
    heartbeat = provided(
        request.app, get_heartbeat
    )  # a direct call: a sync Depends would take a worker thread
    if heartbeat.fresh(time.monotonic()):
        return JSONResponse({"status": "ok"})
    request.state.error_kind = "heartbeat_stale"
    return JSONResponse({"status": "stale"}, status_code=503)


def create_app(settings: Settings | None = None, *, overrides: ContainerOverrides | None = None) -> FastAPI:
    resolved = settings if settings is not None else Settings.from_env(os.environ)
    wall_clock = (
        overrides.wall_clock if overrides is not None and overrides.wall_clock is not None else _utc_now
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        container = build_container(app, resolved, overrides=overrides)
        app.state.container = container
        try:
            yield
        finally:
            app.state.container = None
            container.close()

    app = FastAPI(lifespan=lifespan, openapi_url=None, docs_url=None, redoc_url=None)
    app.state.web_shell = WebShellState(settings=resolved, wall_clock=wall_clock, public_paths=PublicPaths())
    app.add_exception_handler(ApiProblem, handle_api_problem)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_middleware(
        GateMiddleware,
        bindings=GateBindings(
            login_sessions=lambda a: provided(a, get_login_sessions),
            rate_limiter=lambda a: provided(a, get_rate_limiter),
            reset_gate=lambda a: provided(a, get_reset_gate),
            wall_clock=lambda a: provided(a, get_wall_clock),
        ),
    )
    app.include_router(build_router())
    app.add_api_route(HEALTHZ_PATH, healthz, methods=["GET"], include_in_schema=False)
    install_log_formatter()
    return app
