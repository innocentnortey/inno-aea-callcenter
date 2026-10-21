"""AEA-33: the kb_search tool (args, factory, executor, dispatch seam)."""

from __future__ import annotations

import ast
import json
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pytest
from pydantic import ValidationError

from meridian.adapters.retrieval_fastembed import FastembedIndex
from meridian.agent.tools import dispatch, knowledge
from meridian.agent.tools.dispatch import ToolDispatcher, ToolRegistry
from meridian.agent.tools.knowledge import KbSearchArgs, knowledge_tools
from meridian.domain.common import LLMFacing, ToolErrorCode
from meridian.domain.records import Passage, RetrievalResult
from meridian.domain.specialists import KnowledgeCapture
from meridian.domain.tools import ToolCallScope, ToolDef, ToolKind
from meridian.ports.models import ToolCall
from meridian.ports.runtime import UnitOfWorkFactory
from meridian.retrieval.settings import MIN_SCORE, SEARCH_K
from tests.fakes import WORKED_PAIRS_NOW, FakeIndex
from tests.unit.adapters.test_retrieval_fastembed import (
    FIXTURE_SCORES,
    ROOT,
    StandInEmbed,
    fixture_passages,
    write_index_dir,
)
from tests.unit.agent.tools.dispatch_doubles import RecordingUow

THREAD = "3f2b8c1e-5d4a-4e7b-9c2d-1a2b3c4d5e6f"
TURN = "7c9e6679-7425-40de-944b-e07fc1f90ae7"
REQUEST = "16fd2706-8baf-433b-82eb-8c7fada847da"


def make_scope(message_id: int = 41) -> ToolCallScope:
    return ToolCallScope.model_validate(
        {
            "ids": {
                "thread_id": THREAD,
                "turn_id": TURN,
                "request_id": REQUEST,
                "run_tag": "live",
                "run_id": None,
                "agent_version": "test",
            },
            "customer_id": None,
            "shown_slot_ids": frozenset(),
            "now": WORKED_PAIRS_NOW,
            "message_id": message_id,
        }
    )


def scored(passages: Sequence[Passage], scores: Sequence[float]) -> tuple[Passage, ...]:
    return tuple(p.model_copy(update={"score": s}) for p, s in zip(passages, scores, strict=True))


def _args(q: str = "How much is the Comfort Club?") -> KbSearchArgs:
    return KbSearchArgs(query=q)


def test_factory_tooldef_and_binding() -> None:
    ix1 = FakeIndex(scored(fixture_passages()[:3], (0.9, 0.7, 0.65)))
    ix2 = FakeIndex()
    defs = knowledge_tools(ix1)
    assert len(defs) == 1
    d = defs[0]
    assert d.name == "kb_search"
    assert d.kind is ToolKind.KB_SEARCH
    assert d.effect == "read"
    assert d.requires_verified is False
    assert d.args_model is KbSearchArgs
    assert "read_invoices" in d.description
    assert "below_floor" in d.description

    for bad in ({"query": ""}, {"query": "a" * 301}, {"query": "fees", "extra": 1}):
        with pytest.raises(ValidationError):
            KbSearchArgs.model_validate(bad)
    KbSearchArgs.model_validate({"query": "a" * 300})

    d.executor(_args(), make_scope())
    assert ix1.searches == [("How much is the Comfort Club?", SEARCH_K, MIN_SCORE)]
    print(SEARCH_K, MIN_SCORE)

    d2 = knowledge_tools(ix2)[0]
    assert d2 is not d
    assert d2.executor is not d.executor
    d2.executor(_args("other"), make_scope())
    assert len(ix1.searches) == 1
    assert len(ix2.searches) == 1

    for name in dir(knowledge):
        value = getattr(knowledge, name)
        assert not isinstance(value, ToolDef)
        if isinstance(value, list | tuple | set | frozenset):
            assert not any(isinstance(v, ToolDef) for v in value)
        if isinstance(value, dict):
            assert not any(isinstance(v, ToolDef) for v in value.values())

    class Other(LLMFacing):
        pass

    with pytest.raises(TypeError):
        d.executor(Other(), make_scope())


