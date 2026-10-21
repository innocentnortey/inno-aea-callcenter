"""`JourneyRun`, the object journey tests get, and `open_journey()` which wires every part (AEA-57)."""

from __future__ import annotations

import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import httpx

from meridian.domain.common import Role
from tests.journeys.support.client import JourneyClient
from tests.journeys.support.db import DbReader
from tests.journeys.support.env import JourneyEnv, journey_environment
from tests.journeys.support.logtap import LogTap, tap_logs
from tests.journeys.support.scripted_model import JourneyScript, ScriptedModel, scripted_overrides
from tests.journeys.support.server import RunningServer, SocketGuard, StepClock, launch_server, socket_guard
from tests.journeys.support.steps import (
    RunNote,
    StepCollector,
    StepResult,
    blocked_message,
    missing_needs,
    owners_of,
    stop_blocked,
)

if TYPE_CHECKING:
    from fastapi import FastAPI

    from meridian.config import Settings
    from meridian.web.container import Container


@dataclass(frozen=True)
class LoginResult:
    client: JourneyClient
    response: httpx.Response
    session_id: str
    cookie: str  # the mhc_session value: assert with it, never print it


@dataclass
class JourneyRun:
    env: JourneyEnv
    server: RunningServer
    script: JourneyScript
    models: Mapping[Role, ScriptedModel]
    clock: StepClock | None
    db: DbReader
    logs: LogTap
    guard: SocketGuard
    collector: StepCollector
    strict: bool
    nodeid: str
    clients: list[JourneyClient] = field(default_factory=list)

    @property
    def settings(self) -> Settings:
        return self.env.settings

    @property
    def app(self) -> FastAPI:
        return self.server.app

    @property
    def container(self) -> Container:
        return self.server.container

    @property
    def base_url(self) -> str:
        return self.server.base_url

    @property
    def demo_username(self) -> str:
        return self.settings.demo_username.get_secret_value()

    def secret_values(self) -> tuple[str, str]:
        return self.env.secret_values()

    def client(self) -> JourneyClient:
        made = JourneyClient(self.base_url)
        self.clients.append(made)
        return made

    def login(self, client: JourneyClient | None = None) -> LoginResult:
        c = client or self.client()
        before = {r["session_id"] for r in self.db.rows("SELECT session_id FROM staff_sessions")}
        response = c.call(
            "POST",
            "/api/login",
            operation_id="login",
            body={
                "username": self.demo_username,
                "password": self.settings.demo_password.get_secret_value(),
            },
        )
        if response.status_code != 200:
            raise AssertionError(f"login answered HTTP {response.status_code}")
        after = {r["session_id"] for r in self.db.rows("SELECT session_id FROM staff_sessions")}
        new = after - before
        if len(new) != 1:
            raise AssertionError(f"login stored {len(new)} new staff_sessions rows, expected 1")
        cookie = c.cookie()
        if not cookie:
            raise AssertionError("login set no mhc_session cookie")
        return LoginResult(client=c, response=response, session_id=next(iter(new)), cookie=cookie)

    @contextmanager
    def step(
        self, journey: str, name: str, *, needs: Sequence[str] = (), operations: Sequence[str] = ()
    ) -> Iterator[None]:
        start = time.perf_counter()
        missing = missing_needs(self.container, self.app, needs, operations)
        if missing:
            self.collector.add_step(
                StepResult(
                    journey, name, self.nodeid, "blocked", blocked_message(missing), owners_of(missing), 0.0
                )
            )
            stop_blocked(missing, strict=self.strict)
        try:
            yield
        except Exception as exc:
            detail = (str(exc).splitlines() or [""])[0][:300] or type(exc).__name__
            self.collector.add_step(
                StepResult(journey, name, self.nodeid, "fail", detail, (), time.perf_counter() - start)
            )
            raise
        else:
            self.collector.add_step(
                StepResult(journey, name, self.nodeid, "pass", "", (), time.perf_counter() - start)
            )

    def files_containing(self, value: str) -> list[str]:
        needle = value.encode("utf-8")
        found: list[str] = []
        for path in sorted(self.env.data_dir.rglob("*")):
            if path.is_file() and needle in path.read_bytes():
                found.append(str(path.relative_to(self.env.data_dir)))
        return found

    def close_clients(self) -> None:
        for made in self.clients:
            made.close()
        self.clients.clear()


@contextmanager
def open_journey(
    *, collector: StepCollector, strict: bool, with_clock: bool, nodeid: str
) -> Iterator[JourneyRun]:
    with socket_guard() as guard, tap_logs() as logs, journey_environment() as env:
        script = JourneyScript()
        clock = StepClock() if with_clock else None
        overrides, models = scripted_overrides(env.settings, script, wall_clock=clock)
        with launch_server(env.settings, overrides=overrides) as server:
            run = JourneyRun(
                env=env,
                server=server,
                script=script,
                models=models,
                clock=clock,
                db=DbReader(env.db_path),
                logs=logs,
                guard=guard,
                collector=collector,
                strict=strict,
                nodeid=nodeid,
            )
            try:
                yield run
            finally:
                run.close_clients()
        spend = DbReader(env.db_path).one(
            "SELECT COUNT(*) AS n, COALESCE(SUM(cost_usd), 0.0) AS total FROM spend_ledger"
        )
        collector.add_note(
            RunNote(
                host=server.host,
                port=server.port,
                agent_version=env.settings.agent_version,
                models={r.value: f"{m.provider}/{m.model}" for r, m in models.items()},
                issued_sha256=env.issued_sha256_before,
                spend_rows=int(spend["n"]),
                spend_total_usd=float(spend["total"]),
                outbound_blocked=len(guard.blocked),
            )
        )
    if guard.blocked:
        raise AssertionError(
            f"journey socket guard refused {len(guard.blocked)} non-loopback connection(s): {guard.blocked}"
        )
