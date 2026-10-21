"""Generator for the eval case files (AEA-06): split, transcript-derived scripts, mix, schema.

Reshapes issued text only; no model is called. ``python -m eval.cases.build [--check]``.
Standard library, pydantic and eval.cases only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Final
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

from eval.cases.models import (
    SCHEMA_MODELS,
    CaseKey,
    CaseScript,
    MixRecord,
    MixRow,
    RetrievalQuery,
    ScriptedTurn,
    SplitMix,
    SplitRecord,
    dump_canonical,
)

SEED: Final = 20261021  # chosen before any draw: the build date; recorded in split.json
TRANSCRIPT_CASES: Final = 60  # PRD §8 [T]
METHOD: Final = "template-whole, stratified by family and support level"
DEMO_START: Final = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))
LABELLED_BY: Final = "Claude (AEA-06)"
LABELLED_ON: Final = date(2026, 10, 21)  # the date of the first generation run; never recomputed
CALL_MAP: Final = Path("docs/data/handoff-inventory-call-map.csv")
TRANSCRIPTS: Final = Path("docs/data/issued/meridian_dataset/call_transcripts")
CASES: Final = Path("eval/cases")
WORKED_PAIR_CALLS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "WP-1": "CALL-20260707-0148",
        "WP-2": "CALL-20260710-0373",
        "WP-3": "CALL-20260814-0003",
        "WP-4": "CALL-20260902-0001",
        "WP-5": "CALL-20260721-0093",
        "WP-6": "CALL-20260706-0182",
        "WP-7": "CALL-20260710-0136",
        "WP-8": "CALL-20260710-0364",
    }
)
BRAND_WORDS: Final = re.compile(r"\b(trane|carrier|goodman|rheem|lennox)\b")
_NORTH: Final = "MHC-10004"
IDENTITY_SEED: Final[Mapping[str, str]] = MappingProxyType(
    {  # category -> seeded customer (callers cannot be matched to the DB: inventory "Limits" item 2)
        **dict.fromkeys(
            ("SCH-HVAC", "SCH-PLUMB", "SCH-TUNEUP", "EST-REPLACE", "MULTI-REPAIR-PLAN", "WAR-REPEAT"), _NORTH
        ),
        **dict.fromkeys(("SCH-CONFIRM", "SCH-CANCEL", "MEM-RENEW", "MEM-CANCEL", "WAR-PARTS"), "MHC-10001"),
        **dict.fromkeys(("SCH-RESCHED", "SCH-LATE"), "MHC-57204"),
        "WAR-CLAIM": "MHC-10003",
        **dict.fromkeys(("BILL-BALANCE", "BILL-EXPLAIN", "BILL-PAY"), "MHC-10002"),
    }
)
_EARLIEST: Final = "The earliest window works for me."
CLOSING_LINE: Final[Mapping[str, str]] = MappingProxyType(
    {
        **dict.fromkeys(
            ("SCH-HVAC", "SCH-PLUMB", "SCH-TUNEUP", "EST-REPLACE", "MULTI-REPAIR-PLAN", "WAR-REPEAT"),
            _EARLIEST,
        ),
        "SCH-CANCEL": "Yes, please cancel it.",
        "SCH-RESCHED": "Yes, go ahead and move it.",
    }
)
INVOICE_SEEDED: Final = "MHC-10002"  # its one invoice: INV-204411, $478.00 (db:invoices/INV-204411)
INVOICE_ID: Final = re.compile(r"INV-\d{6}")
DOLLARS: Final = re.compile(r"\$\d[\d,]*(?:\.\d{2})?")


@dataclass(frozen=True)
class CallRow:
    call_id: str
    family: str
    category: str
    support_level: str
    template: str


def read_call_map(root: Path) -> list[CallRow]:
    """The 420 rows of the issued call map, sorted by call id."""
    with (root / CALL_MAP).open(newline="", encoding="utf-8") as handle:
        rows = [
            CallRow(r["call_id"], r["family"], r["initial"], r["support_level"], r["template"])
            for r in csv.DictReader(handle)
        ]
    return sorted(rows, key=lambda r: r.call_id)


def draw_unit(template: str) -> str:
    """The unit a template is drawn in: the four brand variants of one complaint are one unit (audit D-1)."""
    return BRAND_WORDS.sub("#", template)


def _strata(rows: Sequence[CallRow]) -> dict[tuple[str, str], list[CallRow]]:
    strata: dict[tuple[str, str], list[CallRow]] = defaultdict(list)
    for row in rows:
        strata[(row.family, row.support_level)].append(row)
    return strata


def draw(rows: Sequence[CallRow], seed: int) -> tuple[dict[str, str], random.Random]:
    """Algorithm A: template -> split. Returns the assignment and the rng, ready for the transcript sample."""
    calls_per_unit = Counter(draw_unit(r.template) for r in rows)
    template_of = {r.call_id: r.template for r in rows}
    forced = {draw_unit(template_of[call]) for call in WORKED_PAIR_CALLS.values()}
    split_of_unit: dict[str, str] = {}
    total = {"dev": 0, "held-out": 0}
    for unit in sorted(forced):
        split_of_unit[unit] = "dev"
        total["dev"] += calls_per_unit[unit]
    rng = random.Random(seed)  # noqa: S311 - reproducible sampling, not security
    for _key, members in sorted(_strata(rows).items()):
        units = {draw_unit(r.template) for r in members}
        stratum = {"dev": sum(calls_per_unit[u] for u in units & forced), "held-out": 0}
        free = sorted(units - forced)
        rng.shuffle(free)
        for unit in free:
            if stratum["dev"] != stratum["held-out"]:
                pick = min(stratum, key=lambda s: stratum[s])
            elif total["dev"] != total["held-out"]:
                pick = min(total, key=lambda s: total[s])
            else:
                pick = "dev"
            split_of_unit[unit] = pick
            stratum[pick] += calls_per_unit[unit]
            total[pick] += calls_per_unit[unit]
    assignment = {r.template: split_of_unit[draw_unit(r.template)] for r in rows}
    return dict(sorted(assignment.items())), rng


def stratum_quotas(rows: Sequence[CallRow], total: int = TRANSCRIPT_CASES) -> dict[tuple[str, str], int]:
    """Largest-remainder quotas per (family, support level) stratum."""
    strata = _strata(rows)
    exact = {k: Fraction(total * len(v), len(rows)) for k, v in strata.items()}
    quotas = {k: math.floor(q) for k, q in exact.items()}
    extra = total - sum(quotas.values())
    by_remainder = sorted(exact, key=lambda k: (-(exact[k] - quotas[k]), k))
    for key in by_remainder[:extra]:
        quotas[key] += 1
    return {k: max(q, 1) for k, q in sorted(quotas.items())}


def sample_calls(rows: Sequence[CallRow], rng: random.Random) -> list[CallRow]:
    """Algorithm B: the transcript sample, drawn with the rng that made the split."""
    quotas = stratum_quotas(rows)
    worked = set(WORKED_PAIR_CALLS.values())
    picked: list[CallRow] = []
    for key, members in sorted(_strata(rows).items()):
        pool = sorted((r for r in members if r.call_id not in worked), key=lambda r: r.call_id)
        picked.extend(sorted(rng.sample(pool, quotas[key]), key=lambda r: r.call_id))
    return picked


def _norm(text: str) -> list[str]:
    return re.sub(r"[^a-z# ]", "", re.sub(r"\d+", "#", text.lower())).split()


def request_line(call_id: str, template: str, transcript: str) -> str:
    """The first customer line that shares at least 60% of the template's words."""
    want = set(_norm(template))
    for line in transcript.splitlines():
        if line.startswith("Customer: "):
            text = line[len("Customer: ") :].strip()
            if len(want & set(_norm(text))) >= 0.6 * len(want):
                return text
    raise ValueError(f"no request line in {call_id}")


