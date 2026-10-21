"""Helpers for the AEA-32 ops tests (not collected by pytest). Synthetic values only; no literal phone or secret."""

from __future__ import annotations

import itertools
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI

from meridian.adapters.sqlite.db import format_wall
from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.config import Settings
from meridian.domain.common import ThreadId
from meridian.policy.limits import Limits
from meridian.services.health import AlertEvaluator, AlertSettings
from meridian.web import deps
from meridian.web.app import ContainerOverrides, create_app
from meridian.web.container import Container, Key, register_ops, register_web
from tests.fixtures.sqlite import TempStore
from tests.unit.adapters.sqlite.helpers import conversation, new_thread

CHI = ZoneInfo("America/Chicago")
_SEQ = itertools.count(1)


def chi(y: int, mo: int, d: int, h: int, mi: int = 0) -> datetime:
    return datetime(y, mo, d, h, mi, tzinfo=CHI)


BASE = chi(2026, 10, 21, 14, 0)


class FakeWall:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class LedgerDouble:
    def __init__(self, spent: float = 0.0) -> None:
        self.spent = spent

    def spend_today(self) -> float:
        return self.spent


class EvaluatorDouble:
    def __init__(self) -> None:
        self.calls = 0

    def evaluate(self) -> tuple[()]:
        self.calls += 1
        return ()


class ProbeDouble:
    def __init__(self, answers: list[bool | Exception]) -> None:
        self._answers = list(answers)

    def __call__(self) -> bool:
        item = self._answers.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def sentinel() -> str:
    return "sentinel-" + uuid.uuid4().hex


def make_settings(data_dir: Path) -> Settings:
    return Settings.model_validate(
        {
            "anthropic_api_key": sentinel(),
            "openrouter_api_key": sentinel(),
            "demo_username": sentinel(),
            "demo_password": sentinel(),
            "session_secret": sentinel(),
            "data_dir": data_dir,
            "agent_version": "test-ops",
        }
    )


def make_evaluator(
    store: TempStore, wall: FakeWall, ledger: LedgerDouble | None = None, cap: float | None = None
) -> AlertEvaluator:
    return AlertEvaluator(
        store.uow,
        ledger or LedgerDouble(),
        AlertSettings(),
        wall,
        Limits().spend.daily_cap_usd if cap is None else cap,
        agent_version="test-ops",
    )


def add_conversation(store: TempStore, *, run_tag: str, started_wall_at: datetime) -> ThreadId:
    thread = new_thread()
    with store.uow(write=True) as tx:
        tx.core.conversations.insert(conversation(thread, run_tag=run_tag, started_wall_at=started_wall_at))
        tx.commit()
    return thread


def add_turn(
    store: TempStore,
    thread_id: ThreadId,
    *,
    run_tag: str,
    replied_at: datetime,
    server_ms: int | None = 4000,
    status: str = "completed",
    outcome: str = "answered",
    degrade_reason: str | None = None,
    trace_export: str | None = "sent",
) -> str:
    turn_id = str(uuid.uuid4())
    with store.uow(write=True) as tx:
        tx.connection.execute(
            "INSERT INTO turns (turn_id, thread_id, request_id, run_tag, agent_version, sequence, received_at, "
            "status, outcome, degrade_reason, replied_at, server_ms, trace_export) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                turn_id,
                str(thread_id),
                str(uuid.uuid4()),
                run_tag,
                "test-ops",
                next(_SEQ),
                format_wall(DEMO_START),
                status,
                outcome,
                degrade_reason,
                format_wall(replied_at),
                server_ms,
                trace_export,
            ),
        )
        tx.commit()
    return turn_id


def add_live_turns(store: TempStore, n: int, *, replied_at: datetime, **kw: Any) -> None:
    thread = add_conversation(store, run_tag="live", started_wall_at=replied_at - timedelta(minutes=30))
    for _ in range(n):
        add_turn(store, thread, run_tag="live", replied_at=replied_at, **kw)


def add_message(store: TempStore, thread_id: ThreadId, text: str) -> None:
    with store.uow(write=True) as tx:
        tx.connection.execute(
            "INSERT INTO messages (thread_id, role, text, at) VALUES (?, 'customer', ?, ?)",
            (str(thread_id), text, format_wall(DEMO_START)),
        )
        tx.commit()


def ops_rows(store: TempStore) -> list[str]:
    out: list[str] = []
    with store.uow() as tx:
        for table in ("health_events", "deploy_records", "eval_runs", "eval_case_results"):
            # table names are constants above
            for row in tx.connection.execute(f"SELECT * FROM {table}"):  # noqa: S608
                out.append(json.dumps(list(row), default=str))
    return out


def health_rows(store: TempStore, kind: str | None = None) -> list[tuple[str, str | None, str | None]]:
    with store.uow() as tx:
        rows = tx.connection.execute(
            "SELECT kind, alert_type, reason_code FROM health_events ORDER BY id"
        ).fetchall()
    return [(r[0], r[1], r[2]) for r in rows if kind is None or r[0] == kind]


def build_ops_app(
    monkeypatch: pytest.MonkeyPatch,
    *,
    store: TempStore,
    settings: Settings,
    wall: FakeWall,
    ledger: LedgerDouble,
) -> FastAPI:
    def build(app: FastAPI, cfg: Any, *, overrides: Any = None) -> Container:
        c = Container(settings=cfg, limits=Limits())
        c.provide(deps.UOW_FACTORY, lambda _c: store.uow)
        c.provide(Key[object]("ledger"), lambda _c: ledger)
        register_web(c, app, settings=cfg, limits=c.limits)
        register_ops(c, app, settings=cfg, limits=c.limits)
        c.build()
        return c

    monkeypatch.setattr(Container, "on_start", lambda self, starter: None)
    monkeypatch.setattr("meridian.web.app.build_container", build)
    return create_app(settings, overrides=ContainerOverrides(wall_clock=wall))
