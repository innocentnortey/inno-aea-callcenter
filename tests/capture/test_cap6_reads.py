"""CAP-6 (DO-6, WF-6): the three read pages equal direct counts over the stored rows, and carry nothing they must not.

AC-2, AC-3 and AC-5 run at store level (mock-tested: real repositories, no server); AC-6, AC-13 and AC-14 run over
HTTP on the app the real container builds. Failure modes guarded: invariant (page == stored count), boundary (tags,
splits), negative (names, codes, cards, keys, trace links). Synthetic values only; sentinels are never printed.
"""

# ruff: noqa: S608 (the f-strings splice module constants into assertion-only SQL; no input reaches them)

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from meridian.adapters.sqlite.db import format_wall
from meridian.adapters.tracing_langfuse import NullTraceSink
from meridian.domain.common import HandoffReason
from meridian.services._case_rules import reason_label
from meridian.services.health import AlertSettings, load_eval_reports
from meridian.services.ledger import LedgerService
from meridian.services.metrics_reader import EVAL_RUN_KEYS, MetricsReader
from meridian.web.container import Key
from meridian.web.schemas.reads import EvalResponse, MonitoringResponse, OwnerMetricsResponse
from tests.api.reads_support import OPERATIONS, get_read
from tests.api.staff_session_support import container_app, login_token, switch, tab
from tests.api.web_shell_support import app_log_text, assert_matches, make_client, make_settings, rand_word
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.journeys.support.server import socket_guard
from tests.unit.services.test_metrics_reader_rows import (
    CHI,
    DEMO_NOW,
    WALL_NOW,
    LedgerDouble,
    Pages,
    WallClock,
    add_turn,
    seed_j10_rows,
    sentinels,
    write_eval_reports,
)

OWNER_TAGS_SQL = "('live','seed')"
HANDLED_SQL = "('booking','membership','billing','warranty')"
FAILURE_SQL = "('model_error','tool_error','timeout')"


def sql(store: TempStore, query: str, params: Sequence[object] = ()) -> list[tuple[Any, ...]]:
    with store.uow() as tx:
        return [tuple(r) for r in tx.connection.execute(query, tuple(params)).fetchall()]


def scalar(store: TempStore, query: str, params: Sequence[object] = ()) -> Any:
    return sql(store, query, params)[0][0]


def reader_for(store: TempStore, ledger: Any = None, version: str = "agent-test") -> Pages:
    return Pages(
        MetricsReader(
            store.uow,
            FixedClock(),
            WallClock(WALL_NOW),
            ledger or LedgerDouble(),
            AlertSettings(),
            version,
            30.0,
        )
    )


def real_ledger(store: TempStore) -> LedgerService:
    return LedgerService(store.uow, wall_clock=WallClock(WALL_NOW), daily_cap_usd=30.0)


