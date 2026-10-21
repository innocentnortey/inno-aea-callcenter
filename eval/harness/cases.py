"""Load case scripts, keys, split, mix and retrieval queries; the held-out key hash check (AC-6, P-1).

Files are only ever opened for reading.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

from pydantic import BaseModel, ValidationError

from eval.cases.models import (
    CaseKey,
    CaseScript,
    MixRecord,
    RetrievalQuery,
    SplitMix,
    SplitRecord,
)

WORKED_PAIR_IDS: Final = (
    "DANGER",
    "NODANGER",
    "WP-1",
    "WP-2",
    "WP-3",
    "WP-4",
    "WP-4F",
    "WP-5",
    "WP-6",
    "WP-7",
    "WP-8",
)
KEY_SUFFIX: Final = ".key.json"
SCRIPT_SUFFIX: Final = ".case.json"


class CaseFileError(Exception):
    """A case file is missing or invalid. Names the path and the model kind only."""


class HeldoutNotSealed(Exception):
    """split.json records no held-out key hash."""


class HeldoutHashMismatch(Exception):
    def __init__(self, recorded: str, computed: str) -> None:
        super().__init__(f"held-out key hash mismatch: recorded {recorded} computed {computed}")
        self.recorded = recorded
        self.computed = computed


@dataclass(frozen=True)
class LoadedCase:
    script: CaseScript
    key: CaseKey | None


@dataclass(frozen=True)
class CaseSet:
    cases: tuple[LoadedCase, ...]
    unscored: tuple[str, ...]
    mix: SplitMix | None
    files_read: tuple[Path, ...]


def heldout_key_sha256(key_dir: Path) -> str:
    """FORMAT.md section 6: SHA-256 over the bytes of every '*.key.json' directly in key_dir, sorted by name."""
    if not key_dir.is_dir():
        raise CaseFileError("held-out key directory is missing")
    files = sorted(
        (p for p in key_dir.iterdir() if p.is_file() and p.name.endswith(KEY_SUFFIX)), key=lambda p: p.name
    )
    if not files:
        raise CaseFileError("no key files")
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _violates_schema(schema_path: Path, kind: str, document: object) -> bool:
    """True when the JSON Schema rejects the document. jsonschema is a dev dependency: absent, the pydantic check stands."""
    try:
        import jsonschema
    except ImportError:
        return False
    schema: dict[str, Any] = json.loads(schema_path.read_text(encoding="utf-8"))
    wrapper = {"$defs": schema["$defs"], "$ref": f"#/$defs/{kind}"}
    return any(True for _ in jsonschema.Draft202012Validator(wrapper).iter_errors(document))


def _read[M: BaseModel](cases_dir: Path, path: Path, model: type[M], files_read: list[Path]) -> M:
    kind = model.__name__
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CaseFileError(f"cannot read {path.name} as {kind}") from exc
    schema_path = cases_dir / "case.schema.json"
    if schema_path.is_file() and _violates_schema(schema_path, kind, json.loads(raw)):
        raise CaseFileError(f"{path.name} does not match the {kind} schema")
    try:
        parsed = model.model_validate_json(raw)
    except ValidationError as exc:
        raise CaseFileError(f"{path.name} is not a valid {kind}") from exc
    files_read.append(path)
    return parsed


def load_split_record(cases_dir: Path) -> SplitRecord:
    return _read(cases_dir, cases_dir / "split.json", SplitRecord, [])


def load_mix(cases_dir: Path) -> MixRecord | None:
    path = cases_dir / "mix.json"
    return _read(cases_dir, path, MixRecord, []) if path.is_file() else None


def load_cases(
    cases_dir: Path,
    *,
    suite: Literal["worked-pairs", "e2e", "load"],
    split: Literal["dev", "held-out"],
    heldout_key_dir: Path | None,
) -> CaseSet:
    files_read: list[Path] = []
    script_dir = cases_dir / ("heldout" if split == "held-out" else "dev")
    if not script_dir.is_dir():
        raise CaseFileError("case directory is missing")
    scripts = [
        _read(cases_dir, p, CaseScript, files_read) for p in sorted(script_dir.glob(f"*{SCRIPT_SUFFIX}"))
    ]
    if suite == "worked-pairs":
        scripts = [s for s in scripts if s.case_id in WORKED_PAIR_IDS]
    if split == "held-out":
        record = _read(cases_dir, cases_dir / "split.json", SplitRecord, files_read)
        if record.heldout_key_sha256 is None:
            raise HeldoutNotSealed("the held-out split is not sealed")
        if heldout_key_dir is None:
            raise CaseFileError("held-out key directory is missing")
        computed = heldout_key_sha256(heldout_key_dir)
        if computed != record.heldout_key_sha256:  # before any key is read
            raise HeldoutHashMismatch(record.heldout_key_sha256, computed)
        key_dir = heldout_key_dir
    else:
        key_dir = script_dir
    cases: list[LoadedCase] = []
    unscored: list[str] = []
    for script in sorted(scripts, key=lambda s: s.case_id):
        key_path = key_dir / f"{script.case_id}{KEY_SUFFIX}"
        key = _read(cases_dir, key_path, CaseKey, files_read) if key_path.is_file() else None
        if key is not None and key.unscored is not None:
            unscored.append(script.case_id)
            continue
        cases.append(LoadedCase(script, key))
    mix_record = load_mix(cases_dir)
    mix = mix_record.splits.get(split) if mix_record is not None else None
    return CaseSet(tuple(cases), tuple(unscored), mix, tuple(files_read))


def load_retrieval_queries(queries_dir: Path) -> tuple[RetrievalQuery, ...]:
    if not queries_dir.is_dir():
        raise CaseFileError("retrieval query directory is missing")
    schema_root = queries_dir.parent
    files_read: list[Path] = []
    queries = [_read(schema_root, p, RetrievalQuery, files_read) for p in sorted(queries_dir.glob("*.json"))]
    return tuple(sorted(queries, key=lambda q: q.query_id))
