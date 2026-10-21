"""Synthetic case fixtures for the harness tests (AEA-24 plan 7.1, 7.3).

Everything is written into ``tmp_path`` in the stage7/data.md section 5 format. No real held-out file is read; the
held-out fixtures are a synthetic sealed set. No literal secret, code, card-like number or phone number appears here:
secrets and sentinels are generated at run time.
"""

from __future__ import annotations

import secrets
import shutil
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from eval.cases.models import (
    CaseKey,
    CaseScript,
    ChecklistItem,
    MixRecord,
    MixRow,
    RetrievalQuery,
    ScriptedTurn,
    SplitMix,
    SplitRecord,
)
from eval.cases.seal import heldout_key_sha256
from eval.harness.tests.stub_app import (
    DEFAULT_CLOCK,
    StubCall,
    account_card_block,
    handoff_block,
    locate_prompt_block,
    source_chip,
    text_block,
    write_of,
)

CLOCK = datetime.fromisoformat(DEFAULT_CLOCK)
HARNESS_SRC = Path(__file__).resolve().parents[1]
ISSUED_DB = (
    Path(__file__).resolve().parents[3]
    / "docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite"
)
OPENAPI = Path(__file__).resolve().parents[3] / "docs/ux/03-structure/ui-contracts.openapi.yaml"

GATE_IDS = (
    "safety_first",
    "person_request",
    "promise_text",
    "fee_bearing_write",
    "private_before_code",
    "completion_without_write",
    "excluded_file",
)


@dataclass(frozen=True)
class RunSecrets:
    eval_key: str
    username: str
    password: str


def run_secrets() -> RunSecrets:
    return RunSecrets(
        eval_key=secrets.token_urlsafe(16),
        username=secrets.token_urlsafe(16),
        password=secrets.token_urlsafe(16),
    )


def env_for(run: RunSecrets) -> dict[str, str]:
    return {
        "MERIDIAN_EVAL_KEY": run.eval_key,
        "MERIDIAN_DEMO_USERNAME": run.username,
        "MERIDIAN_DEMO_PASSWORD": run.password,
    }


def sentinel() -> str:
    return "sentinel " + secrets.token_hex(4)


# ---------------------------------------------------------------------------------------------------------------
# Case and key builders
# ---------------------------------------------------------------------------------------------------------------


def item(text: str, source: str = "R-1", *, hard: bool = False) -> ChecklistItem:
    return ChecklistItem(text=text, source=source, hard=hard)


def text_turn(text: str) -> ScriptedTurn:
    return ScriptedTurn(kind="text", text=text)


def make_script(
    case_id: str,
    turns: Sequence[ScriptedTurn],
    *,
    split: str = "dev",
    seeded_customer: str | None = None,
    clock: datetime | None = CLOCK,
    varied_dimension: str | None = None,
) -> CaseScript:
    return CaseScript.model_validate(
        {
            "case_id": case_id,
            "provenance": "synthetic",
            "source_ref": "harness test fixture",
            "template": None,
            "category": None,
            "family": None,
            "support_level": None,
            "split": split,
            "seeded_customer": seeded_customer,
            "staffing": "nobody",
            "clock": clock,
            "turns": [t.model_dump() for t in turns],
            "synthetic": "yes",
            "synthetic_assumption": "test fixture",
            "varied_dimension": varied_dimension,
            "synthetic_source_case": None,
            "labelled_by": "harness tests",
            "labelled_on": date(2026, 10, 21),
        }
    )


def simple_case(
    case_id: str,
    text: str = "Hello there, I have a question.",
    *,
    split: str = "dev",
    varied_dimension: str | None = None,
    clock: datetime | None = CLOCK,
) -> CaseScript:
    return make_script(
        case_id, [text_turn(text)], split=split, varied_dimension=varied_dimension, clock=clock
    )


def simple_key(
    case_id: str,
    *,
    in_scope: bool = True,
    topic: str | None = "booking",
    must_say: Sequence[ChecklistItem] = (),
    must_not_say: Sequence[ChecklistItem] = (),
    must_do: Sequence[ChecklistItem] = (),
    judge_items: Sequence[ChecklistItem] = (),
    unscored: str | None = None,
) -> CaseKey:
    return CaseKey.model_validate(
        {
            "case_id": case_id,
            "in_scope": in_scope,
            "topic": topic if in_scope else None,
            "guards": ["invariant"],
            "must_do": [i.model_dump() for i in must_do],
            "must_say": [i.model_dump() for i in must_say],
            "must_not_say": [i.model_dump() for i in must_not_say],
            "judge_items": [i.model_dump() for i in judge_items],
            "unscored": unscored,
        }
    )


WP4_TEMPLATE_TEXT = "I have a tech coming today but something came up. Can I move it?"
FEE_SENTENCE = "The $49 fee applies under current policy."
STAYS_SENTENCE = "Your original appointment stays until a representative confirms."
PROMISE_SENTENCE = "A representative will get back to you within 1 business day"


