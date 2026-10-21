"""AEA-45 staff case routes through AEA-23's real app and middleware with service doubles (mock-tested).

AC-1 (each 2xx example), AC-2 (result lines), AC-6, AC-18 (pass-through), AC-21 (skips until the OpenAPI amendment) and
the WP-2 worked pair. Each docstring names the failure it guards."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from meridian.domain.staff import DemoRole
from meridian.domain.views import ActivityResult, CaseDetail, CaseSummaryView, OversightView, QueueView
from meridian.services.staff import FlagRecord
from tests.api.openapi_check import assert_response_matches, load_document
from tests.api.staff_cases_support import (
    as_attrs,
    as_role,
    call,
    case_detail,
    case_rejected,
    flag_record,
    request_example,
    response_example,
    staff_app,
    summary,
)
from tests.api.web_shell_support import assert_matches, make_client, make_settings, rand_word

ACTION_PAIRS = [
    ("CLAIMED", "CLAIM", DemoRole.REPRESENTATIVE),
    ("WAITING", "WAIT", DemoRole.REPRESENTATIVE),
    ("RESOLVED", "RESOLVE", DemoRole.REPRESENTATIVE),
    ("ASSIGNED", "ASSIGN", DemoRole.SUPERVISOR),
    ("PRIORITY_CHANGED", "CHANGE_PRIORITY", DemoRole.SUPERVISOR),
]


def _app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Any:
    return staff_app(monkeypatch, make_settings(tmp_path))


@pytest.mark.parametrize("name", ["SEEDED", "STAFFED_WITH_WAITING", "ALL_CAUGHT_UP", "BRIEF_BEING_WRITTEN"])
def test_getQueue_matches_openapi(name: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-1: the queue body is the service's view, validates against the OpenAPI and equals the example."""
    h = _app(monkeypatch, tmp_path)
    example = response_example("getQueue", name)
    h.cases.queue_result = QueueView.model_validate(example)
    with make_client(h.app) as client:
        r = call(client, "getQueue", as_role(h, DemoRole.REPRESENTATIVE))
    assert r.status_code == 200, r.text
    assert_matches(r, "getQueue")
    assert r.json() == example


