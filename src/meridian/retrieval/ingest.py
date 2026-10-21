"""WF-14 knowledge-base ingestion: read the 17 issued files, chunk the answer sources, embed, write one index directory.

`python -m meridian.retrieval.ingest --kb-dir PATH --transcriptions-dir PATH --out-dir PATH` (stage7/data.md section 3).
Chunk text is never printed or logged; stdout carries paths, IDs, counts, statuses and hashes only.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import re
import shutil
import sys
import tempfile
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, TypeAlias

import numpy as np
import numpy.typing as npt
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from meridian.domain.common import MeridianModel
from meridian.domain.records import Passage
from meridian.ports.runtime import IndexInfo
from meridian.retrieval import settings
from meridian.retrieval.manifest import (
    MANIFEST,
    FileStatus,
    ManifestRow,
    ParseMethod,
    StaffGuidance,
)
from meridian.retrieval.settings import (
    EMBEDDING_MODEL,
    MAX_SECTION_CHARS,
    OVERLAP_CHARS,
    PIECE_CHARS,
)

EmbedFn: TypeAlias = Callable[[Sequence[str]], npt.NDArray[np.float32]]  # texts -> float32 [n, dim]


class IngestRun(MeridianModel):
    """WF-14 record (DAT-12)."""

    ingest_run_id: str
    status: Literal["started", "completed", "failed"]
    started_at: dt.datetime
    finished_at: dt.datetime | None
    manifest_hash: str
    files: int
    chunks: int
    embedding_model: str
    failure: str | None


class IngestError(Exception):
    """Named reasons; the message holds paths and counts only."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.run: IngestRun | None = None


class UnlistedFile(IngestError):
    """A file on disk not in MANIFEST, or a MANIFEST row with no file."""


class MissingSource(IngestError):
    """Unreadable answer source or missing transcription; no output written."""


@dataclass(frozen=True, slots=True)
class _Chunk:
    section: str
    text: str


_HEADING: Final = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_BULLET: Final = re.compile(r"^\s*[-*+]\s+(.+)$")


