"""AEA-16: the manifest covers the 17 issued files; validators; no heavy imports."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from meridian.retrieval.manifest import (
    MANIFEST,
    FileStatus,
    ManifestRow,
    ManifestSpec,
    ParseMethod,
    StaffGuidance,
)

ROOT = Path(__file__).resolve().parents[3]
ISSUED_KB = ROOT / "docs/data/issued/meridian_dataset/knowledge_base"
RETRIEVAL = ROOT / "src/meridian/retrieval"

_EXT = {
    ".md": ParseMethod.MARKDOWN,
    ".txt": ParseMethod.TEXT,
    ".pdf": ParseMethod.PDF_TEXT,
    ".csv": ParseMethod.CSV_ROWS,
    ".png": ParseMethod.PNG_TRANSCRIPTION,
}


def test_manifest_covers_all_17_issued_files() -> None:
    on_disk = {p.relative_to(ISSUED_KB).as_posix() for p in ISSUED_KB.rglob("*") if p.is_file()}
    paths = [s.path for s in MANIFEST]
    assert on_disk == set(paths)
    assert len(MANIFEST) == 17
    assert len(set(paths)) == 17
    assert paths == sorted(paths)
    for s in MANIFEST:
        print(s.path, s.status.value, s.parse_method.value)
        if s.status == FileStatus.CURRENT:
            assert s.version_label
            assert s.reason is None
        else:
            assert s.reason
        assert s.parse_method == _EXT[Path(s.path).suffix]

    def by(status: FileStatus) -> set[str]:
        return {s.path for s in MANIFEST if s.status == status}

    assert by(FileStatus.EXCLUDED) == {
        "archive/comfort_club_overview.md",
        "archive/warranty_terms_2023.txt",
        "faq/faq_old_copy.md",
        "services/scheduling_guide.md",
    }
    assert by(FileStatus.STAFF_ONLY) == {"internal/agent_discretion_notes.md"}
    assert by(FileStatus.STUB) == {"services/duct_cleaning.md"}
    assert len(by(FileStatus.CURRENT)) == 11


def _spec(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "path": "a.md",
        "status": FileStatus.CURRENT,
        "version_label": "2026",
        "parse_method": ParseMethod.MARKDOWN,
        "reason": None,
    }
    return {**base, **over}


def _code(exc: pytest.ExceptionInfo[ValidationError]) -> str:
    return exc.value.errors()[0]["type"]


def test_validators_reject_bad_rows() -> None:
    with pytest.raises(ValidationError) as e1:
        ManifestSpec.model_validate(_spec(version_label=None))
    assert _code(e1) == "manifest_current_row"
    with pytest.raises(ValidationError) as e2:
        ManifestSpec.model_validate(_spec(status=FileStatus.EXCLUDED, version_label=None))
    assert _code(e2) == "manifest_reason_required"
    with pytest.raises(ValidationError) as e3:
        ManifestRow.model_validate(
            {
                **_spec(status=FileStatus.EXCLUDED, reason="old"),
                "source_sha256": "0" * 64,
                "chunks": 1,
            }
        )
    assert _code(e3) == "manifest_noncurrent_chunks"
    good = {
        "passage_id": "internal/agent_discretion_notes.md#0",
        "file": "internal/agent_discretion_notes.md",
    }
    text = "Issue refunds of any kind."
    ok = StaffGuidance.model_validate(
        {
            **good,
            "section": "S",
            "version_label": "undated",
            "text": text,
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        }
    )
    assert StaffGuidance.model_validate(ok.model_dump(mode="json")) == ok
    with pytest.raises(ValidationError) as e4:
        StaffGuidance.model_validate(
            {**good, "section": "S", "version_label": "undated", "text": text, "text_sha256": "0" * 64}
        )
    assert _code(e4) == "staff_guidance_hash_mismatch"


def test_manifest_and_settings_import_no_heavy_stack() -> None:
    heavy = {"numpy", "pypdf", "fastembed", "onnxruntime"}
    for name in ("manifest.py", "settings.py"):
        tree = ast.parse((RETRIEVAL / name).read_text(encoding="utf-8"))
        tops: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                tops.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                tops.add(node.module.split(".")[0])
        assert not tops & heavy
        if name == "settings.py":
            assert tops <= {"__future__", "typing"}
