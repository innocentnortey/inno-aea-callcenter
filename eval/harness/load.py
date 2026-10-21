"""The ``load`` suite (E-8, WF-10): conversations played at once, timed per ``submitTurn`` call (AC-9, AC-22, AC-23)."""

from __future__ import annotations

import asyncio
from typing import Literal

import httpx

from eval.harness.deps import HarnessDeps, RunConfig, RunOutcome
from eval.harness.records import ClientTurnTiming, new_record
from eval.harness.report import build_load_report, gates_failed, write_report
from eval.harness.report import percentile as percentile
from eval.harness.runlog import RunLog
from eval.harness.runner import CaseRefused, PlayedCase, play_case, run_db_check, start_run
from eval.harness.scoring import CaseScore, score_case
from eval.harness.scrub import Scrubber


async def run_load_suite(
    cfg: RunConfig,
    deps: HarnessDeps,
    *,
    log: RunLog,
    scrubber: Scrubber,
    transport: httpx.AsyncBaseTransport | None,
) -> RunOutcome:
    prepared = await start_run(cfg, deps, log=log, scrubber=scrubber, transport=transport, run_tag="load")
    if isinstance(prepared, RunOutcome):
        return prepared
    setup = prepared
    stamp = setup.stamp
    cases = setup.case_set.cases
    chosen = [cases[i % len(cases)] for i in range(cfg.conversations)] if cases else []
    timings: list[ClientTurnTiming] = []
    finished: list[tuple[int, PlayedCase]] = []
    try:
        for repeat in range(1, cfg.repeats + 1):
            lock = asyncio.Lock()
            claimed: set[str] = set()
            outcomes = await asyncio.gather(
                *(
                    play_case(
                        setup.client,
                        case,
                        repeat=repeat,
                        seed_db=deps.issued_db,
                        scrubber=scrubber,
                        log=log,
                        run_id=stamp.run_id,
                        claimed_messages=claimed,
                        identity_lock=lock,
                        conversation_index=i,
                        timings=timings,
                    )
                    for i, case in enumerate(chosen)
                ),
                return_exceptions=True,
            )
            for i, outcome in enumerate(outcomes):
                if isinstance(outcome, PlayedCase):
                    finished.append((i, outcome))
                else:
                    reason = outcome.reason if isinstance(outcome, CaseRefused) else "conversation_failed"
                    log.emit(
                        "case_refused",
                        run_id=stamp.run_id,
                        case_id=chosen[i].script.case_id,
                        repeat=repeat,
                        reason=reason,
                    )
        after = None if cfg.dry_run else await setup.client.monitoring()
    finally:
        await setup.client.aclose()

    db_result = run_db_check(setup, [p for _, p in finished])
    scores: list[CaseScore] = [
        score_case(
            played,
            run_id=stamp.run_id,
            judge=None,
            calibrated=False,
            db=db_result,
            heldout=False,
            hard_only=True,
            scrubber=scrubber,
            case_id=f"L{i:02d}:{played.case.script.case_id}",
        )
        for i, played in finished
    ]
    expected = cfg.conversations * cfg.repeats
    status: Literal["completed", "incomplete"] = "completed" if len(scores) == expected else "incomplete"
    record = new_record(
        stamp,
        suite="load",
        split="dev",
        repeats=cfg.repeats,
        experiment_id=None,
        status=status,
        finished_at=deps.wall_clock(),
        cases_expected=expected,
        cases_scored=len(scores),
    )
    cost = None
    if setup.before is not None and after is not None and finished:
        delta = int(after["spend"]["today_cents"]) - int(setup.before["spend"]["today_cents"])
        cost = round(max(0, delta) / 100 / len(finished), 4)
    ordered_timings = sorted(timings, key=lambda t: (t.sent_at, t.conversation_index, t.turn_index))
    report = build_load_report(
        record,
        scores,
        ordered_timings,
        mix=setup.case_set.mix,
        size=len(chosen),
        db=db_result,
        cost_per_conversation_usd=cost,
    )
    if cfg.dry_run:
        log.emit(
            "dry_run_finished",
            run_id=stamp.run_id,
            cases_expected=expected,
            cases_scored=len(scores),
            status=status,
        )
        return RunOutcome(0 if status == "completed" else 1, None, None)
    path = write_report(report, cfg.reports_dir, scrubber, timings=ordered_timings)
    if status == "incomplete":
        return RunOutcome(1, report, path)
    return RunOutcome(4 if gates_failed(report) else 0, report, path)
