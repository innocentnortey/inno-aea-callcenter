"""AEA-62, J-8 (`J-AUTH`) in Chrome on the production build: role switching and resume, the role guard blocking and
the legitimate path passing, sign-out and expiry, the real header for four roles, a role change made in another tab,
and the evidence and record checks of AC-16 and AC-17. Level: integrated with a scripted model. Blocked steps name
their owner and are never passed.
"""

from __future__ import annotations

import json
import re
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import Response

from meridian.domain.common import Role
from meridian.web.errors import REQUEST_ID_HEADER
from tests.journeys.browser.network import ApiExchange
from tests.journeys.browser.pages import DESKTOP, BrowserPage, BrowserRun
from tests.journeys.browser.record import browser_record_values
from tests.journeys.browser.selectors import locate
from tests.journeys.browser.steps import (
    SIGN_IN_SELECTORS,
    BrowserLogin,
    browser_step,
    first_hop,
    page_fetch,
    sign_in_via_form,
    sign_out_via_shell,
)
from tests.journeys.j1.test_aea_57 import (
    CHAT_NEEDS,
    CLASSIFIER_RAW,
    CUSTOMER_TEXT,
    PLANNER_RAW,
    RESPONDER_TEXT,
    SIGN_IN_NEEDS,
    TURN_NEEDS,
)
from tests.journeys.j2.test_aea_62 import (
    CHAT_SELECTORS,
    IDENTITY_SELECTORS,
    ROLES,
    STAFF_NEEDS,
    VERIFY_NEEDS,
    Factory,
    assert_turn_records,
    block_here,
    browser_run,
    open_chat,
    responder,
    say,
    second_tab,
)
from tests.journeys.j3.test_aea_62 import Verified, billing_through_code
from tests.journeys.j6.test_aea_62 import switch_role
from tests.journeys.support.env import REPO_ROOT
from tests.journeys.support.record import RecordData, build_record_data, render_record
from tests.journeys.support.run import JourneyRun

pytest_plugins = ("tests.journeys.browser.plugin",)
pytestmark = pytest.mark.journey

J8 = "J-8"
SEED_CASE = "MHC-C-0006"  # a seed with no identity data (stage7/cases.md section 7)
EXPECTED_DISPLAY = {
    "customer": "Customer (demo)",
    "representative": "Riley, demo representative",
    "supervisor": "Demo supervisor",
    "owner": "Demo business owner",
}


def chat_sign_in(run: JourneyRun, name: str) -> AbstractContextManager[None]:
    return browser_step(
        run,
        J8,
        name,
        needs=TURN_NEEDS,
        operations=("login", "startChatSession"),
        selectors=(*SIGN_IN_SELECTORS, "screen.scr1"),
    )


def role_of(run: JourneyRun, session_id: str) -> str:
    return str(run.db.scalar("SELECT role FROM staff_sessions WHERE session_id = ?", (session_id,)))


def assert_seed(run: JourneyRun) -> None:
    assert run.db.count("cases", "case_ref = ? AND seed = 1", (SEED_CASE,)) == 1


