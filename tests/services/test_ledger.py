"""LedgerService and SpendRepo (AEA-26; stage7/models.md section 6). Synthetic data only; no model call."""

from __future__ import annotations

import datetime as dt
import inspect
import logging
import sqlite3
import threading
import uuid
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo

import pytest

from meridian.adapters.sqlite.repos_spend import SpendRepo
from meridian.domain.common import ProviderFailure, ProviderFailureKind
from meridian.domain.turn import TurnIds
from meridian.policy.limits import Limits
from meridian.ports.models import CallRecord, Role
from meridian.services.ledger import CallAdmission, LedgerService, SpendGuard
from tests.fixtures.sqlite import TempStore, temp_sqlite

CHI = ZoneInfo("America/Chicago")
RETRYABLE = {
    ProviderFailureKind.TIMEOUT,
    ProviderFailureKind.CONNECTION,
    ProviderFailureKind.RATE_LIMITED,
    ProviderFailureKind.OVERLOADED,
    ProviderFailureKind.SERVER,
}
CAP_KINDS = {ProviderFailureKind.PROVIDER_SPEND_CAP, ProviderFailureKind.OUR_SPEND_LIMIT}
SEED_KEY = "-".join(["sk", "ant", "api03", "SEEDONLY", "Z" * 24])
SEED_SENTENCE = "My furnace at 4417 Pecan Hollow smells like gas, call me back"


class FakeWall:
    def __init__(self, now: dt.datetime) -> None:
        self.now = now

    def __call__(self) -> dt.datetime:
        return self.now


class FakeMono:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


def chi(y: int, mo: int, d: int, h: int = 0, mi: int = 0, s: int = 0) -> dt.datetime:
    return dt.datetime(y, mo, d, h, mi, s, tzinfo=CHI)


def utc(y: int, mo: int, d: int, h: int = 0, mi: int = 0, s: int = 0) -> dt.datetime:
    return dt.datetime(y, mo, d, h, mi, s, tzinfo=dt.UTC)


def make_ids(tag: str = "live", thread: str | None = None) -> TurnIds:
    return TurnIds.model_validate(
        {
            "thread_id": thread or str(uuid.uuid4()),
            "turn_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),
            "run_tag": tag,
            "run_id": None,
            "agent_version": "test-agent-0",
        }
    )


def make_failure(
    kind: ProviderFailureKind, provider: str = "anthropic", http_status: int | None = 429
) -> ProviderFailure:
    return ProviderFailure.model_validate(
        {
            "kind": kind,
            "provider": provider,
            "http_status": http_status,
            "retry_after_s": None,
            "retryable": kind in RETRYABLE,
            "provider_request_id": "req_test_0001",
        }
    )


def make_call(
    *,
    cost: float,
    provider: str = "anthropic",
    role: Role = Role.RESPONDER,
    attempt: int = 1,
    failure: ProviderFailure | None = None,
) -> CallRecord:
    return CallRecord.model_validate(
        {
            "provider": provider,
            "model": "claude-sonnet-test" if provider == "anthropic" else "test/jev-model",
            "latency_ms": 1200,
            "input_tokens": 9000,
            "output_tokens": 700,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "thinking_tokens": 0,
            "cost_usd": cost,
            "cost_source": "price_table",
            "status": "ok" if failure is None else "error",
            "failure": failure,
            "provider_request_id": "req_test_0001",
            "stop_reason": "end_turn" if failure is None else None,
            "role": role,
            "attempt": attempt,
        }
    )


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


def raw(store: TempStore, sql: str) -> list[tuple[object, ...]]:
    conn = sqlite3.connect(store.db_path)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def ledger_for(
    store: TempStore, wall: FakeWall, *, cap: float = 1000.0, mono: FakeMono | None = None
) -> LedgerService:
    return LedgerService(store.uow, wall_clock=wall, daily_cap_usd=cap, monotonic=mono or FakeMono())


