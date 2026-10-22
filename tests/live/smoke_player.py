"""Plays one smoke case over HTTP through the real app and reads its stored evidence and signal records (AEA-61).

Every call goes through `JourneyClient.call`, so every response is validated against the signed OpenAPI. Phones and
codes are read at run time (customer row, demo inbox) and are kept only in `CaseSecrets`, which is never rendered.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Final

import httpx

from eval.cases.models import ScriptedTurn
from meridian.agent.signals import SIGNAL_LOGGER
from tests.journeys.support.run import JourneyRun
from tests.live.smoke_cases import SmokeCase
from tests.live.smoke_spend import SPEND_STOP_KINDS


@dataclass(frozen=True)
class TurnExchange:
    index: int
    kind: str
    operation_id: str
    turn_id: str
    status: int
    body: Mapping[str, Any]

    @property
    def notice_code(self) -> str | None:
        notice = self.body.get("notice")
        if isinstance(notice, Mapping):
            code = notice.get("code")
            return str(code) if code is not None else None
        return None


@dataclass(frozen=True)
class CaseSecrets:
    """(label, value) pairs that must never reach a record or the output. The repr hides the values."""

    values: tuple[tuple[str, str], ...] = ()

    def __repr__(self) -> str:
        return f"CaseSecrets({len(self.values)} values)"


@dataclass(frozen=True)
class CaseEvidence:
    turns: tuple[dict[str, Any], ...] = ()
    spend: tuple[dict[str, Any], ...] = ()
    lookups: tuple[dict[str, Any], ...] = ()
    actions: tuple[dict[str, Any], ...] = ()
    checks: tuple[dict[str, Any], ...] = ()
    cases: tuple[dict[str, Any], ...] = ()
    promises: tuple[dict[str, Any], ...] = ()
    run_tags: tuple[str, ...] = ()
    eval_runs: int = 0
    snapshots_before: Mapping[str, tuple[dict[str, Any], ...]] = field(default_factory=dict)
    snapshots_after: Mapping[str, tuple[dict[str, Any], ...]] = field(default_factory=dict)
    signals: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True)
class CaseOutcome:
    case: SmokeCase
    thread_id: str | None
    exchanges: tuple[TurnExchange, ...]
    evidence: CaseEvidence
    mismatches: tuple[str, ...]
    player_errors: tuple[str, ...]
    header_names: frozenset[str]
    secrets: CaseSecrets = field(default_factory=CaseSecrets, repr=False)

    @property
    def spend_cap_hit(self) -> bool:
        if any(x.notice_code == "SPEND_CAP_REACHED" for x in self.exchanges):
            return True
        return any(row.get("failure_kind") in SPEND_STOP_KINDS for row in self.evidence.spend)

    @property
    def cost_usd(self) -> float:
        return sum(row["cost_usd"] or 0.0 for row in self.evidence.spend)


class SignalTap(logging.Handler):
    """Collects `record.__dict__["signal"]` mappings from the signal logger (LogTap cannot see them, PD-6)."""

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.payloads: list[dict[str, object]] = []

    def emit(self, record: logging.LogRecord) -> None:
        payload = record.__dict__.get("signal")
        if isinstance(payload, Mapping):
            self.payloads.append(dict(payload))  # Handler.handle() already holds self.lock


@contextmanager
def signal_tap() -> Iterator[SignalTap]:
    tap = SignalTap()
    logger = logging.getLogger(SIGNAL_LOGGER)
    logger.addHandler(tap)
    try:
        yield tap
    finally:
        logger.removeHandler(tap)


BeforeTurn = Callable[[int, ScriptedTurn, Sequence[TurnExchange]], None]
SNAPSHOT_SQL: Final[Mapping[str, str]] = {
    "WP-4": "SELECT * FROM appointments WHERE appointment_id = 1",
    "WP-4F": "SELECT * FROM appointments WHERE appointment_id = 159",
}


def _loads(value: Any) -> Any:
    return json.loads(value) if isinstance(value, str) else value


def collect_evidence(
    run: JourneyRun,
    thread_id: str,
    case: SmokeCase,
    before: Mapping[str, tuple[dict[str, Any], ...]],
    signals: Sequence[Mapping[str, object]],
) -> CaseEvidence:
    db = run.db
    p = (thread_id,)
    turns = db.rows(
        "SELECT turn_id, sequence, run_tag, gate_result, outcome, degrade_reason, planner_fallback_used, "
        "danger_raised, server_ms, model_calls, cost_usd, trace_id, trace_export FROM turns "
        "WHERE thread_id = ? ORDER BY sequence",
        p,
    )
    spend = db.rows(
        "SELECT id, turn_id, run_tag, role, provider, model, attempt, latency_ms, cost_usd, status, failure_kind, "
        "http_status, provider_request_id FROM spend_ledger WHERE thread_id = ? ORDER BY id",
        p,
    )
    lookups = []
    for row in db.rows(
        "SELECT id, turn_id, tool, record_ids, passage_ids, result_seen FROM lookup_log "
        "WHERE thread_id = ? ORDER BY id",
        p,
    ):
        seen = row.pop("result_seen")
        row["record_ids"] = _loads(row["record_ids"]) or []
        row["passage_ids"] = _loads(row["passage_ids"]) or []
        row["has_snapshot"] = bool(seen) and not str(seen).startswith("refused:") and seen != "failed"
        lookups.append(row)
    actions = db.rows("SELECT id, turn_id, kind, record_id FROM actions WHERE thread_id = ? ORDER BY id", p)
    checks = db.rows(
        "SELECT turn_id, check_kind, result, removed FROM check_events WHERE thread_id = ? ORDER BY id", p
    )
    cases = db.rows(
        "SELECT case_ref, turn_id, reason, priority, rule_id, due_at FROM cases WHERE thread_id = ? "
        "ORDER BY created_at",
        p,
    )
    promises: list[dict[str, Any]] = []
    if cases:
        marks = ", ".join("?" for _ in cases)
        for row in db.rows(
            "SELECT case_ref, policy_row, text, due_at, due_label, extra_lines FROM promises "  # noqa: S608
            f"WHERE case_ref IN ({marks})",
            tuple(c["case_ref"] for c in cases),
        ):
            row["extra_lines"] = _loads(row["extra_lines"]) or []
            promises.append(row)
    tags = {r["run_tag"] for r in db.rows("SELECT run_tag FROM conversations WHERE thread_id = ?", p)}
    tags.update(t["run_tag"] for t in turns)
    after: dict[str, tuple[dict[str, Any], ...]] = {}
    if case.case_id in SNAPSHOT_SQL:
        after[case.case_id] = tuple(db.rows(SNAPSHOT_SQL[case.case_id]))
    return CaseEvidence(
        turns=tuple(turns),
        spend=tuple(spend),
        lookups=tuple(lookups),
        actions=tuple(actions),
        checks=tuple(checks),
        cases=tuple(cases),
        promises=tuple(promises),
        run_tags=tuple(sorted(tags)),
        eval_runs=db.count("eval_runs"),
        snapshots_before=dict(before),
        snapshots_after=after,
        signals=tuple(dict(s) for s in signals),
    )


def _first_line(exc: BaseException) -> str:
    return (str(exc).splitlines() or [""])[0][:300]


def _body(response: httpx.Response) -> Mapping[str, Any]:
    try:
        parsed = response.json()
    except ValueError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _blocks(exchanges: Sequence[TurnExchange], kind: str) -> list[dict[str, Any]]:
    """Blocks of a kind, newest exchange first."""
    found: list[dict[str, Any]] = []
    for ex in reversed(exchanges):
        found.extend(b for b in ex.body.get("blocks") or [] if isinstance(b, dict) and b.get("type") == kind)
    return found


def _empty(
    case: SmokeCase, secrets: list[tuple[str, str]], errors: list[str], mismatches: list[str]
) -> CaseOutcome:
    return CaseOutcome(
        case=case,
        thread_id=None,
        exchanges=(),
        evidence=CaseEvidence(),
        mismatches=tuple(mismatches),
        player_errors=tuple(errors),
        header_names=frozenset(),
        secrets=CaseSecrets(tuple(secrets)),
    )


def play_case(run: JourneyRun, case: SmokeCase, *, before_turn: BeforeTurn | None = None) -> CaseOutcome:
    cid = case.case_id
    secrets: list[tuple[str, str]] = []
    errors: list[str] = []
    mismatches: list[str] = []
    if case.script.staffing != "nobody":
        errors.append(f"{cid} turn 0: staffing {case.script.staffing} not supported")
        return _empty(case, secrets, errors, mismatches)
    with signal_tap() as tap:
        password, session_secret = run.env.secret_values()
        secrets += [("demo password", password), ("session secret", session_secret)]
        try:
            client = run.login().client
        except AssertionError as exc:
            mismatches.append(_first_line(exc))
            return _empty(case, secrets, errors, mismatches)
        row: dict[str, Any] = {}
        if case.script.seeded_customer:
            row = run.db.one(
                "SELECT customer_id, name, phone, zip FROM customers WHERE customer_id = ?",
                (case.script.seeded_customer,),
            )
            secrets.append(("seeded phone", str(row["phone"])))
            secrets.append(("seeded phone digits", "".join(ch for ch in str(row["phone"]) if ch.isdigit())))
        before: dict[str, tuple[dict[str, Any], ...]] = {}
        if cid in SNAPSHOT_SQL:
            before[cid] = tuple(run.db.rows(SNAPSHOT_SQL[cid]))

        try:
            started = client.call("POST", "/api/chat/sessions", operation_id="startChatSession")
        except AssertionError as exc:
            mismatches.append(_first_line(exc))
            started = client.responses[-1]
        if started.status_code != 201:
            errors.append(f"{cid} turn 0: startChatSession HTTP {started.status_code}")
            return _empty(case, secrets, errors, mismatches)
        thread_id = str(_body(started)["thread_id"])

        exchanges: list[TurnExchange] = []
        codes = 0
        for i, turn in enumerate(case.script.turns):
            if before_turn is not None:
                before_turn(i, turn, exchanges)
            tid = str(uuid.uuid4())
            operation = "submitTurn"
            path = f"/api/chat/sessions/{thread_id}/turns"
            body: dict[str, Any]
            problem: str | None = None
            if turn.kind == "text":
                payload: dict[str, Any] = {"kind": "text", "text": turn.text}
                body = {"turn_id": tid, "payload": payload}
            elif turn.kind == "choice":
                card = next(
                    (
                        (b["card_id"], opt)
                        for ex in reversed(exchanges)
                        for b in ex.body.get("blocks") or []
                        if isinstance(b, dict) and b.get("card_id")
                        for opt in b.get("options") or []
                        if isinstance(opt, dict) and opt.get("option") == turn.choice
                    ),
                    None,
                )
                if card is None:
                    problem = "no card for choice"
                    body = {}
                else:
                    body = {
                        "turn_id": tid,
                        "payload": {"kind": "choice", "card_id": card[0], "option": turn.choice},
                    }
            elif turn.kind == "form":
                prompts = _blocks(exchanges, "locate_prompt") or _blocks(exchanges, "where_prompt")
                if not prompts:
                    problem = "no locate_prompt"
                    body = {}
                else:
                    block = prompts[0]
                    values = _seeded_values(run, turn.form or {}, row)
                    fitting = next(
                        (fs for fs in block.get("field_sets") or [] if all(f in values for f in fs)), None
                    )
                    if fitting is None:
                        problem = "no fillable field_set"
                        body = {}
                    else:
                        body = {
                            "turn_id": tid,
                            "payload": {
                                "kind": "form",
                                "card_id": block["card_id"],
                                "values": {f: values[f] for f in fitting},
                            },
                        }
            elif turn.kind == "code_from_inbox":
                prompts = _blocks(exchanges, "code_prompt")
                code = _inbox_code(client, mismatches)
                if not prompts:
                    problem = "no code_prompt"
                    body = {}
                elif code is None:
                    problem = "no active inbox code"
                    body = {}
                else:
                    codes += 1
                    secrets.append((f"inbox code {codes}", code))
                    body = {
                        "turn_id": tid,
                        "payload": {"kind": "code", "card_id": prompts[0]["card_id"], "code": code},
                    }
            else:  # person_request
                operation = "requestPerson"
                path = f"/api/chat/sessions/{thread_id}/handoff"
                body = {"turn_id": tid}
            if problem is not None:
                errors.append(f"{cid} turn {i + 1}: {problem}")
                break
            try:
                response = client.call("POST", path, operation_id=operation, body=body)
            except AssertionError as exc:
                mismatches.append(_first_line(exc))
                response = client.responses[-1]
            exchanges.append(
                TurnExchange(i, turn.kind, operation, tid, response.status_code, _body(response))
            )
            if response.status_code != 200:
                errors.append(f"{cid} turn {i + 1}: HTTP {response.status_code}")
                break
        header_names = frozenset(name.lower() for r in client.responses for name in r.request.headers)
        evidence = collect_evidence(
            run, thread_id, case, before, [p for p in tap.payloads if p.get("thread_id") == thread_id]
        )
    return CaseOutcome(
        case=case,
        thread_id=thread_id,
        exchanges=tuple(exchanges),
        evidence=evidence,
        mismatches=tuple(mismatches),
        player_errors=tuple(errors),
        header_names=header_names,
        secrets=CaseSecrets(tuple(secrets)),
    )


def _seeded_values(run: JourneyRun, form: Mapping[str, str], row: Mapping[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, value in form.items():
        if not value.startswith("$seed:"):
            out[name] = value
            continue
        field_name = value.removeprefix("$seed:")
        if field_name == "name":
            out[name] = str(row["name"])
        elif field_name == "phone":
            out[name] = str(row["phone"])
        elif field_name == "customer_id":
            out[name] = str(row["customer_id"])
        elif field_name == "zip_or_city":
            out[name] = str(row["zip"])
        elif field_name == "invoice_number":
            out[name] = str(
                run.db.scalar(
                    "SELECT invoice_id FROM invoices WHERE customer_id = ? ORDER BY issued_date DESC LIMIT 1",
                    (row["customer_id"],),
                )
            )
    return out


def _inbox_code(client: Any, mismatches: list[str]) -> str | None:
    try:
        response = client.call("GET", "/api/demo/inbox", operation_id="listDemoInbox")
    except AssertionError as exc:
        mismatches.append(_first_line(exc))
        response = client.responses[-1]
    live = [m for m in _body(response).get("messages") or [] if m.get("status") == "active" and m.get("code")]
    return str(max(live, key=lambda m: m["at"])["code"]) if live else None