def test_j8_role_switch_and_resume(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J8) as (brun, _):
        run = brun.run
        bp = brun.open(DESKTOP)
        with chat_sign_in(run, "13a sign in and chat"):
            login, thread_a = open_chat(run, bp)
            sid = login.session_id
        with browser_step(
            run,
            J8,
            "13b to representative",
            needs=STAFF_NEEDS,
            operations=("switchRole", "getQueue"),
            selectors=("shell.role.representative", "screen.scr5"),
        ):
            switch_role(run, bp, "representative")
            assert urlsplit(bp.page.url).path == "/staff/queue" and role_of(run, sid) == "representative"
        with browser_step(
            run,
            J8,
            "13c back to customer",
            needs=CHAT_NEEDS,
            operations=("switchRole", "getChatThread"),
            selectors=("shell.role.customer", "screen.scr1"),
        ):
            mark = bp.net.mark()
            switch_role(run, bp, "customer")
            assert urlsplit(bp.page.url).path == "/" and role_of(run, sid) == "customer"
            read = bp.net.wait_for(bp.page, "getChatThread", since=mark)
            assert read.path.endswith("/" + thread_a) and "startChatSession" not in bp.net.operations(mark)
        with browser_step(
            run,
            J8,
            "13d case reload keeps role",
            needs=STAFF_NEEDS,
            operations=("switchRole", "getCase", "getSession"),
            selectors=("shell.role.representative", "screen.scr6"),
        ):
            switch_role(run, bp, "representative")
            mark = bp.net.mark()
            bp.page.goto(f"/staff/cases/{SEED_CASE}")
            assert bp.net.wait_for(bp.page, "getCase", since=mark).status == 200
            events = run.db.count("case_events", "case_ref = ?", (SEED_CASE,))
            mark = bp.net.mark()
            bp.page.reload()
            s = bp.net.wait_for(bp.page, "getSession", since=mark)
            assert json.loads(s.body or b"{}")["role"] == "representative"
            assert bp.net.wait_for(bp.page, "getCase", since=mark).status == 200
            assert run.db.count("case_events", "case_ref = ?", (SEED_CASE,)) == events
        with browser_step(
            run,
            J8,
            "13e tab A chats while tab B is representative",
            needs=TURN_NEEDS,
            operations=("switchRole", "submitTurn"),
            selectors=(*CHAT_SELECTORS, "shell.role.customer", "shell.role.representative", "screen.scr4"),
        ):
            switch_role(run, bp, "customer")
            bp.page.goto("/")  # resumes thread_a: no new start
            tab_b = second_tab(bp)
            tab_b.page.goto("/role")
            switch_role(run, tab_b, "representative")
            bp.page.bring_to_front()
            table = {
                Role.PLANNER: PLANNER_RAW,
                Role.CLASSIFIER: CLASSIFIER_RAW,
                Role.RESPONDER: responder(RESPONDER_TEXT),
            }
            say(run, bp, CUSTOMER_TEXT, table=table, must={Role.PLANNER, Role.CLASSIFIER, Role.RESPONDER})
            assert locate(bp.page, "chat.entry.assistant").last.inner_text().strip() == RESPONDER_TEXT
            assert run.db.count("staff_sessions") == 1 and role_of(run, sid) == "representative"
            assert run.db.count("conversations", "demo_session = ?", (sid,)) == 1
            print("operations:", ", ".join(bp.net.operations()))


def test_j8_customer_refused_then_switch_allowed(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J8) as (brun, _):
        run = brun.run
        bp = brun.open(DESKTOP)
        with browser_step(
            run, J8, "14 sign in", needs=SIGN_IN_NEEDS, operations=("login",), selectors=SIGN_IN_SELECTORS
        ):
            first = bp.page.goto("/")
            assert first is not None and first_hop(first).status == 303
            sid = sign_in_via_form(run, bp).session_id
        with browser_step(
            run,
            J8,
            "14a refused",
            needs=STAFF_NEEDS,
            operations=("getQueue",),
            selectors=("role.panel", "queue.row"),
        ):
            events = run.db.count("case_events")
            mark = bp.net.mark()
            r = bp.page.goto("/staff/queue")
            assert r is not None and r.status == 200
            q = bp.net.wait_for(bp.page, "getQueue", since=mark)
            assert q.status == 403
            err = json.loads(q.body or b"{}")["error"]
            assert err["code"] == "ROLE_NOT_ALLOWED" and err["details"]["reason"] == "wrong_role"
            panel = locate(bp.page, "role.panel").inner_text().strip()
            assert "You're acting as the customer. Switch to a staff role to see this." in panel
            assert locate(bp.page, "queue.row").count() == 0 and role_of(run, sid) == "customer"
            print("refused:", err["code"], err["details"]["reason"])
            brun.screenshot(bp, "refused")
        with browser_step(
            run,
            J8,
            "14b switch allowed",
            needs=STAFF_NEEDS,
            operations=("switchRole", "getQueue"),
            selectors=("shell.role.representative", "queue.row"),
        ):
            mark = bp.net.mark()
            switch_role(run, bp, "representative")
            assert bp.net.wait_for(bp.page, "getQueue", since=mark).status == 200
            assert locate(bp.page, "queue.row").count() >= 4 and role_of(run, sid) == "representative"
            assert run.db.count("case_events") == events
            brun.screenshot(bp, "allowed")


