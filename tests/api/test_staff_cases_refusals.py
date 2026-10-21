"""AEA-45 refusals: unknown and malformed references, the 409 and 422 families, the 400s, the contact activity and the
flag rules. Mock-tested: the services are doubles that return the OpenAPI's own error examples."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from meridian.domain.common import ApiErrorCode
from meridian.domain.staff import DemoRole
from meridian.domain.views import CaseActionRejected
from meridian.services.staff import FlagRejected
from tests.api.staff_cases_support import (
    CaseNotFoundStandIn,
    as_role,
    call,
    case_rejected,
    error_example,
    request_example,
    staff_app,
    summary,
)
from tests.api.web_shell_support import assert_matches, error_body, make_client, make_settings

REP = DemoRole.REPRESENTATIVE
LONG_TEXT = "zq" * 1000 + "z"  # 2,001 letters
ACTIONS = "applyCaseAction"
ACTIVITIES = "recordContactActivity"


def _path(op: str, reference: str) -> str:
    suffix = {"getCase": "", ACTIONS: "/actions", ACTIVITIES: "/activities"}[op]
    return f"/api/staff/cases/{reference}{suffix}"


def test_case_not_found_and_malformed_reference(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-7: unknown cases are 404; a malformed reference is 404 on getCase and 400 on the writes; nothing is echoed."""
    h = staff_app(monkeypatch, make_settings(tmp_path))
    missing: dict[str, Any] = {"reference": "MHC-C-0099"}
    with make_client(h.app) as client:
        rep = as_role(h, REP)
        h.cases.detail_raises = CaseNotFoundStandIn("MHC-C-0099")
        r = call(client, "getCase", rep, path=_path("getCase", "MHC-C-0099"))
        assert error_body(r, 404, "CASE_NOT_FOUND")["error"]["details"] == missing
        assert_matches(r, "getCase")

        h.cases.apply_result = CaseActionRejected(code=ApiErrorCode.CASE_NOT_FOUND, details=missing)
        r = call(
            client, ACTIONS, rep, path=_path(ACTIONS, "MHC-C-0099"), body=request_example(ACTIONS, "CLAIM")
        )
        error_body(r, 404, "CASE_NOT_FOUND")
        assert_matches(r, ACTIONS)

        h.cases.activity_result = CaseActionRejected(code=ApiErrorCode.CASE_NOT_FOUND, details=missing)
        r = call(
            client,
            ACTIVITIES,
            rep,
            path=_path(ACTIVITIES, "MHC-C-0099"),
            body=request_example(ACTIVITIES, "CALL"),
        )
        error_body(r, 404, "CASE_NOT_FOUND")
        assert_matches(r, ACTIVITIES)

        h.flags.flag_result = FlagRejected(
            code="CASE_NOT_FOUND", field=None, constraint=None, details=missing
        )
        r = call(client, "createFlag", rep, body=request_example("createFlag", "ANSWER"))
        error_body(r, 404, "CASE_NOT_FOUND")
        assert_matches(r, "createFlag")

        before = len(h.cases.calls)
        r = call(client, "getCase", rep, path=_path("getCase", "MHC-C-7"))
        assert error_body(r, 404, "CASE_NOT_FOUND")["error"]["details"] is None
        assert_matches(r, "getCase")
        for op, example in ((ACTIONS, "CLAIM"), (ACTIVITIES, "CALL")):
            r = call(client, op, rep, path=_path(op, "MHC-C-7"), body=request_example(op, example))
            assert error_body(r, 400, "VALIDATION_ERROR")["error"]["field"] == "reference"
            assert_matches(r, op)
        assert len(h.cases.calls) == before

        flag_calls = len(h.flags.calls)
        r = call(client, "createFlag", rep, body={"case_ref": "MHC-C-7", "target": "answer"})
        assert error_body(r, 400, "VALIDATION_ERROR")["error"]["field"] == "case_ref"
        assert len(h.flags.calls) == flag_calls

        h.cases.detail_raises = KeyError("x")
        r = call(client, "getCase", rep, path=_path("getCase", "MHC-C-0099"))
        assert r.status_code == 500


