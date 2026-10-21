"""J-10 read leg (AEA-53): CON-18, CON-19 and CON-20 over MetricsReader on stored rows, through the real server.

Level: `integrated with a scripted model` for the read leg (real server, DB copy, guards on, the real login and role
check). The WP-2, WP-5 and WP-7 rows are written through the real writers' repositories, not driven through chat (DV-3).
Blocked step: the chat-driven leg waits on AEA-51 (the graph and `run_graph`); it is a declared skip, never a pass.
Asserts what the user sees (labels, denominators, units) and what is stored (direct counts that bracketed each read).
"""

# ruff: noqa: S608 (the f-strings splice module constants into assertion-only SQL; no input reaches them)

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from meridian.domain.common import HandoffReason
from meridian.services._case_rules import reason_label
from meridian.services.health import load_eval_reports
from meridian.web.container import Key
from meridian.web.deps import UOW_FACTORY
from tests.journeys.support.client import JourneyClient
from tests.journeys.support.db import DbReader
from tests.journeys.support.run import JourneyRun
from tests.unit.services.test_metrics_reader_rows import seed_j10_rows, write_eval_reports

pytestmark = pytest.mark.journey

J10 = "J-10"
OWNER = "('live','seed')"
HANDLED = "('booking','membership','billing','warranty')"
OUTCOMES = ("ai_resolved", "handed_off", "safety_reply", "abandoned")
LIVE_TURNS = "FROM turns t JOIN conversations c ON c.thread_id = t.thread_id WHERE t.run_tag = 'live' AND c.run_tag = 'live'"
M3_POPULATION = (
    "FROM conversations c WHERE c.run_tag = 'live' AND c.outcome <> 'open' AND EXISTS "
    f"(SELECT 1 FROM turns t WHERE t.thread_id = c.thread_id AND t.plan_topic IN {HANDLED})"
)


def _counts(db: DbReader) -> dict[str, object]:
    """Every scalar the three pages show, as direct SQL counts over the stored rows (what was stored)."""
    scalar = db.scalar
    counts: dict[str, object] = {
        "ended": scalar(f"SELECT COUNT(*) FROM conversations WHERE run_tag IN {OWNER} AND outcome <> 'open'"),
        "m3_den": scalar(f"SELECT COUNT(*) {M3_POPULATION}"),
        "m3_num": scalar(
            f"SELECT COUNT(*) {M3_POPULATION} AND c.outcome = 'ai_resolved' AND NOT EXISTS "
            "(SELECT 1 FROM flags f JOIN cases k ON k.case_ref = f.case_ref WHERE k.thread_id = c.thread_id)"
        ),
        "seed_count": scalar("SELECT COUNT(*) FROM cases WHERE seed = 1"),
        "kept": scalar("SELECT COUNT(*) FROM promises WHERE due_at IS NOT NULL AND status = 'kept'"),
        "due": scalar(
            "SELECT COUNT(*) FROM promises WHERE due_at IS NOT NULL AND status IN ('kept','missed')"
        ),
        "live_conversations": scalar("SELECT COUNT(*) FROM conversations WHERE run_tag = 'live'"),
        "live_turns": scalar(f"SELECT COUNT(*) {LIVE_TURNS}"),
        "failures": scalar(
            f"SELECT COUNT(*) {LIVE_TURNS} AND t.outcome = 'degraded_handoff' "
            "AND t.degrade_reason IN ('model_error','tool_error','timeout')"
        ),
        "trace_sent": scalar(f"SELECT COUNT(*) {LIVE_TURNS} AND t.trace_export = 'sent'"),
        "reasons": tuple(
            (r["reason"], r["n"])
            for r in db.rows(
                "SELECT k.reason AS reason, COUNT(*) AS n FROM cases k JOIN conversations c ON c.thread_id = k.thread_id "
                f"WHERE c.run_tag IN {OWNER} GROUP BY k.reason ORDER BY k.reason"
            )
        ),
    }
    for outcome in OUTCOMES:
        counts[f"outcome:{outcome}"] = scalar(
            f"SELECT COUNT(*) FROM conversations WHERE run_tag IN {OWNER} AND outcome = ?", (outcome,)
        )
    return counts


def _stable_read(
    journey: JourneyRun, client: JourneyClient
) -> tuple[dict[str, Mapping[str, Any]], dict[str, object]]:
    """D-11: compare a page only with SQL that bracketed it unchanged (a scheduler tick may write between reads)."""
    for _attempt in range(3):
        before = _counts(journey.db)
        bodies = {
            "owner": client.call("GET", "/api/staff/owner-metrics", operation_id="getOwnerMetrics").json(),
            "monitoring": client.call("GET", "/api/monitoring", operation_id="getMonitoring").json(),
            "eval": client.call("GET", "/api/eval/latest", operation_id="getLatestEval").json(),
        }
        after = _counts(journey.db)
        if before == after:
            return bodies, after
    raise AssertionError("store changed during every read attempt")