def test_j8_signed_out_and_expired(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J8, clock=True) as (brun, _):
        run = brun.run
        bp = brun.open(DESKTOP)
        with chat_sign_in(run, "15a sign in, chat, open case"):
            assert_seed(run)
            login_1, thread_1 = open_chat(run, bp)
            switch_role(run, bp, "representative")
            mark = bp.net.mark()
            bp.page.goto(f"/staff/cases/{SEED_CASE}")
            assert bp.net.wait_for(bp.page, "getCase", since=mark).status == 200
        with browser_step(
            run,
            J8,
            "15b sign out on SCR-6",
            operations=("logout",),
            selectors=("shell.sign_out", "screen.scr12"),
        ):
            sign_out_via_shell(run, bp)
            locate(bp.page, "screen.scr12").wait_for()
            assert run.db.count("staff_sessions", "session_id = ?", (login_1.session_id,)) == 0
        with browser_step(run, J8, "15c reload case signed out"):
            reloaded = bp.page.goto(f"/staff/cases/{SEED_CASE}")
            assert reloaded is not None
            hop = first_hop(reloaded)
            assert hop.status == 303
            assert hop.headers["location"] == f"/login?return_to=%2Fstaff%2Fcases%2F{SEED_CASE}&reason=none"
        with browser_step(
            run,
            J8,
            "15d sign in again lands there",
            needs=SIGN_IN_NEEDS,
            operations=("login",),
            selectors=SIGN_IN_SELECTORS,
        ):
            login_2 = sign_in_via_form(run, bp)
            assert login_2.session_id != login_1.session_id
            assert urlsplit(bp.page.url).path == f"/staff/cases/{SEED_CASE}"
        with browser_step(
            run,
            J8,
            "15e SCR-1 starts fresh",
            needs=CHAT_NEEDS,
            operations=("startChatSession", "getChatThread"),
            selectors=("screen.scr1",),
        ):
            mark = bp.net.mark()
            bp.page.goto("/")
            start = bp.net.wait_for(bp.page, "startChatSession", since=mark)
            ops = bp.net.operations(mark)
            asked = [
                e
                for e in bp.net.exchanges
                if e.index >= mark and e.operation_id == "getChatThread" and e.path.endswith("/" + thread_1)
            ]
            if asked:
                block_here(
                    run,
                    J8,
                    "15e SCR-1 starts fresh",
                    "SCR-1 start fresh (the page requested the earlier thread)",
                    "UX session",
                )
            assert ops.count("startChatSession") == 1
            assert json.loads(start.body or b"{}")["thread_id"] != thread_1
            fetched = page_fetch(bp, f"/api/chat/sessions/{thread_1}")
            assert fetched["status"] == 404
            assert json.loads(str(fetched["text"]))["error"]["code"] == "SESSION_NOT_FOUND"
            print("operations after sign-in:", ops, "| earlier thread:", fetched["status"], fetched["text"])
        with browser_step(run, J8, "15f expired", needs=SIGN_IN_NEEDS, selectors=("login.message.expired",)):
            if run.clock is None:
                block_here(run, J8, "15f expired", "wall-clock control in the browser run", "AEA-58")
            run.clock.advance(run.container.limits.web.login_session_lifetime_s + 1)
            nav = bp.page.goto("/staff/queue")
            assert nav is not None
            hop = first_hop(nav)
            assert hop.status == 303
            assert hop.headers["location"] == "/login?return_to=%2Fstaff%2Fqueue&reason=expired"
            cookies = [
                h["value"]
                for h in hop.headers_array()
                if h["name"].lower() == "set-cookie" and h["value"].startswith("mhc_session=")
            ]
            assert len(cookies) == 1 and "max-age=0" in cookies[0].lower()
            expired = locate(bp.page, "login.message.expired").inner_text().strip()
            assert expired == "Your demo session ended, so please sign in again."
            assert run.db.count("staff_sessions", "session_id = ?", (login_2.session_id,)) == 0
            print("expired:", hop.status, hop.headers["location"], "| session row gone")


