"""Play one case over HTTP; run the ``worked-pairs`` and ``e2e`` suites (AC-1, AC-5, AC-6, AC-8)."""

from __future__ import annotations

import asyncio
import os
import secrets
import sqlite3
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Literal

import httpx

from eval.harness.cases import (
    CaseFileError,
    CaseSet,
    HeldoutHashMismatch,
    HeldoutNotSealed,
    LoadedCase,
    load_cases,
)
from eval.harness.client import AgentClient, HarnessHttpError, TurnCall
from eval.harness.dbcheck import DbCheckResult, check_db_copy
from eval.harness.deps import HarnessDeps, RunConfig, RunOutcome, UsageError
from eval.harness.dryrun import dry_run_transport
from eval.harness.freeze import (
    FreezeStamp,
    NotFrozen,
    TamperDetected,
    check_frozen,
    harness_commit,
    harness_digest,
)
from eval.harness.invariants import blocks_show_handoff, db_untouched_ids
from eval.harness.judge import AnthropicJudge, Judge, is_calibrated, load_calibration
from eval.harness.ledger import (
    DEFAULT_JUDGE_CAP_USD,
    RUN_COST_PER_CONVERSATION_USD,
    HarnessLedger,
    JudgeSpendCapReached,
    SpendPreflightRefused,
    preflight_spend,
)
from eval.harness.records import ClientTurnTiming, RunStamp, new_record
from eval.harness.report import (
    build_failed_report,
    build_scored_report,
    gates_failed,
    write_report,
)
from eval.harness.runlog import RunLog
from eval.harness.scoring import CaseScore, score_case
from eval.harness.scrub import Scrubber

FORM_SEED_FIELDS: Final = ("name", "phone", "customer_id", "invoice_number", "zip_or_city", "email")
_SEED_PREFIX: Final = "$seed:"


