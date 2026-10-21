"""AEA-52: staff streams and staffing banner on the real app (AC-14, AC-20). Live-chat stream tests wait on AEA-51."""

from __future__ import annotations

from meridian.policy.texts import TEXTS, TextId
from tests.api.openapi_check import assert_sse_frames_match
from tests.integration.staff_streams_support import read_stream
from tests.integration.staff_support import (
    P1_NEEDS,
    P1_OPERATIONS,
    act,
    assert_bound,
    call,
    reset_demo,
    set_staffing,
    sign_in,
    switch_role,
)
from tests.journeys.support.run import JourneyRun

CASE = "MHC-C-0005"
STREAM = f"/api/staff/cases/{CASE}/events"


def test_case_stream_after_reset(journey: JourneyRun) -> None:
    assert_bound(journey, P1_NEEDS, P1_OPERATIONS)
    rep = sign_in(journey, "representative")
    assert act(rep, CASE, "claim").status_code == 200
    first = read_stream(journey.base_url, rep.cookie, STREAM)
    assert first.status == 200
    assert_sse_frames_match(first.frames, "streamCaseEvents")
    assert [f.event for f in first.frames].count("case_changed") == 1
    last_id = first.frames[-1].id
    assert last_id is not None

    assert reset_demo(rep).status_code == 200
    rep = switch_role(rep, "representative")  # the reset made the session a customer

    fresh = read_stream(journey.base_url, rep.cookie, STREAM)
    assert fresh.status == 200
    assert all(f.event != "demo_reset" for f in fresh.frames)
    assert fresh.closed_by_server is False
    resumed = read_stream(journey.base_url, rep.cookie, STREAM, last_event_id=last_id)
    assert resumed.status == 200
    assert_sse_frames_match(resumed.frames, "streamCaseEvents")
    assert [f.event for f in resumed.frames] == ["demo_reset"]
    assert resumed.closed_by_server is True
    journey.logs.wait_for("stream_reconnect", lambda r: r.get("case_ref") == CASE)
    print("fresh:", [f.event for f in fresh.frames], "resumed:", [f.event for f in resumed.frames])


def test_staff_banner_follows_staffing(journey: JourneyRun) -> None:
    assert_bound(journey, P1_NEEDS, P1_OPERATIONS)
    rep = sign_in(journey, "representative")
    sup = sign_in(journey, "supervisor")
    on = set_staffing(sup, "simulated_on_shift").json()
    banner = call(sup, "GET", "/api/demo/staffing", "getStaffing").json()["banner"]
    assert banner == TEXTS[TextId.STAFFING_BANNER]
    assert on["mode"] == "simulated_on_shift"
    queue = call(rep, "GET", "/api/staff/queue", "getQueue").json()
    oversight = call(sup, "GET", "/api/staff/oversight", "getOversight").json()
    assert queue["staffing"]["mode"] == oversight["staffing"]["mode"] == "simulated_on_shift"
    assert queue["staffing"]["banner"] == oversight["staffing"]["banner"] == banner
    print(
        "on:", queue["staffing"], "live:", queue["live"], "live_queue_length:", oversight["live_queue_length"]
    )

    set_staffing(sup, "nobody_online")
    queue = call(rep, "GET", "/api/staff/queue", "getQueue").json()
    oversight = call(sup, "GET", "/api/staff/oversight", "getOversight").json()
    assert queue["staffing"]["banner"] is None
    assert queue["live"] == []
    assert oversight["staffing"]["banner"] is None
    assert oversight["live_queue_length"] == 0
    rows = list(queue["needs_my_action"])
    for lane in oversight["lanes"].values():
        rows.extend(lane["rows"])
    assert all(row.get("lifecycle") != "live_queued" for row in rows)
    print(
        "off:",
        queue["staffing"],
        "live:",
        queue["live"],
        "live_queue_length:",
        oversight["live_queue_length"],
    )
