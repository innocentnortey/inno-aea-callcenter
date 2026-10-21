"""Spec and builder tests (AEA-35 AC-5…AC-8, AC-17…AC-19). Synthetic values only."""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType

from meridian.agent.prompts.specialists import REPORT_FACTS_DESCRIPTION
from meridian.agent.specialists.specs import (
    SPECS,
    RunOutcome,
    build_account_result,
    build_knowledge_result,
    build_scheduling_result,
    report_facts_schema,
)
from meridian.domain.common import CustomerId, PassageId, ToolErrorCode
from meridian.domain.records import Passage, RetrievalResult
from meridian.domain.specialists import (
    AccountCapture,
    AccountReport,
    KnowledgeCapture,
    KnowledgeReport,
    ReportedPoint,
    SchedulingCapture,
    SchedulingReport,
    SchedulingResult,
)
from meridian.domain.tools import SpecialistTask, ToolKind
from meridian.domain.turn import TaskIntent
from meridian.ports.models import ToolCall
from tests.fakes import FakeToolModel, InMemoryTraceSink
from tests.unit.agent.specialists._doubles import (
    APPT_WP4,
    ARCHIVE_ID,
    DRAFT_WP4,
    FAQ_CREDIT,
    INV_204411,
    SLOT_44,
    SLOT_61,
    TROUBLESHOOTING,
    WP1_INCLUDES,
    WP1_MINIMUM,
    WP1_PRICE,
    WRITE_WP4F,
    ScriptedDispatcher,
    ScriptedGateway,
    dispatched,
    make_runner,
    make_task,
    refused_dispatched,
    report_call,
    scheduling_slice,
    scope,
    step,
    tool_call,
    turn_ctx,
)

_SRC = Path(__file__).resolve().parents[4] / "src" / "meridian" / "agent"
_WP1_ALL = (WP1_INCLUDES, WP1_PRICE, WP1_MINIMUM)


def _outcome(
    task: SpecialistTask,
    *,
    captured: tuple[KnowledgeCapture | AccountCapture | SchedulingCapture, ...] = (),
    passages: tuple[Passage, ...] = (),
    report: object = None,
) -> RunOutcome:
    return RunOutcome(
        task=task,
        captured=captured,
        passages_returned=passages,
        report=report,  # type: ignore[arg-type]
        quick_checks=(),
        tools=(),
        calls=(),
        brake=None,
        failure=None,
    )


def _kb_task() -> SpecialistTask:
    return make_task("knowledge", TaskIntent.ANSWER_QUESTION, "q")


def _kb_cap(passages: tuple[Passage, ...], *, below_floor: bool = False) -> KnowledgeCapture:
    return KnowledgeCapture(result=RetrievalResult(passages=passages, below_floor=below_floor))


def test_specs_cover_every_kind() -> None:
    assert set(SPECS) == {"knowledge", "account", "scheduling"}
    assert SPECS["knowledge"].tool_kinds == frozenset({ToolKind.KB_SEARCH})
    assert SPECS["account"].tool_kinds == frozenset({ToolKind.ACCOUNT_READ})
    assert SPECS["scheduling"].tool_kinds == frozenset(
        {ToolKind.SLOT_SEARCH, ToolKind.BOOK, ToolKind.MOVE, ToolKind.CANCEL, ToolKind.CHANGE_REQUEST}
    )
    assert SPECS["knowledge"].report_model is KnowledgeReport
    assert SPECS["account"].report_model is AccountReport
    assert SPECS["scheduling"].report_model is SchedulingReport
    assert isinstance(SPECS, MappingProxyType)
    from tests.unit.agent.specialists._doubles import turn_ids  # noqa: F401

    sink = InMemoryTraceSink()
    with turn_ctx(sink) as ctx:
        for key, spec in SPECS.items():
            assert spec.kind == key
            task = make_task(key, TaskIntent.ANSWER_QUESTION, "hello")
            out = spec.render(task, ctx)
            assert len(out) == 3
            assert all(isinstance(s, str) for s in out)