def test_record_one_row_per_attempt_including_failures(store: TempStore) -> None:
    wall = FakeWall(chi(2026, 10, 21, 14, 0, 0))
    ledger = ledger_for(store, wall)
    ids = make_ids()
    ok = make_call(cost=0.25, attempt=1)
    err = make_call(cost=0.0, attempt=2, failure=make_failure(ProviderFailureKind.PROVIDER_SPEND_CAP))
    ledger.record(ok, ids)
    ledger.record(err, ids)

    assert raw(store, "SELECT COUNT(*) FROM spend_ledger") == [(2,)]
    columns = {r[1] for r in raw(store, "PRAGMA table_info(spend_ledger)")}
    print(sorted(str(c) for c in columns))
    assert columns == {
        "id", "recorded_at", "thread_id", "turn_id", "request_id", "run_tag", "run_id", "agent_version",
        "role", "provider", "model", "attempt", "latency_ms", "input_tokens", "output_tokens",
        "cache_read_tokens", "cache_write_tokens", "thinking_tokens", "cost_usd", "cost_source", "status",
        "failure_kind", "http_status", "provider_request_id", "stop_reason",
    }  # fmt: skip
    stamps = raw(store, "SELECT recorded_at FROM spend_ledger ORDER BY id")
    assert stamps == [("2026-10-21T19:00:00+00:00",)] * 2
    assert raw(store, "SELECT failure_kind, http_status FROM spend_ledger ORDER BY id")[0] == (None, None)

    with store.uow() as tx:
        rows = tx.spend.for_turn(ids.turn_id)
    assert len(rows) == 2
    assert rows[0].id is not None and rows[1].id is not None and rows[0].id < rows[1].id
    for row, original in zip(rows, (ok, err), strict=True):
        got = CallRecord.model_validate({k: getattr(row, k) for k in CallRecord.model_fields})
        assert got == original
        for field in ("thread_id", "turn_id", "request_id", "run_tag", "run_id", "agent_version"):
            assert getattr(row, field) == getattr(ids, field)
    assert rows[1].failure is not None
    assert rows[1].failure.kind is ProviderFailureKind.PROVIDER_SPEND_CAP
    assert rows[1].failure.http_status == 429
    assert rows[0].failure is None


def test_spend_today_is_the_chicago_day(store: TempStore) -> None:
    wall = FakeWall(chi(2026, 10, 21))
    ledger = ledger_for(store, wall)
    plan = [
        (chi(2026, 10, 20, 23, 59, 59), 1.0, "live"),
        (chi(2026, 10, 21, 0, 0, 0), 2.0, "eval"),
        (chi(2026, 10, 21, 18, 59, 59), 4.0, "load"),
        (chi(2026, 10, 21, 19, 0, 0), 8.0, "live"),
        (chi(2026, 10, 21, 23, 59, 59), 16.0, "eval"),
        (chi(2026, 10, 22, 0, 0, 0), 32.0, "live"),
    ]
    for when, cost, tag in plan:
        wall.now = when
        ledger.record(make_call(cost=cost), make_ids(tag))
    wall.now = chi(2026, 10, 21, 12)
    assert ledger.spend_today() == 30.0
    wall.now = chi(2026, 10, 20, 12)
    assert ledger.spend_today() == 1.0
    wall.now = chi(2026, 10, 22, 12)
    assert ledger.spend_today() == 32.0


def test_spend_day_across_dst_end(store: TempStore) -> None:
    wall = FakeWall(utc(2026, 11, 1, 12))
    ledger = ledger_for(store, wall)
    plan = [
        (utc(2026, 11, 1, 4, 59, 59), 1.0),
        (utc(2026, 11, 1, 5, 0, 0), 2.0),
        (utc(2026, 11, 1, 6, 30, 0), 4.0),
        (utc(2026, 11, 1, 7, 30, 0), 8.0),
        (utc(2026, 11, 2, 5, 30, 0), 16.0),
        (utc(2026, 11, 2, 6, 0, 0), 32.0),
    ]
    for when, cost in plan:
        wall.now = when
        ledger.record(make_call(cost=cost), make_ids())
    for now, expected in [
        (utc(2026, 11, 1, 18), 30.0),
        (utc(2026, 11, 2, 5, 59, 59), 30.0),
        (utc(2026, 11, 2, 6, 0, 0), 32.0),
        (utc(2026, 11, 1, 4), 1.0),
    ]:
        wall.now = now
        assert ledger.spend_today() == expected


