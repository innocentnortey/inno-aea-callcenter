"""AEA-53: the real MetricsReader behind AEA-48's routes, through the app the real container builds (level: mock-tested,
in process, no server). Seam 1 (routes -> reader) and seam 2 (CON-18 role check -> StaffSessionStore)."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

import meridian.checks as checks_module
import meridian.gates.gate as gate_module
import meridian.gates.rules as rules_module
import meridian.policy.booking as booking_module
import meridian.policy.escalation as escalation_module
import meridian.policy.handoff as handoff_module
from meridian.agent.gateway import ModelGateway
from meridian.ports.runtime import UnitOfWork
from meridian.services.health import AlertSettings
from meridian.services.ledger import LedgerService
from meridian.services.metrics_reader import MetricsReader
from meridian.web.container import Key
from meridian.web.deps import METRICS_READS
from tests.api.reads_support import OPERATIONS, get_read
from tests.api.staff_session_support import container_app, login_token, switch, tab
from tests.api.web_shell_support import assert_matches, error_body, make_client
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import temp_sqlite
from tests.unit.services.test_metrics_reader_rows import (
    WALL_NOW,
    WallClock,
    seed_j10_rows,
)


def test_reader_bound_and_access(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    h = container_app(monkeypatch, tmp_path)
    table: dict[str, dict[str, int]] = {}
    with make_client(h.app) as client:
        bound = h.app.state.container.get(METRICS_READS)
        print("bound class:", type(bound).__name__)
        assert isinstance(bound, MetricsReader)
        for op in OPERATIONS:
            error_body(get_read(client, op), 401, "UNAUTHENTICATED")
        token = login_token(client, h.settings)
        for role in ("customer", "representative", "supervisor", "owner"):
            if role != "customer":
                assert switch(client, token, role).status_code == 200
            table[role] = {}
            for op in OPERATIONS:
                response = get_read(client, op, tab(token))
                table[role][op] = response.status_code
                if op == "getOwnerMetrics" and role in ("customer", "representative"):
                    error_body(response, 403, "ROLE_NOT_ALLOWED")
                else:
                    assert response.status_code == 200, response.text
                    assert_matches(response, op)
    for role, statuses in table.items():
        print(role, statuses)
    assert table["customer"] == {"getOwnerMetrics": 403, "getMonitoring": 200, "getLatestEval": 200}
    assert table["representative"] == table["customer"]
    assert set(table["supervisor"].values()) == set(table["owner"].values()) == {200}


class RecordingUow:
    """Wraps a UnitOfWorkFactory and records (write, exclusive) for every call."""

    def __init__(self, inner: Callable[..., AbstractContextManager[UnitOfWork]]) -> None:
        self._inner = inner
        self.calls: list[tuple[bool, bool]] = []

    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]:
        self.calls.append((write, exclusive))
        return self._inner(write=write, exclusive=exclusive)


def refuse_everything(monkeypatch: pytest.MonkeyPatch) -> int:
    """Patch every public function of the gate, check and policy modules and every ModelGateway method to raise."""

    def raiser(*_a: Any, **_k: Any) -> None:
        raise AssertionError("the reader must not recompute an outcome")

    patched = 0
    modules: tuple[ModuleType, ...] = (
        gate_module, rules_module, checks_module, handoff_module, escalation_module, booking_module,
    )  # fmt: skip
    for module in modules:
        for name, obj in list(vars(module).items()):
            if not name.startswith("_") and inspect.isfunction(obj) and obj.__module__ == module.__name__:
                monkeypatch.setattr(module, name, raiser)
                patched += 1
    for name, obj in list(vars(ModelGateway).items()):
        if not name.startswith("_") and inspect.isfunction(obj):
            monkeypatch.setattr(ModelGateway, name, raiser)
            patched += 1
    return patched


def test_reader_never_recomputes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # (a) store level: only read units of work, patched gates, checks, policy and models
    with temp_sqlite() as store:
        wall = WallClock(WALL_NOW)
        ledger_uow = RecordingUow(store.uow)
        ledger = LedgerService(ledger_uow, wall_clock=wall, daily_cap_usd=30.0)
        seed_j10_rows(store.uow, ledger, with_seed=False)
        ledger_uow.calls.clear()
        reader_uow = RecordingUow(store.uow)
        reader = MetricsReader(reader_uow, FixedClock(), wall, ledger, AlertSettings(), "agent-test", 30.0)
        with monkeypatch.context() as patch:
            print("patched callables:", refuse_everything(patch))
            owner: Any = reader.owner_metrics()
            reader.monitoring()
            reader.latest_eval()
        assert reader_uow.calls and ledger_uow.calls
        assert set(reader_uow.calls) == set(ledger_uow.calls) == {(False, False)}
        with store.uow() as tx:
            abandoned_sql = tx.connection.execute(
                "SELECT COUNT(*) FROM conversations WHERE run_tag IN ('live','seed') AND outcome = 'abandoned'"
            ).fetchone()[0]
        abandoned = next(m for m in owner["outcomes"] if m["label"] == "Abandoned")
        assert abandoned["numerator"] == abandoned_sql == 1  # the idle open conversation is not re-judged
        assert owner["in_scope_correct_resolution"]["numerator"] == 1  # the flagged one is dropped
    # (b) app level: the same patches applied after the lifespan started
    h = container_app(monkeypatch, tmp_path)
    with make_client(h.app) as client:
        ledger_b = h.app.state.container.get(Key[Any]("ledger"))
        seed_j10_rows(h.uow, ledger_b, with_seed=True)
        token = login_token(client, h.settings)
        assert switch(client, token, "owner").status_code == 200
        with monkeypatch.context() as patch:
            refuse_everything(patch)
            for op in OPERATIONS:
                response = get_read(client, op, tab(token))
                assert response.status_code == 200, response.text
