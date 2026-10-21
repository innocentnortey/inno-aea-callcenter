"""FakeIndex (AEA-11): the RetrievalIndex port with configured passages. No embedding model."""

from __future__ import annotations

import threading
from collections.abc import Mapping, Sequence

from meridian.domain.records import Passage, RetrievalResult
from meridian.ports.runtime import IndexInfo

FAKE_INDEX_DIMENSION = 384
FAKE_INDEX_FILES = 17


class FakeIndex:
    """Returns configured passages that clear `min_score`, best first, at most `k` (PD-12)."""

    def __init__(
        self,
        passages: Sequence[Passage] = (),
        *,
        by_query: Mapping[str, Sequence[Passage]] | None = None,
        info: IndexInfo | None = None,
    ) -> None:
        self._passages = tuple(passages)
        self._by_query = {q: tuple(p) for q, p in (by_query or {}).items()}
        self._info = info
        self._lock = threading.Lock()
        self.searches: list[tuple[str, int, float]] = []

    def search(self, query: str, *, k: int, min_score: float) -> RetrievalResult:
        with self._lock:
            self.searches.append((query, k, min_score))
        pool = self._by_query[query] if query in self._by_query else self._passages
        cleared = [p for p in pool if p.score >= min_score]
        ranked = sorted(cleared, key=lambda p: p.score, reverse=True)
        return RetrievalResult(passages=tuple(ranked[: max(k, 0)]), below_floor=not cleared)

    def info(self) -> IndexInfo:
        if self._info is not None:
            return self._info
        every = list(self._passages) + [p for ps in self._by_query.values() for p in ps]
        return IndexInfo(
            embedding_model="BAAI/bge-small-en-v1.5",
            dimension=FAKE_INDEX_DIMENSION,
            chunks=len({p.passage_id for p in every}),
            manifest_hash="fake-index",
            files=FAKE_INDEX_FILES,
        )