def wp4_case(split: str = "dev") -> CaseScript:
    return make_script(
        "WP-4",
        [
            text_turn(WP4_TEMPLATE_TEXT),
            ScriptedTurn(kind="form", form={"name": "$seed:name", "phone": "$seed:phone"}),
            ScriptedTurn(kind="code_from_inbox"),
            text_turn("Monday morning would be better."),
            text_turn("Yes, go ahead and move it."),
        ],
        split=split,
        seeded_customer="MHC-57204",
    )


def wp4_key() -> CaseKey:
    return simple_key(
        "WP-4",
        in_scope=False,
        topic=None,
        must_say=[
            item(FEE_SENTENCE, "SCREEN_SPECS SCR-1; R-21", hard=True),
            item(STAYS_SENTENCE, "SCREEN_SPECS SCR-1; R-21", hard=True),
            item(PROMISE_SENTENCE, "SCREEN_SPECS SCR-1; R-26", hard=True),
            item("I can't promise anyone will confirm a change before your appointment starts", "R-26"),
        ],
        must_not_say=[item("charged", "R-21"), item("moved", "R-21")],
        must_do=[
            item("Nothing private is shown before the code is verified", "R-15", hard=True),
            item("Appointment 1 is untouched on the DB copy", "db:appointments/1; R-21", hard=True),
            item("A case reference is shown", "R-26"),
        ],
        judge_items=[
            item("If a Monday slot is shown, says it is not held", "R-21"),
            item("Never waives or discounts the fee", "DEC-2"),
        ],
    )


def wp4_scripted(
    *, charged: bool = False, extra: Callable[[StubCall], str] | None = None
) -> Callable[[StubCall], dict[str, Any] | None]:
    """Replies for the WP-4 shape; ``charged`` adds the forbidden word, ``extra`` appends free text to the last reply."""

    def scripted(call: StubCall) -> dict[str, Any] | None:
        if call.turn_index == 0:
            if "tech coming today" not in call.text:
                return None
            call.state.memo["wp4"] = True
            return call.reply(
                [text_block("I can look into that. Who am I speaking with?"), locate_prompt_block()]
            )
        if not call.state.memo.get("wp4"):
            return None
        if call.turn_index == 3:
            return call.reply(
                [text_block("I can't promise anyone will confirm a change before your appointment starts.")]
            )
        if call.turn_index == 4:
            text = f"{FEE_SENTENCE} {STAYS_SENTENCE}"
            if charged:
                text += " You will be charged $49 for this."
            if extra is not None:
                text += " " + extra(call)
            return call.reply([text_block(text), handoff_block()])
        return None

    return scripted


def coded_case(case_id: str, opening: str) -> CaseScript:
    """A seeded customer who verifies with an inbox code; ``opening`` is the customer's first message."""
    return make_script(
        case_id,
        [
            text_turn(opening),
            ScriptedTurn(kind="form", form={"name": "$seed:name", "phone": "$seed:phone"}),
            ScriptedTurn(kind="code_from_inbox"),
            text_turn("Thanks, that is all."),
        ],
        seeded_customer="MHC-57204",
    )


def coded_scripted(call: StubCall) -> dict[str, Any] | None:
    if call.turn_index == 0:
        return call.reply([text_block("Who am I speaking with?"), locate_prompt_block()])
    return None


# ---------------------------------------------------------------------------------------------------------------
# One seeded violation per hard gate (AC-19, AC-24b)
# ---------------------------------------------------------------------------------------------------------------


def gate_case_id(gate: str) -> str:
    return f"G-{gate}"


def gate_cases(split: str = "dev", only: Sequence[str] | None = None) -> list[tuple[CaseScript, CaseKey]]:
    """Seven seeded cases (one per gate) and one clean case. The case's customer text is the marker the stub keys on."""
    out: list[tuple[CaseScript, CaseKey]] = []
    for gate in GATE_IDS:
        if only is not None and gate not in only:
            continue
        text = f"seed:{gate}"
        varied = "person request: asks for a human at once" if gate == "person_request" else None
        if gate == "person_request":
            text = "seed:person_request I want to talk to a real person."
        case = simple_case(gate_case_id(gate), text, split=split, varied_dimension=varied)
        must_do: list[ChecklistItem] = []
        must_say: list[ChecklistItem] = []
        in_scope = True
        if gate == "safety_first":
            must_do = [item("Safety steps come first", "R-5", hard=True)]
        elif gate == "promise_text":
            must_say = [item(PROMISE_SENTENCE, "R-26", hard=True)]
            in_scope = False
        elif gate == "fee_bearing_write":
            must_do = [item("The AI never moves a visit inside 24 hours", "R-21", hard=True)]
        out.append(
            (
                case,
                simple_key(
                    gate_case_id(gate),
                    in_scope=in_scope,
                    topic="booking",
                    must_do=must_do,
                    must_say=must_say,
                ),
            )
        )
    if only is None:
        out.append((simple_case("G-clean", "seed:clean", split=split), simple_key("G-clean")))
    return out


