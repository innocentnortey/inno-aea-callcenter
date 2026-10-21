"""The one composition root (DO-3 §2.1).

``build_container`` makes the one ``Limits``, takes the built Settings and the FastAPI ``app`` from its caller (the app
lifespan in web/app.py, AEA-23), and calls one ``register_<area>()`` hunk per registering ticket in a fixed order.

Each hunk belongs to the ticket named in its docstring. That ticket edits only that function's body (slice plan §3).
Hunks cooperate through ``Container.provide/get`` (lazy, built once), ``on_start`` (threads and sweeps, run after every
object is built) and ``on_close`` (release, newest first).

A hunk imports its own modules inside its own function body. This file's module-level imports never change after
AEA-01: that keeps wave 0 free of internal edges and stops later tickets from colliding on the import block.

No module-level clients, settings or singletons (DO-3 §2.1).
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from meridian.policy.limits import Limits

if TYPE_CHECKING:
    from fastapi import FastAPI


class ContainerError(RuntimeError):
    """A wiring mistake: an unknown, duplicate or cyclic provider, or use after build or close."""


@dataclass(frozen=True)
class Key[T]:
    """Names one provided object, e.g. Key[LedgerService]("ledger"). Two keys are equal when their names are."""

    name: str


class Container:
    """Lazy, memoised providers plus start and close hooks. Holds no overrides (R-W-8)."""

    def __init__(self, *, settings: Any, limits: Limits) -> None:
        self._settings = settings
        self._limits = limits
        self._factories: dict[str, Callable[[Container], object]] = {}
        self._objects: dict[str, object] = {}
        self._building: list[str] = []
        self._starters: list[Callable[[], None]] = []
        self._closers: list[Callable[[], None]] = []
        self._built = False
        self._closed = False

    @property
    def settings(self) -> Any:
        """AEA-02's Settings; typed Any so this file imports no other ticket's module."""
        return self._settings

    @property
    def limits(self) -> Limits:
        return self._limits

    @property
    def closed(self) -> bool:
        return self._closed

    def provide[T](self, key: Key[T], factory: Callable[[Container], T]) -> None:
        if self._built or self._closed:
            raise ContainerError(f"provide after build: {key.name}")
        if key.name in self._factories:
            raise ContainerError(f"already provided: {key.name}")
        self._factories[key.name] = factory

    def get[T](self, key: Key[T]) -> T:
        name = key.name
        if self._closed:
            raise ContainerError(f"get after close: {name}")
        if name in self._objects:
            return cast(T, self._objects[name])
        if name not in self._factories:
            raise ContainerError(f"not provided: {name}")
        if name in self._building:
            chain = " -> ".join([*self._building[self._building.index(name) :], name])
            raise ContainerError(f"provider cycle: {chain}")
        self._building.append(name)
        try:
            built = self._factories[name](self)
        finally:
            self._building.pop()
        self._objects[name] = built
        return cast(T, built)

    def on_start(self, starter: Callable[[], None]) -> None:
        if self._built:
            raise ContainerError("on_start after build")
        self._starters.append(starter)

    def on_close(self, closer: Callable[[], None]) -> None:
        if self._closed:
            raise ContainerError("on_close after close")
        self._closers.append(closer)

    def build(self) -> None:
        if self._built:
            raise ContainerError("already built")
        for name in list(self._factories):
            self.get(Key[object](name))
        self._built = True
        for starter in self._starters:
            starter()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        errors: list[Exception] = []
        while self._closers:
            closer = self._closers.pop()
            try:
                closer()
            except Exception as exc:
                errors.append(exc)
        if errors:
            raise ExceptionGroup("container close failed", errors)


def register_storage(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-10 storage: SQLite unit of work, migrations and first boot, checkpointer (cases.md §1).

    Provides Key("uow_factory") (SqliteUnitOfWorkFactory; building it migrates the working copy, WF-16),
    Key("checkpointer") (Checkpointer over checkpoints.sqlite, closed with the container) and
    Key("restore_working_copy") (restore_working_copy bound to settings.issued_db_path; cases.md §1.4).
    """
    import functools
    from pathlib import Path

    from meridian.adapters.checkpointer import CHECKPOINTS_DB_NAME, Checkpointer
    from meridian.adapters.sqlite.db import SqliteUnitOfWorkFactory
    from meridian.adapters.sqlite.migrate import WORKING_DB_NAME, migrate, restore_working_copy

    data_dir = Path(settings.data_dir)
    issued_path = Path(settings.issued_db_path)
    db_path = data_dir / WORKING_DB_NAME

    def make_uow_factory(_c: Container) -> SqliteUnitOfWorkFactory:
        migrate(db_path, issued_path=issued_path)  # first boot copies the issued file; DDL every boot
        return SqliteUnitOfWorkFactory(db_path)

    def make_checkpointer(c: Container) -> Checkpointer:
        checkpointer = Checkpointer(data_dir / CHECKPOINTS_DB_NAME)
        c.on_close(checkpointer.close)
        return checkpointer

    container.provide(Key[SqliteUnitOfWorkFactory]("uow_factory"), make_uow_factory)
    container.provide(Key[Checkpointer]("checkpointer"), make_checkpointer)
    container.provide(
        Key[Callable[..., None]]("restore_working_copy"),
        lambda _c: functools.partial(restore_working_copy, issued_path=issued_path),
    )