class CaseRefused(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class SeedValues:
    customer_id: str
    name: str
    phone: str
    email: str | None
    service_address: str
    zip: str
    city: str
    tier: str
    invoice_number: str | None


def read_seed(db_path: Path, customer_id: str) -> SeedValues:
    con = sqlite3.connect(f"{db_path.resolve().as_uri()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,)).fetchone()
        if row is None:
            raise CaseRefused("unknown_seeded_customer")
        invoice = con.execute(
            "SELECT invoice_id FROM invoices WHERE customer_id = ? ORDER BY issued_date DESC, invoice_id DESC LIMIT 1",
            (customer_id,),
        ).fetchone()
    finally:
        con.close()
    return SeedValues(
        customer_id=str(row["customer_id"]),
        name=str(row["name"]),
        phone=str(row["phone"]),
        email=None if row["email"] is None else str(row["email"]),
        service_address=str(row["service_address"]),
        zip=str(row["zip"]),
        city=str(row["city"]),
        tier=str(row["membership_tier"]),
        invoice_number=None if invoice is None else str(invoice["invoice_id"]),
    )


@dataclass(frozen=True)
class PlayedTurn:
    index: int
    kind: str
    turn_id: str | None
    http_status: int
    response: dict[str, Any] | None
    call: TurnCall | None


@dataclass(frozen=True)
class PlayedCase:
    case: LoadedCase
    repeat: int
    thread_id: str | None
    turns: tuple[PlayedTurn, ...]
    stop: Literal["completed", "handed_off", "off_script", "environment_error"]
    stop_turn: int | None
    seed: SeedValues | None
    conversation_index: int | None
    clock_now: datetime | None = None


def _blocks(response: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not response:
        return []
    if "blocks" in response:
        return [b for b in response["blocks"] if isinstance(b, dict)]
    block = response.get("block")
    return [block] if isinstance(block, dict) else []


def _find_card(
    replies: list[list[dict[str, Any]]], accepts: Callable[[dict[str, Any]], bool]
) -> dict[str, Any] | None:
    for blocks in reversed(replies):
        for block in reversed(blocks):
            if accepts(block):
                found: dict[str, Any] = block
                return found
    return None


def _offers(option: str | None) -> Callable[[dict[str, Any]], bool]:
    def accepts(block: dict[str, Any]) -> bool:
        return any(o.get("option") == option for o in block.get("options") or [])

    return accepts


def _seed_form(form: Mapping[str, str], seed: SeedValues | None) -> dict[str, str]:
    values: dict[str, str] = {}
    for name, raw in form.items():
        if not raw.startswith(_SEED_PREFIX):
            values[name] = raw
            continue
        field = raw[len(_SEED_PREFIX) :]
        if seed is None:
            raise CaseRefused("no_seeded_customer")
        source: dict[str, str | None] = {
            "name": seed.name,
            "phone": seed.phone,
            "customer_id": seed.customer_id,
            "invoice_number": seed.invoice_number,
            "zip_or_city": seed.zip,
            "email": seed.email,
        }
        value = source[field]
        if value is None:
            raise CaseRefused("seed_value_missing")
        values[name] = value
    return values


def _timing(
    call: TurnCall, *, run_id: str, thread_id: str, conversation_index: int, turn_index: int
) -> ClientTurnTiming:
    body = call.body or {}
    failure_offer = any(b.get("type") == "failure_offer" for b in _blocks(body))
    notice = body.get("notice")
    outcome: Literal["reply", "notice", "error", "client_timeout"]
    if call.timed_out:
        outcome = "client_timeout"
    elif call.transport_error or call.http_status != 200:
        outcome = "error"
    elif notice is not None or failure_offer:
        outcome = "notice"
    else:
        outcome = "reply"
    code: str | None = None
    if outcome == "notice":
        code = str(notice["code"]) if isinstance(notice, dict) and "code" in notice else "degraded_handoff"
    return ClientTurnTiming(
        run_id=run_id,
        thread_id=thread_id,
        turn_id=call.turn_id,
        conversation_index=conversation_index,
        turn_index=turn_index,
        sent_at=call.sent_at,
        first_byte_ms=call.first_byte_ms,
        total_ms=call.total_ms,
        http_status=call.http_status,
        outcome=outcome,
        notice_code=code,
    )


async def play_case(
    client: AgentClient,
    case: LoadedCase,
    *,
    repeat: int,
    seed_db: Path,
    scrubber: Scrubber,
    log: RunLog,
    run_id: str,
    claimed_messages: set[str],
    identity_lock: asyncio.Lock | None = None,
    conversation_index: int | None = None,
    timings: list[ClientTurnTiming] | None = None,
) -> PlayedCase:
    script = case.script
    if case.key is None:
        raise CaseRefused("missing_key")
    seed: SeedValues | None = None
    for turn in script.turns:
        if turn.kind == "form" and turn.form:
            for raw in turn.form.values():
                if raw.startswith(_SEED_PREFIX):
                    if script.seeded_customer is None:
                        raise CaseRefused("no_seeded_customer")
                    if raw[len(_SEED_PREFIX) :] not in FORM_SEED_FIELDS:
                        raise CaseRefused("unknown_seed_field")
    if script.seeded_customer is not None:
        seed = read_seed(seed_db, script.seeded_customer)
        for value in (seed.name, seed.phone, seed.email, seed.service_address, seed.invoice_number):
            scrubber.add(value)
    now = await client.demo_clock()
    if script.clock is not None and now != script.clock:
        raise CaseRefused("clock_mismatch")
    thread_id = await client.start_chat()
    log.emit("case_started", run_id=run_id, case_id=script.case_id, repeat=repeat, thread_id=thread_id)
    played: list[PlayedTurn] = []
    replies: list[list[dict[str, Any]]] = []
    handed = False
    holding = False

    def result(
        stop: Literal["completed", "handed_off", "off_script", "environment_error"],
        stop_turn: int | None = None,
    ) -> PlayedCase:
        return PlayedCase(
            case, repeat, thread_id, tuple(played), stop, stop_turn, seed, conversation_index, now
        )

    def missing(index: int) -> PlayedCase:
        return result("handed_off") if handed else result("off_script", index)

    try:
        for index, turn in enumerate(script.turns):
            payload: dict[str, Any] | None = None
            if turn.kind == "text":
                payload = {"kind": "text", "text": turn.text or ""}
            elif turn.kind == "choice":
                wanted = turn.choice
                card = _find_card(replies, _offers(wanted))
                if card is None:
                    return missing(index)
                payload = {"kind": "choice", "card_id": card["card_id"], "option": wanted}
            elif turn.kind == "form":
                card = _find_card(replies, lambda b: b.get("type") in {"locate_prompt", "where_prompt"})
                if card is None:
                    return missing(index)
                payload = {
                    "kind": "form",
                    "card_id": card["card_id"],
                    "values": _seed_form(turn.form or {}, seed),
                }
            elif turn.kind == "code_from_inbox":
                card = _find_card(replies, lambda b: b.get("type") == "code_prompt")
                messages = await client.inbox() if card is not None else []
                if identity_lock is not None and holding:
                    identity_lock.release()
                    holding = False
                message = next(
                    (
                        m
                        for m in messages
                        if m.get("status") == "active" and m.get("id") not in claimed_messages
                    ),
                    None,
                )
                if card is None or message is None:
                    return missing(index)
                claimed_messages.add(str(message["id"]))
                code = str(message["code"])
                scrubber.add(code)
                payload = {"kind": "code", "card_id": card["card_id"], "code": code}
            if identity_lock is not None and not holding and index + 1 < len(script.turns):
                if script.turns[index + 1].kind == "code_from_inbox":
                    await identity_lock.acquire()
                    holding = True

            if turn.kind == "person_request":
                handoff = await client.request_person(thread_id)
                status, body, turn_id, call = handoff.http_status, handoff.body, handoff.turn_id, None
            else:
                if payload is None:
                    raise CaseRefused("no_payload")
                call = await client.submit_turn(thread_id, payload)
                status, body, turn_id = call.http_status, call.body, call.turn_id
                if timings is not None:
                    timings.append(
                        _timing(
                            call,
                            run_id=run_id,
                            thread_id=thread_id,
                            conversation_index=conversation_index or 0,
                            turn_index=index,
                        )
                    )
            log.emit(
                "turn_done",
                run_id=run_id,
                case_id=script.case_id,
                repeat=repeat,
                turn_index=index,
                http_status=status,
                elapsed_ms=call.total_ms if call is not None else 0,
            )
            if 400 <= status < 500:
                raise CaseRefused(f"http_{status}")
            played.append(PlayedTurn(index, turn.kind, turn_id, status, body, call))
            if status != 200 or body is None:
                return result("environment_error", index)
            replies.append(_blocks(body))
            if blocks_show_handoff(replies[-1]) or (
                turn.kind == "person_request"
                and body.get("result") in {"case_created", "live_queued", "already_open"}
            ):
                handed = True
        return result("completed")
    finally:
        if identity_lock is not None and holding:
            identity_lock.release()


# ---------------------------------------------------------------------------------------------------------------
# The shared start of every suite: environment, cases, tamper check, login, preflight
# ---------------------------------------------------------------------------------------------------------------


@dataclass
class RunSetup:
    cfg: RunConfig
    deps: HarnessDeps
    log: RunLog
    scrubber: Scrubber
    stamp: RunStamp
    case_set: CaseSet
    client: AgentClient
    before: dict[str, Any] | None
    env: Mapping[str, str]


def _record_split(cfg: RunConfig) -> Literal["dev", "held-out"] | None:
    if cfg.suite == "worked-pairs":
        return None
    return "dev" if cfg.suite == "load" else cfg.split


def refuse(
    setup_cfg: RunConfig,
    deps: HarnessDeps,
    log: RunLog,
    scrubber: Scrubber,
    stamp: RunStamp,
    *,
    reason: str,
    message: str | None = None,
    expected: int = 0,
    **fields: str | int | None,
) -> RunOutcome:
    """A refused or failed run: say why, write the failed report (never on a dry run) and return exit 3."""
    if message is not None:
        log.say(f"refused: {message}")
    log.emit("refused", run_id=stamp.run_id, reason=reason, **fields)
    if setup_cfg.dry_run:
        return RunOutcome(3, None, None)
    record = new_record(
        stamp,
        suite=setup_cfg.suite,
        split=_record_split(setup_cfg),
        repeats=setup_cfg.repeats,
        experiment_id=setup_cfg.experiment_id,
        status="failed",
        finished_at=deps.wall_clock(),
        cases_expected=expected,
    )
    report = build_failed_report(record, reason=reason)
    path = write_report(report, setup_cfg.reports_dir, scrubber)
    return RunOutcome(3, report, path)


def _require(env: Mapping[str, str], name: str) -> str:
    value = env.get(name)
    if not value:
        raise UsageError(f"missing environment variable {name}", reason="missing_env")
    return value


async def start_run(
    cfg: RunConfig,
    deps: HarnessDeps,
    *,
    log: RunLog,
    scrubber: Scrubber,
    transport: httpx.AsyncBaseTransport | None,
    run_tag: Literal["eval", "load"],
) -> RunSetup | RunOutcome:
    env: Mapping[str, str] = deps.env if deps.env is not None else os.environ
    if cfg.dry_run:
        transport = dry_run_transport()
        env = {
            "MERIDIAN_EVAL_KEY": secrets.token_urlsafe(16),
            "MERIDIAN_DEMO_USERNAME": secrets.token_urlsafe(16),
            "MERIDIAN_DEMO_PASSWORD": secrets.token_urlsafe(16),
        }
    eval_key = _require(env, "MERIDIAN_EVAL_KEY")
    username = _require(env, "MERIDIAN_DEMO_USERNAME")
    password = _require(env, "MERIDIAN_DEMO_PASSWORD")
    scrubber.add(eval_key)
    scrubber.add(password)
    if len(username) >= 8:
        scrubber.add(username)
    run_id = str(uuid.uuid4())
    started_at = deps.wall_clock()
    stamp = RunStamp(
        run_id=run_id,
        agent_version="unknown",
        harness_commit=harness_commit(),
        harness_digest=harness_digest(deps.harness_root),
        index_manifest_hash=None,
        started_at=started_at,
    )
    suite_for_cases: Literal["worked-pairs", "e2e", "load"] = cfg.suite
    split_for_cases: Literal["dev", "held-out"] = "dev" if cfg.suite != "e2e" else (cfg.split or "dev")
    try:
        case_set = load_cases(
            cfg.cases_dir, suite=suite_for_cases, split=split_for_cases, heldout_key_dir=cfg.heldout_key_dir
        )
    except HeldoutHashMismatch as exc:
        return refuse(
            cfg,
            deps,
            log,
            scrubber,
            stamp,
            reason="heldout_hash_mismatch",
            message=str(exc),
            expected_sha256=exc.recorded,
            actual_sha256=exc.computed,
        )
    except HeldoutNotSealed as exc:
        return refuse(cfg, deps, log, scrubber, stamp, reason="heldout_not_sealed", message=str(exc))
    except CaseFileError as exc:
        raise UsageError(str(exc), reason="case_files") from exc
    try:
        if cfg.dry_run and not deps.freeze_file.is_file():
            frozen = FreezeStamp(stamp.harness_commit, stamp.harness_digest)
        else:
            frozen = check_frozen(deps.freeze_file, root=deps.harness_root)
    except NotFrozen:
        return refuse(
            cfg, deps, log, scrubber, stamp, reason="not_frozen", message="the harness is not frozen"
        )
    except TamperDetected as exc:
        return refuse(
            cfg,
            deps,
            log,
            scrubber,
            stamp,
            reason="tamper",
            message=str(exc),
            expected_sha256=exc.expected,
            actual_sha256=exc.actual,
        )
    stamp = replace(stamp, harness_commit=frozen.harness_commit, harness_digest=frozen.harness_digest)
    if split_for_cases == "held-out":
        for case in case_set.cases:
            if case.key is not None:
                for item in (
                    *case.key.must_do,
                    *case.key.must_say,
                    *case.key.must_not_say,
                    *case.key.judge_items,
                ):
                    if len(item.text) >= 12:
                        scrubber.add(item.text)
    client = AgentClient(
        cfg.base_url or "http://dry-run.invalid",
        transport=transport,
        eval_key=eval_key,
        run_id=run_id,
        run_tag=run_tag,
        wall_clock=deps.wall_clock,
    )
    expected = (cfg.conversations if cfg.suite == "load" else len(case_set.cases)) * cfg.repeats
    try:
        await client.login(username, password)
        agent_version = str((await client.latest_eval())["current_agent_version"])
        stamp = replace(stamp, agent_version=agent_version)
        before: dict[str, Any] | None = None
        if not cfg.dry_run:
            before = await client.monitoring()
            paid_judge = cfg.judge and deps.judge is None
            preflight_spend(
                before,
                run_estimate_usd=expected * RUN_COST_PER_CONVERSATION_USD,
                judge_cap_usd=DEFAULT_JUDGE_CAP_USD if paid_judge else 0.0,
            )
    except SpendPreflightRefused:
        await client.aclose()
        return refuse(cfg, deps, log, scrubber, stamp, reason="preflight_refused", expected=expected)
    except (HarnessHttpError, httpx.TransportError, KeyError) as exc:
        await client.aclose()
        status = exc.status if isinstance(exc, HarnessHttpError) else 0
        return refuse(
            cfg, deps, log, scrubber, stamp, reason="server_refused", expected=expected, http_status=status
        )
    log.emit(
        "run_started",
        run_id=run_id,
        suite=cfg.suite,
        split=_record_split(cfg),
        harness_commit=stamp.harness_commit,
        harness_digest=stamp.harness_digest,
        agent_version=stamp.agent_version,
        experiment_id=cfg.experiment_id,
        cases_expected=expected,
    )
    return RunSetup(cfg, deps, log, scrubber, stamp, case_set, client, before, env)


def build_judge(setup: RunSetup) -> Judge | None:
    cfg, deps = setup.cfg, setup.deps
    if cfg.dry_run:
        return None
    if deps.judge is not None:
        return deps.judge
    if not cfg.judge:
        return None
    import anthropic

    api_key = _require(setup.env, "ANTHROPIC_API_KEY")
    setup.scrubber.add(api_key)
    ledger = HarnessLedger(path=deps.ledger_dir, now=deps.wall_clock)
    return AnthropicJudge(anthropic.Anthropic(api_key=api_key, max_retries=0), ledger=ledger)


async def run_scored_suite(
    cfg: RunConfig,
    deps: HarnessDeps,
    *,
    log: RunLog,
    scrubber: Scrubber,
    transport: httpx.AsyncBaseTransport | None,
) -> RunOutcome:
    prepared = await start_run(cfg, deps, log=log, scrubber=scrubber, transport=transport, run_tag="eval")
    if isinstance(prepared, RunOutcome):
        return prepared
    setup = prepared
    stamp = setup.stamp
    cases = setup.case_set.cases
    played: list[PlayedCase] = []
    claimed: set[str] = set()
    try:
        for repeat in range(1, cfg.repeats + 1):
            for case in cases:
                try:
                    played.append(
                        await play_case(
                            setup.client,
                            case,
                            repeat=repeat,
                            seed_db=deps.issued_db,
                            scrubber=scrubber,
                            log=log,
                            run_id=stamp.run_id,
                            claimed_messages=claimed,
                        )
                    )
                except CaseRefused as exc:
                    log.emit(
                        "case_refused",
                        run_id=stamp.run_id,
                        case_id=case.script.case_id,
                        repeat=repeat,
                        reason=exc.reason,
                    )
        after: dict[str, Any] | None = None
        if not cfg.dry_run:
            after = await setup.client.monitoring()
    finally:
        await setup.client.aclose()

    db_result = run_db_check(setup, played)
    judge = build_judge(setup)
    outcome = finish_scored(setup, played, db_result=db_result, judge=judge, before=setup.before, after=after)
    return outcome


def run_db_check(setup: RunSetup, played: list[PlayedCase]) -> DbCheckResult | None:
    cfg, deps, log = setup.cfg, setup.deps, setup.log
    clocks = [p.clock_now for p in played if p.clock_now is not None]
    if cfg.db_copy is None or not clocks:
        return None
    untouched: set[int] = set()
    for p in played:
        if p.case.key is not None:
            untouched.update(db_untouched_ids(p.case.key))
    result = check_db_copy(deps.issued_db, cfg.db_copy, now=clocks[0], untouched=sorted(untouched))
    log.emit("db_check_done", run_id=setup.stamp.run_id, count=result.writes, findings=len(result.findings))
    return result


def finish_scored(
    setup: RunSetup,
    played: list[PlayedCase],
    *,
    db_result: DbCheckResult | None,
    judge: Judge | None,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> RunOutcome:
    cfg, deps, log, scrubber, stamp = setup.cfg, setup.deps, setup.log, setup.scrubber, setup.stamp
    heldout = cfg.split == "held-out" and cfg.suite == "e2e"
    initial_judge = judge
    calibrated = judge is not None and is_calibrated(
        load_calibration(cfg.calibration), judge_model=judge.model
    )
    cap_hit = False
    scores: list[CaseScore] = []
    for item in played:
        for attempt in (judge, None):
            try:
                scores.append(
                    score_case(
                        item,
                        run_id=stamp.run_id,
                        judge=attempt,
                        calibrated=calibrated,
                        db=db_result,
                        heldout=heldout,
                        hard_only=False,
                        scrubber=scrubber,
                    )
                )
                break
            except JudgeSpendCapReached:
                cap_hit = True
                judge = None
                log.emit("judge_cap_reached", run_id=stamp.run_id)
        log.emit(
            "case_scored",
            run_id=stamp.run_id,
            case_id=item.case.script.case_id,
            repeat=item.repeat,
            status="hard_pass" if scores[-1].result.passed_hard else "hard_fail",
        )
    expected = len(setup.case_set.cases) * cfg.repeats
    scored = len(scores)
    status: Literal["completed", "incomplete"] = "completed" if scored == expected else "incomplete"
    spend = float(getattr(initial_judge, "spend_usd", 0.0))
    record = new_record(
        stamp,
        suite=cfg.suite,
        split=_record_split(cfg),
        repeats=cfg.repeats,
        experiment_id=cfg.experiment_id,
        status=status,
        finished_at=deps.wall_clock(),
        cases_expected=expected,
        cases_scored=scored,
        judge_spend_usd=round(spend, 6),
    )
    judge_summary = {
        "enabled": initial_judge is not None,
        "model": initial_judge.model if initial_judge is not None else None,
        "calibrated": calibrated,
        "calls": sum(s.judge_calls for s in scores),
        "advisory_pass": sum(s.judge_advisory_pass for s in scores),
        "advisory_fail": sum(s.judge_advisory_fail for s in scores),
        "status": "off" if initial_judge is None else ("cap_reached" if cap_hit else "ok"),
    }
    cost: float | None = None
    if before is not None and after is not None and played:
        delta = int(after["spend"]["today_cents"]) - int(before["spend"]["today_cents"])
        cost = round(max(0, delta) / 100 / len(played), 4)
    report = build_scored_report(
        record,
        scores,
        mix=setup.case_set.mix,
        size=len(setup.case_set.cases),
        db=db_result,
        unscored=setup.case_set.unscored,
        judge_summary=judge_summary,
        cost_per_conversation_usd=cost,
    )
    if cfg.dry_run:
        log.emit(
            "dry_run_finished",
            run_id=stamp.run_id,
            cases_expected=expected,
            cases_scored=scored,
            status=status,
        )
        return RunOutcome(0 if status == "completed" else 1, None, None)
    path = write_report(report, cfg.reports_dir, scrubber)
    if status == "incomplete":
        code = 1
    else:
        code = 4 if gates_failed(report) else 0
    return RunOutcome(code, report, path)
