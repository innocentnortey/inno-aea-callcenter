"""`browser_step`, sign-in and sign-out through the UI, redirect and fetch helpers (AEA-58)."""

from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from meridian.domain.common import Role
from tests.journeys.browser.selectors import locate, missing_selectors
from tests.journeys.j1.test_aea_57 import CLASSIFIER_RAW, CUSTOMER_TEXT, PLANNER_RAW, RESPONDER_TEXT
from tests.journeys.support.steps import StepResult, blocked_message, missing_needs, owners_of, stop_blocked

if TYPE_CHECKING:
    from playwright.sync_api import Response

    from tests.journeys.browser.network import ApiExchange
    from tests.journeys.browser.pages import BrowserPage, BrowserRun
    from tests.journeys.support.run import JourneyRun

SIGN_IN_SELECTORS: Final = ("login.username", "login.password", "login.submit")
SIGN_IN_SCR1: Final = (*SIGN_IN_SELECTORS, "screen.scr1")
ROOT_REDIRECT: Final = "/login?return_to=%2F&reason=none"  # web.md section 6 (WEB-28)


@contextmanager
def browser_step(
    run: JourneyRun,
    journey: str,
    name: str,
    *,
    needs: Sequence[str] = (),
    operations: Sequence[str] = (),
    selectors: Sequence[str] = (),
) -> Iterator[None]:
    """The only way tests open a step. A step lacking a selector is blocked with the UX session, never passed."""
    sel = missing_selectors(selectors)
    if sel:
        svc = missing_needs(run.container, run.app, needs, operations)
        everything = (*svc, *sel)
        run.collector.add_step(
            StepResult(
                journey, name, run.nodeid, "blocked", blocked_message(everything), owners_of(everything), 0.0
            )
        )
        stop_blocked(everything, strict=run.strict)
    with run.step(journey, name, needs=needs, operations=operations):
        yield


@dataclass(frozen=True)
class BrowserLogin:
    session_id: str
    login: ApiExchange  # the POST /api/login exchange (status 200)


def fill_login(run: JourneyRun, bp: BrowserPage, *, password: str) -> None:
    locate(bp.page, "login.username").fill(run.demo_username)
    locate(bp.page, "login.password").fill(password)


def sign_in_via_form(run: JourneyRun, bp: BrowserPage) -> BrowserLogin:
    before = {r["session_id"] for r in run.db.rows("SELECT session_id FROM staff_sessions")}
    mark = bp.net.mark()
    fill_login(run, bp, password=run.settings.demo_password.get_secret_value())
    locate(bp.page, "login.submit").click()
    ex = bp.net.wait_for(bp.page, "login", since=mark)
    if ex.status != 200:
        raise AssertionError(f"login answered HTTP {ex.status}")
    after = {r["session_id"] for r in run.db.rows("SELECT session_id FROM staff_sessions")}
    new = after - before
    if len(new) != 1:
        raise AssertionError(f"login stored {len(new)} new staff_sessions rows, expected 1")
    return BrowserLogin(session_id=next(iter(new)), login=ex)


def sign_out_via_shell(run: JourneyRun, bp: BrowserPage) -> ApiExchange:
    mark = bp.net.mark()
    locate(bp.page, "shell.sign_out").click()
    ex = bp.net.wait_for(bp.page, "logout", since=mark)
    if ex.status != 204:
        raise AssertionError(f"logout answered HTTP {ex.status}")
    return ex


def first_hop(response: Response) -> Response:
    request = response.request
    while request.redirected_from is not None:
        request = request.redirected_from
    hop = request.response()
    if hop is None:
        raise AssertionError("the first request of the redirect chain has no response")
    return hop


def page_fetch(bp: BrowserPage, path: str) -> dict[str, object]:
    result: dict[str, object] = bp.page.evaluate(
        "async (p) => { const r = await fetch(p, {credentials: 'include'}); return {status: r.status, text: await r.text()}; }",
        path,
    )
    return result


def sign_in_to_scr1(brun: BrowserRun, bp: BrowserPage) -> BrowserLogin:
    """Land on the guard, sign in through SCR-12, wait for SCR-1 (the return_to page)."""
    run = brun.run
    first = bp.page.goto("/")
    assert first is not None
    hop = first_hop(first)
    assert hop.status == 303
    assert hop.headers["location"] == ROOT_REDIRECT
    login = sign_in_via_form(run, bp)
    locate(bp.page, "screen.scr1").wait_for(state="visible")
    assert bp.page.url == run.base_url + "/"
    return login


def script_turn(brun: BrowserRun) -> None:
    script = brun.run.script
    script.add(Role.PLANNER, PLANNER_RAW)
    script.add(Role.CLASSIFIER, CLASSIFIER_RAW)
    script.add(Role.RESPONDER, json.dumps({"text": RESPONDER_TEXT}))


def send_turn(brun: BrowserRun, bp: BrowserPage) -> str:
    """Type the J-1 turn and send it; returns the turn_id the page sent."""
    script_turn(brun)
    locate(bp.page, "chat.ready").wait_for()
    mark = bp.net.mark()
    locate(bp.page, "chat.composer").fill(CUSTOMER_TEXT)
    locate(bp.page, "chat.send").click()
    ex = bp.net.wait_for(bp.page, "submitTurn", since=mark)
    assert ex.status == 200
    assert ex.request_body is not None
    return str(json.loads(ex.request_body)["turn_id"])


def thread_id_of(bp: BrowserPage, since: int = 0) -> str:
    ex = bp.net.wait_for(bp.page, "startChatSession", since=since)
    assert ex.status == 201
    assert ex.body is not None
    return str(json.loads(ex.body)["thread_id"])
