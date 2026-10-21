"""MetricsReader unit tests (AEA-53): units, keys, the fixed tile list, worked pairs, latency, the eval projection.
Every output is validated with AEA-48's route models."""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from meridian.domain.common import HandoffReason
from meridian.services._case_rules import reason_label
from meridian.services.health import AlertSettings, load_eval_reports, p95_nearest_rank
from meridian.services.ledger import LedgerService
from meridian.services.metrics_reader import EVAL_RUN_KEYS, MetricsReader
from meridian.web.schemas.reads import EvalResponse, MonitoringResponse, OwnerMetricsResponse
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.unit.services.test_metrics_reader_rows import (
    WALL_NOW,
    LedgerDouble,
    Pages,
    WallClock,
    add_conversation,
    add_turn,
    seed_j10_rows,
    write_eval_reports,
)

EXPECTED_TILES = [
    ("M-22", "Conversations", "count"),
    ("M-22", "Turns", "count"),
    ("M-24", "Failures", "count"),
    ("M-23", "Latency p50", "ms"),
    ("M-23", "Latency p95", "ms"),
    ("scheduler_last_run", "Overdue job last ran", "ms"),
    ("handoff_only", "Handoff-only mode (1 = on)", "count"),
]


def reader_for(store: TempStore, ledger: Any = None) -> Pages:
    return Pages(
        MetricsReader(
            store.uow,
            FixedClock(),
            WallClock(WALL_NOW),
            ledger or LedgerDouble(),
            AlertSettings(),
            "agent-test",
            30.0,
        )
    )


def pages(reader: Pages) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    owner, monitoring, latest = reader.owner_metrics(), reader.monitoring(), reader.latest_eval()
    OwnerMetricsResponse.model_validate(owner)
    MonitoringResponse.model_validate(monitoring)
    EvalResponse.model_validate(latest)
    return owner, monitoring, latest


def seeded(store: TempStore, tmp_path: Path) -> Pages:
    ledger = LedgerService(store.uow, wall_clock=WallClock(WALL_NOW), daily_cap_usd=30.0)
    seed_j10_rows(store.uow, ledger, with_seed=True)
    write_eval_reports(tmp_path / "reports", agent_version="agent-test")
    load_eval_reports(tmp_path / "reports", store.uow)
    return reader_for(store, ledger)


def owner_measures(owner: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        owner["in_scope_correct_resolution"],
        owner["promises_kept_on_time"],
        owner["handoffs"],
        *owner["outcomes"],
        *owner["handoffs_by_reason"],
    ]


def test_units_and_scales(tmp_path: Path) -> None:
    with temp_sqlite() as store:
        owner, monitoring, latest = pages(seeded(store, tmp_path))
    items = [
        *owner_measures(owner),
        *monitoring["health"],
        monitoring["correctness"]["containment_estimate"],
        *monitoring["correctness"]["escalations_by_reason"],
    ]
    units = {m["unit"] for m in items}
    shares = [m["value"] for m in items if m["unit"] == "share" and m["value"] is not None]
    print("units:", sorted(units), "share min/max:", min(shares), max(shares))
    assert units <= {"count", "ms", "share"}
    assert all(0 <= v <= 1 for v in shares)
    for m in items:
        if m["unit"] == "share" and m["value"] is not None:
            assert m["value"] == m["numerator"] / m["denominator"]
    for run in latest["splits"].values():
        assert run is not None
        assert all(0 <= m["value"] <= 1 for m in run["measures"])
    failures = next(t for t in monitoring["health"] if t["id"] == "M-24")
    assert failures["unit"] == "count"
    assert failures["numerator"] is not None and failures["denominator"] is not None


def test_measure_keys_unique(tmp_path: Path) -> None:
    with temp_sqlite() as store:
        owner, monitoring, latest = pages(seeded(store, tmp_path))
    groups = {
        "owner": [(m["id"], m["label"]) for m in owner_measures(owner)],
        "monitoring": [
            (t["id"], t["label"])
            for t in (
                *monitoring["health"],
                monitoring["correctness"]["containment_estimate"],
                *monitoring["correctness"]["escalations_by_reason"],
            )
        ],
    }
    for split, run in latest["splits"].items():
        groups[f"eval-{split}"] = [(m["id"], m["label"]) for m in run["measures"]]
    duplicates = sum(len(pairs) - len(set(pairs)) for pairs in groups.values())
    print("duplicate (id, label) pairs:", duplicates)
    assert duplicates == 0
    for key in ("owner", "monitoring"):
        for mid, _label in groups[key]:
            assert re.fullmatch(r"M-\d+", mid) or mid in {"scheduler_last_run", "handoff_only"}
    stored = {
        m["id"] for run in latest["splits"].values() for m in run["measures"]
    }  # pass-through of the stored ids
    assert stored == {"M-1", "M-1:billing", "M-19", "M-2", "M-4"}


