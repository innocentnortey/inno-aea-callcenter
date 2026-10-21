"""kb_search: the knowledge specialist's one tool (stage7/data.md section 4; graph-tools.md section 1).

knowledge_tools() binds it to a RetrievalIndex; nothing registers itself. Reads only; writes and logs nothing.
"""

from __future__ import annotations

import json
from typing import Final

from pydantic import Field, JsonValue

from meridian.domain.common import LLMFacing
from meridian.domain.records import Passage, RetrievalResult
from meridian.domain.specialists import KnowledgeCapture
from meridian.domain.tools import LookupEntry, ToolCallScope, ToolDef, ToolKind, ToolResult
from meridian.ports.runtime import RetrievalIndex
from meridian.retrieval.settings import MIN_SCORE, SEARCH_K

KB_SEARCH_NAME: Final = "kb_search"
_FOR_MODEL_MAX_CHARS: Final = 4_000  # DO-4 section 5 "<= 4,000 chars rendered"; equals dispatch.MAX_CONTENT_CHARS (AEA-22), asserted by test_knowledge.py
_CUT_MARK: Final = "…"
_SECTION_FALLBACK_CHARS: Final = 80
_DESCRIPTION: Final = (
    "Search Meridian Home Comfort's current company documents: membership plans and prices, fees and the repair "
    "price list, warranty terms, services offered and not offered, phone and holiday hours, the service area, "
    "safety guidance and troubleshooting steps. "
    'Returns {"below_floor": false, "passages": [...]} with up to 3 passages, each with passage_id, file, section, '
    "version_label and text, highest relevance first; cite passage_id for every fact you use. "
    'Returns {"below_floor": true, "passages": []} when no current document is relevant enough: then say '
    "Meridian's documents don't cover it and offer a person; never answer from memory. "
    "Use it for general company and policy questions. Do not use it for one customer's own invoices, membership or "
    "warranty records (use read_invoices, read_membership or read_warranty after the customer is verified), or to "
    "find or change appointments (use the scheduling tools)."
)


class KbSearchArgs(LLMFacing):
    query: str = Field(
        min_length=1,
        max_length=300,
        description="The customer's question in plain words, for example 'How much is the Comfort Club?'",
    )


def _length(value: JsonValue) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def _cut(text: str, m: int) -> str:
    return text if len(text) <= m else text[:m] + _CUT_MARK


def _entry(p: Passage, text: str, section: str) -> dict[str, JsonValue]:
    return {
        "passage_id": p.passage_id,
        "file": p.file,
        "section": section,
        "version_label": p.version_label,
        "text": text,
    }


def _render(entries: list[dict[str, JsonValue]]) -> dict[str, JsonValue]:
    return {"below_floor": False, "passages": list(entries)}


def _fit(passages: tuple[Passage, ...]) -> tuple[dict[str, JsonValue], tuple[Passage, ...]]:
    """Largest text cut that keeps the rendered value within the limit; ids, files and labels are never cut."""

    def render(
        texts_max: int | None, section_max: int | None, kept: tuple[Passage, ...]
    ) -> dict[str, JsonValue]:
        return _render(
            [
                _entry(
                    p,
                    p.text if texts_max is None else _cut(p.text, texts_max),
                    p.section if section_max is None else _cut(p.section, section_max),
                )
                for p in kept
            ]
        )

    full = render(None, None, passages)
    if _length(full) <= _FOR_MODEL_MAX_CHARS:
        return full, passages
    if _length(render(0, None, passages)) <= _FOR_MODEL_MAX_CHARS:
        lo, hi = 0, max(len(p.text) for p in passages)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if _length(render(mid, None, passages)) <= _FOR_MODEL_MAX_CHARS:
                lo = mid
            else:
                hi = mid - 1
        return render(lo, None, passages), passages
    kept = passages
    while len(kept) > 1 and _length(render(0, _SECTION_FALLBACK_CHARS, kept)) > _FOR_MODEL_MAX_CHARS:
        kept = kept[:-1]
    return render(0, _SECTION_FALLBACK_CHARS, kept), kept


def _for_model(result: RetrievalResult) -> tuple[dict[str, JsonValue], tuple[Passage, ...]]:
    if result.below_floor or not result.passages:
        return {"below_floor": True, "passages": []}, ()
    return _fit(result.passages)


def _result_seen(below: bool, shown: tuple[Passage, ...]) -> str:
    if below:
        return "below_floor=true"
    return "; ".join(["below_floor=false", *(f"{p.passage_id}={p.score:.3f}" for p in shown)])


def knowledge_tools(retrieval: RetrievalIndex) -> tuple[ToolDef, ...]:
    def _execute(args: LLMFacing, scope: ToolCallScope) -> ToolResult:
        if not isinstance(args, KbSearchArgs):
            raise TypeError("kb_search expects KbSearchArgs")
        result = retrieval.search(args.query, k=SEARCH_K, min_score=MIN_SCORE)
        for_model, shown = _for_model(result)
        lookup = LookupEntry(
            tool=KB_SEARCH_NAME,
            record_ids=(),
            passage_ids=tuple(p.passage_id for p in shown),
            result_seen=_result_seen(result.below_floor or not shown, shown),
            message_id=scope.message_id,
            turn_id=scope.ids.turn_id,
        )
        return ToolResult(
            ok=True,
            for_model=for_model,
            captured=KnowledgeCapture(result=result),
            lookup=lookup,
            lookup_written=False,
        )

    return (
        ToolDef(
            name=KB_SEARCH_NAME,
            description=_DESCRIPTION,
            args_model=KbSearchArgs,
            kind=ToolKind.KB_SEARCH,
            effect="read",
            requires_verified=False,
            executor=_execute,
        ),
    )