# -- AC-2 -------------------------------------------------------------------------------------------------------
def test_owner_metrics_equal_stored_counts() -> None:
    with temp_sqlite() as store:
        ledger = real_ledger(store)
        seed_j10_rows(store.uow, ledger, with_seed=True)
        owner = reader_for(store, ledger).owner_metrics()
        OwnerMetricsResponse.model_validate(owner)

        ended = scalar(
            store,
            f"SELECT COUNT(*) FROM conversations WHERE run_tag IN {OWNER_TAGS_SQL} AND outcome <> 'open'",
        )
        handed = scalar(
            store,
            f"SELECT COUNT(*) FROM conversations WHERE run_tag IN {OWNER_TAGS_SQL} AND outcome = 'handed_off'",
        )
        assert (owner["handoffs"]["numerator"], owner["handoffs"]["denominator"]) == (handed, ended)
        assert owner["handoffs"]["id"] == "M-18"
        by_label = {m["label"]: m for m in owner["outcomes"]}
        for outcome, label in (
            ("ai_resolved", "Resolved by the AI"), ("handed_off", "Handed off to a person"),
            ("safety_reply", "Safety reply given"), ("abandoned", "Abandoned"),
        ):  # fmt: skip
            n = scalar(
                store,
                f"SELECT COUNT(*) FROM conversations WHERE run_tag IN {OWNER_TAGS_SQL} AND outcome = ?",
                (outcome,),
            )
            assert (by_label[label]["numerator"], by_label[label]["denominator"]) == (n, ended)
            refs = sql(
                store,
                "SELECT k.case_ref FROM cases k JOIN conversations c ON c.thread_id = k.thread_id "
                f"WHERE c.run_tag IN {OWNER_TAGS_SQL} AND c.outcome = ? ORDER BY k.case_ref",
                (outcome,),
            )
            assert by_label[label]["case_refs"] == [r[0] for r in refs]

        population = (
            "FROM conversations c WHERE c.run_tag = 'live' AND c.outcome <> 'open' AND EXISTS (SELECT 1 FROM turns t "
            f"WHERE t.thread_id = c.thread_id AND t.plan_topic IN {HANDLED_SQL})"
        )
        m3_den = scalar(store, f"SELECT COUNT(*) {population}")
        numerator_filter = (
            " AND c.outcome = 'ai_resolved' AND NOT EXISTS (SELECT 1 FROM flags f JOIN cases k "
            "ON k.case_ref = f.case_ref WHERE k.thread_id = c.thread_id)"
        )
        m3_num = scalar(store, f"SELECT COUNT(*) {population}{numerator_filter}")
        m3 = owner["in_scope_correct_resolution"]
        assert (m3["numerator"], m3["denominator"], m3["id"], m3["kind"]) == (
            m3_num,
            m3_den,
            "M-3",
            "estimate",
        )
        m3_refs = sql(
            store,
            f"SELECT k.case_ref FROM cases k WHERE k.thread_id IN (SELECT c.thread_id {population}{numerator_filter}) "
            "ORDER BY k.case_ref",
        )
        assert m3["case_refs"] == [r[0] for r in m3_refs]
        assert all(m["kind"] == "measured" for m in owner_measures_except_m3(owner))
        assert owner["measured_north_star_link"]["path"] == "/eval"

        total_cases = scalar(
            store,
            f"SELECT COUNT(*) FROM cases k JOIN conversations c ON c.thread_id = k.thread_id WHERE c.run_tag IN {OWNER_TAGS_SQL}",
        )
        by_reason = {m["label"]: m for m in owner["handoffs_by_reason"]}
        reasons = sql(
            store,
            "SELECT k.reason, COUNT(*) FROM cases k JOIN conversations c ON c.thread_id = k.thread_id "
            f"WHERE c.run_tag IN {OWNER_TAGS_SQL} GROUP BY k.reason",
        )
        assert len(by_reason) == len(reasons)
        for reason, n in reasons:
            row = by_reason[reason_label(HandoffReason(reason))]
            assert (row["numerator"], row["denominator"], row["id"]) == (n, total_cases, "M-22")
            refs = sql(
                store,
                "SELECT k.case_ref FROM cases k JOIN conversations c ON c.thread_id = k.thread_id "
                f"WHERE c.run_tag IN {OWNER_TAGS_SQL} AND k.reason = ? ORDER BY k.case_ref",
                (reason,),
            )
            assert row["case_refs"] == [r[0] for r in refs]

        seeds = scalar(store, "SELECT COUNT(*) FROM cases WHERE seed = 1")
        assert owner["seeds_included"] is True
        assert owner["seed_count"] == seeds == 4

        promises = dict(
            sql(
                store,
                "SELECT status, COUNT(*) FROM promises WHERE due_at IS NOT NULL AND status IN ('kept','missed') GROUP BY status",
            )
        )
        m13 = owner["promises_kept_on_time"]
        assert (m13["numerator"], m13["denominator"], m13["id"]) == (
            promises.get("kept", 0),
            sum(promises.values()),
            "M-13",
        )
        missed_sql = scalar(
            store, "SELECT COUNT(*) FROM promises WHERE status = 'missed' AND due_at IS NOT NULL"
        )
        assert len(owner["missed_promises"]) == missed_sql
        listed = {c["reference"] for c in owner["cases"]}
        assert {
            r
            for m in (m3, m13, owner["handoffs"], *owner["outcomes"], *owner["handoffs_by_reason"])
            for r in m["case_refs"]
        } <= listed
        print(
            {
                m["label"]: (m["numerator"], m["denominator"])
                for m in (m3, m13, owner["handoffs"], *owner["outcomes"])
            }
        )

    with temp_sqlite() as store:
        empty = reader_for(store).owner_metrics()
        OwnerMetricsResponse.model_validate(empty)
    assert empty["in_scope_correct_resolution"]["value"] is None
    assert empty["in_scope_correct_resolution"]["null_reason"] == "No conversations since the reset."
    assert empty["promises_kept_on_time"]["null_reason"] == "No promises are due yet."
    assert (
        empty["handoffs"]["value"] is None
        and empty["handoffs"]["null_reason"] == "No conversations since the reset."
    )
    assert empty["outcomes"] == [] and empty["handoffs_by_reason"] == []
    assert empty["seeds_included"] is False and empty["seed_count"] == 0