def test_j10_read_pages_show_stored_rows(journey: JourneyRun, tmp_path: Path) -> None:
    uow = journey.container.get(UOW_FACTORY)
    with journey.step(J10, "seed stored rows", needs=("uow_factory", "ledger")):
        seed_j10_rows(uow, journey.container.get(Key[Any]("ledger")), with_seed=False)
        write_eval_reports(tmp_path / "reports", agent_version=journey.settings.agent_version)
        load_eval_reports(tmp_path / "reports", uow)
    with journey.step(
        J10,
        "owner reads the three pages",
        needs=("login_sessions", "staff_access", "demo_clock", "metrics_reads"),
        operations=("login", "switchRole", "getOwnerMetrics", "getMonitoring", "getLatestEval"),
    ):
        signed = journey.login()
        signed.client.call("PUT", "/api/session/role", operation_id="switchRole", body={"role": "owner"})
        bodies, stored = _stable_read(journey, signed.client)
        owner, monitoring, latest = bodies["owner"], bodies["monitoring"], bodies["eval"]

        # what the user sees: labels, denominators and units
        shown = [
            owner["in_scope_correct_resolution"], owner["promises_kept_on_time"], owner["handoffs"],
            *owner["outcomes"], *owner["handoffs_by_reason"], *monitoring["health"],
            monitoring["correctness"]["containment_estimate"], *monitoring["correctness"]["escalations_by_reason"],
        ]  # fmt: skip
        for m in shown:
            assert isinstance(m["label"], str) and m["label"]
            assert m["unit"] in {"count", "ms", "share"}
            if m["unit"] == "share" and m["value"] is not None:
                assert 0 <= m["value"] <= 1
                assert m["value"] == m["numerator"] / m["denominator"]
        for split in latest["splits"].values():
            assert split is not None and all(0 <= em["value"] <= 1 for em in split["measures"])
        assert latest["headline"]["id"] == "M-1"

        # what is stored: each page value equals the direct count that bracketed it
        by_label = {m["label"]: m for m in owner["outcomes"]}
        labels = dict(
            zip(
                OUTCOMES,
                ("Resolved by the AI", "Handed off to a person", "Safety reply given", "Abandoned"),
                strict=True,
            )
        )
        for outcome in OUTCOMES:
            m = by_label[labels[outcome]]
            assert (m["numerator"], m["denominator"]) == (stored[f"outcome:{outcome}"], stored["ended"])
        handoffs = owner["handoffs"]
        assert (handoffs["numerator"], handoffs["denominator"]) == (
            stored["outcome:handed_off"],
            stored["ended"],
        )
        m3 = owner["in_scope_correct_resolution"]
        assert (m3["numerator"], m3["denominator"]) == (stored["m3_num"], stored["m3_den"])
        m13 = owner["promises_kept_on_time"]
        assert (m13["numerator"], m13["denominator"]) == (stored["kept"], stored["due"])
        assert owner["seed_count"] == stored["seed_count"] == 4
        reason_rows = {m["label"]: m["numerator"] for m in owner["handoffs_by_reason"]}
        assert reason_rows == {reason_label(HandoffReason(r)): n for r, n in stored["reasons"]}  # type: ignore[attr-defined]
        tiles = {t["label"]: t for t in monitoring["health"]}
        assert tiles["Conversations"]["value"] == stored["live_conversations"]
        assert tiles["Turns"]["value"] == stored["live_turns"]
        failures = tiles["Failures"]
        assert (failures["numerator"], failures["denominator"]) == (stored["failures"], stored["live_turns"])
        assert monitoring["trace_export"] == f"sent {stored['trace_sent']} of {stored['live_turns']} turns"
        job = tiles["Overdue job last ran"]
        if journey.db.count("job_runs") > 0:
            assert isinstance(job["value"], int) and job["value"] >= 0
        else:
            assert job["value"] is None and job["null_reason"]
        with uow() as tx:
            restart = tx.ops.health.last_restart()
        assert restart is not None and monitoring["last_restart"]["at"] is not None
        # not compared on purpose (D-11): alert states, as_of, demo_now and the job tile value move with wall time


@pytest.mark.skip(
    reason="blocked-on AEA-51: WP-2, WP-5 and WP-7 through the chat API need the graph (run_graph) and AEA-51's "
    "scripts; see the AEA-53 journey record"
)
def test_j10_worked_pairs_driven_through_chat(journey: JourneyRun) -> None:
    """Steps once AEA-51 lands: drive WP-2, WP-5 and WP-7 through the chat API, then re-run the three page reads and
    the stored-count equalities of test_j10_read_pages_show_stored_rows."""
