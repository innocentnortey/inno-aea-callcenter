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

    No-op until AEA-10 fills it.
    """


def register_web(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-23 web shell: login routes, reset gate, rate limiter, public paths, web/deps.py bindings (web.md §1–§7).

    No-op until AEA-23 fills it.
    """


def register_ops(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-32 ops: health events, heartbeat, watchdog, alerts (cases.md §8).

    No-op until AEA-32 fills it.
    """


def register_tracing(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-19 tracing: Langfuse or null trace sink and the project-key check (models.md §4, §7).

    No-op until AEA-19 fills it.
    """


def register_spend(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-26 spend: LedgerService and the spend guard (models.md §6).

    No-op until AEA-26 fills it.
    """


def register_anthropic(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-17 models: the Anthropic adapter (models.md §2, §7).

    No-op until AEA-17 fills it.
    """


def register_jev(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-18 models: the Jev adapter via OpenRouter (models.md §3, §7).

    Provides Key[httpx.Client]("jev_http_client"): the one HTTP client every JevAdapter shares, redirects off, closed
    on shutdown. Provides Key[Callable[[str], JevAdapter]]("jev_adapter_factory"): a model ID gives a JevAdapter bound
    to that client and settings.openrouter_api_key (ValueError for a model with no JEV_PRICES row). AEA-51's
    adapter_for calls the factory once per distinct Jev model and memoises the result. Makes no request.
    """
    import httpx

    from meridian.adapters.models.openrouter_jev import JevAdapter

    http_key = Key[httpx.Client]("jev_http_client")

    def _http(c: Container) -> httpx.Client:
        client = httpx.Client(follow_redirects=False, timeout=5.0)
        c.on_close(client.close)
        return client

    def _factory(c: Container) -> Callable[[str], JevAdapter]:
        http = c.get(http_key)
        api_key = settings.openrouter_api_key

        def make(model: str) -> JevAdapter:
            return JevAdapter(http, api_key=api_key, model=model)

        return make

    container.provide(http_key, _http)
    container.provide(Key[Callable[[str], JevAdapter]]("jev_adapter_factory"), _factory)


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

    No-op until AEA-31 fills it.
    """


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

    No-op until AEA-47 fills it.
    """


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