def test_allow_turn_at_cap_and_overrun_recorded(store: TempStore) -> None:
    cap = Limits().spend.daily_cap_usd
    wall = FakeWall(chi(2026, 10, 21, 14))
    ledger = ledger_for(store, wall, cap=cap)
    ledger.record(make_call(cost=29.98), make_ids())
    assert ledger.allow_turn() is True
    ledger.record(make_call(cost=0.039), make_ids())
    assert raw(store, "SELECT COUNT(*) FROM spend_ledger") == [(2,)]
    assert ledger.spend_today() == pytest.approx(30.019)
    assert ledger.allow_turn() is False
    ledger.record(make_call(cost=0.01), make_ids())
    assert raw(store, "SELECT COUNT(*) FROM spend_ledger") == [(3,)]

    with temp_sqlite() as other:
        small = ledger_for(other, FakeWall(chi(2026, 10, 21, 14)), cap=5.0)
        small.record(make_call(cost=2.5), make_ids())
        small.record(make_call(cost=2.0), make_ids())
        assert small.allow_turn() is True
        small.record(make_call(cost=0.5), make_ids())
        assert small.allow_turn() is False


def test_allow_turn_releases_at_chicago_midnight(store: TempStore) -> None:
    wall = FakeWall(chi(2026, 10, 21, 9))
    ledger = ledger_for(store, wall, cap=1.0)
    ledger.record(make_call(cost=1.0), make_ids())
    wall.now = chi(2026, 10, 21, 23, 59)
    assert ledger.allow_turn() is False
    wall.now = chi(2026, 10, 22, 0, 0)
    assert ledger.allow_turn() is True
    assert raw(store, "SELECT COUNT(*) FROM spend_ledger") == [(1,)]


def test_provider_circuit_probe_cycle(store: TempStore) -> None:
    mono = FakeMono(1000.0)
    ledger = ledger_for(store, FakeWall(chi(2026, 10, 21, 14)), mono=mono)
    cap = make_failure(ProviderFailureKind.PROVIDER_SPEND_CAP)
    ledger.trip_provider_cap(cap)
    for t, expected in [
        (1540, CallAdmission.REFUSE),
        (1600, CallAdmission.PROBE),
        (1600, CallAdmission.REFUSE),
    ]:
        mono.t = t
        assert ledger.admit_call("anthropic") is expected, t
    ledger.close_provider_cap("anthropic")
    assert ledger.admit_call("anthropic") is CallAdmission.ALLOW
    assert ledger.open_circuits() == ()

    mono.t = 2000
    ledger.trip_provider_cap(cap)
    steps = [
        (2600, CallAdmission.PROBE),
    ]
    for t, expected in steps:
        mono.t = t
        assert ledger.admit_call("anthropic") is expected, t
    mono.t = 2605
    ledger.trip_provider_cap(cap)  # the probe met the cap again: new trip time, no probe in flight
    for t, expected in [
        (3204, CallAdmission.REFUSE),
        (3205, CallAdmission.PROBE),
        (3265, CallAdmission.REFUSE),
        (3266, CallAdmission.PROBE),
        (3266, CallAdmission.REFUSE),
    ]:
        mono.t = t
        assert ledger.admit_call("anthropic") is expected, t