def test_j8_header_for_four_roles(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J8) as (brun, _):
        run = brun.run
        bp = brun.open(DESKTOP)
        with browser_step(
            run, J8, "19 sign in", needs=SIGN_IN_NEEDS, operations=("login",), selectors=SIGN_IN_SELECTORS
        ):
            first = bp.page.goto("/")
            assert first is not None and first_hop(first).status == 303
            sign_in_via_form(run, bp)
        for role in ROLES:
            with browser_step(
                run,
                J8,
                f"19 {role}",
                needs=STAFF_NEEDS,
                operations=("getSession", "switchRole"),
                selectors=(f"shell.role.{role}", "shell.header_name"),
            ):
                mark = bp.net.mark()
                if role != "customer":
                    switch_role(run, bp, role)
                else:
                    bp.page.reload()
                body = json.loads(bp.net.wait_for(bp.page, "getSession", since=mark).body or b"{}")
                assert body["role"] == role and body["display_name"] == EXPECTED_DISPLAY[role]
                header = locate(bp.page, "shell.header_name").inner_text().strip()
                assert header == body["display_name"] and locate(bp.page, f"shell.role.{role}").is_checked()
                print(
                    f"{role}: header {header!r} | getSession role {body['role']} name {body['display_name']!r}"
                )


def test_j8_role_change_elsewhere(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J8) as (brun, _):
        run = brun.run
        bp = brun.open(DESKTOP)
        with browser_step(
            run, J8, "20 sign in", needs=SIGN_IN_NEEDS, operations=("login",), selectors=SIGN_IN_SELECTORS
        ):
            first = bp.page.goto("/")
            assert first is not None and first_hop(first).status == 303
            sign_in_via_form(run, bp)
            assert_seed(run)
        with browser_step(
            run,
            J8,
            "20a wrong_role in tab A",
            needs=STAFF_NEEDS,
            operations=("switchRole", "getCase"),
            selectors=(
                "shell.role.customer",
                "shell.role.representative",
                "role.panel.wrong_role",
                "case.root",
            ),
        ):
            switch_role(run, bp, "representative")
            mark = bp.net.mark()
            bp.page.goto(f"/staff/cases/{SEED_CASE}")
            assert bp.net.wait_for(bp.page, "getCase", since=mark).status == 200
            tab_b = second_tab(bp)
            tab_b.page.goto("/role")
            switch_role(run, tab_b, "customer")
            mark = bp.net.mark()
            bp.page.bring_to_front()
            ex = bp.net.wait_for(bp.page, "getCase", since=mark)
            assert ex.status == 403
            assert json.loads(ex.body or b"{}")["error"]["details"]["reason"] == "wrong_role"
            assert locate(bp.page, "role.panel.wrong_role").is_visible()
            assert locate(bp.page, "case.root").count() == 0
            brun.screenshot(bp, "wrong-role")
        with browser_step(
            run,
            J8,
            "20b role_reset in tab A",
            needs=(*STAFF_NEEDS, "reset_service"),
            operations=("switchRole", "resetDemo", "getCase"),
            selectors=(
                "shell.role.representative",
                "demo.reset",
                "demo.reset_result",
                "role.panel.role_reset",
            ),
        ):
            switch_role(run, tab_b, "representative")
            tab_b.page.goto("/demo")
            mark = bp.net.mark()
            locate(tab_b.page, "demo.reset").click()
            assert bp.net.wait_for(tab_b.page, "resetDemo", since=mark).status == 200
            assert locate(tab_b.page, "demo.reset_result").is_visible()
            mark2 = bp.net.mark()
            bp.page.bring_to_front()
            bp.page.reload()
            ex = bp.net.wait_for(bp.page, "getCase", since=mark2)
            assert ex.status in (403, 404)
            if ex.status == 403:
                assert json.loads(ex.body or b"{}")["error"]["details"]["reason"] == "role_reset"
            assert locate(bp.page, "role.panel.role_reset").is_visible()
            brun.screenshot(bp, "role-reset")


