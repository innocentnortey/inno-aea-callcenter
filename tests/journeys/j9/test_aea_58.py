"""J-9 in the browser (AEA-58): the rate-limited login state through SCR-12.

Level: integrated with a scripted model. Each test starts its own server, so the login limiter is fresh. The throttle
line step is blocked-on UX session until the line and its selector row are in the build and `selectors.md`.
"""

from __future__ import annotations

import json

import pytest

from tests.journeys.browser.pages import DEVICES, BrowserRun, Device
from tests.journeys.browser.selectors import locate
from tests.journeys.browser.steps import SIGN_IN_SELECTORS, browser_step, fill_login
from tests.journeys.support.env import letters

pytest_plugins = ("tests.journeys.browser.plugin",)
pytestmark = pytest.mark.journey

J9 = "J-9"
LOGIN_NEEDS = ("login_sessions",)
# SCREEN_SPECS SCR-12 *error*, quoted in the AEA-58 ticket AC-6.
REFUSED_LINE = "That username or password didn't work. Check the README and try again."
# UI_CONTRACTS.md CON-22, LOGIN_RATE_LIMITED row.
THROTTLE_LINE = "Too many attempts. Wait a moment and try again."


@pytest.mark.parametrize("device", DEVICES, ids=lambda d: d.name)
def test_rate_limited_login_throttle_line(browser_journey: BrowserRun, device: Device) -> None:
    brun = browser_journey
    run, bp = brun.run, brun.open(device)
    page = bp.page
    wrong = "wrongpass" + letters(12)
    limit = run.container.limits.web.login_rejects_per_ip
    selectors = (*SIGN_IN_SELECTORS, "login.message.refused")
    with browser_step(
        run, J9, "9a wrong pair refused", needs=LOGIN_NEEDS, operations=("login",), selectors=selectors
    ):
        page.goto("/")
        mark = bp.net.mark()
        fill_login(run, bp, password=wrong)
        locate(page, "login.submit").click()
        ex = bp.net.wait_for(page, "login", since=mark)
        assert ex.status == 401
        assert ex.body is not None
        assert json.loads(ex.body)["error"]["code"] == "LOGIN_FAILED"
        assert locate(page, "login.message.refused").inner_text().strip() == REFUSED_LINE
        assert locate(page, "login.password").input_value() == ""
        assert locate(page, "login.username").input_value() == run.demo_username
    with browser_step(
        run, J9, "9b rejects up to the limit", needs=LOGIN_NEEDS, operations=("login",), selectors=selectors
    ):
        while sum(1 for e in bp.net.exchanges if e.operation_id == "login" and e.status == 401) < limit:
            mark = bp.net.mark()
            locate(page, "login.password").fill(wrong)
            locate(page, "login.submit").click()
            bp.net.wait_for(page, "login", since=mark)
        rejected = sum(1 for e in bp.net.exchanges if e.operation_id == "login" and e.status == 401)
        assert rejected == limit
    with browser_step(
        run,
        J9,
        "9c right pair throttled",
        needs=LOGIN_NEEDS,
        operations=("login",),
        selectors=SIGN_IN_SELECTORS,
    ):
        mark = bp.net.mark()
        fill_login(run, bp, password=run.settings.demo_password.get_secret_value())
        locate(page, "login.submit").click()
        ex = bp.net.wait_for(page, "login", since=mark)
        assert ex.status == 429
        assert ex.body is not None
        assert json.loads(ex.body)["error"]["code"] == "LOGIN_RATE_LIMITED"
        assert ex.header("retry-after") is not None
        assert not [c for c in bp.context.cookies() if c["name"] == "mhc_session" and c["value"]]
        assert run.db.count("staff_sessions") == 0
        print(f"401 x{limit}, then 429")
    with browser_step(run, J9, "9e records", needs=LOGIN_NEEDS):
        events = run.logs.structured("auth_event")
        outcomes = [str(r["outcome"]) for r in events]
        assert outcomes.count("rejected") == limit
        assert outcomes.count("rate_limited") == 1
        assert all(r["session_id"] is None for r in events)
    with browser_step(run, J9, "9d throttle line shown", selectors=("login.message.rate_limited",)):
        assert locate(page, "login.message.rate_limited").inner_text().strip() == THROTTLE_LINE
        assert THROTTLE_LINE != REFUSED_LINE
        brun.screenshot(bp, "throttled")
