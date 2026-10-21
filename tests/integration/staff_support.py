"""AEA-52 helpers: real app on AEA-57's harness; no doubles, no dependency overrides."""

from __future__ import annotations

import hashlib
import secrets
import shutil
import sqlite3
import tempfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from types import MappingProxyType
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from meridian.config import Settings
from meridian.services.reset import SEED_CASES
from meridian.web.container import Container, ContainerError, Key
from tests.fixtures.sqlite import ISSUED_DB
from tests.journeys.support.client import JourneyClient
from tests.journeys.support.db import DbReader, issued_rows, sha256_file
from tests.journeys.support.env import JourneyEnv, journey_environ
from tests.journeys.support.logtap import tap_logs
from tests.journeys.support.run import JourneyRun
from tests.journeys.support.scripted_model import JourneyScript, scripted_overrides
from tests.journeys.support.server import StepClock, launch_server, socket_guard
from tests.journeys.support.steps import StepCollector, blocked_message, missing_needs

CHICAGO = ZoneInfo("America/Chicago")
SEED_REFS: tuple[str, ...] = ("MHC-C-0005", "MHC-C-0006", "MHC-C-0007", "MHC-C-0008")
ISSUED_TABLES: tuple[str, ...] = ("customers", "technicians", "appointment_slots", "appointments", "invoices")
KEPT_TABLES: tuple[str, ...] = (
    "spend_ledger",
    "health_events",
    "deploy_records",
    "eval_runs",
    "job_runs",
    "demo_events",
)
SCHEDULER_JOB: Key[Any] = Key("scheduler_job")  # AEA-30 register_demo
SCHEDULER_THREAD_KEY: Key[Any] = Key("scheduler_thread")  # AEA-30 register_demo -> SchedulerThread
SCHEDULER_THREAD = "meridian-scheduler"  # SchedulerThread's default thread name
OVERDUE_KIND = "overdue"
CLAIM_KIND = "action:claim"  # PROMISE_MISSED_KIND is imported from meridian.services.scheduler
X_ROLES: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "getQueue": ("representative", "supervisor"),
        "getCase": ("representative", "supervisor", "owner"),
        "applyCaseAction": ("representative", "supervisor"),
        "liveChatAction": ("representative",),
        "streamCaseEvents": ("representative", "supervisor", "owner"),
        "recordContactActivity": ("representative",),
        "createFlag": ("representative", "supervisor"),
        "listFlags": ("representative", "supervisor", "owner"),
        "reviewFlag": ("supervisor",),
        "getOversight": ("supervisor",),
        "advanceDemoClock": ("supervisor",),
    }
)
P1_NEEDS = (
    "login_sessions",
    "staff_access",
    "flag_service",
    "case_service",
    "handoff_service",
    "demo_service",
    "demo_clock",
    "live_chat",
    "reset_service",
    "reset_gate",
    "checkpointer",
    "uow_factory",
    "wall_clock",
    "ledger",
)
P1_OPERATIONS = (
    "getSession",
    "switchRole",
    "getQueue",
    "getCase",
    "applyCaseAction",
    "liveChatAction",
    "streamCaseEvents",
    "recordContactActivity",
    "createFlag",
    "listFlags",
    "reviewFlag",
    "getOversight",
    "getStaffing",
    "setStaffing",
    "getDemoClock",
    "advanceDemoClock",
    "resetDemo",
)
DEMO_NEEDS = (
    "login_sessions",
    "staff_access",
    "demo_service",
    "demo_clock",
    "reset_service",
    "reset_gate",
    "checkpointer",
    "uow_factory",
    "wall_clock",
    "ledger",
)  # G0: no AEA-45 object or route
DEMO_OPERATIONS = (
    "getSession",
    "switchRole",
    "getStaffing",
    "setStaffing",
    "getDemoClock",
    "advanceDemoClock",
    "resetDemo",
)


@dataclass(frozen=True)
class Actor:
    client: JourneyClient
    session_id: str
    cookie: str
    role: str


def assert_bound(run: JourneyRun, needs: Sequence[str], operations: Sequence[str]) -> None:
    """Fails (never skips) when a need or route is missing; also checks the scheduler keys AEA-57 does not know."""
    missing = missing_needs(run.container, run.app, needs, operations)
    if missing:
        raise AssertionError(blocked_message(missing))
    for key in (SCHEDULER_JOB, SCHEDULER_THREAD_KEY):
        try:
            run.container.get(key)
        except ContainerError as exc:
            raise AssertionError(f"blocked-on AEA-30: {exc}") from None


def call(
    actor: Actor,
    method: str,
    path: str,
    op: str,
    body: object | None = None,
    headers: Mapping[str, str] | None = None,
) -> httpx.Response:
    return actor.client.call(method, path, operation_id=op, body=body, headers=headers)


def switch_role(actor: Actor, role: str) -> Actor:
    response = call(actor, "PUT", "/api/session/role", "switchRole", {"role": role})
    assert response.status_code == 200, response.text
    assert response.json()["role"] == role
    return Actor(actor.client, actor.session_id, actor.cookie, role)


def sign_in(run: JourneyRun, role: str = "customer") -> Actor:
    logged = run.login()
    actor = Actor(logged.client, logged.session_id, logged.cookie, "customer")
    return actor if role == "customer" else switch_role(actor, role)


def error_of(response: httpx.Response) -> dict[str, Any]:
    error: dict[str, Any] = response.json()["error"]
    return error


