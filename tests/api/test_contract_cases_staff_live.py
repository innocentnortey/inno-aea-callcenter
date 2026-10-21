"""AEA-46 AC-22 (local driver): tests/contract/cases/staff_live.py holds the server cases for `liveChatAction` and
`streamCaseEvents`. AEA-59's runner reads the same data later; until it lands this file drives every case through the
in-process app. Failure mode guarded: contract (each case yields the status it names, valid against the OpenAPI, and
every documented status has a case)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import anyio
import pytest
from pydantic import JsonValue

from meridian.adapters.sqlite.rows import StreamEvent, case_stream
from meridian.domain.staff import DemoRole, StaffRole
from tests.api.openapi_check import assert_sse_frames_match, load_contract, load_document
from tests.api.staff_live_support import (
    app_uow,
    close_stream,
    events_url,
    fast_stream,
    live_url,
    open_stream,
    read_frames,
    running,
    staff_live_app,
)
from tests.api.web_shell_support import (
    FakeSessionStore,
    assert_matches,
    cookie_header,
    error_body,
    make_client,
)
from tests.contract.cases.staff_live import CASES, ROUTE_FILE
from tests.services.live_chat_support import JOIN_AT, RILEY, WP2_REF, new_service, seed_live_case

KNOWN = {
    "login",
    "as_representative",
    "live_case_claimed",
    "live_case_joined",
    "live_case_unclaimed",
    "case_claimed_by_supervisor",
    "case_events",
}


def _prepare(app: Any, steps: tuple[str, ...]) -> None:
    uow = app_uow(app)
    if "live_case_claimed" in steps or "live_case_joined" in steps:
        seed_live_case(uow)
    if "live_case_unclaimed" in steps:
        seed_live_case(uow, owner_role=None)
    if "case_claimed_by_supervisor" in steps:
        seed_live_case(uow, owner_role=StaffRole.SUPERVISOR)
    if "live_case_joined" in steps:
        new_service(uow).join(WP2_REF, RILEY)
    if "case_events" in steps:
        stored: tuple[tuple[str, dict[str, JsonValue]], ...] = (
            ("controller_changed", {"controller": {"kind": "human", "display_name": "Riley"}, "line": "x"}),
            ("case_changed", {"version": 2, "lifecycle": "claimed"}),
            ("chat_closed", {"reason": "closed_by_staff"}),
        )
        with uow(write=True) as tx:
            for kind, payload in stored:
                tx.core.events.append(
                    case_stream(WP2_REF), StreamEvent(type=kind, payload=payload, at=JOIN_AT)
                )
            tx.commit()


def test_staff_live_cases_drive_documented_statuses(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """contract (AC-22): each case produces its status; all documented statuses are covered."""
    assert ROUTE_FILE == "staff_live"
    assert set(CASES) == {"liveChatAction", "streamCaseEvents"}
    fast_stream(monkeypatch)
    contract = load_contract()
    examples = load_document()["paths"]["/api/staff/cases/{reference}/live"]["post"]["requestBody"][
        "content"
    ]["application/json"]["examples"]
    covered: dict[str, set[str]] = {"liveChatAction": set(), "streamCaseEvents": set()}
    for operation, spec in CASES.items():
        for case in spec["drives"]:  # type: ignore[attr-defined]
            steps = tuple(case["preconditions"])
            assert set(steps) <= KNOWN, f"unknown precondition in {case['name']}"
            store = FakeSessionStore()
            headers: dict[str, str] = {}
            token: str | None = None
            if "as_representative" in steps:
                token = store.issue(DemoRole.REPRESENTATIVE)
            elif "login" in steps:
                token = store.issue(DemoRole.CUSTOMER)
            if token is not None:
                headers = cookie_header(token)
            app = staff_live_app(monkeypatch, tmp_path / f"{operation}-{case['name']}", store=store)
            ref = case["reference"]
            if operation == "liveChatAction":
                body = case["body"]
                payload = examples[body["example"]]["value"] if "example" in body else body["raw"]
                with make_client(app) as client:
                    _prepare(app, steps)
                    response = client.post(live_url(ref), json=payload, headers=headers)
                assert response.status_code == case["status"], f"{case['name']}: {response.text}"
                if case["status"] != 200:
                    error_body(response, case["status"], case["code"])
                assert_matches(response, "liveChatAction")
            elif case["status"] == 200:

                async def scenario(
                    app: Any = app,
                    steps: tuple[str, ...] = steps,
                    token: str | None = token,
                    case: dict[str, Any] = case,
                ) -> None:
                    async with running(app) as tg:
                        _prepare(app, steps)
                        last = case.get("last_event_id")
                        handle = await open_stream(
                            tg,
                            app,
                            events_url(case["reference"]),
                            token=token,
                            last_event_id=None if last is None else str(last),
                        )
                        assert handle.status == 200
                        frames = await read_frames(handle, case["frames"])
                        assert_sse_frames_match(frames, "streamCaseEvents")
                        await close_stream(handle)

                anyio.run(scenario)
                response = None
            else:
                with make_client(app) as client:
                    _prepare(app, steps)
                    response = client.get(events_url(ref), headers=headers)
                assert response.status_code == case["status"], f"{case['name']}: {response.text}"
                error_body(response, case["status"], case["code"])
                assert_matches(response, "streamCaseEvents")
            covered[operation].add(str(case["status"]))
            print(f"{operation} {case['name']}: {case['status']}")
    assert (
        covered["liveChatAction"]
        == set(contract.operations["liveChatAction"].responses)
        == {"200", "400", "401", "403", "404", "409"}
    )
    assert (
        covered["streamCaseEvents"]
        == set(contract.operations["streamCaseEvents"].responses)
        == {"200", "401", "403", "404"}
    )