# ---------------------------------------------------------------------------------------------------------------
# AC-16 and AC-17: one identity and staff path, scanned and listed
# ---------------------------------------------------------------------------------------------------------------
@dataclass
class PathValues:
    bp: BrowserPage
    thread_id: str
    login: BrowserLogin
    verified: Verified
    first_page: Response
    case_page: Response
    exchanges: dict[str, ApiExchange]
    cookie: str = field(repr=False)


def identity_and_staff_path(brun: BrowserRun) -> PathValues:
    run = brun.run
    bp = brun.open(DESKTOP)
    with browser_step(run, J8, "16a signed-out page", needs=SIGN_IN_NEEDS, operations=("login",)):
        first = bp.page.goto("/")
        assert first is not None
    with chat_sign_in(run, "16b sign in and chat"):
        mark = bp.net.mark()
        login = sign_in_via_form(run, bp)
        locate(bp.page, "screen.scr1").wait_for(state="visible")
        start = bp.net.wait_for(bp.page, "startChatSession", since=mark)
        assert start.status == 201
        tid = str(json.loads(start.body or b"{}")["thread_id"])
        cookie = next(c["value"] for c in bp.context.cookies() if c["name"] == "mhc_session")
    with browser_step(
        run,
        J8,
        "16c identity",
        needs=VERIFY_NEEDS,
        operations=("submitTurn", "listDemoInbox"),
        selectors=(*CHAT_SELECTORS, *IDENTITY_SELECTORS, "chat.block.account_card"),
    ):
        verified = billing_through_code(run, bp)
    exchanges: dict[str, ApiExchange] = {}
    with browser_step(
        run,
        J8,
        "16d staff",
        needs=STAFF_NEEDS,
        operations=("switchRole", "getQueue", "getCase"),
        selectors=("shell.role.representative", "screen.scr5", "screen.scr6"),
    ):
        mark = bp.net.mark()
        exchanges["switchRole"] = switch_role(run, bp, "representative")
        exchanges["getQueue"] = bp.net.wait_for(bp.page, "getQueue", since=mark)
        mark = bp.net.mark()
        case_page = bp.page.goto(f"/staff/cases/{SEED_CASE}")
        assert case_page is not None
        exchanges["getCase"] = bp.net.wait_for(bp.page, "getCase", since=mark)
    with browser_step(run, J8, "16e sign out", operations=("logout",), selectors=("shell.sign_out",)):
        exchanges["logout"] = sign_out_via_shell(run, bp)
    return PathValues(bp, tid, login, verified, first, case_page, exchanges, cookie)


