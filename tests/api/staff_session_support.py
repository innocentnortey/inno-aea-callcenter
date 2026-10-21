"""AEA-44 shared test support (frozen with the AEA-44 tests). Synthetic only; no `.env`, no paid call, no socket.

Imports of AEA-44's own modules happen inside helpers so the suite collects before they exist. Not a conftest.
Distinctive "must be absent" values come from `rand_word` (letters only), so no value looks like a code, card or phone.
"""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

import meridian.web.app as app_module
import meridian.web.container as container_mod
from meridian.adapters.sqlite.db import SqliteUnitOfWorkFactory
from meridian.adapters.sqlite.migrate import WORKING_DB_NAME
from meridian.config import Settings
from meridian.domain.common import CaseRef
from meridian.domain.staff import StaffActor, StaffRole
from meridian.policy.limits import Limits
from meridian.ports.runtime import Clock
from meridian.web.app import ContainerOverrides, create_app
from meridian.web.container import Container, Key, register_staff_session, register_web
from meridian.web.deps import UOW_FACTORY, get_heartbeat, require_staff
from tests.api.openapi_check import load_document
from tests.api.web_shell_support import (
    FakeHeartbeat,
    MutableClock,
    RecordingTraceSink,
    add_probe_route,
    cookie_header,
    demo_pair,
    make_settings,
    session_cookie_value,
    suppress_container_starters,
)
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import TempStore
from tests.unit.adapters.sqlite.helpers import case_ref, case_row, conversation, new_thread

REPO_ROOT = Path(__file__).resolve().parents[2]
WALL_T0 = datetime(2026, 10, 21, 19, 0, tzinfo=UTC)
LIFETIME_S = 43_200
ROLE_NAMES = ("customer", "representative", "supervisor", "owner")


@dataclass
class StaffHarness:
    app: FastAPI
    db: TempStore
    settings: Settings
    wall: MutableClock
    demo: FixedClock
    trace: RecordingTraceSink


def queue_probe(
    actor: StaffActor = Depends(require_staff(StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR)),  # noqa: B008
) -> dict[str, str]:
    return {"role": actor.role.value, "name": actor.name, "signature": actor.signature}


def owner_probe(
    actor: StaffActor = Depends(require_staff(StaffRole.OWNER, StaffRole.SUPERVISOR)),  # noqa: B008
) -> dict[str, str]:
    return {"role": actor.role.value, "name": actor.name, "signature": actor.signature}


def staff_app(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    db: TempStore,
    *,
    demo: FixedClock | None = None,
    wall: MutableClock | None = None,
) -> StaffHarness:
    """`create_app` over a container that runs `register_web`, provides the unit of work and demo clock, and runs the
    REAL `register_staff_session` hunk. Two probe routes stand in for the real staff routes."""
    suppress_container_starters(monkeypatch)
    trace = RecordingTraceSink()
    demo_clock = demo or FixedClock()
    wall_clock = wall or MutableClock(WALL_T0)
    settings = make_settings(tmp_path)

    def build(app: FastAPI, settings_: Any, *, overrides: Any = None) -> Container:
        limits = Limits()
        container = Container(settings=settings_, limits=limits)
        register_web(container, app, settings=settings_, limits=limits)
        container.provide(UOW_FACTORY, lambda _c: db.uow)
        container.provide(Key("demo_clock"), lambda _c: demo_clock)
        container.provide(Key("trace"), lambda _c: trace)
        register_staff_session(container, app, settings=settings_, limits=limits)
        container.build()
        return container

    monkeypatch.setattr(app_module, "build_container", build)
    app = create_app(settings, overrides=ContainerOverrides(wall_clock=wall_clock, trace=trace))
    app.dependency_overrides[get_heartbeat] = lambda: FakeHeartbeat()
    add_probe_route(app, "getQueue", endpoint=queue_probe)
    add_probe_route(app, "getOwnerMetrics", endpoint=owner_probe)
    return StaffHarness(app, db, settings, wall_clock, demo_clock, trace)


@dataclass
class ContainerHarness:
    app: FastAPI
    settings: Settings
    wall: MutableClock
    data_dir: Path

    @property
    def uow(self) -> SqliteUnitOfWorkFactory:
        """Over the working copy the container migrated (valid once the client has entered the lifespan)."""
        return SqliteUnitOfWorkFactory(self.data_dir / WORKING_DB_NAME)


