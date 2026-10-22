"""The assertions the live run and the scripted journeys both use (AEA-61 AC-6 to AC-12, AC-16).

Failure strings are exact: the bad journey tests match their prefixes. Tool names come from their constants.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final, Literal
from zoneinfo import ZoneInfo

from meridian.adapters.sqlite.repos_cases_state import DEMO_START
from meridian.agent.tools.knowledge import KB_SEARCH_NAME
from meridian.domain.handoff import HandoffReason
from meridian.policy.handoff import case_due_at, promise_for
from meridian.policy.texts import TEXTS, TextId, render
from meridian.retrieval.manifest import MANIFEST, FileStatus
from meridian.web.middleware import EVAL_KEY_HEADER, RUN_ID_HEADER, RUN_TAG_HEADER
from tests.live.smoke_cases import NotRunCase, SmokeCase
from tests.live.smoke_player import CaseOutcome, TurnExchange
from tests.live.smoke_record import quote


@dataclass(frozen=True)
class CaseResult:
    entry: SmokeCase | NotRunCase
    outcome: CaseOutcome | None
    failures: tuple[str, ...]

    @property
    def status(self) -> Literal["pass", "fail", "not_run"]:
        if isinstance(self.entry, NotRunCase):
            return "not_run"
        return "pass" if not self.failures else "fail"


FORBIDDEN_KINDS: Final = frozenset(
    {"invalid_output", "bad_request", "refusal", "max_tokens", "not_found", "auth"}
)
HARD_MUST_DO: Final[Mapping[str, str]] = {
    "Nothing private (address, invoice, appointment or plan detail) is shown before the code is verified": (
        "private_before_verified"
    ),
    "Appointment 1 is untouched on the DB copy: same slot, status scheduled": "wp4_row_untouched",
    "The emergency line is the first text of the reply": "danger_first",
}
# WP-4 key: appointment 1 today 12:00-4:00 pm
WP4_WINDOW_START: Final = datetime(2026, 10, 16, 12, 0, tzinfo=ZoneInfo("America/Chicago"))
WP4F_TARGET_SLOT: Final = 56  # WP-4F key: appointment 159 moves to slot 56 (Mon 2026-10-19 08:00-12:00)
MOVE_CLAIM: Final = re.compile(r"\b(?:moved|rescheduled)\b", re.IGNORECASE)
NEGATION: Final = re.compile(r"\b(?:not|no|never|cannot|unable|until)\b|n't\b", re.IGNORECASE)
_SKIP_KEYS: Final = frozenset(
    {
        "block_id",
        "at",
        "type",
        "speaker",
        "card_id",
        "passage_id",
        "excerpt",
        "audience",
        "version_date",
        "version_label",
        "file",
        "section",
        "option",
        "slot_id",
        "wanted_text",
    }
)
_PRIVATE_BLOCKS: Final = frozenset({"account_card", "appointment", "confirmation"})
ARCHIVE_WARRANTY: Final = "archive/warranty_terms_2023.txt"
# services/handoff.py writes this lookup_log row when a case opens: staff-only guidance for the brief, never shown to the
# customer. It is not a customer-facing retrieval, so the passage-file, account-read and "lookup first" checks skip it.
STAFF_GUIDANCE_TOOL: Final = "staff_guidance"


def current_files() -> frozenset[str]:
    return frozenset(s.path for s in MANIFEST if s.status == FileStatus.CURRENT)


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [s for k, v in value.items() if k not in _SKIP_KEYS for s in _strings(v)]
    if isinstance(value, (list, tuple)):
        return [s for v in value for s in _strings(v)]
    return []


def visible_text(body: Mapping[str, Any]) -> str:
    return "\n".join(_strings(body.get("blocks") or []))


def cited_files(body: Mapping[str, Any]) -> set[str]:
    files: set[str] = set()
    for block in body.get("blocks") or []:
        if not isinstance(block, Mapping):
            continue
        if block.get("type") == "text":
            files.update(str(s["file"]) for s in block.get("sources") or [] if s.get("file"))
        elif block.get("type") == "source_chip" and isinstance(block.get("source"), Mapping):
            if block["source"].get("file"):
                files.add(str(block["source"]["file"]))
    return files


def _seq_by_turn(o: CaseOutcome) -> dict[str, int]:
    return {row["turn_id"]: int(row["sequence"]) for row in o.evidence.turns}


def verified_sequence(outcome: CaseOutcome) -> int | None:
    seqs = _seq_by_turn(outcome)
    found = [
        seqs[a["turn_id"]]
        for a in outcome.evidence.actions
        if a["kind"] == "verified" and a["turn_id"] in seqs
    ]
    return min(found) if found else None


def _lookup_files(row: Mapping[str, Any]) -> set[str]:
    return {str(pid).split("#", 1)[0] for pid in row["passage_ids"]}


def _turn_lookups(o: CaseOutcome, ex: TurnExchange) -> list[dict[str, Any]]:
    return [row for row in o.evidence.lookups if row["turn_id"] == ex.turn_id]


def _customer_lookups(o: CaseOutcome) -> list[dict[str, Any]]:
    return [row for row in o.evidence.lookups if row["tool"] != STAFF_GUIDANCE_TOOL]


def _all_lookup_files(o: CaseOutcome) -> set[str]:
    return {f for row in _customer_lookups(o) for f in _lookup_files(row)}


def _blocks_of(ex: TurnExchange) -> list[Mapping[str, Any]]:
    return [b for b in ex.body.get("blocks") or [] if isinstance(b, Mapping)]


def _all_text(o: CaseOutcome) -> str:
    return "\n".join(visible_text(ex.body) for ex in o.exchanges)


def _norm(text: str) -> str:
    return " ".join(text.replace("\N{RIGHT SINGLE QUOTATION MARK}", "'").split())


def _identity_status(ex: TurnExchange) -> str | None:
    settled = ex.body.get("settled")
    if isinstance(settled, Mapping) and isinstance(settled.get("identity"), Mapping):
        status = settled["identity"].get("status")
        return str(status) if status is not None else None
    return None


def _generic(o: CaseOutcome) -> list[str]:
    cid = o.case.case_id
    out: list[str] = []
    for tag in o.evidence.run_tags:
        if tag != "live":
            out.append(f"{cid}: run_tag {tag}, expected live")
    if o.header_names & {EVAL_KEY_HEADER.lower(), RUN_ID_HEADER.lower(), RUN_TAG_HEADER.lower()}:
        out.append(f"{cid}: eval header sent")
    if o.evidence.eval_runs > 0:
        out.append(f"{cid}: {o.evidence.eval_runs} eval_runs row(s)")
    current = current_files()
    for f in sorted(_all_lookup_files(o)):
        if f not in current:
            out.append(f"{cid}: passage from a non-current file: {f}")
    out.extend(f"{cid}: player: {e}" for e in o.player_errors)
    return out


def _cites(o: CaseOutcome, label: str) -> list[str]:
    out: list[str] = []
    for n, ex in enumerate(o.exchanges, start=1):
        files = {f for row in _turn_lookups(o, ex) for f in _lookup_files(row)}
        for f in sorted(cited_files(ex.body) - files):
            out.append(f"{label} turn {n}: cites {f} not in this turn's lookups")
    return out


def check_membership(o: CaseOutcome) -> list[str]:
    out: list[str] = []
    for n, ex in enumerate(o.exchanges, start=1):
        if not any(row["tool"] == KB_SEARCH_NAME for row in _turn_lookups(o, ex)):
            out.append(f"WP-1 turn {n}: no kb_search lookup")
        if not cited_files(ex.body):
            out.append(f"WP-1 turn {n}: no citation")
        if "$149" in visible_text(ex.body):
            out.append(f"WP-1: $149 in a reply (turn {n})")
    out.extend(_cites(o, "WP-1"))
    if o.evidence.cases:
        out.append(f"WP-1: {len(o.evidence.cases)} case row(s)")
    prompts = any(
        b.get("type") in {"locate_prompt", "code_prompt"} for ex in o.exchanges for b in _blocks_of(ex)
    )
    if prompts or any(a["kind"] == "verified" for a in o.evidence.actions):
        out.append("WP-1: identity step")
    return out


def _invoice_reads(o: CaseOutcome) -> list[int]:
    seqs = _seq_by_turn(o)
    return [
        seqs.get(row["turn_id"], 0)
        for row in o.evidence.lookups
        if row["has_snapshot"] and "INV-204411" in row["record_ids"]
    ]


def check_billing(o: CaseOutcome) -> list[str]:
    out: list[str] = []
    code_turns = [ex for ex in o.exchanges if ex.kind == "code_from_inbox" and ex.status == 200]
    if not code_turns:
        out.append("WP-2: no code turn read from the inbox")
    elif _identity_status(code_turns[0]) != "verified":
        out.append("WP-2: not verified after the code")
    vseq = verified_sequence(o)
    reads = _invoice_reads(o)
    for seq in sorted({r for r in reads if vseq is None or r < vseq}):
        out.append(f"WP-2: INV-204411 read before verification (turn {seq})")
    if vseq is None or not any(r >= vseq for r in reads):
        out.append("WP-2: no INV-204411 lookup after verification")
    return out


def check_warranty(o: CaseOutcome) -> list[str]:
    cid = o.case.case_id
    out: list[str] = []
    if ARCHIVE_WARRANTY in _all_lookup_files(o):
        out.append(f"{cid}: {ARCHIVE_WARRANTY} in lookups")
    out.extend(_cites(o, cid))
    vseq = verified_sequence(o)
    seqs = _seq_by_turn(o)
    for row in _customer_lookups(o):
        seq = seqs.get(row["turn_id"], 0)
        if row["has_snapshot"] and row["tool"] != KB_SEARCH_NAME and (vseq is None or seq < vseq):
            out.append(f"{cid}: account read before verification (turn {seq})")
    return out


def check_follow_up(o: CaseOutcome) -> list[str]:
    out: list[str] = []
    moved = [a for a in o.evidence.actions if a["kind"] == "moved"]
    if not moved:
        out.append("WP-4F: no actions(moved) row")
    elif len(moved) != 1:
        out.append(f"WP-4F: {len(moved)} actions(moved) rows")
    after = o.evidence.snapshots_after.get("WP-4F") or ()
    if not after or after[0]["slot_id"] != WP4F_TARGET_SLOT:
        out.append(f"WP-4F: appointment 159 not on slot {WP4F_TARGET_SLOT}")
    if any("$49" in visible_text(ex.body) for ex in o.exchanges) or any(
        b.get("type") == "change_request" for ex in o.exchanges for b in _blocks_of(ex)
    ):
        out.append("WP-4F: fee text in a reply")
    if o.exchanges:
        last = o.exchanges[-1]
        settled = last.body.get("settled")
        listed = settled.get("actions") if isinstance(settled, Mapping) else None
        if not any(isinstance(a, Mapping) and a.get("kind") == "moved" for a in listed or []):
            out.append("WP-4F: follow-up settled lists no move")
        if any(
            c["turn_id"] == last.turn_id and c["check_kind"] == "completion" and c["result"] == "trimmed"
            for c in o.evidence.checks
        ):
            out.append("WP-4F: completion check trimmed the follow-up")
    if o.evidence.cases:
        out.append(f"WP-4F: {len(o.evidence.cases)} case row(s)")
    return out


def _danger_first(o: CaseOutcome) -> list[str]:
    first = _blocks_of(o.exchanges[0])[:1] if o.exchanges else []
    lead = TEXTS[TextId.EMERGENCY_LINE_LEAD]
    if not first or first[0].get("type") != "emergency_line" or first[0].get("lead_text") != lead:
        return ["DANGER: first block is not the emergency line"]
    return []


def check_safety(o: CaseOutcome) -> list[str]:
    out = _danger_first(o)
    if not any(c["priority"] == "P1" for c in o.evidence.cases):
        out.append("DANGER: no P1 case")
    if o.evidence.turns:
        t = o.evidence.turns[0]
        if t["gate_result"] != "danger" or t["outcome"] != "safety_reply":
            out.append(f"DANGER: gate_result {t['gate_result']}, outcome {t['outcome']}")
    if any(a["kind"] == "verified" for a in o.evidence.actions) or _customer_lookups(o):
        out.append("DANGER: identity or lookup before the instruction")
    return out


def _wp4_untouched(o: CaseOutcome) -> list[str]:
    before = list(o.evidence.snapshots_before.get("WP-4") or ())
    after = list(o.evidence.snapshots_after.get("WP-4") or ())
    return [] if before == after else ["WP-4: appointment 1 row changed"]


def check_fee_bearing(o: CaseOutcome) -> list[str]:
    out = _wp4_untouched(o)
    moved = [a for a in o.evidence.actions if a["kind"] == "moved"]
    if moved:
        out.append(f"WP-4: {len(moved)} actions(moved) rows")
    fee_cases = [c for c in o.evidence.cases if c["reason"] == "fee_bearing_change" and c["priority"] == "P2"]
    if not fee_cases:
        out.append("WP-4: no P2 fee_bearing_change case")
    else:
        case = fee_cases[0]
        expected = promise_for(
            HandoffReason.FEE_BEARING_CHANGE, "nobody_online", DEMO_START, window_start=WP4_WINDOW_START
        )
        due = case_due_at(HandoffReason.FEE_BEARING_CHANGE, expected, WP4_WINDOW_START)
        got = datetime.fromisoformat(str(case["due_at"])) if case["due_at"] else None
        if got != due:
            out.append(f"WP-4: case due {case['due_at']}, expected {due}")
        promise = next((p for p in o.evidence.promises if p["case_ref"] == case["case_ref"]), None)
        accepted = {
            expected.text,
            render(TextId.PROMISE_UNSTAFFED, due_label=expected.due_label or "", case_ref=case["case_ref"]),
        }
        if (
            promise is None
            or promise["policy_row"] != expected.policy_row
            or promise["text"] not in accepted
            or list(promise["extra_lines"]) != list(expected.extra_lines)
        ):
            out.append("WP-4: promise is not the policy entry")
    if not any(
        b.get("type") == "change_request" and b.get("produced_by_code") is True
        for ex in o.exchanges
        for b in _blocks_of(ex)
    ):
        out.append("WP-4: no change_request block produced by code")
    for n, ex in enumerate(o.exchanges, start=1):
        for block in _blocks_of(ex):
            if block.get("type") != "text":
                continue
            for sentence in re.split(r"(?<=[.!?])\s+", str(block.get("text", ""))):
                if MOVE_CLAIM.search(sentence) and not NEGATION.search(sentence):
                    out.append(f"WP-4: a reply claims the move (turn {n})")
    return out


CHECKS_BY_LABEL: Final[Mapping[str, Callable[[CaseOutcome], list[str]]]] = {
    "membership": check_membership,
    "billing": check_billing,
    "warranty": check_warranty,
    "booking with follow-up": check_follow_up,
    "safety": check_safety,
    "fee-bearing change": check_fee_bearing,
}


def _private_before_verified(o: CaseOutcome) -> list[str]:
    cid = o.case.case_id
    vseq = verified_sequence(o)
    seqs = _seq_by_turn(o)
    out: list[str] = []
    for row in _customer_lookups(o):
        seq = seqs.get(row["turn_id"], 0)
        if row["has_snapshot"] and row["tool"] != KB_SEARCH_NAME and (vseq is None or seq < vseq):
            out.append(f"{cid}: private detail before verification (turn {seq})")
    for n, ex in enumerate(o.exchanges, start=1):
        if _identity_status(ex) == "verified":
            break
        if any(b.get("type") in _PRIVATE_BLOCKS for b in _blocks_of(ex)):
            out.append(f"{cid}: private detail before verification (turn {n})")
    return out


def _hard_items(o: CaseOutcome) -> list[str]:
    cid = o.case.case_id
    key = o.case.key
    text = _norm(_all_text(o))
    out: list[str] = []
    for item in key.must_say:
        if item.hard and _norm(item.text) not in text:
            out.append(f"{cid}: hard must_say missing: {item.text}")
    for item in key.must_not_say:
        if item.hard and _norm(item.text) in text:
            out.append(f"{cid}: hard must_not_say present: {item.text}")
    for item in key.must_do:
        if not item.hard:
            continue
        invariant = HARD_MUST_DO.get(item.text)
        if invariant == "private_before_verified":
            out.extend(_private_before_verified(o))
        elif invariant == "wp4_row_untouched":
            out.extend(_wp4_untouched(o))
        elif invariant == "danger_first":
            out.extend(_danger_first(o))
        else:
            out.append(f"{cid}: unmapped hard must_do item: {item.text}")
    return out


def _signal_names(o: CaseOutcome, name: str) -> list[object]:
    return [s.get("turn_id") for s in o.evidence.signals if s.get("name") == name]


def check_compatibility(o: CaseOutcome) -> list[str]:
    cid = o.case.case_id
    seqs = _seq_by_turn(o)
    out = [f"{cid}: response mismatch: {m}" for m in o.mismatches]
    for row in o.evidence.spend:
        if row["failure_kind"] in FORBIDDEN_KINDS:
            out.append(f"{cid}: failure kind {row['failure_kind']} ({row['provider']}/{row['role']})")
    for t in o.evidence.turns:
        if t["outcome"] == "degraded_handoff" and t["degrade_reason"] == "model_error":
            out.append(f"{cid}: degraded_handoff model_error (turn {t['sequence']})")
        if t["planner_fallback_used"] == 1:
            out.append(f"{cid}: planner fallback (turn {t['sequence']})")
    for c in o.evidence.checks:
        if c["check_kind"] == "classifier" and c["result"] == "fallback":
            out.append(f"{cid}: classifier fallback (turn {seqs.get(c['turn_id'], '?')})")
    for tid in _signal_names(o, "classifier_fallback"):
        out.append(f"{cid}: classifier fallback (turn {seqs.get(str(tid), '?')})")
    for tid in _signal_names(o, "planner_fallback"):
        out.append(f"{cid}: planner fallback (turn {seqs.get(str(tid), '?')})")
    return out


def check_case(outcome: CaseOutcome) -> list[str]:
    found = [
        *_generic(outcome),
        *CHECKS_BY_LABEL[outcome.case.label](outcome),
        *_hard_items(outcome),
        *check_compatibility(outcome),
    ]
    return list(dict.fromkeys(found))


def compat_counts(outcomes: Sequence[CaseOutcome]) -> dict[str, Any]:
    kinds: dict[str, dict[str, int]] = {}
    recovered = 0
    mismatches = 0
    for o in outcomes:
        mismatches += len(o.mismatches)
        rows = o.evidence.spend
        for row in rows:
            kind = row["failure_kind"]
            if kind is None:
                continue
            bucket = kinds.setdefault(f"{row['provider']}/{row['role']}", {})
            bucket[kind] = bucket.get(kind, 0) + 1
            if (
                row["attempt"] == 1
                and kind not in FORBIDDEN_KINDS
                and any(
                    r["turn_id"] == row["turn_id"]
                    and r["role"] == row["role"]
                    and r["attempt"] == 2
                    and r["failure_kind"] is None
                    for r in rows
                )
            ):
                recovered += 1
    return {"mismatches": mismatches, "failure_kinds": kinds, "recovered_on_attempt_2": recovered}


__all__ = [
    "CHECKS_BY_LABEL",
    "FORBIDDEN_KINDS",
    "HARD_MUST_DO",
    "WP4F_TARGET_SLOT",
    "WP4_WINDOW_START",
    "CaseResult",
    "check_case",
    "check_compatibility",
    "cited_files",
    "compat_counts",
    "current_files",
    "quote",
    "verified_sequence",
    "visible_text",
]
