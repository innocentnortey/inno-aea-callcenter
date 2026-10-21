"""FastembedIndex: the built KB index behind RetrievalIndex (DO-4 section 13; stage7/data.md section 4).

Loads AEA-16's index directory, searches by cosine similarity with a relevance floor, and checks readiness. Logs nothing.
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, TypeAlias

import numpy as np
import numpy.typing as npt

from meridian.domain.common import MeridianModel
from meridian.domain.records import Passage, RetrievalResult
from meridian.ports.runtime import IndexInfo
from meridian.retrieval import settings
from meridian.retrieval.manifest import ManifestRow

_REQUIRED_FILES: Final = ("manifest.json", "passages.jsonl", "vectors.npy", "index_record.json")
# The settings that shape the vectors; SEARCH_K and MIN_SCORE are query-time, so tuning them needs no rebuild.
_BUILD_SETTINGS: Final = (
    "EMBEDDING_MODEL",
    "SIMILARITY",
    "CHUNKER",
    "MAX_SECTION_CHARS",
    "PIECE_CHARS",
    "OVERLAP_CHARS",
)
_MANIFEST_FILES: Final = 17
_Reason: TypeAlias = Literal["index_missing", "dimension_mismatch", "manifest_not_17", "record_mismatch"]
_REASON_ORDER: Final[tuple[_Reason, ...]] = (
    "index_missing",
    "dimension_mismatch",
    "manifest_not_17",
    "record_mismatch",
)


class Readiness(MeridianModel):
    ok: bool
    reasons: tuple[_Reason, ...]


@dataclass(frozen=True, slots=True)
class _Loaded:
    info: IndexInfo
    passages: tuple[Passage, ...]
    matrix: npt.NDArray[np.float64]


def _manifest_hash(rows: tuple[ManifestRow, ...]) -> str:
    return hashlib.sha256(
        json.dumps(
            [r.model_dump(mode="json") for r in sorted(rows, key=lambda r: r.path)],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def _check(index_dir: Path) -> tuple[_Loaded | None, tuple[_Reason, ...]]:
    """Read every artefact; each fault maps to exactly its own reason."""
    if not index_dir.is_dir() or any(not (index_dir / name).is_file() for name in _REQUIRED_FILES):
        return None, ("index_missing",)
    found: set[_Reason] = set()

    raw: object = None
    info: IndexInfo | None = None
    try:
        raw = json.loads((index_dir / "index_record.json").read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("record is not an object")
        info = IndexInfo.model_validate({name: raw[name] for name in IndexInfo.model_fields if name in raw})
    except Exception:  # any failure reading this artefact is this reason, never an exception
        info = None
        found.add("record_mismatch")

    if isinstance(raw, dict):
        recorded = raw.get("settings")
        if not isinstance(recorded, dict) or any(
            recorded.get(name) != getattr(settings, name) for name in _BUILD_SETTINGS
        ):
            found.add("record_mismatch")

    rows: tuple[ManifestRow, ...] | None = None
    try:
        data = json.loads((index_dir / "manifest.json").read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("manifest is not a list")
        rows = tuple(ManifestRow.model_validate(item) for item in data)
        if len(rows) != _MANIFEST_FILES or len({r.path for r in rows}) != len(rows):
            found.add("manifest_not_17")
    except Exception:  # any failure reading this artefact is this reason, never an exception
        rows = None
        found.add("manifest_not_17")

    vectors: npt.NDArray[np.float32] | None = None
    try:
        loaded_vectors = np.load(index_dir / "vectors.npy", allow_pickle=False)
        if loaded_vectors.ndim != 2 or loaded_vectors.dtype != np.float32:
            found.add("dimension_mismatch")
        else:
            vectors = loaded_vectors
            if info is not None and loaded_vectors.shape[1] != info.dimension:
                found.add("dimension_mismatch")
    except Exception:  # any failure reading this artefact is this reason, never an exception
        vectors = None
        found.add("dimension_mismatch")

    passages: list[Passage] | None = None
    try:
        parsed: list[Passage] = []
        for line in (index_dir / "passages.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError("passage line is not an object")
            obj.pop("embed_text", None)
            parsed.append(Passage.model_validate({**obj, "score": 0.0}))
        passages = parsed
    except Exception:  # any failure reading this artefact is this reason, never an exception
        passages = None
        found.add("record_mismatch")

    if info is not None:
        if rows is not None and (info.files != len(rows) or info.manifest_hash != _manifest_hash(rows)):
            found.add("record_mismatch")
        if passages is not None and info.chunks != len(passages):
            found.add("record_mismatch")
        if vectors is not None and info.chunks != vectors.shape[0]:
            found.add("record_mismatch")

    if found or info is None or passages is None or vectors is None:
        return None, tuple(r for r in _REASON_ORDER if r in found) or ("record_mismatch",)
    return _Loaded(info, tuple(passages), np.asarray(vectors, dtype=np.float64)), ()


def _fastembed_query_embedder(cache_dir: Path | None) -> Callable[[str], npt.NDArray[np.float32]]:
    from fastembed import TextEmbedding  # local: readiness() and info() never load onnxruntime

    model = TextEmbedding(settings.EMBEDDING_MODEL, cache_dir=None if cache_dir is None else str(cache_dir))

    def embed(query: str) -> npt.NDArray[np.float32]:
        return np.asarray(next(iter(model.query_embed(query))), dtype=np.float32)

    return embed


class FastembedIndex:
    """Implements RetrievalIndex (DO-4 section 13) unchanged. No I/O in the constructor."""

    def __init__(
        self,
        index_dir: Path,
        *,
        model_cache_dir: Path | None = None,
        embed_query: Callable[[str], npt.NDArray[np.float32]] | None = None,
    ) -> None:
        self._index_dir = index_dir
        self._model_cache_dir = model_cache_dir
        self._embed_query = embed_query
        self._loaded: _Loaded | None = None
        self._load_lock = threading.Lock()
        self._embed_lock = threading.Lock()

    def readiness(self) -> Readiness:
        try:
            loaded, reasons = _check(self._index_dir)
        except (
            Exception
        ):  # never raises: anything outside the per-artefact blocks (e.g. permissions) is a missing index
            return Readiness(ok=False, reasons=("index_missing",))
        if loaded is not None:
            with self._load_lock:
                if self._loaded is None:
                    self._loaded = loaded
        return Readiness(ok=not reasons, reasons=reasons)

    def _ensure_loaded(self) -> _Loaded:
        with self._load_lock:
            if self._loaded is None:
                try:
                    loaded, reasons = _check(self._index_dir)
                except Exception:  # same net as readiness()
                    loaded, reasons = None, ("index_missing",)
                if loaded is None:
                    raise RuntimeError("retrieval index not ready: " + ", ".join(reasons))
                self._loaded = loaded
            return self._loaded

    def info(self) -> IndexInfo:
        return self._ensure_loaded().info

    def _embed(self, query: str) -> npt.NDArray[np.float32]:
        with self._embed_lock:
            if self._embed_query is None:
                self._embed_query = _fastembed_query_embedder(self._model_cache_dir)
            return self._embed_query(query)

    def search(self, query: str, *, k: int, min_score: float) -> RetrievalResult:
        if k < 1:
            raise ValueError("k must be at least 1")
        loaded = self._ensure_loaded()
        q = np.asarray(self._embed(query), dtype=np.float64).reshape(-1)
        if q.shape[0] != loaded.info.dimension:
            raise ValueError("query vector dimension does not match the index")
        norm = float(np.linalg.norm(q))
        if not np.isfinite(norm) or norm == 0.0:
            raise ValueError("query vector is empty")
        q = q / norm
        scores = loaded.matrix @ q
        order = np.argsort(-scores, kind="stable")
        hits: list[Passage] = []
        for i in order:
            s = float(scores[i])
            if s < min_score:
                break
            hits.append(loaded.passages[int(i)].model_copy(update={"score": s}))
            if len(hits) == k:
                break
        return RetrievalResult(passages=tuple(hits), below_floor=not hits)