def test_health_tiles_fixed_list(tmp_path: Path) -> None:
    with temp_sqlite() as store:
        empty = [(t["id"], t["label"], t["unit"]) for t in reader_for(store).monitoring()["health"]]
        print("empty:", empty)
    with temp_sqlite() as store:
        full = [(t["id"], t["label"], t["unit"]) for t in seeded(store, tmp_path).monitoring()["health"]]
        print("seeded:", full)
    assert empty == EXPECTED_TILES
    assert full == EXPECTED_TILES


def test_worked_pairs_wp2_wp5_wp7_counted() -> None:
    with temp_sqlite() as store:
        ledger = LedgerService(store.uow, wall_clock=WallClock(WALL_NOW), daily_cap_usd=30.0)
        rows = seed_j10_rows(store.uow, ledger, with_seed=False)
        owner, monitoring, _ = pages(reader_for(store, ledger))
        spent_cents = round(ledger.spend_today() * 100)
    turns = next(t for t in monitoring["health"] if t["label"] == "Turns")
    assert turns["value"] == 6  # WP-2 (2), WP-5, WP-7, the failure turn, the flagged turn
    safety = next(
        t
        for t in monitoring["correctness"]["escalations_by_reason"]
        if t["label"] == reason_label(HandoffReason.SAFETY)
    )
    assert safety["value"] == 1
    refund = next(m for m in owner["handoffs_by_reason"] if m["label"] == "Refund request")
    assert refund["case_refs"] == [str(rows.wp7_case)]
    assert [m["reference"] for m in owner["missed_promises"]] == [str(rows.wp7_case)]
    assert monitoring["spend"]["today_cents"] == spent_cents == 6


def test_never_recomputed_example_3_of_12() -> None:
    with temp_sqlite() as store:
        thread = add_conversation(store.uow)
        for i in range(12):
            if i < 3:
                add_turn(
                    store.uow,
                    thread,
                    outcome="degraded_handoff",
                    degrade_reason="model_error",
                    path="degraded",
                )
            else:
                add_turn(store.uow, thread)
        _, monitoring, _ = pages(reader_for(store))
    failures = next(t for t in monitoring["health"] if t["id"] == "M-24")
    assert (failures["value"], failures["numerator"], failures["denominator"]) == (3, 3, 12)


def test_latency_null_reasons_and_nearest_rank() -> None:
    def tiles(monitoring: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
        return {t["label"]: t for t in monitoring["health"]}

    with temp_sqlite() as store:
        zero = tiles(reader_for(store).monitoring())
        assert zero["Latency p50"]["null_reason"] == "No turns yet"
        assert zero["Failures"]["null_reason"] == "No turns yet"
        thread = add_conversation(store.uow)
        for ms in (100, 200, 300, 400, 500):
            add_turn(store.uow, thread, server_ms=ms)
        few = tiles(reader_for(store).monitoring())
        assert few["Latency p95"]["null_reason"] == "Not enough turns yet (fewer than 20)"
        assert few["Latency p95"]["value"] is None
    with temp_sqlite() as store:
        thread = add_conversation(store.uow)
        values = [(i * 37) % 997 + 1 for i in range(20)]
        for ms in values:
            add_turn(store.uow, thread, server_ms=ms)
        full = tiles(reader_for(store).monitoring())
    ordered = sorted(values)
    assert full["Latency p50"]["value"] == ordered[9]  # ceil(0.5 * 20) - 1
    assert full["Latency p95"]["value"] == ordered[18]  # ceil(0.95 * 20) - 1
    assert full["Latency p95"]["value"] == int(p95_nearest_rank(values))
    assert full["Latency p95"]["null_reason"] is None


def test_eval_projection_and_unreadable_summary(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    with temp_sqlite() as store:
        ids = write_eval_reports(tmp_path / "reports", agent_version="agent-test")
        load_eval_reports(tmp_path / "reports", store.uow)
        reader = reader_for(store)
        latest = reader.latest_eval()
        EvalResponse.model_validate(latest)
        with store.uow() as tx:
            stored = {
                split: __import__("json").loads(
                    tx.connection.execute(
                        "SELECT summary_json FROM eval_runs WHERE run_id = ?", (rid,)
                    ).fetchone()[0]
                )
                for split, rid in ids.items()
            }
        for key, split in (("dev", "dev"), ("held_out", "held-out")):
            run = latest["splits"][key]
            assert tuple(run) == EVAL_RUN_KEYS
            assert all(run[k] == stored[split][k] for k in EVAL_RUN_KEYS)
            assert not {"suite", "gates", "headline", "withheld"} & set(run)
        assert latest["headline"] == stored["held-out"]["headline"]

        held_id = ids["held-out"]
        for broken in (
            "[]",
            '{"run_id": "x", "date": "d", "agent_version": "a", "size": 1, "mix": [], "dev_failures": []}',
        ):
            with store.uow(write=True) as tx:
                tx.connection.execute(
                    "UPDATE eval_runs SET summary_json = ? WHERE run_id = ?", (broken, held_id)
                )
                tx.commit()
            caplog.clear()
            with caplog.at_level(logging.WARNING, logger="meridian.reads"):
                again = reader.latest_eval()
            assert again["splits"]["held_out"] is None
            assert again["headline"] is None
            assert [r.getMessage() for r in caplog.records] == [f"eval_summary_unreadable run_id={held_id}"]