def transcript_script(row: CallRow, split: str, transcript: str) -> CaseScript:
    """One generated case script for a sampled transcript call."""
    text = request_line(row.call_id, row.template, transcript)
    seed = IDENTITY_SEED.get(row.category)
    notes: list[str] = []
    if seed is not None:
        notes.append(
            f"Callers cannot be matched to the DB (inventory, Limits 2); seeded customer {seed} substituted."
        )
    if seed == INVOICE_SEEDED:
        text = DOLLARS.sub("$478", INVOICE_ID.sub("INV-204411", text))
        notes.append("Invoice number and amount replaced by the seeded customer's INV-204411 and $478.")
    turns = [ScriptedTurn(kind="text", text=text)]
    if seed is not None:
        turns.append(ScriptedTurn(kind="form", form={"name": "$seed:name", "phone": "$seed:phone"}))
        turns.append(ScriptedTurn(kind="code_from_inbox"))
    closing = CLOSING_LINE.get(row.category)
    if closing is not None:
        turns.append(ScriptedTurn(kind="text", text=closing))
        notes.insert(
            1 if seed is not None else 0,
            f"Closing line '{closing}' scripted: the call's own slot talk refers to its July–September calendar.",
        )
    return CaseScript(
        case_id=f"T-{row.call_id}",
        provenance="issued-transcript",
        source_ref=row.call_id,
        template=row.template,
        category=row.category,
        family=row.family,
        support_level=row.support_level,
        split="held-out" if split == "held-out" else "dev",
        seeded_customer=seed,
        clock=DEMO_START,
        turns=tuple(turns),
        synthetic="partly" if notes else "no",
        synthetic_assumption=" ".join(notes) if notes else None,
        varied_dimension=None,
        synthetic_source_case=None,
        labelled_by=LABELLED_BY,
        labelled_on=LABELLED_ON,
    )


