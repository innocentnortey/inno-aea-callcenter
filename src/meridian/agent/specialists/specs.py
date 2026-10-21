"""The three specialists as data (AEA-35; DO-3 §4.5, S-12; graph-tools §2–§3, GRT-6, GRT-7).

Each `SpecialistSpec` names its tool kinds, report model, wording and result builder. Builders fold what the tools
captured into the result and never read model text for a record value.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, cast

from pydantic import JsonValue

from meridian.agent.prompts.specialists import (
    REPORT_FACTS_DESCRIPTION,
    render_account,
    render_knowledge,
    render_scheduling,
)
from meridian.agent.prompts.specialists import REPORT_FACTS_TOOL as REPORT_FACTS_TOOL
from meridian.domain.common import HaltReason, LLMFacing, PassageId, ProviderFailure, ToolErrorCode
from meridian.domain.records import Passage, ShownSlot
from meridian.domain.specialists import (
    AccountCapture,
    AccountReport,
    AccountResult,
    KnowledgeCapture,
    KnowledgePoint,
    KnowledgeReport,
    KnowledgeResult,
    SchedulingCapture,
    SchedulingReport,
    SchedulingResult,
    SpecialistResult,
)
from meridian.domain.tools import SpecialistTask, ToolCallRecord, ToolKind
from meridian.domain.turn import SpecialistKind, TurnContext
from meridian.ports.models import CallRecord, ToolSchema

__all__ = [
    "REPORT_FACTS_TOOL",
    "SPECS",
    "TROUBLESHOOTING_FILE",
    "RunOutcome",
    "SpecialistSpec",
    "build_account_result",
    "build_knowledge_result",
    "build_scheduling_result",
    "report_facts_schema",
]

TROUBLESHOOTING_FILE: Final = "faq/troubleshooting_before_you_call.md"  # graph-tools §6; DO-4 §5 quick_checks


@dataclass(frozen=True)
class RunOutcome:  # graph-tools §2, fields exactly; never leaves the run
    task: SpecialistTask
    captured: tuple[KnowledgeCapture | AccountCapture | SchedulingCapture, ...]  # model rounds only, in order
    passages_returned: tuple[Passage, ...]  # model-requested kb_search passages, de-duplicated, first kept
    report: LLMFacing | None  # the validated report_facts args, or None
    quick_checks: tuple[Passage, ...]  # graph-tools §6; () unless the task asked for the offer
    tools: tuple[ToolCallRecord, ...]
    calls: tuple[CallRecord, ...]
    brake: HaltReason | None
    failure: ProviderFailure | None


@dataclass(frozen=True)
class SpecialistSpec:  # graph-tools §2, fields exactly
    kind: SpecialistKind
    tool_kinds: frozenset[ToolKind]
    report_model: type[LLMFacing]
    render: Callable[[SpecialistTask, TurnContext], tuple[str, str, str]]
    build_result: Callable[[RunOutcome], SpecialistResult]


def report_facts_schema(spec: SpecialistSpec) -> ToolSchema:
    # PD-9: the report model's own schema, untrimmed (AEA-60 AC-5 compares it to spec.report_model's).
    return ToolSchema(
        name=REPORT_FACTS_TOOL,
        description=REPORT_FACTS_DESCRIPTION,
        input_schema=cast("dict[str, JsonValue]", spec.report_model.model_json_schema()),
        strict=True,
    )


def build_knowledge_result(outcome: RunOutcome) -> KnowledgeResult:
    """GRT-7, R-13: a point counts only if a search this run returned its passage above the floor."""
    caps = [c for c in outcome.captured if isinstance(c, KnowledgeCapture)]
    citable: set[PassageId] = {
        p.passage_id for c in caps if not c.result.below_floor for p in c.result.passages
    }
    report = outcome.report if isinstance(outcome.report, KnowledgeReport) else None
    points: tuple[KnowledgePoint, ...] = ()
    if report is not None and report.answered:
        points = tuple(
            KnowledgePoint(text=p.text, passage_id=p.passage_id)
            for p in report.points
            if p.passage_id in citable
        )
    quick = tuple(
        p.passage_id
        for p in outcome.passages_returned
        if p.file == TROUBLESHOOTING_FILE and p.passage_id in citable
    )
    if outcome.failure is not None:
        status: str = "failed"
        points = ()
    elif points:
        status = "answered"
    else:
        status = "no_current_source"
        points = ()
    return KnowledgeResult.model_validate(
        {
            "status": status,
            "passages": outcome.passages_returned,
            "points": points,
            "quick_checks": quick,
            "tools": outcome.tools,
            "calls": outcome.calls,
            "brake": outcome.brake,
            "failure": outcome.failure,
        }
    )


def build_account_result(outcome: RunOutcome) -> AccountResult:
    """R-17, HP-3: invoices as billed; staff notes are copied for the brief and case view only."""
    caps = [c for c in outcome.captured if isinstance(c, AccountCapture)]
    seen_inv: set[str] = set()
    ordered = []
    for c in caps:
        for inv in c.invoices:
            if str(inv.invoice_id) not in seen_inv:
                seen_inv.add(str(inv.invoice_id))
                ordered.append(inv)
    invoices = tuple(ordered)
    membership = None
    warranty = None
    for c in caps:
        if c.membership is not None:
            membership = c.membership
        if c.warranty is not None:
            warranty = c.warranty
    seen_notes: set[tuple[str, str, str]] = set()
    notes = []
    for c in caps:
        for n in c.staff_notes:
            key = (n.kind, str(n.record_id), n.text)
            if key not in seen_notes:
                seen_notes.add(key)
                notes.append(n)
    if outcome.failure is not None:
        status = "failed"
    elif caps:
        status = "read"
    elif any(r.error == ToolErrorCode.NOT_VERIFIED for r in outcome.tools):
        status = "not_verified"
    else:
        status = "failed"
    return AccountResult.model_validate(
        {
            "status": status,
            "invoices": invoices,
            "membership": membership,
            "warranty": warranty,
            "staff_notes": tuple(notes),
            "tools": outcome.tools,
            "calls": outcome.calls,
            "brake": outcome.brake,
            "failure": outcome.failure,
        }
    )


_REFUSAL_STATUS: Final = MappingProxyType(
    {
        ToolErrorCode.NOT_VERIFIED: "not_verified",
        ToolErrorCode.SLOT_TAKEN: "slot_taken",
        ToolErrorCode.OUTSIDE_SERVICE_AREA: "out_of_area",
        ToolErrorCode.BOOKING_CAP: "booking_cap",
    }
)


def build_scheduling_result(outcome: RunOutcome) -> SchedulingResult:
    """R-18…R-22, WP-4: a fee-bearing request is never a write."""
    caps = [c for c in outcome.captured if isinstance(c, SchedulingCapture)]
    write = None
    change_request = None
    for c in caps:
        if c.write is not None:
            write = c.write
        if c.change_request is not None:
            change_request = c.change_request
    windows: tuple[ShownSlot, ...] = ()
    for c in caps:
        if c.windows:
            windows = c.windows
    refusal: str | None = None
    for r in outcome.tools:
        if r.error is not None and r.error in _REFUSAL_STATUS:
            refusal = _REFUSAL_STATUS[r.error]
    searched_empty = any(
        not c.windows and c.write is None and c.change_request is None and c.refused is None for c in caps
    )
    if outcome.failure is not None:
        status = "failed"
    elif write is not None:
        status = "written"
    elif change_request is not None:
        status = "staff_change_request"
    elif refusal is not None:
        status = refusal
    elif windows:
        status = "windows_shown"
    elif searched_empty:
        status = "no_fit"
    else:
        status = "failed"
    return SchedulingResult.model_validate(
        {
            "status": status,
            "windows": windows,
            "write": write,
            "change_request": change_request,
            "quick_checks": outcome.quick_checks,
            "tools": outcome.tools,
            "calls": outcome.calls,
            "brake": outcome.brake,
            "failure": outcome.failure,
        }
    )


_SPECS: dict[SpecialistKind, SpecialistSpec] = {
    "knowledge": SpecialistSpec(
        kind="knowledge",
        tool_kinds=frozenset({ToolKind.KB_SEARCH}),
        report_model=KnowledgeReport,
        render=render_knowledge,
        build_result=build_knowledge_result,
    ),
    "account": SpecialistSpec(
        kind="account",
        tool_kinds=frozenset({ToolKind.ACCOUNT_READ}),
        report_model=AccountReport,
        render=render_account,
        build_result=build_account_result,
    ),
    "scheduling": SpecialistSpec(
        kind="scheduling",
        tool_kinds=frozenset(
            {ToolKind.SLOT_SEARCH, ToolKind.BOOK, ToolKind.MOVE, ToolKind.CANCEL, ToolKind.CHANGE_REQUEST}
        ),
        report_model=SchedulingReport,
        render=render_scheduling,
        build_result=build_scheduling_result,
    ),
}
SPECS: Final[Mapping[SpecialistKind, SpecialistSpec]] = MappingProxyType(_SPECS)