@pytest.mark.parametrize("kind", list(ProviderFailureKind), ids=lambda k: k.value)
def test_trip_by_kind_and_per_provider(store: TempStore, kind: ProviderFailureKind) -> None:
    assert len(list(ProviderFailureKind)) == 14
    ledger = ledger_for(store, FakeWall(chi(2026, 10, 21, 14)))
    ledger.trip_provider_cap(make_failure(kind, "anthropic"))
    if kind in CAP_KINDS:
        assert ledger.admit_call("anthropic") is CallAdmission.REFUSE
        assert ledger.open_circuits() == ("anthropic",)
    else:
        assert ledger.admit_call("anthropic") is CallAdmission.ALLOW
        assert ledger.open_circuits() == ()
    assert ledger.admit_call("openrouter_jev") is CallAdmission.ALLOW


def test_circuit_not_released_by_midnight_and_not_persisted(store: TempStore) -> None:
    wall = FakeWall(chi(2026, 10, 21, 23, 55))
    mono = FakeMono(1000.0)
    ledger = ledger_for(store, wall, cap=1000.0, mono=mono)
    ids = make_ids()
    f = make_failure(ProviderFailureKind.PROVIDER_SPEND_CAP)
    ledger.record(make_call(cost=0.0, failure=f), ids)
    ledger.trip_provider_cap(f)
    wall.now = chi(2026, 10, 22, 0, 0, 1)
    mono.t = 1360
    assert ledger.admit_call("anthropic") is CallAdmission.REFUSE
    assert ledger.allow_turn() is True

    fresh = LedgerService(store.uow, wall_clock=wall, daily_cap_usd=1000.0, monotonic=mono)
    assert fresh.open_circuits() == ()
    assert fresh.admit_call("anthropic") is CallAdmission.ALLOW
    with store.uow() as tx:
        rows = tx.spend.for_turn(ids.turn_id)
    assert len(rows) == 1
    assert rows[0].failure is not None
    assert rows[0].failure.kind is ProviderFailureKind.PROVIDER_SPEND_CAP


def test_models_disabled_either_cause(store: TempStore) -> None:
    wall = FakeWall(chi(2026, 10, 21, 14))
    cap_failure = make_failure(ProviderFailureKind.PROVIDER_SPEND_CAP)

    a = ledger_for(store, wall, cap=1.0)
    assert a.models_disabled() is False
    assert a.allow_turn() is True

    b = ledger_for(store, wall, cap=1.0)
    b.trip_provider_cap(cap_failure)
    assert b.models_disabled() is True
    assert b.allow_turn() is True

    b.record(make_call(cost=1.0), make_ids())

    c = ledger_for(store, wall, cap=1.0)
    assert c.models_disabled() is True
    assert c.allow_turn() is False

    d = ledger_for(store, wall, cap=1.0)
    d.trip_provider_cap(cap_failure)
    assert d.models_disabled() is True


def test_concurrent_records_all_written(store: TempStore) -> None:
    ledger = ledger_for(store, FakeWall(chi(2026, 10, 21, 14)))
    ids = make_ids()
    barrier = threading.Barrier(20)

    def work(i: int) -> None:
        barrier.wait()
        ledger.record(make_call(cost=0.25 * (i + 1)), ids)

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = [pool.submit(work, i) for i in range(20)]
        for f in futures:
            f.result()
    with store.uow() as tx:
        assert len(tx.spend.for_turn(ids.turn_id)) == 20
    assert ledger.spend_today() == 52.5


def test_spend_repo_append_only_and_spend_guard(store: TempStore) -> None:
    public = {n for n, _ in inspect.getmembers(SpendRepo, inspect.isfunction) if not n.startswith("_")}
    assert public == {"append", "total_between", "for_turn"}
    ledger = ledger_for(store, FakeWall(chi(2026, 10, 21, 14)))
    assert isinstance(ledger, SpendGuard)
    assert not isinstance(object(), SpendGuard)


