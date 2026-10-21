"""AEA-28 AC-15, AC-16, PA-4, PA-5, PA-7: the scheduling executors over the real service and a temp working copy."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from contextlib import closing

import pytest
from pydantic import JsonValue

from meridian.agent.tools.dispatch import DispatchedCall, ToolDispatcher, ToolRegistry
from meridian.agent.tools.scheduling import (
    BookVisitArgs,
    CancelVisitArgs,
    FindWindowsArgs,
    MoveVisitArgs,
    RequestVisitChangeArgs,
    scheduling_tools,
    tool_error_for,
)
from meridian.domain.common import CustomerId, ToolErrorCode, ToolKind
from meridian.domain.specialists import SchedulingCapture
from meridian.domain.tools import ToolCallScope, ToolError, ToolResult
from meridian.policy.booking import fee_note
from meridian.ports.models import ToolCall
from meridian.services.scheduling import OutOfArea, Refused, SlotTaken
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.scheduling_helpers import (
    LINDA,
    MHC_57204,
    appt_row,
    count,
    issued_sha256,
    raw,
    scope,
    service,
    thread,
    turn,
)

ALL_KINDS = frozenset(
    {ToolKind.SLOT_SEARCH, ToolKind.BOOK, ToolKind.MOVE, ToolKind.CANCEL, ToolKind.CHANGE_REQUEST}
)
CODES = ["fee_bearing", "not_shown", "outside_service_area", "wrong_service_type", "booking_cap", "not_owned"]


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


@pytest.fixture(scope="module", autouse=True)
def issued_unchanged() -> Iterator[None]:
    before = issued_sha256()
    yield
    assert issued_sha256() == before


def _tools(store: TempStore) -> dict[str, object]:
    return {d.name: d for d in scheduling_tools(service(store))}


def _run(store: TempStore, name: str, args: object, sc: ToolCallScope) -> ToolResult:
    d = {t.name: t for t in scheduling_tools(service(store))}[name]
    return d.executor(args, sc)  # type: ignore[arg-type]


def _lookups(store: TempStore, sc: ToolCallScope) -> int:
    return count(store, "SELECT COUNT(*) FROM lookup_log WHERE thread_id = ?", (str(sc.ids.thread_id),))


def test_tool_defs_lookup_rule_and_error_codes(store: TempStore) -> None:
    defs = scheduling_tools(service(store))
    ToolRegistry(defs)
    assert {d.kind for d in defs} == ALL_KINDS
    assert len({d.name for d in defs}) == 5
    for d in defs:
        assert d.effect == ("read" if d.kind is ToolKind.SLOT_SEARCH else "write")
        assert d.requires_verified is (d.kind is not ToolKind.SLOT_SEARCH)
        assert not any("customer" in f for f in d.args_model.model_fields)
        assert len(d.description) > 80
        assert any(o.name in d.description for o in defs if o is not d)

    sc = scope(store, thread(1), turn(1), LINDA)
    r = _run(store, "find_windows", FindWindowsArgs(service_type="hvac_repair"), sc)
    assert r.ok and r.lookup_written is False and _lookups(store, sc) == 0

    cases: list[tuple[str, object, ToolCallScope]] = [
        (
            "book_visit",
            BookVisitArgs(slot_id=56, issue="AC not cooling"),
            scope(store, thread(2), turn(1), LINDA, {56}),
        ),
        (
            "move_visit",
            MoveVisitArgs(appointment_id=94, new_slot_id=53),
            scope(store, thread(3), turn(1), MHC_57204, {53}),
        ),
        ("cancel_visit", CancelVisitArgs(appointment_id=94), scope(store, thread(4), turn(1), MHC_57204)),
        (
            "request_visit_change",
            RequestVisitChangeArgs(appointment_id=1, change="move"),
            scope(store, thread(5), turn(1), MHC_57204, {44}),
        ),
    ]
    for name, args, s in cases:
        res = _run(store, name, args, s)
        assert res.ok, name
        assert res.lookup_written is True
        assert _lookups(store, s) == 1

    for c in CODES:
        e = tool_error_for(Refused(code=c))  # type: ignore[arg-type]
        assert e.code == ToolErrorCode(c) and e.code.value == c
    assert tool_error_for(SlotTaken(slot_id=56, alternatives=())).code == ToolErrorCode.SLOT_TAKEN
    assert tool_error_for(OutOfArea(reason="not_served")).code == ToolErrorCode.OUTSIDE_SERVICE_AREA
    assert tool_error_for(OutOfArea(reason="unknown_location")).code == ToolErrorCode.OUTSIDE_SERVICE_AREA


def _contact(store: TempStore, cid: str) -> list[str]:
    with closing(raw(store)) as c:
        row = c.execute("SELECT phone, email FROM customers WHERE customer_id = ?", (cid,)).fetchone()
    return [str(v) for v in row if v]


def _text(r: ToolResult) -> str:
    fm = r.for_model.model_dump(mode="json") if isinstance(r.for_model, ToolError) else r.for_model
    return json.dumps(fm) + "\n" + r.lookup.result_seen


def test_for_model_excludes_issue_text_and_contact(
    store: TempStore, caplog: pytest.LogCaptureFixture
) -> None:
    issue = "ZEBRA-ISSUE-7731 synthetic"
    secrets = [issue, *_contact(store, "MHC-10001"), *_contact(store, "MHC-57204")]
    assert len(secrets) > 1
    results: list[ToolResult] = []
    with caplog.at_level(logging.DEBUG):
        results.append(
            _run(
                store,
                "book_visit",
                BookVisitArgs(slot_id=56, issue=issue),
                scope(store, thread(1), turn(1), LINDA, {56}),
            )
        )
        results.append(
            _run(
                store,
                "find_windows",
                FindWindowsArgs(service_type="hvac_repair"),
                scope(store, thread(1), turn(2), LINDA),
            )
        )
        results.append(
            _run(
                store,
                "move_visit",
                MoveVisitArgs(appointment_id=160, new_slot_id=42),
                scope(store, thread(1), turn(3), LINDA, {42}),
            )
        )
        results.append(
            _run(
                store,
                "cancel_visit",
                CancelVisitArgs(appointment_id=160),
                scope(store, thread(1), turn(4), LINDA),
            )
        )
        results.append(
            _run(
                store,
                "request_visit_change",
                RequestVisitChangeArgs(appointment_id=1, change="move", wanted_text="Monday morning"),
                scope(store, thread(2), turn(1), MHC_57204, {44}),
            )
        )
    assert results[0].ok
    for r in results:
        text = _text(r)
        assert "Monday morning" not in text
        assert not any(s in text for s in secrets)
    assert "Monday morning" not in caplog.text
    assert not any(s in caplog.text for s in secrets)


def test_slot_search_zone_and_tier_source(store: TempStore) -> None:
    r = _run(
        store,
        "find_windows",
        FindWindowsArgs(service_type="hvac_repair", zone_hint="Kyle"),
        scope(store, thread(1), turn(1), LINDA),
    )
    assert isinstance(r.for_model, dict)
    assert r.for_model["zone"] == "north"
    assert r.for_model["fee_line"] == fee_note("hvac_repair", "standard").line
    r = _run(
        store,
        "find_windows",
        FindWindowsArgs(service_type="hvac_repair"),
        scope(store, thread(2), turn(1), None),
    )
    assert isinstance(r.for_model, ToolError) and r.for_model.code == ToolErrorCode.BAD_ARGUMENTS
    r = _run(
        store,
        "find_windows",
        FindWindowsArgs(service_type="hvac_repair", zone_hint="78640"),
        scope(store, thread(3), turn(1), None),
    )
    assert isinstance(r.for_model, dict)
    assert r.for_model["zone"] == "south"
    assert r.for_model["fee_line"] == fee_note("hvac_repair", "none").line
    r = _run(
        store,
        "find_windows",
        FindWindowsArgs(service_type="hvac_repair", zone_hint="Lakeway"),
        scope(store, thread(4), turn(1), None),
    )
    assert isinstance(r.for_model, ToolError) and r.for_model.code == ToolErrorCode.OUTSIDE_SERVICE_AREA
    assert isinstance(r.captured, SchedulingCapture)
    assert r.captured.refused == ToolErrorCode.OUTSIDE_SERVICE_AREA


def test_change_request_fee_free_not_allowed(store: TempStore) -> None:
    sc = scope(store, thread(1), turn(1), MHC_57204)
    r = _run(store, "request_visit_change", RequestVisitChangeArgs(appointment_id=94, change="move"), sc)
    assert isinstance(r.for_model, ToolError) and r.for_model.code == ToolErrorCode.NOT_ALLOWED
    assert isinstance(r.captured, SchedulingCapture)
    assert r.captured.refused == ToolErrorCode.NOT_ALLOWED
    assert r.lookup_written is False
    assert count(store, "SELECT COUNT(*) FROM actions WHERE thread_id = ?", (str(sc.ids.thread_id),)) == 0


def test_dispatch_leaves_one_lookup_row_per_call(store: TempStore) -> None:
    dispatcher = ToolDispatcher(ToolRegistry(scheduling_tools(service(store))), store.uow)

    def go(
        n: int, who: CustomerId | None, shown: set[int], name: str, args: dict[str, JsonValue]
    ) -> tuple[ToolCallScope, DispatchedCall]:
        sc = scope(store, thread(n), turn(1), who, shown)
        (d,) = dispatcher.dispatch([ToolCall(id="c1", name=name, args=args)], kinds=ALL_KINDS, scope=sc)
        return sc, d

    sc, d = go(1, LINDA, {56}, "book_visit", {"slot_id": 56, "issue": "AC not cooling"})
    assert d.record.outcome == "ok" and d.record.lookup_id is None
    assert _lookups(store, sc) == 1
    assert (
        count(
            store,
            "SELECT COUNT(*) FROM lookup_log WHERE thread_id = ? AND tool = 'book_visit'",
            (str(sc.ids.thread_id),),
        )
        == 1
    )

    before = appt_row(store, 1)
    sc, d = go(2, MHC_57204, {44}, "move_visit", {"appointment_id": 1, "new_slot_id": 44})
    assert d.record.outcome == "refused" and d.record.error == ToolErrorCode.FEE_BEARING
    assert d.record.lookup_id is not None
    assert _lookups(store, sc) == 1
    assert appt_row(store, 1) == before

    appts = count(store, "SELECT COUNT(*) FROM appointments")
    sc, d = go(3, None, {56}, "book_visit", {"slot_id": 56, "issue": "AC not cooling"})
    assert d.record.error == ToolErrorCode.NOT_VERIFIED
    assert _lookups(store, sc) == 1
    assert count(store, "SELECT COUNT(*) FROM appointments") == appts

    sc, d = go(4, None, set(), "find_windows", {"service_type": "hvac_repair", "zone_hint": "Round Rock"})
    assert d.record.outcome == "ok"
    assert _lookups(store, sc) == 1
    assert (
        count(
            store,
            "SELECT COUNT(*) FROM lookup_log WHERE thread_id = ? AND tool = 'find_windows'",
            (str(sc.ids.thread_id),),
        )
        == 1
    )
