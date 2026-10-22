"""Quote and scrub helpers, record rendering and writing for the live smoke (AEA-61 AC-14, AC-15, AC-16)."""

from __future__ import annotations

import re
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from meridian.privacy.redact import RedactionProfile, redact
from tests.journeys.support.record import FIELDS, ISSUED_REL, RecordData, render_record
from tests.live.smoke_cases import NotRunCase, SmokeCase

if TYPE_CHECKING:
    from tests.live.smoke_checks import CaseResult
    from tests.live.smoke_player import CaseOutcome

NOT_AN_EVAL_LINE: Final = "Compatibility only; not a containment, accuracy or quality result"
LIVE_LEVEL: Final = "verified with live models"
SPENT_SOURCE: Final = "LIVE_SMOKE_SPENT_TODAY_USD as stated by the gate::paid approver"
LIVE_TITLE_SUFFIX: Final = " (live-model smoke run)"
_NUMBER = re.compile(r"-live-smoke-(\d+)\.md$")
_DASH = "\N{EM DASH}"


def scrub(text: str, forbidden: Iterable[str]) -> str:
    for value in sorted({v for v in forbidden if v}, key=len, reverse=True):
        text = text.replace(value, "[removed]")
    return text


def quote(text: str, forbidden: Iterable[str] = ()) -> str:
    """TRACE-profile redaction (LOG returns an empty string by contract), cut to 300 characters, then scrubbed (PD-1)."""
    return scrub(redact(text, RedactionProfile.TRACE).text[:300], forbidden)


@dataclass
class SmokeRun:
    spent_today_usd: float
    cap_usd: float
    results: list[CaseResult]
    agent_version: str = "dev"
    role_models: Mapping[str, str] = field(default_factory=dict)
    index_note: str = ""
    issued_sha_before: str = ""
    issued_sha_after: str = ""
    opened_counts: Mapping[str, int] = field(default_factory=dict)
    offending: tuple[str, ...] = ()
    eval_reports_unchanged: bool = True
    langfuse_on: bool = False
    output_text: str = field(default="", repr=False)
    record_path: Path | None = None
    forbidden: tuple[str, ...] = field(default=(), repr=False)

    @property
    def outcomes(self) -> list[CaseOutcome]:
        return [r.outcome for r in self.results if r.outcome is not None]

    @property
    def run_total_usd(self) -> float:
        return sum(o.cost_usd for o in self.outcomes)


def _case_id(entry: SmokeCase | NotRunCase) -> str:
    return entry.case_id or _DASH


def _seq(outcome: CaseOutcome, turn_id: object) -> Any:
    for row in outcome.evidence.turns:
        if row["turn_id"] == turn_id:
            return row["sequence"]
    return "?"


def _text_blocks(body: Mapping[str, Any]) -> str:
    blocks = body.get("blocks") or []
    return " ".join(
        str(b.get("text", "")) for b in blocks if isinstance(b, Mapping) and b.get("type") == "text"
    )


def _result_lines(run: SmokeRun, forbidden: Collection[str]) -> list[str]:
    lines: list[str] = []
    for r in run.results:
        entry = r.entry
        head = f"{_case_id(entry)} ({entry.label}, {entry.journey})"
        if isinstance(entry, NotRunCase):
            lines.append(f"{head}: {entry.reason}")
        elif r.failures:
            lines.append(f"{head}: fail: " + "; ".join(quote(f, forbidden) for f in r.failures))
        else:
            lines.append(f"{head}: pass")
    for r in run.results:
        o = r.outcome
        if o is None:
            continue
        cid = o.case.case_id
        if cid == "DANGER" and o.evidence.turns:
            first = o.evidence.turns[0]
            raised = any(
                c["check_kind"] == "classifier" and c["result"] == "raised" for c in o.evidence.checks
            )
            lines.append(
                f"DANGER path: {'classifier' if raised else 'danger_rule'}; model calls: {first['model_calls']}"
            )
        if cid == "WP-4F" and o.exchanges:
            reply = quote(_text_blocks(o.exchanges[-1].body), forbidden)
            lines.append(f"WP-4F follow-up reply: {reply}")
        if cid == "WP-4":
            for case in o.evidence.cases:
                promise = next((p for p in o.evidence.promises if p["case_ref"] == case["case_ref"]), None)
                text = quote(str(promise["text"]), forbidden) if promise else ""
                lines.append(
                    f"WP-4 case {case['case_ref']} {case['priority']} due {case['due_at']}; promise: {text}"
                )
        if cid == "WP-2":
            verified = [a for a in o.evidence.actions if a["kind"] == "verified"]
            vseq = min((_seq(o, a["turn_id"]) for a in verified), default="never")
            reads = sorted(
                {
                    _seq(o, row["turn_id"])
                    for row in o.evidence.lookups
                    if row["has_snapshot"] and "INV-204411" in row["record_ids"]
                }
            )
            lines.append(f"WP-2 verified at turn {vseq}; INV-204411 snapshots at turns {reads}")
    return lines