def owner_measures_except_m3(owner: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        owner["promises_kept_on_time"],
        owner["handoffs"],
        *owner["outcomes"],
        *owner["handoffs_by_reason"],
    ]


# -- AC-3 -------------------------------------------------------------------------------------------------------
def test_monitoring_equals_stored_counts() -> None:
    with temp_sqlite() as store:
        ledger = real_ledger(store)
        seed_j10_rows(store.uow, ledger, with_seed=True)
        page = reader_for(store, ledger).monitoring()
        MonitoringResponse.model_validate(page)
        tiles = {t["label"]: t for t in page["health"]}
        live_turns = "FROM turns t JOIN conversations c ON c.thread_id = t.thread_id WHERE t.run_tag = 'live' AND c.run_tag = 'live'"
        assert (
            tiles["Conversations"]["value"]
            == scalar(store, "SELECT COUNT(*) FROM conversations WHERE run_tag = 'live'")
            == 7
        )
        assert tiles["Turns"]["value"] == scalar(store, f"SELECT COUNT(*) {live_turns}") == 6
        failures = scalar(
            store,
            f"SELECT COUNT(*) {live_turns} AND t.outcome = 'degraded_handoff' AND t.degrade_reason IN {FAILURE_SQL}",
        )
        f = tiles["Failures"]
        assert (f["value"], f["numerator"], f["denominator"]) == (failures, failures, 6) == (1, 1, 6)
        assert tiles["Latency p95"]["null_reason"] == "Not enough turns yet (fewer than 20)"
        assert tiles["Overdue job last ran"]["value"] == 120000
        assert tiles["Handoff-only mode (1 = on)"]["value"] == 0
        sent = scalar(store, f"SELECT COUNT(*) {live_turns} AND t.trace_export = 'sent'")
        assert page["trace_export"] == f"sent {sent} of 6 turns"
        total_live = scalar(store, f"SELECT COUNT(*) {live_turns}")
        assert page["trace_export"].endswith(f"of {total_live} turns")

        reasons = dict(
            sql(
                store,
                "SELECT k.reason, COUNT(*) FROM cases k JOIN conversations c ON c.thread_id = k.thread_id "
                "WHERE c.run_tag = 'live' GROUP BY k.reason",
            )
        )
        escalations = {t["label"]: t["value"] for t in page["correctness"]["escalations_by_reason"]}
        assert escalations == {reason_label(HandoffReason(r)): n for r, n in reasons.items()}
        assert sum(escalations.values()) == 3  # the 4 seed cases are not live

        start = datetime_chicago_day_start_utc()
        end = start + __import__("datetime").timedelta(days=1)
        spent = scalar(
            store,
            "SELECT COALESCE(SUM(cost_usd), 0) FROM spend_ledger WHERE recorded_at >= ? AND recorded_at < ?",
            (format_wall(start), format_wall(end)),
        )
        assert page["spend"]["today_cents"] == round(spent * 100)
        stored_restart = scalar(
            store, "SELECT at_wall FROM health_events WHERE kind = 'restart' ORDER BY id DESC LIMIT 1"
        )
        assert format_wall(page["last_restart"]["at"]) == stored_restart
        health_pairs = {(t["id"], t["label"]) for t in page["health"]}
        corr = page["correctness"]
        correctness_pairs = {
            (t["id"], t["label"]) for t in (corr["containment_estimate"], *corr["escalations_by_reason"])
        }
        assert health_pairs.isdisjoint(correctness_pairs)
        m3 = corr["containment_estimate"]
        assert (m3["numerator"], m3["denominator"]) == (1, 3)  # eval, load and seed rows are not counted


def datetime_chicago_day_start_utc() -> Any:
    from datetime import UTC, datetime

    return datetime(
        WALL_NOW.astimezone(CHI).year,
        WALL_NOW.astimezone(CHI).month,
        WALL_NOW.astimezone(CHI).day,
        tzinfo=CHI,
    ).astimezone(UTC)