def register_web(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-23 web shell: login routes, reset gate, rate limiter, public paths, web/deps.py bindings (web.md §1–§7).

    Binds the reset gate, the rate limiter, the one stream CapacityLimiter(4) and the wall clock create_app chose,
    and registers the two public paths. An app that create_app did not build has no web shell, so this does nothing.
    """
    import anyio

    from meridian.services.reset_gate import ResetGate
    from meridian.web.deps import (
        RATE_LIMITER,
        RESET_GATE,
        STREAM_POLL_LIMITER,
        STREAM_POLL_THREADS,
        WALL_CLOCK,
    )
    from meridian.web.middleware import RateLimiter, WebShellState

    shell = getattr(app.state, "web_shell", None)
    if not isinstance(shell, WebShellState):
        return
    container.provide(RESET_GATE, lambda _c: ResetGate())
    container.provide(RATE_LIMITER, lambda _c: RateLimiter(limits.web))
    container.provide(STREAM_POLL_LIMITER, lambda _c: anyio.CapacityLimiter(STREAM_POLL_THREADS))
    container.provide(WALL_CLOCK, lambda _c: shell.wall_clock)
    shell.public_paths.add_exact("POST", "/api/login")
    shell.public_paths.add_exact("GET", "/healthz")


def register_ops(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-32 ops: health events, heartbeat, watchdog, alerts (cases.md §8).

    Provides deps.HEARTBEAT (the Heartbeat /healthz reads), Key[AlertWriter]("alert_writer") (AEA-19 binds the trace
    sink's on_alert to it) and Key[AlertSettings]("alert_settings") (AEA-53). Its starter runs the heartbeat task on the
    lifespan's event loop and the watchdog thread; it reads Key("uow_factory") (AEA-10), Key("wall_clock") (AEA-23) and
    Key("ledger") (AEA-26). An app that create_app did not build has no /healthz to probe, so this does nothing.
    """
    import asyncio
    import os
    import threading
    import time

    import httpx

    from meridian.services.health import (
        AlertEvaluator,
        AlertSettings,
        AlertWriter,
        Heartbeat,
        SpendReader,
        Watchdog,
        run_beats,
    )
    from meridian.web import deps
    from meridian.web.middleware import HEALTHZ_PATH, WebShellState

    if not isinstance(getattr(app.state, "web_shell", None), WebShellState):
        return
    alert_settings = AlertSettings()
    agent_version = str(settings.agent_version)
    heartbeat = Heartbeat(alert_settings, started_mono=time.monotonic())
    running: dict[str, Any] = {}

    container.provide(Key[AlertSettings]("alert_settings"), lambda _c: alert_settings)
    container.provide(deps.HEARTBEAT, lambda _c: heartbeat)
    container.provide(
        Key[AlertWriter]("alert_writer"),
        lambda c: AlertWriter(c.get(deps.UOW_FACTORY), c.get(deps.WALL_CLOCK), agent_version),
    )

    def hard_exit(code: int) -> None:
        os._exit(code)  # sys.exit in a thread would end only the thread; Railway restarts on a non-zero exit

    def start() -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            raise RuntimeError("register_ops: start needs the app lifespan's running event loop") from None
        uow = container.get(deps.UOW_FACTORY)
        wall_clock = container.get(deps.WALL_CLOCK)
        evaluator = AlertEvaluator(
            uow,
            container.get(Key[SpendReader]("ledger")),
            alert_settings,
            wall_clock,
            limits.spend.daily_cap_usd,
            agent_version=agent_version,
        )

        async def healthz_ok() -> bool:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://watchdog.local") as client:
                response = await client.get(HEALTHZ_PATH)
            return response.status_code == 200

        def probe() -> bool:
            future = asyncio.run_coroutine_threadsafe(healthz_ok(), loop)
            try:
                return future.result(timeout=alert_settings.probe_timeout_s)
            except Exception:
                future.cancel()
                return False

        watchdog = Watchdog(
            uow, probe, hard_exit, evaluator, alert_settings, wall_clock, agent_version=agent_version
        )
        stop = threading.Event()
        thread = threading.Thread(
            target=watchdog.run_until, args=(stop,), name="meridian-watchdog", daemon=True
        )
        running.update(
            loop=loop,
            stop=stop,
            thread=thread,
            task=loop.create_task(run_beats(heartbeat, alert_settings), name="meridian-heartbeat"),
        )
        thread.start()

    def close() -> None:
        stop = running.get("stop")
        if stop is not None:
            stop.set()
            running["thread"].join(timeout=1.0)
        task, loop = running.get("task"), running.get("loop")
        if task is not None and loop is not None:
            with contextlib.suppress(RuntimeError):
                loop.call_soon_threadsafe(task.cancel)

    container.on_start(start)
    container.on_close(close)


def register_tracing(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-19 tracing: Langfuse or null trace sink and the project-key check (models.md §4, §7).

    Provides Key[TraceSink]("trace"). LangfuseTraceSink only when all four LANGFUSE_* settings are set
    (Settings.langfuse_complete()); otherwise NullTraceSink and no alert (MOD-6 step 5, MC-24). The sink's on_alert
    calls the container's "alert_writer".fire("trace_export_failed", reason) (AEA-32, cases.md §8); until that key
    exists it logs a fixed line. One LangfuseTraceSink per Langfuse public key per process.
    """
    import logging

    from meridian.adapters.tracing_langfuse import (
        LangfuseExportSettings,
        LangfuseTraceSink,
        NullTraceSink,
        TraceAlertReason,
    )
    from meridian.config import Settings
    from meridian.ports.runtime import TraceSink
    from meridian.privacy.redact import redact

    log = logging.getLogger("meridian.tracing")
    trace_key = Key[TraceSink]("trace")
    typed = cast(Settings, settings)
    pk, sk = typed.langfuse_public_key, typed.langfuse_secret_key
    base_url, project_id = typed.langfuse_base_url, typed.langfuse_project_id
    if not typed.langfuse_complete() or pk is None or sk is None or base_url is None or project_id is None:
        null_sink = NullTraceSink()
        container.provide(trace_key, lambda _c: null_sink)
        return

    def on_alert(reason: TraceAlertReason) -> None:
        try:
            writer = container.get(Key[Any]("alert_writer"))
        except ContainerError:
            log.warning("trace_alert_unbound reason=%s", reason)
            return
        writer.fire("trace_export_failed", reason)

    export_settings = LangfuseExportSettings(
        public_key=pk, secret_key=sk, base_url=base_url, project_id=project_id
    )
    try:
        sink = LangfuseTraceSink(export_settings, redact, on_alert)
    except Exception as exc:
        log.warning("trace_sink_error op=build error=%s", type(exc).__name__)
        fallback = NullTraceSink()
        container.provide(trace_key, lambda _c: fallback)
        return
    container.provide(trace_key, lambda _c: sink)
    container.on_start(sink.start)
    container.on_close(sink.close)


def register_spend(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-26 spend: LedgerService and the spend guard (models.md §6).

    Provides Key[LedgerService]("ledger"), the one LedgerService, built from the "uow_factory" key (AEA-10), the
    "wall_clock" key (AEA-23, create_app's choice; MC-20, D-13) and limits.spend.daily_cap_usd (MC-22). The gateway
    (AEA-20), the turn service (AEA-40, typed as SpendGuard), the alert evaluator (AEA-32), the metrics reader (AEA-53)
    and GraphDeps.ledger (AEA-51) all get it with container.get(Key[LedgerService]("ledger")).
    """
    import datetime as dt

    from meridian.ports.runtime import UnitOfWorkFactory
    from meridian.services.ledger import LedgerService

    uow_key: Key[UnitOfWorkFactory] = Key("uow_factory")  # = web.deps.UOW_FACTORY (keys are equal by name)
    wall_key: Key[Callable[[], dt.datetime]] = Key("wall_clock")  # = web.deps.WALL_CLOCK

    def build(c: Container) -> LedgerService:
        return LedgerService(
            c.get(uow_key),
            wall_clock=c.get(wall_key),
            daily_cap_usd=limits.spend.daily_cap_usd,
            probe_lost_after_s=float(limits.turn.deadline_s),
        )

    container.provide(Key[LedgerService]("ledger"), build)


def register_anthropic(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-17 models: the Anthropic adapter (models.md §2, §7).

    No-op until AEA-17 fills it.
    """


def register_jev(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-18 models: the Jev adapter via OpenRouter (models.md §3, §7).

    No-op until AEA-18 fills it.
    """


def register_gateway(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-20 models: the ModelGateway (DO-4 §12; models.md §5, §7).

    No-op until AEA-20 fills it.
    """


def register_retrieval(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-33 retrieval: empty unless AEA-33 needs it; knowledge_tools() is wired in register_graph (data.md §4).

    No-op until AEA-33 fills it.
    """


def register_tool_dispatch(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-22 tools: empty unless AEA-22 needs it; the ToolRegistry and ToolDispatcher are wired in register_graph (graph-tools §1).

    No-op until AEA-22 fills it.
    """


def register_identity(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-27 identity: IdentityService and the demo inbox (graph-tools §5).

    No-op until AEA-27 fills it.
    """


def register_scheduling(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-28 scheduling: SchedulingService (cases.md §4).

    No-op until AEA-28 fills it.
    """


def register_cases(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-29 cases and handoff: CaseService, HandoffService, BriefAssembler (cases.md §5).

    No-op until AEA-29 fills it.
    """


def register_demo(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-30 demo: DemoClock, staffing, the scheduler job thread (cases.md §6).

    No-op until AEA-30 fills it.
    """


def register_reset(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-31 reset: ResetService and the demo seed (cases.md §7).

    Binds the reset service (restore and checkpoint clear from storage, the reset gate, the seed with AEA-29's
    BriefAssembler, AEA-30's format_clock) and loads the demo seed once at first boot. An app create_app did not build
    has no web shell, so this does nothing.
    """
    import functools
    import importlib

    from meridian.services.reset import ResetService, seed_demo, seed_first_boot
    from meridian.web.deps import RESET_GATE, RESET_SERVICE, UOW_FACTORY, WALL_CLOCK
    from meridian.web.middleware import WebShellState

    shell = getattr(app.state, "web_shell", None)
    if not isinstance(shell, WebShellState):
        return

    def sibling(module: str, name: str) -> Any:
        # Same-wave siblings (AEA-29, AEA-30), resolved when the container builds, not at import.
        return getattr(importlib.import_module(module), name)

    def seed() -> Callable[[Any], int]:
        return functools.partial(
            seed_demo, assembler=sibling("meridian.services.handoff", "BriefAssembler")()
        )

    def lazy_seed(tx: Any) -> int:
        # Resolved on first call, so the container builds before AEA-29 lands.
        return seed()(tx)

    def lazy_format_clock(*args: Any, **kwargs: Any) -> Any:
        return sibling("meridian.services.demo", "format_clock")(*args, **kwargs)

    def sibling_present(module: str) -> bool:
        try:
            importlib.import_module(module)
        except ImportError:
            return False
        return True

    def build(c: Container) -> ResetService:
        checkpointer = c.get(Key[Any]("checkpointer"))
        return ResetService(
            c.get(UOW_FACTORY),
            c.get(RESET_GATE),
            c.get(Key[Any]("restore_working_copy")),
            checkpointer.clearing,
            lazy_seed,
            format_clock=lazy_format_clock,
        )

    def first_boot() -> None:
        if not sibling_present("meridian.services.handoff"):
            return  # AEA-29 not merged yet: nothing to assemble briefs with, so no first-boot seed
        seed_first_boot(container.get(UOW_FACTORY), seed(), container.get(WALL_CLOCK)())

    container.provide(RESET_SERVICE, build)
    container.on_start(first_boot)


def register_staff_session(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-44 staff: StaffSessionStore, FlagService, CON-10 routes (staff.md §2).

    No-op until AEA-44 fills it.
    """


def register_chat(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-40 customer API: SessionService, TurnService, CON-1 and CON-2 routes, the start-up turn sweep (web.md §9, §14).

    No-op until AEA-40 fills it.
    """


def register_events(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-41 customer API: the CON-3 event stream route (web.md §11).

    No-op until AEA-41 fills it.
    """


def register_person_request(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-42 customer API: PersonRequestService, CON-4 and CON-5 routes (web.md §8).

    No-op until AEA-42 fills it.
    """


def register_demo_routes(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-43 customer API: CON-6 to CON-9 demo routes (web.md §7).

    No-op until AEA-43 fills it.
    """


def register_staff_cases(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-45 staff API: queue, case, actions, contact log, flags, oversight routes (staff.md §6).

    No-op until AEA-45 fills it.
    """


def register_staff_live(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-46 staff API: LiveChatService, CON-14 and CON-21 routes (staff.md §5, §7).

    No-op until AEA-46 fills it.
    """


def register_staff_clock(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-47 staff API: the CON-8 clock-advance route (staff.md §8).

    Includes routes/staff_clock.py's router (advanceDemoClock: POST /api/demo/clock only; the GET on the same path is
    AEA-43's) once per app. Provides nothing: DemoService is bound by AEA-30's register_demo hunk. An app that
    create_app did not build has no web shell, so this does nothing.
    """
    from meridian.web.middleware import WebShellState
    from meridian.web.routes.staff_clock import build_router

    if not isinstance(getattr(app.state, "web_shell", None), WebShellState):
        return
    if getattr(app.state, "staff_clock_routes_included", False):
        return  # a second lifespan on the same app must not add the route again (FastAPI includes lazily)
    app.include_router(build_router())
    app.state.staff_clock_routes_included = True


def register_metrics_reader(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-53 reads: MetricsReader bound to get_metrics_reads() (cases.md §9).

    No-op until AEA-53 fills it.
    """


def register_reads(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-48 reads API: CON-18 to CON-20 routes (staff.md §9).

    No-op until AEA-48 fills it.
    """


def register_graph(
    container: Container, app: FastAPI, *, settings: Any, limits: Limits, overrides: Any
) -> None:
    """AEA-51 integration: completes the graph and binds run_graph; the only reader of overrides (web.md §15, R-W-8).

    No-op until AEA-51 fills it.
    """


def register_frontend(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-49 frontend: serves apps/web/dist; runs last so its SPA fallback never shadows an API route (web.md §12).

    No-op until AEA-49 fills it.
    """


def build_container(app: FastAPI, settings: Any, *, overrides: Any = None) -> Container:
    """Build the one container: one Limits, the 27 hunks in order, then every object and starter.

    ``overrides`` reaches only ``register_graph``, untouched (R-W-8). A failed build closes what it opened.
    """
    limits = Limits()
    container = Container(settings=settings, limits=limits)
    try:
        register_storage(container, app, settings=settings, limits=limits)
        register_web(container, app, settings=settings, limits=limits)
        register_ops(container, app, settings=settings, limits=limits)
        register_tracing(container, app, settings=settings, limits=limits)
        register_spend(container, app, settings=settings, limits=limits)
        register_anthropic(container, app, settings=settings, limits=limits)
        register_jev(container, app, settings=settings, limits=limits)
        register_gateway(container, app, settings=settings, limits=limits)
        register_retrieval(container, app, settings=settings, limits=limits)
        register_tool_dispatch(container, app, settings=settings, limits=limits)
        register_identity(container, app, settings=settings, limits=limits)
        register_scheduling(container, app, settings=settings, limits=limits)
        register_cases(container, app, settings=settings, limits=limits)
        register_demo(container, app, settings=settings, limits=limits)
        register_reset(container, app, settings=settings, limits=limits)
        register_staff_session(container, app, settings=settings, limits=limits)
        register_chat(container, app, settings=settings, limits=limits)
        register_events(container, app, settings=settings, limits=limits)
        register_person_request(container, app, settings=settings, limits=limits)
        register_demo_routes(container, app, settings=settings, limits=limits)
        register_staff_cases(container, app, settings=settings, limits=limits)
        register_staff_live(container, app, settings=settings, limits=limits)
        register_staff_clock(container, app, settings=settings, limits=limits)
        register_metrics_reader(container, app, settings=settings, limits=limits)
        register_reads(container, app, settings=settings, limits=limits)
        register_graph(container, app, settings=settings, limits=limits, overrides=overrides)
        register_frontend(container, app, settings=settings, limits=limits)
        container.build()
    except BaseException:
        with contextlib.suppress(Exception):
            container.close()
        raise
    return container