def container_app(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, wall: MutableClock | None = None
) -> ContainerHarness:
    """`create_app` over the REAL `build_container` (every hunk). AEA-30 may not be merged: while `register_demo` is
    still a no-op, a stand-in provides Key("demo_clock")."""
    suppress_container_starters(monkeypatch)
    if "No-op until" in (container_mod.register_demo.__doc__ or ""):

        def stand_in(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
            from meridian.web.middleware import WebShellState

            if isinstance(getattr(app.state, "web_shell", None), WebShellState):
                container.provide(Key("demo_clock"), lambda _c: FixedClock())

        monkeypatch.setattr(container_mod, "register_demo", stand_in)
    wall_clock = wall or MutableClock(WALL_T0)
    settings = make_settings(tmp_path)
    app = create_app(settings, overrides=ContainerOverrides(wall_clock=wall_clock))
    app.dependency_overrides[get_heartbeat] = lambda: FakeHeartbeat()
    add_probe_route(app, "getQueue", endpoint=queue_probe)
    return ContainerHarness(app, settings, wall_clock, Path(settings.data_dir))


# -- request helpers -----------------------------------------------------------------------------------------------
def login_token(client: TestClient, settings: Settings) -> str:
    response = client.post("/api/login", json=demo_pair(settings))
    assert response.status_code == 200, response.text
    token = session_cookie_value(response)
    assert token, "login set no session cookie"
    client.cookies.clear()
    return token


def tab(token: str) -> dict[str, str]:
    """A "tab" is a request stream that carries the cookie by header; two tabs share one token."""
    return cookie_header(token)


def switch(client: TestClient, token: str, role: str) -> Any:
    return client.put("/api/session/role", json={"role": role}, headers=tab(token))


# -- storage helpers -----------------------------------------------------------------------------------------------
_STAFF_COLUMNS = (
    "token_hash, session_id, role, role_reset_pending, signed_in_demo, created_real, expires_real"
)


def staff_rows(uow: Any) -> list[dict[str, object]]:
    with uow() as tx:
        cur = tx.connection.execute(f"SELECT {_STAFF_COLUMNS} FROM staff_sessions ORDER BY session_id")  # noqa: S608
        names = [d[0] for d in cur.description]
        return [dict(zip(names, row, strict=True)) for row in cur.fetchall()]


def flag_rows(uow: Any) -> list[dict[str, object]]:
    with uow() as tx:
        cur = tx.connection.execute("SELECT * FROM flags ORDER BY id")
        names = [d[0] for d in cur.description]
        return [dict(zip(names, row, strict=True)) for row in cur.fetchall()]


def table_counts(uow: Any, *, skip: frozenset[str]) -> dict[str, int]:
    with uow() as tx:
        conn: sqlite3.Connection = tx.connection
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            ).fetchall()
            if r[0] not in skip and not r[0].startswith("sqlite_")
        ]
        return {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}  # noqa: S608


def dir_digest(path: Path) -> str:
    if not path.exists():
        return "absent"
    digest = hashlib.sha256()
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(str(item.relative_to(path)).encode("utf-8"))
        digest.update(item.read_bytes())
    return digest.hexdigest()


def run_reset(uow: Any) -> int:
    """AEA-10's reset write over an exclusive unit of work; returns how many staff roles it sent back to customer."""
    with uow(exclusive=True) as tx:
        cleared = tx.core.reset.clear_demo_tables("reset-" + uuid.uuid4().hex[:8])
        tx.commit()
    return int(cleared.roles_reset)


def seed_case(uow: Any, ref: int) -> tuple[CaseRef, int]:
    """A conversation, an escalated case and one customer message. Returns (case_ref, message_id)."""
    thread = new_thread()
    with uow(write=True) as tx:
        tx.core.conversations.insert(conversation(thread))
        tx.cases.cases.insert(case_row(thread, ref))
        message_id = tx.core.messages.append(
            thread, "customer", "synthetic flagged answer", datetime(2026, 10, 16, 15, 0, tzinfo=UTC)
        )
        tx.commit()
    return case_ref(ref), int(message_id)


# -- OpenAPI examples ----------------------------------------------------------------------------------------------
_PATHS = {
    "getSession": ("/api/session", "get"),
    "listDemoRoles": ("/api/session/roles", "get"),
    "switchRole": ("/api/session/role", "put"),
}


def example(operation_id: str, name: str, *, request: bool = False) -> dict[str, Any]:
    """A named example value of the operation's 200 response (or its request body) from the OpenAPI document."""
    path, method = _PATHS[operation_id]
    operation = load_document()["paths"][path][method]
    if request:
        content = operation["requestBody"]["content"]["application/json"]
    else:
        content = operation["responses"]["200"]["content"]["application/json"]
    value = content["examples"][name]["value"]
    assert isinstance(value, dict)
    return dict(value)


def without_signed_in_at(body: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in body.items() if k != "signed_in_at"}


class CountingUow:
    """A UnitOfWorkFactory double that counts calls and raises if it is ever used."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, *, write: bool = False, exclusive: bool = False) -> Any:
        self.calls += 1
        raise AssertionError("the unit of work must not be used here")


# -- service builders (lazy imports: the module does not exist before AEA-44) --------------------------------------
def make_store(
    uow: Any, *, secret: SecretStr, demo: Clock | None = None, lifetime_s: int = LIFETIME_S
) -> Any:
    from meridian.services.staff import StaffSessionStore

    return StaffSessionStore(uow, secret, demo if demo is not None else FixedClock(), lifetime_s)


def make_flags(uow: Any, demo: Clock) -> Any:
    from meridian.services.staff import FlagService

    return FlagService(uow, demo)


@contextmanager
def noop() -> Any:
    yield
