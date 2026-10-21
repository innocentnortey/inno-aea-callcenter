"""Build the retrieval index from the current KB files (PRD R-9…R-12).

Run: `uv run python -m meridian.kb.ingest` — writes var/kb_index/{chunks.json,vectors.npy,manifest.json}.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import numpy as np

from meridian.config import KB_DIR, ROOT, SETTINGS
from meridian.kb.manifest import MANIFEST

EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def _md_chunks(path: str, text: str) -> list[dict]:
    """Split Markdown by headings; keep the heading path with each chunk."""
    chunks, heads, buf = [], [], []
    title = ""

    def flush():
        body = "\n".join(buf).strip()
        if body:
            section = " > ".join(h for h in heads if h)
            chunks.append({"file": path, "section": section or title, "text": body})

    for line in text.splitlines():
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            flush()
            buf = []
            level = len(m.group(1))
            heads = heads[: level - 1] + [m.group(2).strip()]
            if level == 1:
                title = m.group(2).strip()
        else:
            buf.append(line)
    flush()
    # very long sections: split by blank-line paragraphs into ~900-char pieces
    out = []
    for c in chunks:
        if len(c["text"]) <= 1100:
            out.append(c)
            continue
        part = ""
        for para in re.split(r"\n\s*\n", c["text"]):
            if len(part) + len(para) > 900 and part:
                out.append({**c, "text": part.strip()})
                part = ""
            part += para + "\n\n"
        if part.strip():
            out.append({**c, "text": part.strip()})
    return out


def _pdf_text(p: Path) -> str:
    from pypdf import PdfReader

    return "\n".join((page.extract_text() or "") for page in PdfReader(str(p)).pages)


def _csv_chunks(path: str, p: Path) -> list[dict]:
    rows = list(csv.DictReader(p.open()))
    out = []
    for r in rows:
        price = f"${r['low_price']}" if r["low_price"] == r["high_price"] else f"${r['low_price']}–${r['high_price']}"
        note = f" Note: {r['notes']}." if r.get("notes") else ""
        out.append({"file": path, "section": f"{r['category']} · {r['sku']}",
                    "text": f"{r['description']} ({r['category']}): typical price {price}. Member discount eligible: "
                            f"{r['member_discount_eligible']}.{note} Exact pricing is confirmed by the technician on site."})
    return out


def build_chunks() -> tuple[list[dict], dict]:
    chunks, report = [], {}
    for rel, meta in MANIFEST.items():
        p = KB_DIR / rel
        status = meta["status"]
        report[rel] = {**meta, "chunks": 0}
        if status in ("excluded", "stub"):
            continue  # never searched (DEC-4); kept on disk untouched
        if rel.endswith(".md") or rel.endswith(".txt"):
            cs = _md_chunks(rel, p.read_text())
        elif rel.endswith(".pdf"):
            text = _pdf_text(p)
            cs = [{"file": rel, "section": "2026 Residential Fee Schedule", "text": text.strip()}]
        elif rel.endswith(".csv"):
            cs = _csv_chunks(rel, p)
        elif rel.endswith(".png"):
            t = (ROOT / meta["transcription"]).read_text()
            t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
            cs = [{**c, "file": rel} for c in _md_chunks(rel, t)]
        else:
            continue
        for c in cs:
            c["status"] = status
            c["version"] = meta.get("version", "")
        report[rel]["chunks"] = len(cs)
        chunks.extend(cs)
    for i, c in enumerate(chunks):
        c["id"] = f"P{i:03d}"
    return chunks, report


def _embedder():
    from fastembed import TextEmbedding

    return TextEmbedding(EMBED_MODEL)


def embed_texts(texts: list[str]) -> np.ndarray:
    vecs = np.array(list(_embedder().embed(texts)), dtype=np.float32)
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)


def main() -> None:
    chunks, report = build_chunks()
    d = SETTINGS.index_dir
    d.mkdir(parents=True, exist_ok=True)
    texts = [f"{c['section']}\n{c['text']}" for c in chunks]
    np.save(d / "vectors.npy", embed_texts(texts))
    (d / "chunks.json").write_text(json.dumps(chunks, indent=1))
    (d / "manifest.json").write_text(json.dumps(report, indent=1))
    print(f"indexed {len(chunks)} chunks from {sum(1 for r in report.values() if r['chunks'])} files; "
          f"excluded: {[k for k, v in report.items() if v['status'] in ('excluded', 'stub')]}")


if __name__ == "__main__":
    main()