# -- AC-5 -------------------------------------------------------------------------------------------------------
def stored_summary(store: TempStore, split: str) -> dict[str, Any] | None:
    rows = sql(
        store,
        "SELECT summary_json FROM eval_runs WHERE suite = 'e2e' AND split = ? AND status = 'completed' "
        "ORDER BY finished_at DESC, started_at DESC LIMIT 1",
        (split,),
    )
    return json.loads(rows[0][0]) if rows else None


def test_latest_eval_per_split(tmp_path: Path) -> None:
    scenarios: dict[str, dict[str, Any]] = {
        "both": {},
        "dev only": {"held_out": False},
        "stale": {"agent_version": "agent-old"},
        "no run": {"dev": False, "held_out": False},
        "held-out incomplete only": {"dev": False, "held_out_incomplete": True},
        "newer incomplete held-out": {"extra_incomplete_held_out": True},
    }
    for name, kw in scenarios.items():
        folder = tmp_path / re.sub(r"\W", "_", name)
        options = {"agent_version": "agent-new", **kw}
        with temp_sqlite() as store:
            write_eval_reports(folder, **options)
            load_eval_reports(folder, store.uow)
            page = reader_for(store, version="agent-new").latest_eval()
            EvalResponse.model_validate(page)
            print(name, json.dumps({k: page[k] for k in ("headline", "current_agent_version")}, default=str),
                  {s: (r["run_id"] if r else None) for s, r in page["splits"].items()})  # fmt: skip
            for key, split in (("dev", "dev"), ("held_out", "held-out")):
                stored = stored_summary(store, split)
                shown = page["splits"][key]
                if stored is None:
                    assert shown is None, name
                    continue
                assert shown == {k: stored[k] for k in EVAL_RUN_KEYS}, name
                for m in shown["measures"]:
                    assert re.fullmatch(r"[ME]-\d+(:[a-z_]+)?", m["id"])
                    assert m["target"] is None or isinstance(m["target"], str)
                    assert all(isinstance(m[f], int | float) for f in ("value", "numerator", "denominator"))
            held = stored_summary(store, "held-out")
            assert page["headline"] == (held["headline"] if held else None), name
            assert page["current_agent_version"] == "agent-new"
            if name == "dev only" or name == "no run":
                assert page["splits"]["held_out"] is None and page["headline"] is None
            if name == "stale":
                assert page["splits"]["dev"]["agent_version"] == "agent-old" != page["current_agent_version"]
                assert page["splits"]["held_out"]["agent_version"] == "agent-old"
            if name == "held-out incomplete only":
                assert page["splits"]["held_out"] is None and page["headline"] is None
                assert scalar(store, "SELECT COUNT(*) FROM eval_runs WHERE status = 'incomplete'") >= 0
            if name == "newer incomplete held-out":
                incomplete_ids = {
                    r[0] for r in sql(store, "SELECT run_id FROM eval_runs WHERE status = 'incomplete'")
                }
                assert page["splits"]["held_out"]["run_id"] not in incomplete_ids


# -- AC-6, AC-13, AC-14 (HTTP) ---------------------------------------------------------------------------------------
def get_pages(client: Any, token: str) -> dict[str, Any]:
    responses = {op: get_read(client, op, tab(token)) for op in OPERATIONS}
    for op, response in responses.items():
        assert response.status_code == 200, response.text
        assert_matches(response, op)
    return responses


def key_names(node: object) -> set[str]:
    if isinstance(node, Mapping):
        return set(map(str, node)) | {k for v in node.values() for k in key_names(v)}
    if isinstance(node, list):
        return {k for v in node for k in key_names(v)}
    return set()


