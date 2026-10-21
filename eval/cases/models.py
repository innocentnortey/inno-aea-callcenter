"""The eval case-file models (contract stage7/data.md §5, DAT-27). Standard library and pydantic only."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class _CaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ScriptedTurn(_CaseModel):  # discriminated on "kind"; mirrors CON-2 payloads
    kind: Literal["text", "choice", "form", "code_from_inbox", "person_request"]
    text: str | None = None
    choice: str | None = None
    form: dict[str, str] | None = None


class CaseScript(_CaseModel):
    case_id: str
    provenance: Literal["worked-pair", "issued-transcript", "synthetic", "promoted-trace"]
    source_ref: str
    template: str | None
    category: str | None
    family: str | None
    support_level: str | None
    split: Literal["dev", "held-out"]
    seeded_customer: str | None
    staffing: Literal["nobody", "staffed"] = "nobody"
    clock: datetime | None
    turns: tuple[ScriptedTurn, ...]
    synthetic: Literal["no", "partly", "yes"]
    synthetic_assumption: str | None
    varied_dimension: str | None
    synthetic_source_case: str | None
    labelled_by: str
    labelled_on: date


class ChecklistItem(_CaseModel):
    text: str
    source: str
    hard: bool = False


class CaseKey(_CaseModel):
    case_id: str
    in_scope: bool
    topic: Literal["booking", "membership", "billing", "warranty"] | None
    guards: tuple[Literal["boundary", "invariant", "regression"], ...]
    must_do: tuple[ChecklistItem, ...]
    must_say: tuple[ChecklistItem, ...]
    must_not_say: tuple[ChecklistItem, ...]
    judge_items: tuple[ChecklistItem, ...] = ()
    unscored: str | None = None


class RetrievalQuery(_CaseModel):
    query_id: str
    query: str
    expected_file: str | None
    expect_below_floor: bool = False
    trap: str | None
    source: str
    synthetic: bool


class SplitRecord(_CaseModel):
    seed: int
    method: Literal["template-whole, stratified by family and support level"]
    assignment: dict[str, Literal["dev", "held-out"]]
    heldout_key_sha256: str | None


class MixRow(_CaseModel):  # one OpenAPI EvalRun.mix item (category, count, origin, tests)
    category: str
    count: int
    origin: Literal["transcript", "synthetic"]
    tests: str | None


class SplitMix(_CaseModel):  # data.md §5 names it ("size; categories; transcript vs synthetic")
    size: int
    transcript_derived: int
    synthetic: int
    categories: tuple[str, ...]
    rows: tuple[MixRow, ...]


class MixRecord(_CaseModel):
    splits: dict[Literal["dev", "held-out"], SplitMix]


SCHEMA_MODELS: tuple[type[BaseModel], ...] = (CaseScript, CaseKey, RetrievalQuery, SplitRecord, MixRecord)


def dump_canonical(model: BaseModel) -> bytes:
    """The one serialisation for every file under eval/cases/: sorted keys, 2-space indent, UTF-8, newline at end."""
    text = json.dumps(model.model_dump(mode="json"), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return text.encode("utf-8")
