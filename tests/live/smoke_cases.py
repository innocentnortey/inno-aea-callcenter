"""Custody-checked loading of dev case scripts and keys, and the six-case selection (AEA-61 AC-1, AC-2).

Only a regular file directly inside `eval/cases/dev/` is ever opened. The held-out folder and the sealed key root are
named below as constants and are never opened, listed or globbed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

import jsonschema
from pydantic import ValidationError

from eval.cases.checks import CASE_ID
from eval.cases.models import CaseKey, CaseScript
from meridian.adapters.sqlite.repos_cases_state import DEMO_START

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
CASES_DIR: Final = REPO_ROOT / "eval" / "cases"
DEV_DIR: Final = CASES_DIR / "dev"
SCHEMA_PATH: Final = CASES_DIR / "case.schema.json"
HELDOUT_SCRIPTS_DIR: Final = CASES_DIR / "heldout"  # never opened or listed
HELDOUT_KEY_ROOT: Final = Path(
    "/home/linuxuser/.meridian-sealed"
)  # FORMAT.md section 6 (DAT-2 = B); never opened
CustodyReason = Literal[
    "bad_case_id",
    "outside_dev",
    "missing",
    "not_dev_split",
    "clock_mismatch",
    "schema_invalid",
    "id_mismatch",
]
NO_WARRANTY: Final = "NOT_RUN: no dev warranty case"


class CaseCustodyError(Exception):
    def __init__(self, case_id: str, reason: CustodyReason) -> None:
        self.case_id = case_id
        self.reason = reason
        super().__init__(str(self))

    def __str__(self) -> str:  # the case id and a code only, never a path
        return f"{self.case_id}: {self.reason}"


@dataclass(frozen=True)
class SmokeCase:
    label: str
    journey: str
    case_id: str
    script: CaseScript
    key: CaseKey


@dataclass(frozen=True)
class NotRunCase:
    label: str
    journey: str
    case_id: str | None
    reason: str


SMOKE_TABLE: Final[tuple[tuple[str, str, str | None], ...]] = (
    ("membership", "J-2", "WP-1"),
    ("billing", "J-2", "WP-2"),
    ("warranty", "J-2", None),
    ("booking with follow-up", "J-3", "WP-4F"),
    ("safety", "J-5", "DANGER"),
    ("fee-bearing change", "J-4", "WP-4"),
)


def checked_dev_path(path: Path, case_id: str, *, dev_dir: Path = DEV_DIR) -> Path:
    resolved = path.resolve(strict=False)
    if resolved.parent != dev_dir.resolve():
        raise CaseCustodyError(case_id, "outside_dev")
    if not resolved.is_file():
        raise CaseCustodyError(case_id, "missing")
    return resolved


def _validate(kind: str, document: Any, case_id: str) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator({"$defs": schema["$defs"], "$ref": f"#/$defs/{kind}"})
    if next(iter(validator.iter_errors(document)), None) is not None:
        raise CaseCustodyError(case_id, "schema_invalid")


def _read_json(path: Path, case_id: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise CaseCustodyError(case_id, "schema_invalid") from None


def load_dev_case(case_id: str, *, dev_dir: Path = DEV_DIR) -> tuple[CaseScript, CaseKey]:
    if CASE_ID.fullmatch(case_id) is None:
        raise CaseCustodyError(case_id, "bad_case_id")
    script_path = checked_dev_path(dev_dir / f"{case_id}.case.json", case_id, dev_dir=dev_dir)
    key_path = checked_dev_path(dev_dir / f"{case_id}.key.json", case_id, dev_dir=dev_dir)
    script_doc = _read_json(script_path, case_id)
    key_doc = _read_json(key_path, case_id)
    _validate("CaseScript", script_doc, case_id)
    _validate("CaseKey", key_doc, case_id)
    try:
        script = CaseScript.model_validate(script_doc)
        key = CaseKey.model_validate(key_doc)
    except ValidationError:
        raise CaseCustodyError(case_id, "schema_invalid") from None
    if script.case_id != case_id or key.case_id != case_id:
        raise CaseCustodyError(case_id, "id_mismatch")
    if script.split != "dev":
        raise CaseCustodyError(case_id, "not_dev_split")
    if script.clock is None or script.clock != DEMO_START:
        raise CaseCustodyError(case_id, "clock_mismatch")
    return script, key


def first_warranty_case(dev_dir: Path = DEV_DIR) -> str | None:
    for path in sorted(dev_dir.glob("*.key.json")):
        case_id = path.name.removesuffix(".key.json")
        checked = checked_dev_path(path, case_id, dev_dir=dev_dir)
        try:
            key = CaseKey.model_validate(_read_json(checked, case_id))
        except ValidationError:
            raise CaseCustodyError(case_id, "schema_invalid") from None
        if key.topic == "warranty" and key.in_scope:
            return case_id
    return None


def select_smoke_set(dev_dir: Path = DEV_DIR) -> tuple[SmokeCase | NotRunCase, ...]:
    chosen: list[SmokeCase | NotRunCase] = []
    for label, journey, fixed in SMOKE_TABLE:
        case_id = first_warranty_case(dev_dir) if label == "warranty" else fixed
        if case_id is None:
            chosen.append(NotRunCase(label, journey, None, NO_WARRANTY))
            continue
        script, key = load_dev_case(case_id, dev_dir=dev_dir)
        chosen.append(SmokeCase(label, journey, case_id, script, key))
    return tuple(chosen)
