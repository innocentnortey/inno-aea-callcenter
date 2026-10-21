"""A ``SearchesPassages`` double over hand-written passages (AEA-24 plan 7.1). No index, no model, no network."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from eval.cases.models import RetrievalQuery
from eval.harness.tests.fixture_cases import retrieval_query

INDEX_MANIFEST = hashlib.sha256(b"fixture manifest for the harness tests").hexdigest()
FLOOR = 0.6


@dataclass(frozen=True)
class DocPassage:
    file: str
    section: str
    version_label: str
    score: float


@dataclass(frozen=True)
class DocResult:
    passages: tuple[DocPassage, ...]
    below_floor: bool


@dataclass
class ScriptedIndex:
    table: Mapping[str, Sequence[tuple[str, str, float]]]
    raises_on: Collection[str] = ()
    calls: list[tuple[str, int, float]] = field(default_factory=list)

    def search(self, query: str, *, k: int, min_score: float) -> DocResult:
        self.calls.append((query, k, min_score))
        if query in self.raises_on:
            raise RuntimeError("index unavailable")
        rows = sorted(self.table[query], key=lambda r: -r[2])[:k]
        passages = tuple(DocPassage(file, "Section", label, score) for file, label, score in rows)
        if min_score != float("-inf"):
            passages = tuple(p for p in passages if p.score >= min_score)
        return DocResult(passages, below_floor=not passages)


CURRENT = "warranty/warranty_policy.md"
STALE = "archive/warranty_terms_2023.txt"

QUERY_TEXTS = {
    "R-1": "How does the comfort club work for members?",
    "R-2": "What does the labor warranty cover after a repair?",
    "R-3": "How long is the installation labor warranty?",
    "R-4": "Who won the football game last night?",
    "R-5": "What does an HVAC repair visit include?",
}

TABLE: dict[str, list[tuple[str, str, float]]] = {
    QUERY_TEXTS["R-1"]: [
        ("membership/comfort_club.md", "Rev 2026-01", 0.91),
        ("faq/faq_current.md", "Rev 2026-01", 0.72),
        ("services/hvac_repair.md", "undated", 0.65),
    ],
    QUERY_TEXTS["R-2"]: [
        ("faq/faq_current.md", "Rev 2026-01", 0.70),
        ("services/hvac_repair.md", "undated", 0.66),
        ("membership/comfort_club.md", "Rev 2026-01", 0.61),
    ],
    QUERY_TEXTS["R-3"]: [
        (STALE, "2023", 0.82),
        (CURRENT, "Rev 2026-01", 0.80),
        ("faq/faq_current.md", "Rev 2026-01", 0.50),
    ],
    QUERY_TEXTS["R-4"]: [
        ("faq/faq_current.md", "Rev 2026-01", 0.31),
        ("services/hvac_repair.md", "undated", 0.28),
        ("membership/comfort_club.md", "Rev 2026-01", 0.22),
    ],
    QUERY_TEXTS["R-5"]: [
        ("services/hvac_repair.md", "undated", 0.88),
        ("faq/faq_current.md", "Rev 2026-01", 0.40),
        ("pricing/fee_schedule.md", "Rev 2026-01", 0.30),
    ],
}


def queries(*ids: str, query_texts: Mapping[str, str] = QUERY_TEXTS) -> list[RetrievalQuery]:
    expected = {
        "R-1": "membership/comfort_club.md",
        "R-2": CURRENT,
        "R-3": CURRENT,
        "R-4": None,
        "R-5": "services/hvac_repair.md",
    }
    return [
        retrieval_query(i, query_texts[i], expected_file=expected[i], expect_below_floor=i == "R-4")
        for i in ids
    ]


def stamp() -> Any:
    from eval.harness.records import RunStamp

    return RunStamp(
        run_id=str(uuid.uuid4()),
        agent_version="v-test",
        harness_commit="abc123",
        harness_digest="d" * 64,
        index_manifest_hash=INDEX_MANIFEST,
        started_at=datetime.now(UTC),
    )


def write_index_dir(root: Path) -> Path:
    index_dir = root / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    (index_dir / "index_record.json").write_text(
        json.dumps({"manifest_hash": INDEX_MANIFEST}), encoding="utf-8"
    )
    return index_dir