def test_no_source_below_floor() -> None:
    passages = scored(fixture_passages()[:2], (0.55, 0.4))
    d = knowledge_tools(FakeIndex(passages))[0]
    result = d.executor(_args(), make_scope())
    assert result.ok is True
    assert result.for_model == {"below_floor": True, "passages": []}
    dumped = json.dumps(result.for_model)
    assert all(p.text not in dumped for p in passages)
    assert result.lookup.passage_ids == ()
    assert result.lookup.result_seen == "below_floor=true"
    assert isinstance(result.captured, KnowledgeCapture)
    assert result.captured.result.below_floor is True


def _long(text_len: int, section: str = "Plans") -> tuple[Passage, ...]:
    return tuple(
        Passage.model_validate(
            {
                "passage_id": f"membership/comfort_club_overview.md#{i}",
                "file": "membership/comfort_club_overview.md",
                "section": section,
                "version_label": "Effective 2026-01-01",
                "version_date": "2026-01-01",
                "text": ("a" if text_len == 1100 else "b") * text_len,
                "score": s,
            }
        )
        for i, s in enumerate((0.9, 0.8, 0.7))
    )


@pytest.mark.parametrize(
    ("passages", "whole"),
    [
        pytest.param(_long(1100), True, id="a_fits_whole"),
        pytest.param(_long(1500), False, id="b_cut"),
        pytest.param(_long(1500, "Very long section " * 30), False, id="c_cut_long_section"),
    ],
)
def test_for_model_within_limit(passages: tuple[Passage, ...], whole: bool) -> None:
    result = knowledge_tools(FakeIndex(passages))[0].executor(_args(), make_scope())
    fm = cast(dict[str, list[dict[str, str]]], result.for_model)
    n = len(json.dumps(fm, ensure_ascii=False, separators=(",", ":")))
    print("for_model chars", n)
    assert n <= 4000
    assert len(fm["passages"]) == 3
    for shown, original in zip(fm["passages"], passages, strict=True):
        assert shown["passage_id"] == original.passage_id
        assert shown["file"] == original.file
        assert shown["version_label"] == original.version_label
        if whole:
            assert shown["text"] == original.text
        else:
            assert shown["text"].endswith("…")
            assert original.text.startswith(shown["text"][:-1])
    assert result.lookup.passage_ids == tuple(p.passage_id for p in passages)


