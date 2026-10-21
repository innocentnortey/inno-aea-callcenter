"""Shared loaders for the eval case-file tests (AEA-06)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Final

from eval.cases.models import CaseKey, CaseScript, RetrievalQuery
from meridian.retrieval.manifest import MANIFEST

ROOT: Final = Path(__file__).resolve().parents[2]
CASES: Final = ROOT / "eval/cases"
DB: Final = ROOT / "docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite"
SCREEN_SPECS: Final = ROOT / "docs/ux/03-structure/SCREEN_SPECS.md"
FIRST_DEV: Final = (
    "WP-1",
    "WP-2",
    "WP-3",
    "WP-4",
    "WP-5",
    "WP-6",
    "WP-7",
    "WP-8",
    "WP-4F",
    "DANGER",
    "NODANGER",
)

_ID_COLUMN: Final = {
    "customers": "customer_id",
    "appointments": "appointment_id",
    "appointment_slots": "slot_id",
    "invoices": "invoice_id",
    "technicians": "tech_id",
}


def load_scripts(dirname: str) -> dict[str, CaseScript]:
    out: dict[str, CaseScript] = {}
    for path in sorted((CASES / dirname).glob("*.case.json")):
        script = CaseScript.model_validate_json(path.read_bytes())
        out[script.case_id] = script
    return out


def load_keys() -> dict[str, CaseKey]:
    out: dict[str, CaseKey] = {}
    for path in sorted((CASES / "dev").glob("*.key.json")):
        key = CaseKey.model_validate_json(path.read_bytes())
        out[key.case_id] = key
    return out


def load_queries() -> dict[str, RetrievalQuery]:
    out: dict[str, RetrievalQuery] = {}
    for path in sorted((CASES / "retrieval").glob("*.json")):
        query = RetrievalQuery.model_validate_json(path.read_bytes())
        out[query.query_id] = query
    return out


def kb_status() -> dict[str, str]:
    return {spec.path: spec.status.value for spec in MANIFEST}


def db_has(table: str, key: str) -> bool:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        # table and column come from a closed allow-list above, never from input
        row = conn.execute(f"SELECT 1 FROM {table} WHERE {_ID_COLUMN[table]} = ?", (key,)).fetchone()  # noqa: S608
    finally:
        conn.close()
    return row is not None