def test_real_case_not_found_maps_to_404(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-7 seam: AEA-29's real CaseNotFound is a 404. Skips until services/cases.py is merged."""
    mod = pytest.importorskip("meridian.services.cases")
    exc = getattr(mod, "CaseNotFound", None)
    if exc is None:
        pytest.skip("AEA-29 CaseNotFound not merged")
    h = staff_app(monkeypatch, make_settings(tmp_path))
    h.cases.detail_raises = exc("MHC-C-0099")
    with make_client(h.app) as client:
        r = call(client, "getCase", as_role(h, REP), path=_path("getCase", "MHC-C-0099"))
    error_body(r, 404, "CASE_NOT_FOUND")


@pytest.mark.parametrize("name", ["VERSION_CONFLICT", "CASE_ALREADY_CLAIMED", "NOT_ALLOWED_IN_STATE"])
def test_case_action_409s(name: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-8: each 409 carries the service's field, constraint and details unchanged."""
    h = staff_app(monkeypatch, make_settings(tmp_path))
    h.cases.apply_result = case_rejected(ACTIONS, "409", name)
    with make_client(h.app) as client:
        r = call(client, ACTIONS, as_role(h, REP), body=request_example(ACTIONS, "CLAIM"))
    assert r.status_code == 409
    assert r.json()["error"] == error_example(ACTIONS, "409", name)
    assert_matches(r, ACTIONS)


@pytest.mark.parametrize("name", ["REASON_REQUIRED", "WAKE_UP_REQUIRED", "OUTCOME_REQUIRED"])
def test_named_422_vs_400(name: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-9: the named refusals stay 422; a body missing expected_version is a 400 and never reaches apply."""
    h = staff_app(monkeypatch, make_settings(tmp_path))
    h.cases.apply_result = case_rejected(ACTIONS, "422", name)
    with make_client(h.app) as client:
        rep = as_role(h, REP)
        r = call(client, ACTIONS, rep, body=request_example(ACTIONS, "CLAIM"))
        expected = error_example(ACTIONS, "422", name)
        assert r.status_code == 422
        assert (r.json()["error"]["field"], r.json()["error"]["constraint"]) == (
            expected["field"],
            expected["constraint"],
        )
        assert_matches(r, ACTIONS)
        calls = len(h.cases.calls_of("apply"))
        r = call(client, ACTIONS, rep, body={"action": "claim"})
        assert error_body(r, 400, "VALIDATION_ERROR")["error"]["field"] == "expected_version"
        assert_matches(r, ACTIONS)
        assert len(h.cases.calls_of("apply")) == calls


def test_contact_activity(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-10: 201 with the label unchanged; the two 409s keep their codes."""
    h = staff_app(monkeypatch, make_settings(tmp_path))
    with make_client(h.app) as client:
        rep = as_role(h, REP)
        r = call(client, ACTIVITIES, rep, body=request_example(ACTIVITIES, "CALL"))
        assert r.status_code == 201, r.text
        assert r.json()["activity"]["label"] == "Demo: recorded, not sent"
        assert r.json()["activity"] == h.cases.activity_result.activity.model_dump(mode="json")
        assert_matches(r, ACTIVITIES)
        for name in ("NOT_ALLOWED_IN_STATE", "VERSION_CONFLICT"):
            h.cases.activity_result = case_rejected(ACTIVITIES, "409", name)
            r = call(client, ACTIVITIES, rep, body=request_example(ACTIVITIES, "CALL"))
            error_body(r, 409, name)
            assert_matches(r, ACTIVITIES)
        h.cases.apply_result = summary()


def test_flags(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-11: blank text becomes null, 2,001 characters is a 400 that echoes nothing, rejections map to their status."""
    h = staff_app(monkeypatch, make_settings(tmp_path))
    answer = request_example("createFlag", "ANSWER")
    with make_client(h.app) as client:
        rep = as_role(h, REP)
        sup = as_role(h, DemoRole.SUPERVISOR)
        for reason in ({}, {"reason": "   "}):
            body = {k: v for k, v in answer.items() if k != "reason"} | reason
            r = call(client, "createFlag", rep, body=body)
            assert r.status_code == 201, r.text
            assert r.json()["reason"] is None
            assert h.flags.calls[-1].args["flag"].reason is None
            assert_matches(r, "createFlag")
        for field in ("note", "reason"):
            r = call(client, "createFlag", rep, body={**answer, field: LONG_TEXT})
            body = error_body(r, 400, "VALIDATION_ERROR")
            assert body["error"]["field"] == field
            assert body["error"]["constraint"] == "at most 2000 characters"
            assert LONG_TEXT not in r.text
            assert_matches(r, "createFlag")
        r = call(client, "reviewFlag", sup, body={"status": "reviewed", "note": LONG_TEXT})
        assert error_body(r, 400, "VALIDATION_ERROR")["error"]["field"] == "note"
        assert LONG_TEXT not in r.text

        h.flags.flag_result = FlagRejected(
            code="VALIDATION_ERROR", field="message_id", constraint="not a message of this case", details=None
        )
        r = call(client, "createFlag", rep, body=answer)
        body = error_body(r, 400, "VALIDATION_ERROR")
        assert (body["error"]["field"], body["error"]["constraint"]) == (
            "message_id",
            "not a message of this case",
        )
        assert_matches(r, "createFlag")

        r = call(client, "reviewFlag", sup, body={"status": "new"})
        assert error_body(r, 400, "VALIDATION_ERROR")["error"]["field"] == "status"

        h.flags.review_result = FlagRejected(
            code="FLAG_NOT_FOUND", field=None, constraint=None, details={"flag_id": "flg-99"}
        )
        r = call(client, "reviewFlag", sup, body=request_example("reviewFlag", "REVIEW"))
        error_body(r, 404, "FLAG_NOT_FOUND")
        assert_matches(r, "reviewFlag")

        r = call(client, "listFlags", rep)
        assert [f["flag_id"] for f in r.json()["flags"]] == [f.flag_id for f in h.flags.list_result]