def test_rows_and_logs_hold_allow_listed_fields_only(
    store: TempStore, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    mono = FakeMono(1000.0)
    ledger = ledger_for(store, FakeWall(chi(2026, 10, 21, 14)), mono=mono)
    f = make_failure(ProviderFailureKind.PROVIDER_SPEND_CAP)
    try:
        raise RuntimeError(f"{SEED_KEY} {SEED_SENTENCE}")
    except RuntimeError:
        ledger.record(make_call(cost=0.0, failure=f), make_ids())
        ledger.trip_provider_cap(f)
    mono.t = 1700
    ledger.admit_call("anthropic")
    ledger.close_provider_cap("anthropic")

    table = "\n".join(repr(r) for r in raw(store, "SELECT * FROM spend_ledger"))
    assert SEED_KEY not in table and SEED_SENTENCE not in table
    print(caplog.text)
    assert "provider_circuit_open" in caplog.text
    assert SEED_KEY not in caplog.text and SEED_SENTENCE not in caplog.text
    assert set(inspect.signature(LedgerService.__init__).parameters) == {
        "self", "uow", "wall_clock", "daily_cap_usd", "probe_after_s", "monotonic", "probe_lost_after_s",
    }  # fmt: skip


def test_rows_queryable_by_turn_and_thread(store: TempStore) -> None:
    ledger = ledger_for(store, FakeWall(chi(2026, 10, 21, 14)))
    x, y = str(uuid.uuid4()), str(uuid.uuid4())
    ids_a = make_ids("eval", x)
    ids_b = make_ids("live", y)
    ledger.record(
        make_call(cost=0.25, attempt=1, failure=make_failure(ProviderFailureKind.RATE_LIMITED)), ids_a
    )
    ledger.record(make_call(cost=0.5, attempt=2), ids_a)
    ledger.record(make_call(cost=1.0), ids_b)
    with store.uow() as tx:
        assert [r.attempt for r in tx.spend.for_turn(ids_a.turn_id)] == [1, 2]
        assert len(tx.spend.for_turn(ids_b.turn_id)) == 1
    grouped = raw(
        store,
        "SELECT thread_id, run_tag, SUM(cost_usd), COUNT(*) FROM spend_ledger GROUP BY thread_id, run_tag",
    )
    assert {(r[0], r[1]): (r[2], r[3]) for r in grouped} == {(x, "eval"): (0.75, 2), (y, "live"): (1.0, 1)}


def test_example_pair_cap_overrun_midnight_and_probe(store: TempStore) -> None:
    wall = FakeWall(chi(2026, 10, 21, 14, 0))
    mono = FakeMono(0.0)
    ledger = ledger_for(store, wall, cap=Limits().spend.daily_cap_usd, mono=mono)
    ledger.record(make_call(cost=29.98), make_ids())
    assert ledger.allow_turn() is True
    turn = make_ids()
    for role in (Role.PLANNER, Role.SPECIALIST, Role.RESPONDER):
        ledger.record(make_call(cost=0.013, role=role), turn)
    assert raw(store, "SELECT COUNT(*) FROM spend_ledger") == [(4,)]
    assert ledger.allow_turn() is False
    wall.now = chi(2026, 10, 22, 0, 0)
    assert ledger.allow_turn() is True

    ledger.trip_provider_cap(make_failure(ProviderFailureKind.PROVIDER_SPEND_CAP, http_status=429))
    mono.t = 599
    assert ledger.admit_call("anthropic") is CallAdmission.REFUSE
    mono.t = 600
    assert ledger.admit_call("anthropic") is CallAdmission.PROBE
    ledger.close_provider_cap("anthropic")
    assert ledger.admit_call("anthropic") is CallAdmission.ALLOW


def test_naive_wall_clock_rejected(store: TempStore) -> None:
    ledger = ledger_for(store, FakeWall(dt.datetime(2026, 10, 21, 14, 0)))
    with pytest.raises(ValueError):
        ledger.spend_today()
    with pytest.raises(ValueError):
        ledger.record(make_call(cost=1.0), make_ids())
    assert raw(store, "SELECT COUNT(*) FROM spend_ledger") == [(0,)]