@pytest.mark.parametrize(
    "name",
    [
        "DEFAULT",
        "BRIEF_BEING_WRITTEN",
        "TRIMMED_STOP",
        "SAFETY_CASE",
        "LIVE_JOINED",
        "WAITING",
        "FEE_BEARING_CHANGE",
    ],
)
def test_getCase_matches_openapi(name: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-1: every getCase example comes back unchanged."""
    h = _app(monkeypatch, tmp_path)
    example = response_example("getCase", name)
    h.cases.detail_result = CaseDetail.model_validate(example)
    with make_client(h.app) as client:
        r = call(client, "getCase", as_role(h, DemoRole.REPRESENTATIVE))
    assert r.status_code == 200, r.text
    assert_matches(r, "getCase")
    assert r.json() == example


@pytest.mark.parametrize(("name", "request_name", "role"), ACTION_PAIRS)
def test_applyCaseAction_matches_openapi(
    name: str, request_name: str, role: DemoRole, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC-1 and AC-2: the full body, result_line included, equals the example (five sourced lines)."""
    h = _app(monkeypatch, tmp_path)
    example = response_example("applyCaseAction", name)
    h.cases.apply_result = summary(name)
    body = request_example("applyCaseAction", request_name)
    with make_client(h.app) as client:
        r = call(client, "applyCaseAction", as_role(h, role), body=body)
    assert r.status_code == 200, r.text
    assert_matches(r, "applyCaseAction")
    assert r.json() == example


@pytest.mark.parametrize("name", ["CALL_REACHED", "EMAIL_LEFT_MESSAGE"])
def test_recordContactActivity_matches_openapi(
    name: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC-1: 201 with the activity and the case view unchanged."""
    h = _app(monkeypatch, tmp_path)
    example = response_example("recordContactActivity", name, "201")
    h.cases.activity_result = ActivityResult.model_validate(example)
    with make_client(h.app) as client:
        r = call(
            client,
            "recordContactActivity",
            as_role(h, DemoRole.REPRESENTATIVE),
            body=request_example("recordContactActivity", "CALL"),
        )
    assert r.status_code == 201, r.text
    assert_matches(r, "recordContactActivity")
    assert r.json() == example


def test_createFlag_matches_openapi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-1: the ANSWER flag comes back as the example."""
    h = _app(monkeypatch, tmp_path)
    example = response_example("createFlag", "ANSWER", "201")
    h.flags.flag_result = flag_record()
    with make_client(h.app) as client:
        r = call(
            client,
            "createFlag",
            as_role(h, DemoRole.REPRESENTATIVE),
            body=request_example("createFlag", "ANSWER"),
        )
    assert r.status_code == 201, r.text
    assert_matches(r, "createFlag")
    assert r.json() == example


@pytest.mark.parametrize("name", ["THREE", "EMPTY"])
def test_listFlags_matches_openapi(name: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-1: as_of is the one demo-clock reading; the flags keep the service's order."""
    h = _app(monkeypatch, tmp_path)
    example = response_example("listFlags", name)
    h.demo.now = datetime.fromisoformat(example["as_of"])
    h.flags.list_result = tuple(FlagRecord.model_validate(f) for f in example["flags"])
    with make_client(h.app) as client:
        r = call(client, "listFlags", as_role(h, DemoRole.OWNER))
    assert r.status_code == 200, r.text
    assert_matches(r, "listFlags")
    assert r.json() == example


def test_reviewFlag_matches_openapi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-1: the supervisor's review answers the REVIEWED example."""
    h = _app(monkeypatch, tmp_path)
    example = response_example("reviewFlag", "REVIEWED")
    with make_client(h.app) as client:
        r = call(
            client,
            "reviewFlag",
            as_role(h, DemoRole.SUPERVISOR),
            body=request_example("reviewFlag", "REVIEW"),
        )
    assert r.status_code == 200, r.text
    assert_matches(r, "reviewFlag")
    assert r.json() == example


@pytest.mark.parametrize("name", ["SEEDED", "AFTER_ADVANCE", "SHIFT_ENDED_WITH_WAITING", "NOTHING_URGENT"])
def test_getOversight_matches_openapi(name: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-1: every oversight example comes back unchanged."""
    h = _app(monkeypatch, tmp_path)
    example = response_example("getOversight", name)
    h.cases.oversight_result = OversightView.model_validate(example)
    with make_client(h.app) as client:
        r = call(client, "getOversight", as_role(h, DemoRole.SUPERVISOR))
    assert r.status_code == 200, r.text
    assert_matches(r, "getOversight")
    assert r.json() == example


RESULT_LINE_CASES = [
    ("claim", DemoRole.REPRESENTATIVE, {}, {}, "Claimed · Riley (demo)"),
    (
        "wait",
        DemoRole.REPRESENTATIVE,
        {"lifecycle": "waiting", "wake_up_at": "2026-10-19T09:00:00-05:00"},
        {"wake_up_at": "2026-10-19T09:00:00-05:00", "reason": "zqwait"},
        "Waiting until Mon Oct 19 · 9:00 am",
    ),
    (
        "resolve",
        DemoRole.REPRESENTATIVE,
        {"lifecycle": "resolved"},
        {"outcome": "zqdone"},
        "MHC-C-0007 resolved.",
    ),
    (
        "assign",
        DemoRole.SUPERVISOR,
        {"owner": "Riley"},
        {"assignee": "riley", "reason": "zqassign"},
        "Assigned to Riley (demo).",
    ),
    (
        "change_priority",
        DemoRole.SUPERVISOR,
        {"priority": {"level": "P2", "word": "Time-sensitive"}},
        {"priority": "P2", "reason": "zqprio"},
        "Priority is now P2 · Time-sensitive.",
    ),
    (
        "release",
        DemoRole.REPRESENTATIVE,
        {"lifecycle": "unassigned", "owner": None},
        {"reason": "zqrelease"},
        "Released back to Unassigned.",
    ),
    ("start", DemoRole.REPRESENTATIVE, {"lifecycle": "in_progress"}, {}, "In progress · Riley (demo)"),
    (
        "close_unresolved",
        DemoRole.REPRESENTATIVE,
        {"lifecycle": "closed_unresolved"},
        {"reason": "zqclose"},
        "MHC-C-0007 closed unresolved.",
    ),
]


@pytest.mark.parametrize(("action", "role", "changes", "extra", "expected"), RESULT_LINE_CASES)
def test_result_lines(
    action: str,
    role: DemoRole,
    changes: dict[str, Any],
    extra: dict[str, Any],
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """AC-2: one composed sentence per action (staff.md section 6)."""
    h = _app(monkeypatch, tmp_path)
    h.cases.apply_result = summary("CLAIMED", **changes)
    with make_client(h.app) as client:
        r = call(
            client,
            "applyCaseAction",
            as_role(h, role),
            body={"action": action, "expected_version": 4, **extra},
        )
    assert r.status_code == 200, r.text
    assert r.json()["result_line"] == expected


@pytest.mark.parametrize("role", [DemoRole.REPRESENTATIVE, DemoRole.SUPERVISOR, DemoRole.OWNER])
@pytest.mark.parametrize(
    "name",
    [
        "DEFAULT",
        "BRIEF_BEING_WRITTEN",
        "TRIMMED_STOP",
        "SAFETY_CASE",
        "LIVE_JOINED",
        "WAITING",
        "FEE_BEARING_CHANGE",
    ],
)
def test_case_detail_passthrough(
    name: str, role: DemoRole, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC-6: the service's CaseDetail is the body, whichever staff role asks; never a 403 to a staff role."""
    h = _app(monkeypatch, tmp_path)
    detail = case_detail(name)
    if role is DemoRole.OWNER:
        detail = detail.model_copy(update={"case": detail.case.model_copy(update={"allowed_actions": ()})})
    h.cases.detail_result = detail
    with make_client(h.app) as client:
        r = call(client, "getCase", as_role(h, role))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == detail.model_dump(mode="json")
    assert [h_["number"] for h_ in body["brief"]["headings"]] == list(range(1, 9))
    assert [h_["title"] for h_ in body["brief"]["headings"]] == [h_.title for h_ in detail.brief.headings]
    if any(s.audience == "staff_only" for s in detail.sources):
        assert "staff_only" in {s["audience"] for s in body["sources"]}
    if role is DemoRole.OWNER:
        assert body["case"]["allowed_actions"] == []


def test_views_pass_through_unchanged(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-18 (R-W-13): distinctive display strings and allowed_actions reach the wire exactly as the service made them."""
    h = _app(monkeypatch, tmp_path)
    words = {role: rand_word() for role in DemoRole}
    actions = {
        DemoRole.REPRESENTATIVE: ["claim", "flag"],
        DemoRole.SUPERVISOR: ["claim", "assign", "change_priority", "flag"],
        DemoRole.OWNER: [],
    }
    priority_word = {
        DemoRole.REPRESENTATIVE: "Danger",
        DemoRole.SUPERVISOR: "Standard",
        DemoRole.OWNER: "Routine",
    }

    def _case(d: dict[str, Any], role: DemoRole) -> None:
        d["reason"] = words[role]
        d["due_label"] = words[role] + "due"
        d["priority"] = {"level": d["priority"]["level"], "word": priority_word[role]}
        d["allowed_actions"] = actions[role]

    for role in (DemoRole.REPRESENTATIVE, DemoRole.SUPERVISOR):
        queue = response_example("getQueue", "STAFFED_WITH_WAITING")
        rows = [*queue["live"], *queue["needs_my_action"]]
        for row in rows:
            row["reason"] = words[role]
            row["due_label"] = words[role] + "due"
            row["age_label"] = words[role] + "age"
            row["follow_up_short"] = words[role] + "follow"
            row["queued_at"] = "2026-10-16T09:31:00-05:00"
            row["priority"] = {"level": row["priority"]["level"], "word": priority_word[role]}
        h.cases.queue_result = QueueView.model_validate(queue)
        claimed = response_example("applyCaseAction", "CLAIMED")["case"]
        _case(claimed, role)
        h.cases.apply_result = CaseSummaryView.model_validate(claimed)
        with make_client(h.app) as client:
            headers = as_role(h, role)
            rq = call(client, "getQueue", headers)
            ra = call(client, "applyCaseAction", headers, body={"action": "claim", "expected_version": 3})
        assert rq.json() == queue
        assert ra.json()["case"] == claimed
    for role in DemoRole:
        if role is DemoRole.CUSTOMER:
            continue
        detail = response_example("getCase", "DEFAULT")
        _case(detail["case"], role)
        detail["identity"]["line"] = words[role] + "id"
        for heading in detail["brief"]["headings"]:
            for item in heading["items"]:
                item["source_ids"] = [s + "x" for s in item["source_ids"]]
        for source in detail["sources"]:
            source["source_id"] = source["source_id"] + "x"
            source["version_label"] = words[role] + "ver"
        h.cases.detail_result = CaseDetail.model_validate(detail)
        with make_client(h.app) as client:
            r = call(client, "getCase", as_role(h, role))
        assert r.json() == detail


def test_case_detail_carries_last_event_id(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-21 (D-5): events.last_event_id passes through. Skips until the UX session amends the OpenAPI."""
    props = load_document()["components"]["schemas"]["CaseDetail"]["properties"]
    if "events" not in props:
        pytest.skip(
            "blocked-on UX session: OpenAPI amendment CaseDetail.events.last_event_id (Decision 2 option A, D-5)"
        )
    h = _app(monkeypatch, tmp_path)
    h.cases.detail_result = as_attrs(
        {**response_example("getCase", "DEFAULT"), "events": {"last_event_id": 41}}
    )
    with make_client(h.app) as client:
        r = call(client, "getCase", as_role(h, DemoRole.REPRESENTATIVE))
    assert r.status_code == 200, r.text
    assert_response_matches(r, "getCase")
    assert r.json()["events"]["last_event_id"] == 41


def test_wp2_example_pair_mhc_c_0007(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """WP-2: the representative claims MHC-C-0007; the refusals the ticket names answer with their own details."""
    h = _app(monkeypatch, tmp_path)
    with make_client(h.app) as client:
        rep = as_role(h, DemoRole.REPRESENTATIVE)
        h.cases.apply_result = summary("CLAIMED")
        r = call(client, "applyCaseAction", rep, body={"action": "claim", "expected_version": 3})
        assert r.status_code == 200, r.text
        assert_matches(r, "applyCaseAction")
        body = r.json()
        assert body["case"]["lifecycle"] == "claimed"
        assert body["case"]["owner"] == "Riley"
        assert body["case"]["version"] == 4
        assert body["result_line"] == "Claimed · Riley (demo)"

        h.cases.apply_result = case_rejected("applyCaseAction", "409", "CASE_ALREADY_CLAIMED")
        r = call(client, "applyCaseAction", rep, body={"action": "claim", "expected_version": 4})
        assert r.status_code == 409
        assert_matches(r, "applyCaseAction")
        assert r.json()["error"]["details"]["claimed_by"] == "Demo supervisor"

        h.cases.apply_result = case_rejected("applyCaseAction", "409", "VERSION_CONFLICT")
        r = call(client, "applyCaseAction", rep, body={"action": "claim", "expected_version": 3})
        assert r.status_code == 409
        assert_matches(r, "applyCaseAction")
        details = r.json()["error"]["details"]
        assert {"changed_by", "changed_at"} <= set(details)
        assert details["current_version"] == 4

        h.cases.apply_result = case_rejected("applyCaseAction", "422", "REASON_REQUIRED")
        r = call(client, "applyCaseAction", rep, body={"action": "release", "expected_version": 4})
        assert r.status_code == 422
        assert_matches(r, "applyCaseAction")
        assert r.json()["error"]["field"] == "reason"
        assert r.json()["error"]["constraint"] == "required for release, assign and change_priority"

        applied = len(h.cases.calls_of("apply"))
        r = call(
            client,
            "applyCaseAction",
            rep,
            body={"action": "assign", "assignee": "riley", "reason": rand_word(), "expected_version": 4},
        )
        assert r.status_code == 403
        assert_matches(r, "applyCaseAction")
        assert r.json()["error"]["details"]["needs"] == ["supervisor"]
        assert len(h.cases.calls_of("apply")) == applied