def _read(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise MissingSource(f"{label}: unreadable") from exc


def _decode(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise MissingSource(f"{label}: not UTF-8") from exc


def _version_date(label: str) -> dt.date | None:
    found = re.search(r"(?<![0-9])([0-9]{4})-([0-9]{2})-([0-9]{2})(?![0-9])", label)
    if found is None:
        return None
    try:
        return dt.date(int(found.group(1)), int(found.group(2)), int(found.group(3)))
    except ValueError:
        return None


def _cut(body: str) -> list[str]:
    """Cut an over-long section at blank-line paragraphs; no overlap, every paragraph in exactly one piece."""
    if len(body) <= MAX_SECTION_CHARS:
        return [body]
    paras = [p.strip() for p in re.split(r"\n[ \t]*\n", body) if p.strip()]
    units: list[str] = []
    for para in paras:
        if len(para) <= MAX_SECTION_CHARS:
            units.append(para)
            continue
        joined = ""
        for line in para.split("\n"):
            if len(line) > MAX_SECTION_CHARS:
                if joined:
                    units.append(joined)
                    joined = ""
                units.extend(line[i : i + PIECE_CHARS] for i in range(0, len(line), PIECE_CHARS))
                continue
            candidate = line if not joined else joined + "\n" + line
            if joined and len(candidate) > PIECE_CHARS:
                units.append(joined)
                joined = line
            else:
                joined = candidate
        if joined:
            units.append(joined)
    pieces: list[str] = []
    cur = ""
    for unit in units:
        cand = unit if not cur else cur + "\n\n" + unit
        if cur and len(cand) > PIECE_CHARS:
            pieces.append(cur)
            cur = unit
        else:
            cur = cand
    if cur:
        pieces.append(cur)
    return pieces


def _strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _chunk_markdown(text: str, *, file_name: str) -> list[_Chunk]:
    chunks: list[_Chunk] = []
    heads: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        body = "\n".join(buf).strip()
        buf.clear()
        if not body or re.fullmatch(r"_[^\n]*_", body):
            return
        section = " > ".join(heads) if heads else file_name
        chunks.extend(_Chunk(section, piece) for piece in _cut(body))

    for line in _strip_comments(text).splitlines():
        match = _HEADING.match(line)
        if match:
            flush()
            level = len(match.group(1))
            heads[:] = [*heads[: level - 1], match.group(2).strip()]
        else:
            buf.append(line)
    flush()
    return chunks


def _pdf_text(data: bytes, label: str) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        pages: list[str] = []
        for page in reader.pages:
            raw = page.extract_text(extraction_mode="layout")
            lines = [re.sub(r" {2,}", " | ", line.strip()) for line in raw.splitlines()]
            pages.append("\n".join(lines))
    except PyPdfError as exc:
        raise MissingSource(f"{label}: unreadable PDF") from exc
    return "\n\n".join(pages)


def _chunk_plain_text(text: str, *, file_name: str) -> list[_Chunk]:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.strip():
            current.append(line.strip())
        elif current:
            paragraphs.append("\n".join(current))
            current = []
    if current:
        paragraphs.append("\n".join(current))
    if len(paragraphs) >= 2:
        section = " ".join(paragraphs[0].split("\n"))
        body_paragraphs = paragraphs[1:]
    else:
        section = file_name
        body_paragraphs = paragraphs
    if not body_paragraphs:
        return []
    body = "\n\n".join(body_paragraphs)
    return [_Chunk(section, piece) for piece in _cut(body)]


def _chunk_csv(text: str, *, file_name: str, label: str) -> list[_Chunk]:
    chunks: list[_Chunk] = []
    try:
        reader = csv.DictReader(io.StringIO(text))
        fields = list(reader.fieldnames or [])
        for i, row in enumerate(reader, start=1):
            body = "; ".join(f"{f}: {row[f].strip()}" for f in fields if row.get(f) and row[f].strip())
            if not body:
                continue
            category = (row.get("category") or "").strip()
            description = (row.get("description") or "").strip()
            section = f"{category} > {description}" if category and description else f"{file_name} > row {i}"
            chunks.append(_Chunk(section, body))
    except csv.Error as exc:
        raise MissingSource(f"{label}: unreadable CSV") from exc
    return chunks


def _staff_passages(text: str) -> list[_Chunk]:
    chunks: list[_Chunk] = []
    heads: list[str] = []
    lead_in: str | None = None
    for line in _strip_comments(text).splitlines():
        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            heads[:] = [*heads[: level - 1], heading.group(2).strip()]
            lead_in = None
            continue
        base = " > ".join(heads)
        bullet = _BULLET.match(line)
        if bullet:
            section = f"{base} > {lead_in}" if lead_in else base
            chunks.append(_Chunk(section, bullet.group(1).strip()))
        elif line.strip():
            if line.strip().endswith(":"):
                lead_in = line.strip().rstrip(":").strip()
            else:
                chunks.append(_Chunk(base, line.strip()))
                lead_in = None
    return chunks


def _json_text(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _status_of(path: str) -> FileStatus:
    return next(spec.status for spec in MANIFEST if spec.path == path)


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def build_index(kb_dir: Path, out_dir: Path, *, transcriptions_dir: Path, embed: EmbedFn) -> IngestRun:
    if OVERLAP_CHARS != 0:
        raise IngestError("OVERLAP_CHARS other than 0 is not implemented")
    run_id = str(uuid.uuid4())
    started_at = _now()
    tmp: Path | None = None
    rows: list[ManifestRow] = []
    passages: list[Passage] = []
    manifest_hash = ""
    try:
        if out_dir.exists():
            raise IngestError(f"output directory already exists: {out_dir}")
        if not kb_dir.is_dir():
            raise MissingSource(f"knowledge base directory not found: {kb_dir}")
        on_disk = {p.relative_to(kb_dir).as_posix() for p in kb_dir.rglob("*") if p.is_file()}
        listed = {spec.path for spec in MANIFEST}
        extra = sorted(on_disk - listed)
        if extra:
            raise UnlistedFile(f"files not in MANIFEST: {extra}")
        absent = sorted(listed - on_disk)
        absent_sources = [p for p in absent if _status_of(p) in {FileStatus.CURRENT, FileStatus.STAFF_ONLY}]
        if absent_sources:
            raise MissingSource(f"answer source missing: {absent_sources}")
        if absent:
            raise UnlistedFile(f"MANIFEST rows with no file: {absent}")

        out_dir.parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix=f".{out_dir.name}.tmp-", dir=out_dir.parent))
        started = IngestRun(
            ingest_run_id=run_id,
            status="started",
            started_at=started_at,
            finished_at=None,
            manifest_hash="",
            files=0,
            chunks=0,
            embedding_model=EMBEDDING_MODEL,
            failure=None,
        )
        (tmp / "ingest_run.json").write_text(_json_text(started.model_dump(mode="json")), encoding="utf-8")

        staff: list[StaffGuidance] = []
        for spec in MANIFEST:
            data = _read(kb_dir / spec.path, spec.path)
            sha = hashlib.sha256(data).hexdigest()
            file_name = Path(spec.path).name
            n_chunks = 0
            if spec.status == FileStatus.CURRENT:
                found: list[_Chunk]
                if spec.parse_method == ParseMethod.MARKDOWN:
                    found = _chunk_markdown(_decode(data, spec.path), file_name=file_name)
                elif spec.parse_method == ParseMethod.TEXT:
                    found = _chunk_plain_text(_decode(data, spec.path), file_name=file_name)
                elif spec.parse_method == ParseMethod.PDF_TEXT:
                    found = _chunk_plain_text(_pdf_text(data, spec.path), file_name=file_name)
                elif spec.parse_method == ParseMethod.CSV_ROWS:
                    found = _chunk_csv(_decode(data, spec.path), file_name=file_name, label=spec.path)
                else:
                    tr_path = transcriptions_dir / (Path(spec.path).stem + ".md")
                    tr_label = f"transcription missing for {spec.path}: {tr_path.name}"
                    tr_data = _read(tr_path, tr_label)
                    sha = hashlib.sha256(data + tr_data).hexdigest()
                    found = _chunk_markdown(_decode(tr_data, tr_label), file_name=file_name)
                if not found:
                    raise MissingSource(f"{spec.path}: no text extracted")
                label = spec.version_label or ""
                for n, c in enumerate(found):
                    passages.append(
                        Passage.model_validate(
                            {
                                "passage_id": f"{spec.path}#{n}",
                                "file": spec.path,
                                "section": c.section,
                                "version_label": label,
                                "version_date": _version_date(label),
                                "text": c.text,
                                "score": 0.0,
                            }
                        )
                    )
                n_chunks = len(found)
            elif spec.status == FileStatus.STAFF_ONLY:
                for n, c in enumerate(_staff_passages(_decode(data, spec.path))):
                    staff.append(
                        StaffGuidance.model_validate(
                            {
                                "passage_id": f"{spec.path}#{n}",
                                "file": spec.path,
                                "section": c.section,
                                "version_label": spec.version_label or "undated",
                                "text": c.text,
                                "text_sha256": hashlib.sha256(c.text.strip().encode("utf-8")).hexdigest(),
                            }
                        )
                    )
            rows.append(
                ManifestRow.model_validate(
                    {
                        "path": spec.path,
                        "status": spec.status,
                        "version_label": spec.version_label,
                        "parse_method": spec.parse_method,
                        "reason": spec.reason,
                        "source_sha256": sha,
                        "chunks": n_chunks,
                    }
                )
            )

        texts = [p.section + "\n" + p.text for p in passages]
        if not texts:
            raise IngestError("no passages to embed")
        vecs = np.asarray(embed(texts), dtype=np.float32)
        if vecs.ndim != 2 or vecs.shape[0] != len(texts) or vecs.shape[1] <= 0 or not np.isfinite(vecs).all():
            raise IngestError(f"embedder returned an unusable array of shape {tuple(vecs.shape)}")
        norms = np.linalg.norm(vecs, axis=1)
        if bool((norms == 0).any()):
            raise IngestError("embedder returned a zero vector")
        vecs = (vecs / norms[:, None]).astype(np.float32)

        rows = sorted(rows, key=lambda r: r.path)
        manifest_rows = [r.model_dump(mode="json") for r in rows]
        manifest_hash = hashlib.sha256(
            json.dumps(manifest_rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
                "utf-8"
            )
        ).hexdigest()
        info = IndexInfo(
            embedding_model=EMBEDDING_MODEL,
            dimension=int(vecs.shape[1]),
            chunks=len(passages),
            manifest_hash=manifest_hash,
            files=len(rows),
        )
        index_record = {
            **info.model_dump(mode="json"),
            "settings": {name: value for name, value in vars(settings).items() if name.isupper()},
        }
        completed = IngestRun(
            ingest_run_id=run_id,
            status="completed",
            started_at=started_at,
            finished_at=_now(),
            manifest_hash=manifest_hash,
            files=len(rows),
            chunks=len(passages),
            embedding_model=EMBEDDING_MODEL,
            failure=None,
        )
        (tmp / "manifest.json").write_text(_json_text(manifest_rows), encoding="utf-8")
        lines = [
            json.dumps(
                {**p.model_dump(mode="json", exclude={"score"}), "embed_text": p.section + "\n" + p.text},
                sort_keys=True,
                ensure_ascii=False,
            )
            for p in passages
        ]
        (tmp / "passages.jsonl").write_text("".join(line + "\n" for line in lines), encoding="utf-8")
        np.save(tmp / "vectors.npy", vecs, allow_pickle=False)
        (tmp / "index_record.json").write_text(_json_text(index_record), encoding="utf-8")
        (tmp / "staff_notes.json").write_text(
            _json_text([s.model_dump(mode="json") for s in staff]), encoding="utf-8"
        )
        (tmp / "ingest_run.json").write_text(_json_text(completed.model_dump(mode="json")), encoding="utf-8")
        tmp.rename(out_dir)
        tmp = None
        return completed
    except IngestError as exc:
        exc.run = IngestRun(
            ingest_run_id=run_id,
            status="failed",
            started_at=started_at,
            finished_at=_now(),
            manifest_hash=manifest_hash,
            files=len(rows),
            chunks=len(passages),
            embedding_model=EMBEDDING_MODEL,
            failure=type(exc).__name__,
        )
        raise
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)