def case_view(actor: Actor, ref: str) -> dict[str, Any]:
    response = call(actor, "GET", f"/api/staff/cases/{ref}", "getCase")
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()
    return body


def version_of(actor: Actor, ref: str) -> int:
    return int(case_view(actor, ref)["case"]["version"])


def act(
    actor: Actor, ref: str, action: str, *, version: int | None = None, **fields: object
) -> httpx.Response:
    expected = version if version is not None else version_of(actor, ref)
    body = {"action": action, "expected_version": expected, **fields}
    return call(actor, "POST", f"/api/staff/cases/{ref}/actions", "applyCaseAction", body)


def live(actor: Actor, ref: str, action: str, text: str | None = None) -> httpx.Response:
    body: dict[str, object] = {"action": action}
    if text is not None:
        body["text"] = text
    return call(actor, "POST", f"/api/staff/cases/{ref}/live", "liveChatAction", body)


def set_staffing(actor: Actor, mode: str) -> httpx.Response:
    response = call(actor, "PUT", "/api/demo/staffing", "setStaffing", {"mode": mode})
    assert response.status_code == 200, response.text
    return response


def advance(actor: Actor, step: str) -> httpx.Response:
    return call(actor, "POST", "/api/demo/clock", "advanceDemoClock", {"step": step})


def reset_demo(actor: Actor) -> httpx.Response:
    return call(actor, "POST", "/api/demo/reset", "resetDemo", {"confirm": True})


def parse_dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None, f"naive datetime {value!r}"
    return parsed


def demo_now(actor: Actor) -> datetime:
    response = call(actor, "GET", "/api/demo/clock", "getDemoClock")
    assert response.status_code == 200, response.text
    return parse_dt(response.json()["now"])


def scheduler_job(run: JourneyRun) -> Any:
    return run.container.get(SCHEDULER_JOB)


def _seed_customers(run: JourneyRun) -> list[tuple[Any, ...]]:
    ids = [s.customer_id for s in SEED_CASES if s.customer_id]
    marks = ",".join("?" for _ in ids)
    return [
        tuple(r.values())
        for r in run.db.rows(
            f"SELECT name, phone, email, service_address FROM customers WHERE customer_id IN ({marks})",  # noqa: S608
            ids,
        )
    ]


def seed_contact_values(run: JourneyRun) -> tuple[str, ...]:
    """Phone, email and service address of the seed customers, read from the working copy at run time."""
    return tuple(str(v) for row in _seed_customers(run) for v in row[1:] if v)


def seed_customer_names(run: JourneyRun) -> tuple[str, ...]:
    return tuple(str(row[0]) for row in _seed_customers(run))


def write_working_copy(run: JourneyRun, sql: str, params: Sequence[object] = ()) -> None:
    """Test-only edit of the DISPOSABLE working copy (simulates an outside change). Never the issued file."""
    conn = sqlite3.connect(run.env.db_path, timeout=5.0)
    try:
        conn.execute(sql, tuple(params))
        conn.commit()
    finally:
        conn.close()


def tree_digest(path: Path) -> str:
    if not path.exists():
        return f"missing:{path}"
    digest = hashlib.sha256()
    for item in sorted(p for p in path.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        digest.update(str(item.relative_to(path)).encode())
        digest.update(item.read_bytes())
    return digest.hexdigest()


def sentinel(label: str) -> str:
    return f"aea52-{label}-{secrets.token_hex(8)}"


def card_like_number() -> str:
    digits = "".join(str(secrets.randbelow(10)) for _ in range(16))
    return " ".join(digits[i : i + 4] for i in range(0, 16, 4))


def issued_equal(run: JourneyRun, table: str) -> bool:
    return run.db.table_rows(table) == issued_rows(table)


def one_day_on(clock: StepClock) -> datetime:
    return clock() + timedelta(days=1)


@contextmanager
def open_staff_run(
    *, extra_env: Mapping[str, str] = MappingProxyType({}), strict: bool, nodeid: str
) -> Iterator[JourneyRun]:
    """`open_journey` with an environment extension: the server stops inside the `with`, key sentinels can be set."""
    with socket_guard() as guard, tap_logs() as logs:
        root = Path(tempfile.mkdtemp(prefix="meridian-aea52-"))
        try:
            for name in ("data", "no-dist", "index"):
                (root / name).mkdir()
            settings = Settings.from_env({**journey_environ(root), **extra_env})
            if Path(settings.issued_db_path).resolve() != ISSUED_DB.resolve():
                raise RuntimeError(
                    "journey harness: run pytest from the repository root (Settings.issued_db_path resolves elsewhere)"
                )
            before = sha256_file(ISSUED_DB)
            env = JourneyEnv(root, root / "data", root / "no-dist", root / "index", settings, before)
            script = JourneyScript()
            clock = StepClock()
            overrides, models = scripted_overrides(settings, script, wall_clock=clock)
            with launch_server(settings, overrides=overrides) as server:
                run = JourneyRun(
                    env=env,
                    server=server,
                    script=script,
                    models=models,
                    clock=clock,
                    db=DbReader(env.db_path),
                    logs=logs,
                    guard=guard,
                    collector=StepCollector(),
                    strict=strict,
                    nodeid=nodeid,
                )
                try:
                    yield run
                finally:
                    run.close_clients()
            assert sha256_file(ISSUED_DB) == before, "the issued scheduling DB changed"
        finally:
            shutil.rmtree(root, ignore_errors=True)
    assert not guard.blocked, f"socket guard refused {guard.blocked}"


__all__ = ["Container"]