def test_j_aea62_evidence_clean(
    browser_journey_factory: Factory, capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest
) -> None:
    with browser_run(browser_journey_factory, J8) as (brun, _):
        run = brun.run
        pv = identity_and_staff_path(brun)
        with browser_step(run, J8, "16f scans"):
            values = {
                "code": pv.verified.code,
                "phone": pv.verified.phone,
                "phone digits": re.sub(r"\D", "", pv.verified.phone),
                "demo password": run.settings.demo_password.get_secret_value(),
                "mhc_session value": pv.cookie,
            }
            captured = capsys.readouterr()
            print(captured.out, end="")
            base = build_record_data(scope="AEA-62", collector=run.collector, root=REPO_ROOT, command="j8")
            record_values = browser_record_values(base, brun.session, collector=run.collector, root=REPO_ROOT)
            record = render_record(RecordData(scope="AEA-62", values=record_values))
            places = {
                "server logs": run.logs.all_text(),
                "screenshot names": "\n".join(p.name for p in brun.shots_dir.glob("*"))
                if brun.shots_dir.exists()
                else "",
                "test id": request.node.nodeid,
                "record": record,
                "pytest output": captured.out + captured.err,
            }
            for label, value in values.items():
                hits = {where: text.count(value) for where, text in places.items()}
                assert sum(hits.values()) == 0, f"{label}: {hits}"
            assert pv.bp.net.dev_param_hits() == []
            assert pv.bp.net.origins() == {run.base_url}
            assert run.guard.blocked == []
            print(f"secret hits: 0 per value; origins: {sorted(pv.bp.net.origins())}")


def test_j_aea62_records_present(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J8) as (brun, _):
        run = brun.run
        pv = identity_and_staff_path(brun)
        with browser_step(run, J8, "17a records"):
            problems: list[str] = []

            def rec(ex: ApiExchange) -> dict[str, object]:
                rid = ex.header(REQUEST_ID_HEADER)
                return run.logs.wait_for("request", lambda r: r["request_id"] == rid)

            hop = rec_of(run, first_hop(pv.first_page))
            if (hop["route"], hop["status"], hop["caller_role"]) != ("spa_fallback", 303, "anonymous"):
                problems.append(
                    f"WF-19: signed-out hop record {hop['route']}/{hop['status']}/{hop['caller_role']}"
                )
            page = rec_of(run, pv.case_page)
            if page["route"] != "spa_fallback":
                problems.append(f"WF-19: case page load route {page['route']}")
            ok = run.logs.wait_for(
                "auth_event", lambda r: r["request_id"] == pv.login.login.header(REQUEST_ID_HEADER)
            )
            out = run.logs.wait_for(
                "auth_event", lambda r: r["request_id"] == pv.exchanges["logout"].header(REQUEST_ID_HEADER)
            )
            if (ok["outcome"], out["outcome"]) != ("ok", "logged_out"):
                problems.append(f"WF-18: outcomes {ok['outcome']}/{out['outcome']}")
            if not ok["session_id"] == out["session_id"] == pv.login.session_id:
                problems.append("WF-18: auth_event session ids differ")
            inbox = rec(pv.verified.inbox)
            if inbox["status"] != 200 or inbox.get("thread_id") != pv.thread_id:
                got = inbox.get("thread_id") or "empty"
                problems.append(
                    f"WF-3: the listDemoInbox request record has thread_id {got}, not the code request's thread "
                    "(seam: AEA-43 route / AEA-23 request record)"
                )
            if rec(pv.exchanges["switchRole"])["status"] != 200:
                problems.append("WF-4: switchRole record status is not 200")
            for op in ("getQueue", "getCase"):
                if rec(pv.exchanges[op])["caller_role"] != "representative":
                    problems.append(f"WF-4: {op} record caller_role is not representative")
            try:
                assert_turn_records(run, pv.thread_id)
                first_turn = run.db.one(
                    "SELECT turn_id FROM turns WHERE thread_id = ? ORDER BY sequence", (pv.thread_id,)
                )
                assert run.db.count("spend_ledger", "turn_id = ?", (first_turn["turn_id"],)) >= 1
            except AssertionError as e:
                problems.append(f"WF-1: {e}")
            print("record problems:", problems)
            assert problems == []


def rec_of(run: JourneyRun, response: Response) -> dict[str, object]:
    rid = response.headers.get(REQUEST_ID_HEADER.lower())
    return run.logs.wait_for("request", lambda r: r["request_id"] == rid)