def test_report_facts_schema_from_report_model() -> None:
    for spec in SPECS.values():
        s = report_facts_schema(spec)
        assert s.name == "report_facts"
        assert s.strict is True
        assert s.input_schema == spec.report_model.model_json_schema()
        assert s.description == REPORT_FACTS_DESCRIPTION


def test_results_from_captured_not_report() -> None:
    acct = build_account_result(
        _outcome(
            make_task("account", TaskIntent.READ_INVOICE, "q"),
            captured=(AccountCapture(invoices=(INV_204411,)),),
            report=AccountReport(summary="Total $999.00, due tomorrow"),
        )
    )
    assert acct.invoices == (INV_204411,)
    assert "999" not in acct.model_dump_json()
    sched = build_scheduling_result(
        _outcome(
            make_task("scheduling", TaskIntent.BOOK_NEW, "q"),
            captured=(SchedulingCapture(windows=(SLOT_44, SLOT_61)),),
            report=SchedulingReport(appointment_id=999, wanted_time="slot 77", note="booked slot 77"),
        )
    )
    assert sched.windows == (SLOT_44, SLOT_61)
    assert sched.write is None
    assert 77 not in [w.slot_id for w in sched.windows]
    assert sched.status == "windows_shown"


def test_zero_valid_points_no_current_source() -> None:
    result = build_knowledge_result(
        _outcome(
            _kb_task(),
            captured=(_kb_cap(_WP1_ALL),),
            passages=_WP1_ALL,
            report=KnowledgeReport(points=[ReportedPoint(text="x", passage_id=ARCHIVE_ID)], answered=True),
        )
    )
    assert result.status == "no_current_source"
    assert result.points == ()
    assert result.passages == _WP1_ALL


def test_below_floor_no_current_source() -> None:
    result = build_knowledge_result(
        _outcome(
            _kb_task(),
            captured=(_kb_cap((), below_floor=True),),
            report=KnowledgeReport(
                points=[
                    ReportedPoint(text="x", passage_id=PassageId("membership/comfort_club_overview.md#0"))
                ],
                answered=True,
            ),
        )
    )
    assert result.status == "no_current_source"
    assert result.points == ()


def test_knowledge_quick_checks_only_from_troubleshooting() -> None:
    both = (TROUBLESHOOTING, FAQ_CREDIT)
    r1 = build_knowledge_result(_outcome(_kb_task(), captured=(_kb_cap(both),), passages=both))
    assert r1.quick_checks == (TROUBLESHOOTING.passage_id,)
    r2 = build_knowledge_result(
        _outcome(_kb_task(), captured=(_kb_cap((FAQ_CREDIT,)),), passages=(FAQ_CREDIT,))
    )
    assert r2.quick_checks == ()


def test_wp1_points_cite_only_this_runs_passages() -> None:
    points = [ReportedPoint(text=p.text[:100], passage_id=p.passage_id) for p in _WP1_ALL]
    points.append(ReportedPoint(text="$149 a year", passage_id=ARCHIVE_ID))
    result = build_knowledge_result(
        _outcome(
            _kb_task(),
            captured=(_kb_cap(_WP1_ALL),),
            passages=_WP1_ALL,
            report=KnowledgeReport(points=points, answered=True),
        )
    )
    assert result.status == "answered"
    assert len(result.points) == 3
    assert all(p.passage_id != ARCHIVE_ID for p in result.points)


def _wp4_task() -> SpecialistTask:
    return make_task(
        "scheduling",
        TaskIntent.RESCHEDULE,
        "I have a tech coming but something came up. Can I move it?",
        slice_=scheduling_slice(appointments=(APPT_WP4,), shown=(SLOT_44, SLOT_61)),
    )