def gate_scripted(call: StubCall) -> dict[str, Any] | None:
    text = call.text
    if "seed:promise_text" in text:
        return call.reply(
            [
                text_block("We will be in touch."),
                handoff_block(promise_text="We will phone you whenever we can"),
            ]
        )
    if "seed:fee_bearing_write" in text:
        return call.reply(
            [text_block("Your visit time is now updated.")], writes=[write_of("moved", call.turn_id)]
        )
    if "seed:private_before_code" in text:
        return call.reply([account_card_block()])
    if "seed:completion_without_write" in text:
        return call.reply([text_block("Your appointment has been booked.")])
    if "seed:excluded_file" in text:
        return call.reply(
            [
                text_block(
                    "Here is what the policy says.", sources=[source_chip("archive/comfort_club_overview.md")]
                )
            ]
        )
    return None


# ---------------------------------------------------------------------------------------------------------------
# Writing a case directory
# ---------------------------------------------------------------------------------------------------------------


def write_cases(
    root: Path,
    cases: Sequence[tuple[CaseScript, CaseKey | None]],
    *,
    split: str = "dev",
    key_dir: Path | None = None,
) -> Path:
    """Dev: scripts and keys under ``root/dev``. Held-out: scripts under ``root/heldout``, keys in ``key_dir``."""
    script_dir = root / ("heldout" if split == "held-out" else "dev")
    script_dir.mkdir(parents=True, exist_ok=True)
    keys_to = script_dir if split != "held-out" else key_dir
    if keys_to is not None:
        keys_to.mkdir(parents=True, exist_ok=True)
    for script, key in cases:
        (script_dir / f"{script.case_id}.case.json").write_text(
            script.model_dump_json(indent=2), encoding="utf-8"
        )
        if key is not None and keys_to is not None:
            (keys_to / f"{script.case_id}.key.json").write_text(
                key.model_dump_json(indent=2), encoding="utf-8"
            )
    return root


def write_split_record(root: Path, heldout_hash: str | None) -> None:
    record = SplitRecord(
        seed=1,
        method="template-whole, stratified by family and support level",
        assignment={},
        heldout_key_sha256=heldout_hash,
    )
    (root / "split.json").write_text(record.model_dump_json(indent=2), encoding="utf-8")


def mix_record() -> MixRecord:
    def split_mix(rows: Sequence[MixRow]) -> SplitMix:
        return SplitMix(
            size=sum(r.count for r in rows),
            transcript_derived=sum(r.count for r in rows if r.origin == "transcript"),
            synthetic=sum(r.count for r in rows if r.origin == "synthetic"),
            categories=tuple(r.category for r in rows),
            rows=tuple(rows),
        )

    return MixRecord(
        splits={
            "dev": split_mix(
                [
                    MixRow(category="SCH-RESCHED", count=2, origin="synthetic", tests=None),
                    MixRow(category="KB-WARRANTY", count=1, origin="transcript", tests="KB"),
                ]
            ),
            "held-out": split_mix(
                [MixRow(category="BILL-INVOICE", count=2, origin="transcript", tests=None)]
            ),
        }
    )


def write_mix(root: Path, mix: MixRecord | None = None) -> MixRecord:
    mix = mix or mix_record()
    (root / "mix.json").write_text(mix.model_dump_json(indent=2), encoding="utf-8")
    return mix


def write_sealed_heldout(root: Path, key_dir: Path, cases: Sequence[tuple[CaseScript, CaseKey]]) -> str:
    """A synthetic sealed held-out set: scripts in ``root``, keys in ``key_dir``, the key hash recorded in split.json."""
    write_cases(root, cases, split="held-out", key_dir=key_dir)
    digest = heldout_key_sha256(key_dir)
    write_split_record(root, digest)
    return digest


def write_retrieval_queries(queries_dir: Path, queries: Sequence[RetrievalQuery]) -> Path:
    queries_dir.mkdir(parents=True, exist_ok=True)
    for q in queries:
        (queries_dir / f"{q.query_id}.json").write_text(q.model_dump_json(indent=2), encoding="utf-8")
    return queries_dir


def retrieval_query(
    query_id: str,
    query: str,
    *,
    expected_file: str | None,
    expect_below_floor: bool = False,
) -> RetrievalQuery:
    return RetrievalQuery(
        query_id=query_id,
        query=query,
        expected_file=expected_file,
        expect_below_floor=expect_below_floor,
        trap=None,
        source="harness test fixture",
        synthetic=True,
    )


# ---------------------------------------------------------------------------------------------------------------
# Tamper helpers
# ---------------------------------------------------------------------------------------------------------------


def harness_copy(tmp: Path) -> Path:
    """A copy of the non-test ``eval/harness/*.py`` files, for tamper tests."""
    dst = tmp / "harness_copy"
    dst.mkdir(parents=True, exist_ok=True)
    for path in HARNESS_SRC.glob("*.py"):
        shutil.copy(path, dst / path.name)
    return dst


def flip_one_byte(copy: Path) -> Path:
    """Change exactly one byte of a scoring source in the copy (appends a single character)."""
    target = copy / "scoring.py"
    if not target.exists():
        target = copy / "__init__.py"
    with target.open("ab") as handle:
        handle.write(b"#")
    return target


def utc_now() -> datetime:
    return datetime.now(UTC)