def load_staff_guidance(index_dir: Path) -> tuple[StaffGuidance, ...]:
    data = json.loads((index_dir / "staff_notes.json").read_text(encoding="utf-8"))
    return tuple(StaffGuidance.model_validate(item) for item in data)


def _fastembed_embed(texts: Sequence[str]) -> npt.NDArray[np.float32]:
    from fastembed import TextEmbedding

    model = TextEmbedding(EMBEDDING_MODEL)
    return np.asarray(list(model.embed(list(texts))), dtype=np.float32)


def main(argv: Sequence[str] | None = None, *, embed: EmbedFn | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m meridian.retrieval.ingest", description="Build the KB index (WF-14)."
    )
    parser.add_argument("--kb-dir", type=Path, required=True)
    parser.add_argument("--transcriptions-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    embed_fn = embed if embed is not None else _fastembed_embed
    try:
        run = build_index(
            args.kb_dir, args.out_dir, transcriptions_dir=args.transcriptions_dir, embed=embed_fn
        )
    except IngestError as exc:
        run_id = exc.run.ingest_run_id if exc.run else "-"
        print(f"ingest_run_id={run_id} status=failed failure={type(exc).__name__}")
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    manifest = json.loads((args.out_dir / "manifest.json").read_text(encoding="utf-8"))
    record = json.loads((args.out_dir / "index_record.json").read_text(encoding="utf-8"))
    for row in manifest:
        print(f"{row['path']} status={row['status']} parse={row['parse_method']} chunks={row['chunks']}")
    print(
        f"ingest_run_id={run.ingest_run_id} status={run.status} files={run.files} chunks={run.chunks} "
        f"dimension={record['dimension']} manifest_hash={run.manifest_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