def test_lookup_and_logs_hold_no_text(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    ix = FastembedIndex(write_index_dir(tmp_path / "i"), embed_query=StandInEmbed())
    sentinel = "zebra-quartz-7731"
    result = knowledge_tools(ix)[0].executor(_args(f"{sentinel} how much is the Comfort Club"), make_scope())
    assert sentinel not in result.lookup.model_dump_json()
    assert sentinel not in json.dumps(result.for_model, ensure_ascii=False)
    assert sentinel not in caplog.text
    assert "FIXTURE-PASSAGE-" not in result.lookup.result_seen
    assert "FIXTURE-PASSAGE-" not in caplog.text
    assert all(len(tok) <= 80 for tok in result.lookup.result_seen.split("; "))
    assert caplog.records == []


def test_lookup_entry_and_capture_complete() -> None:
    passages = scored(fixture_passages(), FIXTURE_SCORES)
    scope = make_scope(message_id=41)
    result = knowledge_tools(FakeIndex(passages))[0].executor(_args(), scope)
    top3 = passages[:3]
    assert result.lookup.tool == "kb_search"
    assert result.lookup.record_ids == ()
    assert result.lookup.passage_ids == tuple(p.passage_id for p in top3)
    assert result.lookup.result_seen == (
        "below_floor=false; membership/comfort_club_overview.md#0=0.900; "
        "faq/customer_faq.md#1=0.700; policies/escalation_and_safety.md#0=0.650"
    )
    assert result.lookup.message_id == 41
    assert result.lookup.turn_id == scope.ids.turn_id
    assert result.lookup_written is False
    assert result.ok is True
    assert result.captured == KnowledgeCapture(result=RetrievalResult(passages=top3, below_floor=False))
    fm = cast(dict[str, list[dict[str, str]]], result.for_model)
    assert fm["passages"][0] == {
        "passage_id": "membership/comfort_club_overview.md#0",
        "file": "membership/comfort_club_overview.md",
        "section": top3[0].section,
        "version_label": "Effective 2026-01-01",
        "text": top3[0].text,
    }


def test_knowledge_imports_and_literals() -> None:
    path = ROOT / "src/meridian/agent/tools/knowledge.py"
    source = path.read_text(encoding="utf-8")
    modules: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    for banned in (
        "fastembed",
        "numpy",
        "onnxruntime",
        "meridian.adapters",
        "meridian.agent",
        "meridian.retrieval.ingest",
    ):
        assert not any(m == banned or m.startswith(banned + ".") for m in modules), banned
    for m in modules:
        if m.startswith("meridian"):
            assert (
                m.startswith(("meridian.domain.", "meridian.ports.")) or m == "meridian.retrieval.settings"
            ), m
    squashed = source.replace(" ", "")
    assert "0.6" not in squashed
    assert "k=3" not in squashed
    print(knowledge._FOR_MODEL_MAX_CHARS, dispatch.MAX_CONTENT_CHARS)
    assert knowledge._FOR_MODEL_MAX_CHARS == dispatch.MAX_CONTENT_CHARS


def test_search_error_propagates() -> None:
    class _Boom:
        def search(self, query: str, *, k: int, min_score: float) -> RetrievalResult:
            raise RuntimeError("index not ready")

        def info(self) -> None:
            raise RuntimeError("index not ready")

    with pytest.raises(RuntimeError):
        knowledge_tools(cast(FakeIndex, _Boom()))[0].executor(_args("x"), make_scope())


def test_kb_search_through_dispatcher() -> None:
    ix = FakeIndex(scored(fixture_passages()[:3], (0.9, 0.7, 0.65)))
    registry = ToolRegistry(knowledge_tools(ix))
    kinds = frozenset({ToolKind.KB_SEARCH})
    registry.check_covers(kinds)
    uow = RecordingUow()
    d = ToolDispatcher(registry, cast(UnitOfWorkFactory, uow))
    call1 = ToolCall(id="c1", name="kb_search", args={"query": "How much is the Comfort Club?"})
    call2 = ToolCall(id="c2", name="kb_search", args={"query": ""})
    out = d.dispatch([call1, call2], kinds=kinds, scope=make_scope())

    schemas = d.schemas(kinds)
    assert [s.name for s in schemas] == ["kb_search"]
    assert set(cast(dict[str, object], schemas[0].input_schema["properties"])) == {"query"}

    assert out[0].record.outcome == "ok"
    assert json.loads(out[0].content) == out[0].result.for_model
    assert not out[0].content.startswith('{"truncated"')
    ids = tuple(p.passage_id for p in fixture_passages()[:3])
    assert out[0].record.passage_ids == ids
    # dispatch also writes a row for the refused call (result_seen "refused:bad_arguments", no passages)
    assert len(uow.appended) == 2
    row = uow.appended[0]
    assert row.tool == "kb_search"
    assert row.passage_ids == ids
    assert row.result_seen == out[0].result.lookup.result_seen
    assert out[1].record.outcome == "refused"
    assert out[1].record.error is ToolErrorCode.BAD_ARGUMENTS
    assert uow.appended[1].passage_ids == ()
    assert [q for q, _, _ in ix.searches] == ["How much is the Comfort Club?"]
