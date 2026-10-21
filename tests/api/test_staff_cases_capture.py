"""AEA-45 capture: the demo clock is the only clock, queue and oversight carry no contact value, staff free text is never
logged, and every call leaves one `request` record through the real container (WF-4)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from meridian.domain.staff import DemoRole
from tests.api.openapi_check import load_contract
from tests.api.staff_cases_support import (
    FIXED_NOW,
    FakeCaseService,
    FakeDemoService,
    FakeFlagService,
    as_attrs,
    as_role,
    call,
    default_body,
    request_example,
    response_example,
    seeded_contact,
    staff_app,
    staff_full_app,
    summary,
)
from tests.api.web_shell_support import (
    FakeSessionStore,
    app_log_text,
    captured_log,
    cookie_header,
    make_client,
    make_settings,
    rand_word,
    records_of,
)

REP = DemoRole.REPRESENTATIVE


def test_now_is_demo_clock(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-12: each case route takes exactly one demo-clock reading and hands it to the service as `now`."""
    h = staff_app(monkeypatch, make_settings(tmp_path), demo=FakeDemoService(FIXED_NOW))
    with make_client(h.app) as client:
        rep = as_role(h, REP)
        sup = as_role(h, DemoRole.SUPERVISOR)
        reads = h.demo.reads
        for op, headers in (
            ("getQueue", rep),
            ("getCase", rep),
            ("applyCaseAction", rep),
            ("recordContactActivity", rep),
            ("getOversight", sup),
        ):
            r = call(client, op, headers, body=default_body(op))
            assert r.status_code in (200, 201), r.text
            assert h.demo.reads == reads + 1, op
            reads = h.demo.reads
        assert [c.args["now"] for c in h.cases.calls] == [FIXED_NOW] * 5
        r = call(client, "listFlags", rep)
        assert h.demo.reads == reads + 1
        assert r.json()["as_of"] == "2026-10-19T07:00:00-05:00"
        reads = h.demo.reads
        call(client, "createFlag", rep, body=default_body("createFlag"))
        call(client, "reviewFlag", sup, body=default_body("reviewFlag"))
        assert h.demo.reads == reads


def _with_contact(rows: list[Any], email: str, address: str) -> None:
    for row in rows:
        row.contact_email = email
        row.service_address = address


def test_queue_and_oversight_carry_no_contact(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-13: undocumented attributes on the service's rows (a contact email, a service address) never reach the wire."""
    email, address = seeded_contact()
    h = staff_app(monkeypatch, make_settings(tmp_path))
    queue = as_attrs(response_example("getQueue", "SEEDED"))
    rows = [*queue.live, *queue.needs_my_action]
    oversight = as_attrs(response_example("getOversight", "SEEDED"))
    lanes = vars(oversight.lanes).values()
    rows += [row for lane in lanes for row in lane.rows]
    assert rows, "the examples must hold rows for this check to mean anything"
    _with_contact(rows, email, address)
    assert all(row.contact_email == email and row.service_address == address for row in rows)
    h.cases.queue_result = queue
    h.cases.oversight_result = oversight
    with make_client(h.app) as client:
        rq = call(client, "getQueue", as_role(h, REP))
        ro = call(client, "getOversight", as_role(h, DemoRole.SUPERVISOR))
    assert rq.status_code == 200 and ro.status_code == 200
    for response in (rq, ro):
        assert email not in response.text
        assert address not in response.text


def test_staff_text_never_logged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-14: free text reaches the service but never a log line, a request record or a 400 body."""
    h = staff_app(monkeypatch, make_settings(tmp_path))
    release, outcome, note, flag_note, flag_reason = (rand_word() for _ in range(5))
    caplog.set_level(logging.DEBUG)
    with captured_log() as stream, make_client(h.app) as client:
        rep = as_role(h, REP)
        h.cases.apply_result = summary()
        call(
            client,
            "applyCaseAction",
            rep,
            body={"action": "release", "expected_version": 4, "reason": release},
        )
        call(
            client,
            "applyCaseAction",
            rep,
            body={"action": "resolve", "expected_version": 4, "outcome": outcome},
        )
        body = request_example("recordContactActivity", "CALL") | {"note": note}
        call(client, "recordContactActivity", rep, body=body)
        flag = request_example("createFlag", "ANSWER") | {"note": flag_note, "reason": flag_reason}
        call(client, "createFlag", rep, body=flag)
        too_long = call(client, "createFlag", rep, body=flag | {"note": "zq" * 1001})
    applied = [c.args["action"] for c in h.cases.calls_of("apply")]
    assert (applied[0].reason, applied[1].outcome) == (release, outcome)
    assert h.cases.calls_of("record_activity")[0].args["activity"].note == note
    created = h.flags.calls[0].args["flag"]
    assert (created.note, created.reason) == (flag_note, flag_reason)
    seen = stream.getvalue() + app_log_text(caplog) + caplog.text
    for value in (release, outcome, note, flag_note, flag_reason):
        assert value not in seen
    assert too_long.status_code == 400
    assert "zqzq" not in too_long.text


def test_wf4_case_entry_points_emit_records(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-17 (WF-4): through the real container each of the 8 operations leaves one request record, and the writes get
    the actor and the free text."""
    store = FakeSessionStore()
    cases, flags, demo = FakeCaseService(), FakeFlagService(), FakeDemoService()
    app = staff_full_app(
        monkeypatch, make_settings(tmp_path), store=store, cases=cases, flags=flags, demo=demo
    )
    cases.apply_result = summary()
    release_reason = rand_word()
    plan = (
        ("getQueue", REP, None),
        ("getCase", REP, None),
        ("applyCaseAction", REP, {"action": "release", "expected_version": 4, "reason": release_reason}),
        ("recordContactActivity", REP, request_example("recordContactActivity", "CALL") | {"note": "zqnote"}),
        ("createFlag", REP, request_example("createFlag", "ANSWER") | {"note": "zqfn", "reason": "zqfr"}),
        ("listFlags", REP, None),
        ("reviewFlag", DemoRole.SUPERVISOR, {"status": "reviewed", "note": "zqrev"}),
        ("getOversight", DemoRole.SUPERVISOR, None),
    )
    responses = []
    with captured_log() as stream, make_client(app) as client:
        for op, role, body in plan:
            responses.append((op, role, call(client, op, cookie_header(store.issue(role)), body=body)))
    records = records_of(stream, "request")
    assert len(records) == 8
    seen = []
    for (op, role, r), rec in zip(responses, records, strict=True):
        assert r.status_code in (200, 201), (op, r.text)
        assert rec["request_id"] == r.headers["X-Request-ID"]
        assert rec["route"] == load_contract().operations[op].path_template
        assert "MHC-C-" not in rec["route"]
        assert rec["status"] == r.status_code
        assert rec["caller_role"] == role.value
        seen.append((rec["route"], rec["status"], rec["caller_role"]))
    release = cases.calls_of("apply")[0].args
    assert release["actor"].role.value == "representative" and release["action"].reason == release_reason
    assert cases.calls_of("record_activity")[0].args["activity"].note == "zqnote"
    assert flags.calls[0].args["flag"].note == "zqfn"
    review = next(c for c in flags.calls if c.method == "review")
    assert review.args["note"] == "zqrev" and review.args["actor"].role.value == "supervisor"
    print(seen)
    print(
        [
            cases.calls_of("apply")[0].args["actor"],
            cases.calls_of("record_activity")[0].args["actor"],
            flags.calls[0].args["actor"],
            review.args["actor"],
        ]
    )
