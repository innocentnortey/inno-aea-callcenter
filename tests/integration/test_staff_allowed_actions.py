"""AEA-52: `allowed_actions` lists exactly what each role is accepted to do (AC-16). Live variants wait on AEA-51."""

from __future__ import annotations

from datetime import datetime, timedelta

import httpx
import pytest

from tests.integration.staff_support import (
    P1_NEEDS,
    P1_OPERATIONS,
    Actor,
    act,
    assert_bound,
    call,
    case_view,
    demo_now,
    error_of,
    live,
    reset_demo,
    sign_in,
    switch_role,
    version_of,
)
from tests.journeys.support.run import JourneyRun
from tests.journeys.support.server import StepClock

REF = "MHC-C-0007"
OPERATION_KEYS = {
    "applyCaseAction": (
        "claim",
        "release",
        "start",
        "wait",
        "resolve",
        "close_unresolved",
        "assign",
        "change_priority",
    ),
    "liveChatAction": ("join_chat", "send_live_message", "hand_back", "close_chat"),
    "recordContactActivity": ("log_call", "log_email"),
    "createFlag": ("flag",),
}
LIVE_OR_CONTACT = {
    "claim_and_join",
    "join_chat",
    "send_live_message",
    "hand_back",
    "close_chat",
    "log_call",
    "log_email",
}
REFUSAL_CODES = {
    "ROLE_NOT_ALLOWED",
    "NOT_ALLOWED_IN_STATE",
    "CASE_ALREADY_CLAIMED",
    "NOT_CLAIMED_BY_YOU",
    "NOT_LIVE",
}
REASON = "Synthetic reason."


def send_key(actor: Actor, ref: str, key: str, *, version: int, now: datetime) -> list[httpx.Response]:
    if key in ("claim", "start"):
        return [act(actor, ref, key, version=version)]
    if key in ("release", "close_unresolved"):
        return [act(actor, ref, key, version=version, reason=REASON)]
    if key == "wait":
        return [act(actor, ref, key, version=version, wake_up_at=(now + timedelta(days=1)).isoformat())]
    if key == "resolve":
        return [act(actor, ref, key, version=version, outcome="Resolved by the integration test.")]
    if key == "assign":
        return [act(actor, ref, key, version=version, assignee="riley", reason=REASON)]
    if key == "change_priority":
        return [act(actor, ref, key, version=version, priority="P2", reason=REASON)]
    if key == "join_chat":
        return [live(actor, ref, "join")]
    if key == "send_live_message":
        return [live(actor, ref, "send", "Synthetic staff reply.")]
    if key == "hand_back":
        return [live(actor, ref, "hand_back")]
    if key == "close_chat":
        return [live(actor, ref, "close")]
    if key in ("log_call", "log_email"):
        body = {
            "kind": "call" if key == "log_call" else "email",
            "outcome": "reached",
            "note": None,
            "expected_version": version,
        }
        return [call(actor, "POST", f"/api/staff/cases/{ref}/activities", "recordContactActivity", body)]
    if key == "flag":
        return [call(actor, "POST", "/api/staff/flags", "createFlag", {"case_ref": ref, "target": "brief"})]
    if key == "claim_and_join":
        return [act(actor, ref, "claim", version=version), live(actor, ref, "join")]
    raise AssertionError(f"unknown key {key}")


@pytest.mark.parametrize("source", ["seed_mhc_c_0007"])
def test_listed_iff_accepted_per_role(journey: JourneyRun, journey_clock: StepClock, source: str) -> None:
    assert_bound(journey, P1_NEEDS, P1_OPERATIONS)
    actors = {
        "representative": sign_in(journey, "representative"),
        "supervisor": sign_in(journey, "supervisor"),
        "owner": sign_in(journey, "owner"),
    }

    resets = [0]

    def fresh() -> None:
        # the reset limiter allows 10 per 10-minute wall window per client: move the wall clock past it every 8
        if resets[0] and resets[0] % 8 == 0:
            journey_clock.advance(601)
        resets[0] += 1
        r = reset_demo(actors["representative"])
        assert r.status_code == 200, r.text
        for role, actor in actors.items():
            switch_role(actor, role)

    for role, actor in actors.items():
        fresh()
        listed = case_view(actor, REF)["case"]["allowed_actions"]
        if role == "owner":
            assert listed == []
        if role == "supervisor":
            assert not (set(listed) & LIVE_OR_CONTACT), listed
        for key in listed:
            fresh()
            now = demo_now(actor)
            for response in send_key(actor, REF, key, version=version_of(actor, REF), now=now):
                assert 200 <= response.status_code < 300, (role, key, response.status_code, response.text)
            print(role, key, "listed -> accepted")
        for op, keys in OPERATION_KEYS.items():
            unlisted = next((k for k in keys if k not in listed), None)
            if unlisted is None:
                continue
            fresh()
            now = demo_now(actor)
            responses = send_key(actor, REF, unlisted, version=version_of(actor, REF), now=now)
            last = responses[-1]
            assert last.status_code in (403, 409), (role, op, unlisted, last.status_code)
            assert error_of(last)["code"] in REFUSAL_CODES, (role, unlisted, error_of(last)["code"])
            print(role, unlisted, "unlisted -> refused", error_of(last)["code"])