def test_no_pii_codes_cards_or_trace_links(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    h = container_app(monkeypatch, tmp_path)
    s = sentinels()
    with make_client(h.app) as client:
        ledger = h.app.state.container.get(Key[Any]("ledger"))
        rows = seed_j10_rows(h.uow, ledger, with_seed=True)
        with h.uow(write=True) as tx:
            tx.core.messages.append(
                rows.wp2,
                "customer",
                f"call {s['name']} on {s['phone']} code {s['code']} card {s['card']}",
                DEMO_NOW,
            )
            tx.commit()
        add_turn(h.uow, rows.wp2, response=f"Reply for {s['name']} {s['phone']}", trace_id=s["trace_id"])
        write_eval_reports(tmp_path / "reports", agent_version="agent-test", quote=f"{s['name']} {s['card']}")
        load_eval_reports(tmp_path / "reports", h.uow)
        token = login_token(client, h.settings)
        assert switch(client, token, "owner").status_code == 200
        responses = get_pages(client, token)
    hits = 0
    for op, response in responses.items():
        text = response.text
        hits += sum(1 for v in s.values() if v in text)
        assert "http" not in text and "/trace" not in text, op
        assert not {"trace_id", "trace_url"} & key_names(response.json()), op
    print("sentinel hits:", hits)
    assert hits == 0


def test_monitoring_says_export_off_and_no_outbound(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    h = container_app(monkeypatch, tmp_path)
    with make_client(h.app) as client:
        container = h.app.state.container
        assert isinstance(container.get(Key[Any]("trace")), NullTraceSink)
        ledger = container.get(Key[Any]("ledger"))
        seed_j10_rows(h.uow, ledger, with_seed=True)
        from meridian.adapters.sqlite.repos_ops import HealthEvent

        with h.uow(write=True) as tx:
            tx.ops.health.append(
                HealthEvent(at_wall=WALL_NOW, kind="alert_fired", alert_type="trace_export_failed",
                            reason_code=None, value=1.0, threshold=None, agent_version="test")
            )  # fmt: skip
            tx.commit()
        token = login_token(client, h.settings)
        assert switch(client, token, "owner").status_code == 200
        with socket_guard() as guard:
            responses = get_pages(client, token)
        with h.uow() as tx:
            n = tx.connection.execute(
                "SELECT COUNT(*) FROM turns t JOIN conversations c ON c.thread_id = t.thread_id "
                "WHERE t.run_tag = 'live' AND c.run_tag = 'live'"
            ).fetchone()[0]
            off = tx.connection.execute(
                "SELECT COUNT(*) FROM turns WHERE run_tag = 'live' AND trace_export = 'off'"
            ).fetchone()[0]
    monitoring = responses["getMonitoring"].json()
    print("trace_export:", monitoring["trace_export"], "N:", n, "blocked:", guard.blocked)
    assert off == n
    assert monitoring["trace_export"] == f"sent 0 of {n} turns"
    alert = next(a for a in monitoring["alerts"] if a["type"] == "trace_export_failed")
    assert alert["state"] == "firing"  # as stored
    assert guard.blocked == []


def test_no_key_values_or_message_text(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    secrets_ = {name: rand_word(18, "sx") for name in ("s1", "s2", "s3", "s4", "s5", "s6")}
    monkeypatch.setattr(
        "tests.api.staff_session_support.make_settings",
        lambda path, **kw: make_settings(
            path,
            anthropic_api_key=secrets_["s1"],
            openrouter_api_key=secrets_["s2"],
            demo_password=secrets_["s3"],
            eval_key=secrets_["s4"],
            langfuse_public_key=secrets_["s5"],
            langfuse_secret_key=secrets_["s6"],
            **kw,
        ),
    )
    phrase = rand_word(24, "phrase")
    h = container_app(monkeypatch, tmp_path)
    caplog.set_level(logging.DEBUG)
    with make_client(h.app) as client:
        ledger = h.app.state.container.get(Key[Any]("ledger"))
        rows = seed_j10_rows(h.uow, ledger, with_seed=True)
        with h.uow(write=True) as tx:
            tx.core.messages.append(rows.wp2, "customer", f"{phrase} please", DEMO_NOW)
            tx.core.messages.append(rows.wp2, "assistant", f"{phrase} answer", DEMO_NOW)
            tx.commit()
        add_turn(h.uow, rows.wp2, response=f"{phrase} reply")
        write_eval_reports(tmp_path / "reports", agent_version="agent-test")
        load_eval_reports(tmp_path / "reports", h.uow)
        token = login_token(client, h.settings)
        assert switch(client, token, "owner").status_code == 200
        caplog.clear()
        responses = get_pages(client, token)
        logs = app_log_text(caplog)
        with h.uow() as tx:
            stored = json.loads(
                tx.connection.execute(
                    "SELECT summary_json FROM eval_runs WHERE split = 'dev' AND status = 'completed'"
                ).fetchone()[0]
            )
    needles = [*secrets_.values(), phrase]
    for op, response in responses.items():
        assert not [n for n in needles if n in response.text], op
    assert not [n for n in needles if n in logs]
    assert responses["getLatestEval"].json()["splits"]["dev"]["dev_failures"] == stored["dev_failures"]
