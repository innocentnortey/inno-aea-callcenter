"""AEA-33: the RetrievalIndex contract (fixture index and FakeIndex) and the DEC-4 traps on the real index."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterator, Sequence
from pathlib import Path

import numpy as np
import numpy.typing as npt
import pytest

from meridian.adapters.retrieval_fastembed import FastembedIndex, Readiness
from meridian.agent.tools.knowledge import KbSearchArgs, knowledge_tools
from meridian.ports.runtime import RetrievalIndex
from meridian.retrieval.ingest import build_index
from meridian.retrieval.settings import EMBEDDING_MODEL, MIN_SCORE, SEARCH_K
from tests.fakes import FakeIndex
from tests.unit.adapters.test_retrieval_fastembed import (
    FIXTURE_SCORES,
    KB_DIR,
    TRANSCRIPTIONS_DIR,
    StandInEmbed,
    cached_model_dir,
    fixture_passages,
    requires_model,
    write_index_dir,
)
from tests.unit.agent.tools.test_knowledge import make_scope, scored

NEG_INF = float("-inf")
_DATE = re.compile(r"(?<![0-9])[0-9]{4}-[0-9]{2}-[0-9]{2}(?![0-9])")


@pytest.fixture(params=["fastembed-fixture", "fake-index"])
def index_impl(request: pytest.FixtureRequest, tmp_path: Path) -> RetrievalIndex:
    if request.param == "fastembed-fixture":
        return FastembedIndex(write_index_dir(tmp_path / "i"), embed_query=StandInEmbed())
    return FakeIndex(scored(fixture_passages(), FIXTURE_SCORES))


@pytest.mark.parametrize(
    ("k", "min_score"),
    [(3, 0.6), (2, 0.6), (5, 0.6), (1, 0.0), (5, 0.95), (3, NEG_INF), (10, NEG_INF)],
)
def test_search_shape_and_floor(index_impl: RetrievalIndex, k: int, min_score: float) -> None:
    expected = min(k, sum(s >= min_score for s in FIXTURE_SCORES))
    r = index_impl.search("q", k=k, min_score=min_score)
    assert len(r.passages) == expected
    scores = [p.score for p in r.passages]
    assert all(s >= min_score for s in scores)
    assert scores == sorted(scores, reverse=True)
    assert scores == pytest.approx(list(FIXTURE_SCORES[:expected]), abs=1e-5)
    for p in r.passages:
        assert p.passage_id.startswith(p.file + "#")
        assert p.section
        assert p.version_label
        found = _DATE.search(p.version_label)
        if found is None:
            assert p.version_date is None
        else:
            assert p.version_date == dt.date.fromisoformat(found.group(0))
    assert r.below_floor == (expected == 0)


@pytest.fixture(scope="module")
def real_index(tmp_path_factory: pytest.TempPathFactory) -> Iterator[FastembedIndex]:
    cache = cached_model_dir()
    if cache is None:
        pytest.skip("bge-small-en-v1.5 is not cached locally")
    from fastembed import TextEmbedding

    model = TextEmbedding(EMBEDDING_MODEL, cache_dir=str(cache), local_files_only=True)

    def embed(texts: Sequence[str]) -> npt.NDArray[np.float32]:
        return np.asarray([np.asarray(v) for v in model.embed(list(texts))], dtype=np.float32)

    out = tmp_path_factory.mktemp("real") / "index"
    run = build_index(KB_DIR, out, transcriptions_dir=TRANSCRIPTIONS_DIR, embed=embed)
    assert run.status == "completed"
    ix = FastembedIndex(out, model_cache_dir=cache)
    assert ix.readiness() == Readiness(ok=True, reasons=())
    yield ix


_TRAPS = {
    "archive/",
    "faq/faq_old_copy.md",
    "services/scheduling_guide.md",
}
_STALE_QUERIES = [
    ("How much is the Comfort Club?", {"membership/comfort_club_overview.md"}),
    ("How long is the repair warranty?", {"warranty/warranty_policy.md"}),
    (
        "What's the diagnostic fee?",
        {"faq/customer_faq.md", "pricing/2026_fee_schedule.pdf", "pricing/repair_price_book_2026.csv"},
    ),
    (
        "Can I cancel any time for a full refund?",
        {"membership/comfort_club_overview.md", "faq/customer_faq.md"},
    ),
    (
        "What are your phone hours?",
        {"faq/customer_faq.md", "policies/service_area.md", "policies/holiday_hours_2026.png"},
    ),
]


@requires_model
@pytest.mark.parametrize(("query", "expected"), _STALE_QUERIES)
def test_stale_traps_on_real_index(real_index: FastembedIndex, query: str, expected: set[str]) -> None:
    r = real_index.search(query, k=SEARCH_K, min_score=MIN_SCORE)
    files = [p.file for p in r.passages]
    print(query, "->", [(p.file, round(p.score, 3)) for p in r.passages])
    assert r.below_floor is False
    assert not any(f.startswith("archive/") or f in _TRAPS for f in files)
    assert expected & set(files)


@requires_model
def test_off_corpus_below_floor(real_index: FastembedIndex) -> None:
    query = "How long have you been in business?"
    r = real_index.search(query, k=SEARCH_K, min_score=MIN_SCORE)
    assert r.below_floor is True
    assert r.passages == ()
    top = real_index.search(query, k=1, min_score=NEG_INF).passages[0]
    print("top score", round(top.score, 3), top.file)
    result = knowledge_tools(real_index)[0].executor(KbSearchArgs(query=query), make_scope())
    assert result.for_model == {"below_floor": True, "passages": []}


@requires_model
def test_staff_only_and_stub_not_returned(real_index: FastembedIndex) -> None:
    banned = ("internal/agent_discretion_notes.md", "services/duct_cleaning.md")
    queries = [
        "Can you waive the late-cancellation fee?",
        "Can I get a courtesy discount?",
        "The technician was late, can you waive the diagnostic fee?",
        "Do you do duct cleaning?",
    ]
    tool = knowledge_tools(real_index)[0]
    for q in queries:
        result = tool.executor(KbSearchArgs(query=q), make_scope())
        captured = result.captured
        assert captured is not None and captured.kind == "knowledge"
        files = [p.file for p in captured.result.passages]
        print(q, "->", files)
        assert not any(f in banned for f in files)
        rendered = str(result.for_model)
        assert not any(b in rendered for b in banned)
    everything = real_index.search("x", k=real_index.info().chunks, min_score=NEG_INF)
    assert not any(p.file in banned for p in everything.passages)


@requires_model
def test_wp1_stale_twin_on_real_index(real_index: FastembedIndex) -> None:
    r = real_index.search("How much is the Comfort Club?", k=SEARCH_K, min_score=MIN_SCORE)
    assert r.below_floor is False
    assert not any(p.file.startswith("archive/") for p in r.passages)
    hits = [p for p in r.passages if p.file == "membership/comfort_club_overview.md"]
    assert hits
    assert any(
        p.version_label == "Effective 2026-01-01"
        and p.version_date == dt.date(2026, 1, 1)
        and "$189" in p.text
        and "$16.99" in p.text
        for p in hits
    )


@requires_model
def test_duct_cleaning_answered_from_catalog(real_index: FastembedIndex) -> None:
    r = real_index.search("Do you do duct cleaning?", k=SEARCH_K, min_score=MIN_SCORE)
    print([(p.file, round(p.score, 3)) for p in r.passages])
    assert "services/service_catalog.md" in [p.file for p in r.passages]