def compute_mix(scripts: Sequence[CaseScript]) -> MixRecord:
    """The published mix per split: size, categories, transcript vs synthetic."""
    splits: dict[str, SplitMix] = {}
    for name in ("dev", "held-out"):
        members = [s for s in scripts if s.split == name]
        counts: Counter[tuple[str, str, str | None]] = Counter()
        for s in members:
            origin = "synthetic" if s.synthetic == "yes" else "transcript"
            tests = (s.varied_dimension or "").split(": ", 1)[0] if origin == "synthetic" else None
            counts[(s.category or "none", origin, tests)] += 1
        rows = tuple(
            MixRow(category=c, count=n, origin=o, tests=t)  # type: ignore[arg-type]
            for (c, o, t), n in sorted(counts.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2] or ""))
        )
        synthetic = sum(1 for s in members if s.synthetic == "yes")
        splits[name] = SplitMix(
            size=len(members),
            transcript_derived=len(members) - synthetic,
            synthetic=synthetic,
            categories=tuple(sorted({s.category for s in members if s.category})),
            rows=rows,
        )
    return MixRecord(splits=splits)  # type: ignore[arg-type]


def schema_text() -> str:
    """case.schema.json: the JSON Schema of every model."""
    _, doc = models_json_schema(
        [(m, "validation") for m in SCHEMA_MODELS],
        title="Meridian eval case files (stage7/data.md §5, DAT-27)",
    )
    doc["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _redump(path: Path, model: type[BaseModel]) -> bytes:
    return dump_canonical(model.model_validate_json(path.read_bytes()))


def render_all(root: Path) -> dict[Path, bytes]:
    """Every file the generator owns or canonicalises, with its bytes."""
    cases = root / CASES
    rows = read_call_map(root)
    assignment, rng = draw(rows, SEED)
    out: dict[Path, bytes] = {cases / "case.schema.json": schema_text().encode("utf-8")}
    generated: dict[Path, CaseScript] = {}
    for row in sample_calls(rows, rng):
        split = assignment[row.template]
        text = (root / TRANSCRIPTS / f"{row.call_id}.txt").read_text(encoding="utf-8")
        folder = "heldout" if split == "held-out" else "dev"
        generated[cases / folder / f"T-{row.call_id}.case.json"] = transcript_script(row, split, text)
    for path, script in generated.items():
        out[path] = dump_canonical(script)
    for folder, pattern, model in (
        ("dev", "*.case.json", CaseScript),
        ("heldout", "*.case.json", CaseScript),
        ("dev", "*.key.json", CaseKey),
        ("retrieval", "*.json", RetrievalQuery),
    ):
        for path in sorted((cases / folder).glob(pattern)):
            if path not in out:
                out[path] = _redump(path, model)
    scripts = [CaseScript.model_validate_json(b) for p, b in out.items() if p.name.endswith(".case.json")]
    old = cases / "split.json"
    sealed = SplitRecord.model_validate_json(old.read_bytes()).heldout_key_sha256 if old.exists() else None
    split_record = SplitRecord.model_validate(
        {"seed": SEED, "method": METHOD, "assignment": assignment, "heldout_key_sha256": sealed}
    )
    out[old] = dump_canonical(split_record)
    out[cases / "mix.json"] = dump_canonical(compute_mix(scripts))
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the eval case files.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 if any file would change")
    args = parser.parse_args(argv)
    root: Path = args.root
    out = render_all(root)
    cases = root / CASES
    stale = [
        p
        for folder in ("dev", "heldout")
        for p in sorted((cases / folder).glob("T-*.case.json"))
        if p not in out
    ]
    changed = [p for p, b in out.items() if not p.exists() or p.read_bytes() != b]
    if args.check:
        for p in [*changed, *stale]:
            print(f"would change: {p.relative_to(root)}")
        return 1 if changed or stale else 0
    for p in changed:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(out[p])
    for p in stale:
        p.unlink()
    assignment = SplitRecord.model_validate_json(out[cases / "split.json"]).assignment
    units = {draw_unit(t): s for t, s in assignment.items()}
    dev_units = sum(1 for s in units.values() if s == "dev")
    n_dev = sum(1 for p in out if p.parent.name == "dev" and p.name.endswith(".case.json"))
    n_held = sum(1 for p in out if p.parent.name == "heldout")
    print(
        f"dev scripts {n_dev}, held-out scripts {n_held}, units {dev_units}/{len(units) - dev_units}, seed {SEED}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