def _evidence_lines(run: SmokeRun) -> list[str]:
    lines: list[str] = []
    for o in run.outcomes:
        cid = o.case.case_id
        for t in o.evidence.turns:
            lines.append(
                f"{cid} t{t['sequence']}: trace_id={t['trace_id']} trace_export={t['trace_export']} "
                f"server_ms={t['server_ms']}"
            )
        for s in o.evidence.spend:
            lines.append(
                f"{cid} t{_seq(o, s['turn_id'])} {s['role']} a{s['attempt']}: {s['provider']}/{s['model']} "
                f"req={s['provider_request_id']} failure={s['failure_kind']} latency_ms={s['latency_ms']} "
                f"cost_usd={(s['cost_usd'] or 0.0):.6f}"
            )
        lines.append(f"{cid} total cost_usd {o.cost_usd:.6f}")
    lines.append(
        f"run total cost_usd {run.run_total_usd:.6f} (SUM(cost_usd) over the run's spend_ledger rows)"
    )
    lines.append(
        f"spent today before the run: {run.spent_today_usd:.3f} USD ({SPENT_SOURCE}); cap {run.cap_usd:.2f}"
    )
    return lines


def render_smoke_record(
    run: SmokeRun, *, scope: str, revision: str, command: str, forbidden: Collection[str]
) -> str:
    from tests.live.smoke_checks import compat_counts

    entries = [r.entry for r in run.results]
    claim = (
        "AEA-61 live-model smoke set: "
        + ", ".join(f"{_case_id(e)} ({e.label}, {e.journey})" for e in entries)
        + f" through the real app with the production model adapters. {NOT_AN_EVAL_LINE}."
    )
    not_passed = sum(1 for r in run.results if r.status != "pass")
    level = LIVE_LEVEL + " for the cases marked pass" + (f"; {not_passed} not passed" if not_passed else "")
    models = ", ".join(f"{role}={model}" for role, model in sorted(run.role_models.items()))
    environment = (
        "127.0.0.1, ephemeral port per case; server: launch_server(settings, overrides=None) over "
        "create_app(Settings.from_env(<live environ>)) (web.md section 15, no overrides); "
        f"DB copy: {ISSUED_REL} (sha256 {run.issued_sha_before}) copied by the app's first boot into a temp data dir "
        f"per case; index: {run.index_note}; model adapters: production (AnthropicAdapter, JevAdapter); "
        f"role models: {models}; Langfuse export {'on' if run.langfuse_on else 'off'}"
    )
    result = _result_lines(run, forbidden)
    result.append(f"compatibility counts: {compat_counts(run.outcomes)}")
    result.append(f"opened paths by folder: {dict(run.opened_counts)}; offending: {len(run.offending)}")
    result.append(f"issued DB sha256 before {run.issued_sha_before} after {run.issued_sha_after}")
    result.append(f"eval/reports unchanged: {'yes' if run.eval_reports_unchanged else 'no'}")
    blocked = "browser-level live smoke waits on AEA-58 and the UX session's selector contract (docs/plans/ux-join/)"
    if not run.langfuse_on:
        blocked += "; trace IDs: the four LANGFUSE_* values were not set, so trace_export = off"
    values = {
        "Claim": claim,
        "Level": level,
        "Tested revision": revision,
        "Environment": environment,
        "Command": command,
        "Result": "\n".join(result),
        "Evidence location": "\n".join(_evidence_lines(run)),
        "Remaining limitations": (
            "API level only, no browser (AEA-58, AEA-62); one run, no repeats; judge items and soft key items are not "
            "scored; dev split only; server_ms measured one case at a time, not the 20-at-once condition (M-23); "
            + NOT_AN_EVAL_LINE
        ),
        "Blocked by": blocked,
    }
    assert set(values) == set(FIELDS)
    text = render_record(RecordData(scope=scope, values=values))
    text = text.replace(" (journey harness run)", LIVE_TITLE_SUFFIX, 1)
    return scrub(text, forbidden)


def next_smoke_number(folder: Path) -> int:
    numbers = [int(m.group(1)) for p in folder.glob("*-live-smoke-*.md") if (m := _NUMBER.search(p.name))]
    return 1 + max(numbers, default=0)


def write_smoke_record(
    run: SmokeRun, *, root: Path, day: date, revision: str, command: str, forbidden: Collection[str]
) -> Path:
    folder = root / "docs" / "testing" / "journeys"
    folder.mkdir(parents=True, exist_ok=True)
    number = next_smoke_number(folder)
    text = render_smoke_record(
        run, scope=f"live-smoke-{number}", revision=revision, command=command, forbidden=forbidden
    )
    path = folder / f"{day.isoformat()}-live-smoke-{number}.md"
    path.write_text(text, encoding="utf-8")
    return path
