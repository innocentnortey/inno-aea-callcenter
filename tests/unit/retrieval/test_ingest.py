"""AEA-16: ingestion of the issued KB with a stand-in embedder (no model download, no paid call)."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import shutil
import uuid
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pytest

from meridian.ports.runtime import IndexInfo
from meridian.retrieval import ingest, settings
from meridian.retrieval.ingest import (
    IngestError,
    MissingSource,
    UnlistedFile,
    build_index,
    load_staff_guidance,
    main,
)
from meridian.retrieval.manifest import MANIFEST, FileStatus

ROOT = Path(__file__).resolve().parents[3]
ISSUED_KB = ROOT / "docs/data/issued/meridian_dataset/knowledge_base"
TRANSCRIPTIONS = ROOT / "data/kb_transcriptions"
PDF = "pricing/2026_fee_schedule.pdf"
PNG = "policies/holiday_hours_2026.png"
CURRENT = {s.path for s in MANIFEST if s.status == FileStatus.CURRENT}
NON_CURRENT = {s.path for s in MANIFEST} - CURRENT


def _fake_embed(texts: Sequence[str]) -> npt.NDArray[np.float32]:
    rows = [
        np.frombuffer(hashlib.sha256(t.encode("utf-8")).digest()[:8], dtype=np.uint8).astype(np.float32) + 1.0
        for t in texts
    ]
    return np.stack(rows)


def _kb(tmp_path: Path) -> Path:
    return Path(shutil.copytree(ISSUED_KB, tmp_path / "kb"))


def _tr(tmp_path: Path) -> Path:
    return Path(shutil.copytree(TRANSCRIPTIONS, tmp_path / "tr"))


def _build(kb: Path, out: Path, tr: Path = TRANSCRIPTIONS) -> ingest.IngestRun:
    return build_index(kb, out, transcriptions_dir=tr, embed=_fake_embed)


def _passages(index: Path) -> list[dict[str, object]]:
    text = (index / "passages.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines()]


def _manifest(index: Path) -> list[dict[str, object]]:
    data: list[dict[str, object]] = json.loads((index / "manifest.json").read_text(encoding="utf-8"))
    return data


def _no_temp(parent: Path, out: Path) -> None:
    assert not out.exists()
    if not parent.exists():
        return
    assert not [p for p in parent.iterdir() if p.name.startswith(f".{out.name}.tmp-")]


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("built") / "index"
    _build(ISSUED_KB, out)
    return out


def test_unlisted_file_fails_build(tmp_path: Path) -> None:
    kb = _kb(tmp_path)
    (kb / "faq/extra_notes.md").write_text("# Extra\n\nx\n", encoding="utf-8")
    out = tmp_path / "out1" / "index"
    with pytest.raises(UnlistedFile) as ei:
        _build(kb, out)
    assert "faq/extra_notes.md" in str(ei.value)
    assert ei.value.run is not None
    assert ei.value.run.status == "failed"
    assert ei.value.run.failure == "UnlistedFile"
    _no_temp(out.parent, out)

    kb2 = tmp_path / "kb2"
    shutil.copytree(ISSUED_KB, kb2)
    (kb2 / "archive/warranty_terms_2023.txt").unlink()
    out2 = tmp_path / "out2" / "index"
    with pytest.raises(UnlistedFile) as ei2:
        _build(kb2, out2)
    assert "archive/warranty_terms_2023.txt" in str(ei2.value)
    assert ei2.value.run is not None
    assert ei2.value.run.failure == "UnlistedFile"
    _no_temp(out2.parent, out2)


def test_only_current_files_indexed(built: Path) -> None:
    lines = _passages(built)
    files = {str(p["file"]) for p in lines}
    assert files == CURRENT
    assert not files & NON_CURRENT
    rows = _manifest(built)
    for row in rows:
        if row["path"] in CURRENT:
            assert isinstance(row["chunks"], int)
            assert row["chunks"] > 0
        else:
            assert row["chunks"] == 0
    assert sum(int(str(r["chunks"])) for r in rows) == len(lines)


def test_each_format_parsed(tmp_path: Path, built: Path) -> None:
    lines = _passages(built)

    def of(path: str) -> list[dict[str, object]]:
        return [p for p in lines if p["file"] == path]

    pdf = of(PDF)
    assert pdf
    assert any("Diagnostic visit" in str(p["text"]) and "$89" in str(p["text"]) for p in pdf)
    with (ISSUED_KB / "pricing/repair_price_book_2026.csv").open(encoding="utf-8-sig", newline="") as fh:
        n_rows = len(list(csv.DictReader(fh)))
    csv_p = of("pricing/repair_price_book_2026.csv")
    assert len(csv_p) == n_rows
    assert any("sku: HV-CAP-01" in str(p["text"]) for p in csv_p)
    assert any("Christmas Eve" in str(p["text"]) for p in of(PNG))
    png_bytes = (ISSUED_KB / PNG).read_bytes()
    tr_bytes = (TRANSCRIPTIONS / "holiday_hours_2026.md").read_bytes()
    row = next(r for r in _manifest(built) if r["path"] == PNG)
    assert row["source_sha256"] == hashlib.sha256(png_bytes + tr_bytes).hexdigest()
    assert row["source_sha256"] != hashlib.sha256(png_bytes).hexdigest()
    tr = _tr(tmp_path)
    md = tr / "holiday_hours_2026.md"
    md.write_text(md.read_text(encoding="utf-8") + "\nOne more line.\n", encoding="utf-8")
    out = tmp_path / "o" / "index"
    _build(ISSUED_KB, out, tr)
    row2 = next(r for r in _manifest(out) if r["path"] == PNG)
    assert row2["source_sha256"] != row["source_sha256"]
    ext = {
        ".md": "markdown",
        ".txt": "text",
        ".pdf": "pdf_text",
        ".csv": "csv_rows",
        ".png": "png_transcription",
    }
    for r in _manifest(built):
        assert r["parse_method"] == ext[Path(str(r["path"])).suffix]


def test_heading_split_and_long_section_cut(tmp_path: Path) -> None:
    """Synthetic long section: four paragraphs of about 635 characters under one heading."""
    kb = _kb(tmp_path)
    paras = [f"Paragraph {k} " + " ".join(["alpha", "bravo", "charlie", "delta"] * 24) for k in range(1, 5)]
    body = "# Synthetic Policy\n_Effective: 2026-01-01_\n\n## Long Section\n\n" + "\n\n".join(paras) + "\n"
    (kb / "services/technician_arrival_and_etas.md").write_text(body, encoding="utf-8")
    out = tmp_path / "o" / "index"
    _build(kb, out)
    mine = [p for p in _passages(out) if p["file"] == "services/technician_arrival_and_etas.md"]
    assert len(mine) >= 3
    assert all(len(str(p["text"])) <= settings.MAX_SECTION_CHARS for p in mine)
    assert all(p["section"] == "Synthetic Policy > Long Section" for p in mine)
    assert "\n\n".join(str(p["text"]) for p in mine) == "\n\n".join(paras)
    assert [p["passage_id"] for p in mine] == [
        f"services/technician_arrival_and_etas.md#{i}" for i in range(len(mine))
    ]


def test_chunk_provenance(built: Path) -> None:
    lines = _passages(built)

    def of(path: str) -> list[dict[str, object]]:
        return [p for p in lines if p["file"] == path]

    member = of("membership/comfort_club_overview.md")
    assert member
    assert all(p["version_label"] == "Effective 2026-01-01" for p in member)
    assert all(p["version_date"] == "2026-01-01" for p in member)
    for undated in ("policies/escalation_and_safety.md", "faq/troubleshooting_before_you_call.md"):
        assert all(p["version_date"] is None for p in of(undated))
    assert all(p["version_date"] == "2026-01-01" for p in of(PDF))
    ids = [p["passage_id"] for p in lines]
    assert len(set(ids)) == len(ids)
    for path in CURRENT:
        assert [p["passage_id"] for p in of(path)] == [f"{path}#{n}" for n in range(len(of(path)))]
    for p in lines:
        assert p["embed_text"] == f"{p['section']}\n{p['text']}"
        assert "score" not in p
    vecs = np.load(built / "vectors.npy", allow_pickle=False)
    assert vecs.shape == (len(lines), 8)
    assert vecs.dtype == np.float32
    assert np.allclose(np.linalg.norm(vecs, axis=1), 1.0, atol=1e-5)


def test_missing_source_fails_build(tmp_path: Path) -> None:
    kb = _kb(tmp_path)
    (kb / PDF).unlink()
    out = tmp_path / "o1" / "index"
    with pytest.raises(MissingSource) as ei:
        _build(kb, out)
    assert PDF in str(ei.value)
    assert ei.value.run is not None
    assert ei.value.run.failure == "MissingSource"
    _no_temp(out.parent, out)
    tr = _tr(tmp_path)
    (tr / "holiday_hours_2026.md").unlink()
    out2 = tmp_path / "o2" / "index"
    with pytest.raises(MissingSource) as ei2:
        _build(ISSUED_KB, out2, tr)
    assert "holiday_hours_2026.md" in str(ei2.value)
    assert ei2.value.run is not None
    assert ei2.value.run.failure == "MissingSource"
    _no_temp(out2.parent, out2)


def _args(kb: Path, tr: Path, out: Path) -> list[str]:
    return ["--kb-dir", str(kb), "--transcriptions-dir", str(tr), "--out-dir", str(out)]


def test_cli_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(_args(ISSUED_KB, TRANSCRIPTIONS, tmp_path / "a" / "index"), embed=_fake_embed) == 0
    out = capsys.readouterr().out
    assert "status=completed" in out
    assert "files=17" in out
    kb = _kb(tmp_path)
    (kb / PDF).unlink()
    assert main(_args(kb, TRANSCRIPTIONS, tmp_path / "b" / "index"), embed=_fake_embed) == 1
    captured = capsys.readouterr()
    assert "failure=MissingSource" in captured.out
    assert captured.err.startswith("MissingSource:")
    with pytest.raises(SystemExit) as ei:
        main(["--kb-dir", "x"])
    assert ei.value.code == 2


def test_staff_notes_written_not_indexed(built: Path) -> None:
    guidance = load_staff_guidance(built)
    assert guidance
    raw = json.loads((built / "staff_notes.json").read_text(encoding="utf-8"))
    from meridian.retrieval.manifest import StaffGuidance

    assert guidance == tuple(StaffGuidance.model_validate(i) for i in raw)
    passages_text = (built / "passages.jsonl").read_text(encoding="utf-8")
    for g in guidance:
        assert g.text_sha256 == hashlib.sha256(g.text.encode("utf-8")).hexdigest()
        assert g.passage_id.startswith("internal/agent_discretion_notes.md#")
        assert str(g.passage_id) not in passages_text
        assert g.text not in passages_text
    prefixes = (
        "Waive the $49 late-cancellation fee once per customer per year",
        "Waive the diagnostic fee when the technician arrived more than 30 minutes",
        "Extend a 10% courtesy discount on a repair invoice under $500",
        "Issue refunds of any kind.",
    )
    for prefix in prefixes:
        assert any(g.text.startswith(prefix) for g in guidance), prefix
    refund = next(g for g in guidance if g.text.startswith("Issue refunds of any kind."))
    assert refund.section.endswith("Agents may NOT")


def test_excluded_text_absent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
) -> None:
    kb = _kb(tmp_path)
    for rel, sentinel in (
        ("archive/comfort_club_overview.md", "SENTINELARCHIVEQX"),
        ("services/duct_cleaning.md", "SENTINELSTUBQX"),
        ("internal/agent_discretion_notes.md", "SENTINELSTAFFQX"),
    ):
        with (kb / rel).open("a", encoding="utf-8") as fh:
            fh.write(f"\n- {sentinel} line\n")
    caplog.set_level(logging.DEBUG)
    out = tmp_path / "o" / "index"
    assert main(_args(kb, TRANSCRIPTIONS, out), embed=_fake_embed) == 0
    captured = capsys.readouterr()
    shown = captured.out + captured.err + caplog.text
    names = (
        "manifest.json",
        "passages.jsonl",
        "vectors.npy",
        "index_record.json",
        "staff_notes.json",
        "ingest_run.json",
    )
    for name in names:
        blob = (out / name).read_bytes()
        assert b"SENTINELARCHIVEQX" not in blob
        assert b"SENTINELSTUBQX" not in blob
        assert (b"SENTINELSTAFFQX" in blob) == (name == "staff_notes.json")
    for sentinel in ("SENTINELARCHIVEQX", "SENTINELSTUBQX", "SENTINELSTAFFQX"):
        assert sentinel not in shown


def test_entry_point_writes_wf14_records(tmp_path: Path) -> None:
    out1 = tmp_path / "o1" / "index"
    assert main(_args(ISSUED_KB, TRANSCRIPTIONS, out1), embed=_fake_embed) == 0
    rows = _manifest(out1)
    assert len(rows) == 17
    keys = {"path", "status", "version_label", "parse_method", "reason", "source_sha256", "chunks"}
    assert all(set(r) == keys for r in rows)
    rec = json.loads((out1 / "index_record.json").read_text(encoding="utf-8"))
    n_lines = len(_passages(out1))
    assert rec["embedding_model"] == "BAAI/bge-small-en-v1.5"
    assert rec["dimension"] == 8
    assert rec["chunks"] == n_lines
    assert rec["files"] == 17
    assert rec["settings"] == {n: getattr(settings, n) for n in dir(settings) if n.isupper()}
    IndexInfo.model_validate({k: rec[k] for k in IndexInfo.model_fields})
    run = json.loads((out1 / "ingest_run.json").read_text(encoding="utf-8"))
    assert str(uuid.UUID(run["ingest_run_id"], version=4)) == run["ingest_run_id"]
    assert run["status"] == "completed"
    assert run["failure"] is None
    assert run["manifest_hash"] == rec["manifest_hash"]
    assert (run["files"], run["chunks"], run["embedding_model"]) == (17, n_lines, rec["embedding_model"])

    out2 = tmp_path / "o2" / "index"
    assert main(_args(ISSUED_KB, TRANSCRIPTIONS, out2), embed=_fake_embed) == 0
    assert (
        json.loads((out2 / "index_record.json").read_text(encoding="utf-8"))["manifest_hash"]
        == rec["manifest_hash"]
    )

    kb = _kb(tmp_path)
    with (kb / "policies/service_area.md").open("ab") as fh:
        fh.write(b" ")
    out3 = tmp_path / "o3" / "index"
    assert main(_args(kb, TRANSCRIPTIONS, out3), embed=_fake_embed) == 0
    assert (
        json.loads((out3 / "index_record.json").read_text(encoding="utf-8"))["manifest_hash"]
        != rec["manifest_hash"]
    )

    kb2 = tmp_path / "kb2"
    shutil.copytree(ISSUED_KB, kb2)
    (kb2 / PDF).unlink()
    with pytest.raises(MissingSource) as ei:
        _build(kb2, tmp_path / "o4" / "index")
    assert ei.value.run is not None
    assert (ei.value.run.status, ei.value.run.failure) == ("failed", "MissingSource")


def test_wp1_stale_twin_by_path(built: Path) -> None:
    lines = _passages(built)
    member = [p for p in lines if p["file"] == "membership/comfort_club_overview.md"]
    assert member
    assert all(p["version_label"] == "Effective 2026-01-01" for p in member)
    assert any("$189" in str(p["text"]) for p in member)
    assert not any(str(p["file"]).startswith("archive/") for p in lines)
    row = next(r for r in _manifest(built) if r["path"] == "archive/comfort_club_overview.md")
    assert row["status"] == "excluded"
    assert row["reason"]
    assert row["chunks"] == 0
    assert any("$149" in str(p["text"]) for p in lines if p["file"] == PDF)


def test_existing_out_dir_refused(tmp_path: Path) -> None:
    out = tmp_path / "index"
    out.mkdir()
    (out / "keep.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(IngestError) as ei:
        _build(ISSUED_KB, out)
    assert type(ei.value) is IngestError
    assert [p.name for p in out.iterdir()] == ["keep.txt"]
    assert [p.name for p in tmp_path.iterdir()] == ["index"]


def test_plain_text_paragraph_groups() -> None:
    chunks = ingest._chunk_plain_text("TITLE LINE\n\nPara one.\n\nPara two.", file_name="x.txt")
    assert [(c.section, c.text) for c in chunks] == [("TITLE LINE", "Para one.\n\nPara two.")]
    single = ingest._chunk_plain_text("Only one paragraph.", file_name="x.txt")
    assert [c.section for c in single] == ["x.txt"]