def test_wp4_fee_bearing_becomes_change_request() -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel(
        [
            step(tool_call("c1", "move_visit", appointment_id=1, new_slot_id=44)),
            step(
                tool_call(
                    "c2",
                    "request_visit_change",
                    appointment_id=1,
                    change="move",
                    wanted_text="Monday morning",
                )
            ),
            step(report_call("r1", appointment_id=1, wanted_time="Monday morning", note="recorded")),
        ]
    )
    with turn_ctx(sink) as ctx:

        def handler(call: ToolCall):
            if call.name == "move_visit":
                return refused_dispatched(
                    call,
                    ctx,
                    ToolErrorCode.FEE_BEARING,
                    kind=ToolKind.MOVE,
                    captured=SchedulingCapture(refused=ToolErrorCode.FEE_BEARING),
                )
            return dispatched(
                call,
                ctx,
                kind=ToolKind.CHANGE_REQUEST,
                for_model={"recorded": True},
                captured=SchedulingCapture(change_request=DRAFT_WP4),
            )

        runner = make_runner(ScriptedGateway(model), model, ScriptedDispatcher(handler), sink)
        result = runner.run(
            _wp4_task(), scope(ctx, customer_id=CustomerId("MHC-57204"), shown=frozenset({44, 61})), ctx
        )
    assert isinstance(result, SchedulingResult)
    assert result.status == "staff_change_request"
    assert result.change_request == DRAFT_WP4
    assert result.write is None
    assert [t.outcome for t in result.tools] == ["refused", "ok"]
    assert result.tools[0].error == ToolErrorCode.FEE_BEARING


def test_wp4f_fee_free_move_written() -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel(
        [
            step(tool_call("c1", "move_visit", appointment_id=1, new_slot_id=44)),
            step(report_call("r1", appointment_id=1, wanted_time="", note="moved")),
        ]
    )
    with turn_ctx(sink) as ctx:

        def handler(call: ToolCall):
            return dispatched(
                call,
                ctx,
                kind=ToolKind.MOVE,
                for_model={"moved": True},
                captured=SchedulingCapture(write=WRITE_WP4F),
            )

        runner = make_runner(ScriptedGateway(model), model, ScriptedDispatcher(handler), sink)
        result = runner.run(
            _wp4_task(), scope(ctx, customer_id=CustomerId("MHC-57204"), shown=frozenset({44, 61})), ctx
        )
    assert isinstance(result, SchedulingResult)
    assert result.status == "written"
    assert result.write == WRITE_WP4F
    assert result.change_request is None


def test_runner_never_branches_on_kind() -> None:
    tree = ast.parse((_SRC / "specialists" / "runner.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert node.value not in {"knowledge", "account", "scheduling"}
        if isinstance(node, ast.Compare):
            for side in (node.left, *node.comparators):
                if isinstance(side, ast.Attribute) and side.attr == "kind":
                    assert not (isinstance(side.value, ast.Name) and side.value.id == "spec")


def _imports(path: Path) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative import"
            assert node.module is not None
            out.add(node.module)
        elif isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
    return out


def test_modules_import_only_allowed_layers() -> None:
    allowed = {
        "prompts/specialists.py": ("meridian.domain.", "meridian.privacy.redact"),
        "specialists/specs.py": (
            "meridian.domain.",
            "meridian.ports.models",
            "meridian.agent.prompts.specialists",
        ),
        "specialists/runner.py": (
            "meridian.domain.",
            "meridian.ports.",
            "meridian.policy.limits",
            "meridian.agent.gateway",
            "meridian.agent.tools.dispatch",
            "meridian.agent.specialists.specs",
        ),
    }
    forbidden = (
        "meridian.services",
        "meridian.web",
        "meridian.adapters",
        "anthropic",
        "httpx",
        "langgraph",
        "sqlite3",
    )
    for rel, prefixes in allowed.items():
        for module in _imports(_SRC / rel):
            assert not module.startswith(forbidden), (rel, module)
            if module.startswith("meridian"):
                assert module.startswith(prefixes), (rel, module)
