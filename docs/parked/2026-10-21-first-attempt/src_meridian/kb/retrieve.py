"""Hybrid retrieval over the current KB: embedding cosine + a small keyword boost (PRD R-11)."""
from __future__ import annotations

import json
import re
from functools import lru_cache

import numpy as np

from meridian.config import SETTINGS


@lru_cache(maxsize=1)
def _index():
    d = SETTINGS.index_dir
    if not (d / "chunks.json").exists():
        from meridian.kb import ingest

        ingest.main()
    chunks = json.loads((d / "chunks.json").read_text())
    vecs = np.load(d / "vectors.npy")
    return chunks, vecs


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding

    from meridian.kb.ingest import EMBED_MODEL

    return TextEmbedding(EMBED_MODEL)


def _tokens(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9$]+", s.lower()) if len(t) > 2}


def search(query: str, k: int = 4, staff: bool = False) -> list[dict]:
    chunks, vecs = _index()
    q = np.array(list(_model().query_embed(query)), dtype=np.float32)[0]
    q /= np.linalg.norm(q)
    sims = vecs @ q
    qt = _tokens(query)
    scored = []
    for i, c in enumerate(chunks):
        if c["status"] == "staff_only" and not staff:
            continue
        overlap = len(qt & _tokens(c["section"] + " " + c["text"])) / (len(qt) or 1)
        scored.append((float(sims[i]) + 0.15 * overlap, i))
    scored.sort(reverse=True)
    out = []
    for score, i in scored[:k]:
        c = chunks[i]
        out.append({"id": c["id"], "file": c["file"], "section": c["section"], "version": c["version"],
                    "text": c["text"], "score": round(score, 3)})
    return out
