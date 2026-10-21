"""J-1 in the browser (AEA-58): system Chrome against the production build served by the real app.

Level: integrated with a scripted model. Real server, real DB copy, guards on, the normal SCR-12 login, the
production build (`require_frontend=True`), the scripted adapter at the provider boundary. Steps whose services or
UX selectors are not available yet are reported blocked (never passed): at the time of writing AEA-51 (`run_graph`,
`reply_composer`) and the UX session's selector contract (`docs/plans/ux-join/selectors.md`).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from urllib.parse import urlsplit

import pytest

from meridian.policy.texts import TextId, render
from tests.api.openapi_check import assert_response_matches
from tests.fixtures.sqlite import ISSUED_DB
from tests.journeys.browser.network import to_httpx
from tests.journeys.browser.pages import DESKTOP, DEVICES, BrowserRun, Device
from tests.journeys.browser.record import sample_record_values
from tests.journeys.browser.selectors import DEV_LAYER_GLOBAL, DEV_PANEL_ROOT_ID, locate, locate_in
from tests.journeys.browser.steps import (
    ROOT_REDIRECT,
    SIGN_IN_SCR1,
    SIGN_IN_SELECTORS,
    browser_step,
    fill_login,
    first_hop,
    page_fetch,
    send_turn,
    sign_in_to_scr1,
    sign_in_via_form,
    sign_out_via_shell,
    thread_id_of,
)
from tests.journeys.j1.test_aea_57 import (
    CHAT_NEEDS,
    CUSTOMER_TEXT,
    RESPONDER_TEXT,
    SIGN_IN_NEEDS,
    TURN_NEEDS,
)
from tests.journeys.support.db import sha256_file
from tests.journeys.support.record import RecordData, render_record
from tests.journeys.support.scripted_model import ScriptedModel
from tests.journeys.support.server import FORBIDDEN_PORTS

pytest_plugins = ("tests.journeys.browser.plugin",)
pytestmark = pytest.mark.journey

J1 = "J-1"
PROBE = "/?signedin=1&role=owner"
REDIRECTS: Mapping[str, str] = {
    "/": ROOT_REDIRECT,
    "/staff/queue": "/login?return_to=%2Fstaff%2Fqueue&reason=none",
    PROBE: "/login?return_to=%2F%3Fsignedin%3D1%26role%3Downer&reason=none",
}
SEND_SELECTORS = ("chat.ready", "chat.composer", "chat.send")
ENTRY_SELECTORS = ("chat.entry.customer", "chat.entry.assistant", "chat.block.text")
device_param = pytest.mark.parametrize("device", DEVICES, ids=lambda d: d.name)


def test_serves_production_build(browser_journey: BrowserRun) -> None:
    brun = browser_journey
    run, bp = brun.run, brun.open(DESKTOP)
    with browser_step(run, J1, "1a build served"):
        assert run.settings.require_frontend is True
        assert run.settings.web_dist_dir == brun.build.dist_dir
        resp = bp.page.goto("/login")
        assert resp is not None
        assert resp.status == 200
        assert resp.request.redirected_from is None
        assert hashlib.sha256(resp.body()).hexdigest() == brun.build.index_sha256
        assert resp.headers["cache-control"] == "no-cache"
    with browser_step(run, J1, "1b no dev layer"):
        assert bp.page.evaluate(f"() => typeof window.{DEV_LAYER_GLOBAL}") == "undefined"
        assert bp.page.evaluate("id => document.getElementById(id) === null", DEV_PANEL_ROOT_ID) is True
        brun.screenshot(bp, "login-page")
        print(f"index.html sha256 {brun.build.index_sha256}; dev layer absent")


@device_param
def test_signed_out_pages_redirect_to_login(browser_journey: BrowserRun, device: Device) -> None:
    brun = browser_journey
    run, bp = brun.run, brun.open(device)
    for path, location in REDIRECTS.items():
        with browser_step(run, J1, f"2a redirect {path}"):
            resp = bp.page.goto(path)
            assert resp is not None
            hop = first_hop(resp)
            assert hop.status == 303
            assert hop.headers["location"] == location
            assert bp.page.url == run.base_url + location
            print(f"{path} -> {hop.status} {hop.headers['location']}")
    with browser_step(run, J1, "2b no api 2xx before sign-in"):
        bp.page.wait_for_load_state("networkidle")
        ok = [e for e in bp.net.exchanges if 200 <= e.status < 300 and e.operation_id != "login"]
        assert ok == []
    with browser_step(run, J1, "2c SCR-12 drawn", selectors=("screen.scr12",)):
        for n, path in enumerate(REDIRECTS, 1):
            bp.page.goto(path)
            locate(bp.page, "screen.scr12").wait_for(state="visible")
            brun.screenshot(bp, f"scr12-{n}")


@device_param
def test_j1_login_turn_refresh_resume(browser_journey: BrowserRun, device: Device) -> None:
    brun = browser_journey
    run, bp = brun.run, brun.open(device)
    state: dict[str, str] = {}
    start_mark = bp.net.mark()
    with browser_step(
        run, J1, "3a sign in", needs=SIGN_IN_NEEDS, operations=("login",), selectors=SIGN_IN_SCR1
    ):
        login = sign_in_to_scr1(brun, bp)
        state["session"] = login.session_id
        print(f"signed in via SCR-12; session {login.session_id[:8]}...; on {bp.page.url}")
    with browser_step(
        run,
        J1,
        "3b greeting",
        needs=CHAT_NEEDS,
        operations=("startChatSession",),
        selectors=("chat.entry", "chat.entry.assistant", "chat.block.text"),
    ):
        start = bp.net.wait_for(bp.page, "startChatSession", since=start_mark)
        assert start.status == 201
        assert start.body is not None
        body = json.loads(start.body)
        thread_id = str(body["thread_id"])
        state["thread"] = thread_id
        assert body["greeting"]["text"] == render(TextId.GREETING)
        first = locate_in(locate(bp.page, "chat.entry").first, "chat.block.text")
        assert first.inner_text().strip() == render(TextId.GREETING)
        conv = run.db.one("SELECT * FROM conversations WHERE thread_id = ?", (thread_id,))
        assert conv["demo_session"] == state["session"]
        assert run.db.count("conversations", "demo_session = ?", (state["session"],)) == 1
        print(
            f"startChatSession 201; thread {thread_id[:8]}...; one conversation row owned by the login session"
        )
    thread_id = state.get("thread", "")
    with browser_step(
        run,
        J1,
        "3c one turn",
        needs=TURN_NEEDS,
        operations=("submitTurn",),
        selectors=(*SEND_SELECTORS, *ENTRY_SELECTORS),
    ):
        sent_turn_id = send_turn(brun, bp)
        while locate(bp.page, "chat.entry.assistant").count() < 2:
            bp.page.wait_for_timeout(50)
        reply = (
            locate_in(locate(bp.page, "chat.entry.assistant").last, "chat.block.text").inner_text().strip()
        )
        turn = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (sent_turn_id,))
        assert turn["status"] == "completed"
        assert turn["thread_id"] == thread_id
        stored = [b["text"] for b in json.loads(turn["response"])["blocks"] if b["type"] == "text"]
        assert stored == [reply]
        assert reply == RESPONDER_TEXT
        assert run.script.problems() == ()
        assert run.script.remaining() == 0
        assert run.db.count("turns", "thread_id = ?", (thread_id,)) == 1
        state["reply"] = reply
        brun.screenshot(bp, "after-reply")
        print(f"submitTurn 200; turn {sent_turn_id[:8]}... completed; reply equals the stored text blocks")
    with browser_step(
        run,
        J1,
        "3d reload resumes",
        needs=TURN_NEEDS,
        operations=("getChatThread",),
        selectors=ENTRY_SELECTORS,
    ):
        mark = bp.net.mark()
        bp.page.reload()
        read = bp.net.wait_for(bp.page, "getChatThread", since=mark)
        assert read.status == 200
        assert read.path.endswith("/" + thread_id)
        assert "startChatSession" not in bp.net.operations(mark)
        assert "submitTurn" not in bp.net.operations(mark)
        customer = locate(bp.page, "chat.entry.customer").first
        assistant = locate(bp.page, "chat.entry.assistant").last
        customer.wait_for()
        assistant.wait_for()
        assert CUSTOMER_TEXT in customer.inner_text()
        assert locate_in(assistant, "chat.block.text").inner_text().strip() == state["reply"]
        c_box, a_box = customer.bounding_box(), assistant.bounding_box()
        assert c_box is not None
        assert a_box is not None
        assert c_box["y"] < a_box["y"]
        assert run.db.count("conversations", "demo_session = ?", (state["session"],)) == 1
        assert run.db.count("turns", "thread_id = ?", (thread_id,)) == 1
        brun.screenshot(bp, "after-reload")
        print("getChatThread 200 after reload; still one conversation and one turn")
        state["read"] = (read.body or b"").decode()
    with browser_step(
        run,
        J1,
        "3e greeting after reload",
        needs=CHAT_NEEDS,
        operations=("getChatThread",),
        selectors=("chat.entry", "chat.block.text"),
    ):
        first = locate_in(locate(bp.page, "chat.entry").first, "chat.block.text")
        assert first.inner_text().strip() == render(TextId.GREETING)
        assert json.loads(state["read"])["turns"][0]["turn_id"] == "greeting"


@device_param
def test_reload_resumes_without_new_session(browser_journey: BrowserRun, device: Device) -> None:
    brun = browser_journey
    run, bp = brun.run, brun.open(device)
    start_mark = bp.net.mark()
    with browser_step(
        run, J1, "4a sign in", needs=SIGN_IN_NEEDS, operations=("login",), selectors=SIGN_IN_SCR1
    ):
        sign_in_to_scr1(brun, bp)
    with browser_step(
        run,
        J1,
        "4b reload before a turn",
        needs=CHAT_NEEDS,
        operations=("startChatSession", "getChatThread"),
        selectors=("screen.scr1",),
    ):
        thread_id = thread_id_of(bp, start_mark)
        mark = bp.net.mark()
        bp.page.reload()
        read = bp.net.wait_for(bp.page, "getChatThread", since=mark)
        assert read.path.endswith(thread_id)
        assert bp.net.operations(mark).count("startChatSession") == 0
    with browser_step(
        run,
        J1,
        "4c one turn then reload",
        needs=TURN_NEEDS,
        operations=("submitTurn", "getChatThread"),
        selectors=SEND_SELECTORS,
    ):
        send_turn(brun, bp)
        mark = bp.net.mark()
        bp.page.reload()
        bp.net.wait_for(bp.page, "getChatThread", since=mark)
        after = bp.net.operations(mark)
        assert "startChatSession" not in after
        assert "submitTurn" not in after
        print("operations: " + ", ".join(bp.net.operations()))


@device_param
def test_sign_out_restores_the_guard(browser_journey: BrowserRun, device: Device) -> None:
    brun = browser_journey
    run, bp = brun.run, brun.open(device)
    state: dict[str, str] = {}
    start_mark = bp.net.mark()
    with browser_step(
        run,
        J1,
        "5a sign in and start",
        needs=CHAT_NEEDS,
        operations=("login", "startChatSession"),
        selectors=SIGN_IN_SCR1,
    ):
        state["session_1"] = sign_in_to_scr1(brun, bp).session_id
        state["thread_1"] = thread_id_of(bp, start_mark)
    with browser_step(run, J1, "5b signed-in deep link", needs=SIGN_IN_NEEDS):
        resp = bp.page.goto("/staff/queue")
        assert resp is not None
        assert resp.status == 200
        assert resp.request.redirected_from is None
    with browser_step(
        run, J1, "5c sign out", needs=SIGN_IN_NEEDS, operations=("logout",), selectors=("shell.sign_out",)
    ):
        sign_out_via_shell(run, bp)
        assert not [c for c in bp.context.cookies() if c["name"] == "mhc_session" and c["value"]]
    with browser_step(run, J1, "5d guard again"):
        first = bp.page.goto("/")
        assert first is not None
        hop = first_hop(first)
        assert hop.status == 303
        assert hop.headers["location"] == REDIRECTS["/"]
        fetched = page_fetch(bp, f"/api/chat/sessions/{state['thread_1']}")
        assert fetched["status"] == 401
        assert json.loads(str(fetched["text"]))["error"]["code"] == "UNAUTHENTICATED"
        last = [e for e in bp.net.exchanges if e.operation_id == "getChatThread"][-1]
        assert_response_matches(to_httpx(last), "getChatThread")
    with browser_step(
        run,
        J1,
        "5e sign in again starts fresh",
        needs=CHAT_NEEDS,
        operations=("login", "startChatSession", "getChatThread"),
        selectors=SIGN_IN_SCR1,
    ):
        mark = bp.net.mark()
        login_2 = sign_in_via_form(run, bp)
        assert login_2.session_id != state["session_1"]
        thread_2 = thread_id_of(bp, mark)
        assert bp.net.operations(mark).count("startChatSession") == 1
        assert thread_2 != state["thread_1"]
        old = page_fetch(bp, f"/api/chat/sessions/{state['thread_1']}")
        assert old["status"] == 404
        assert json.loads(str(old["text"]))["error"]["code"] == "SESSION_NOT_FOUND"
        print("operations after sign-in: " + ", ".join(bp.net.operations(mark)))
        print(f"earlier thread now 404: {old['text']}")


def test_no_dev_params_or_foreign_hosts(browser_journey: BrowserRun) -> None:
    brun = browser_journey
    run, bp = brun.run, brun.open(DESKTOP)

    def checks() -> None:
        assert bp.net.origins() == {run.base_url}
        assert bp.net.dev_param_hits(allowed_urls=(PROBE,)) == []
        assert run.server.port not in FORBIDDEN_PORTS
        assert all(urlsplit(s.url).port not in FORBIDDEN_PORTS for s in bp.net.requests)
        assert all(isinstance(m, ScriptedModel) for m in run.models.values())
        assert run.guard.blocked == []
        print(f"origins: {sorted(bp.net.origins())}")

    with browser_step(run, J1, "8a signed-out loads"):
        bp.page.goto("/")
        probe = bp.page.goto(PROBE)
        assert probe is not None
        assert first_hop(probe).status == 303
        bp.page.goto("/login")
        bp.page.wait_for_load_state("networkidle")
        checks()
    with browser_step(
        run, J1, "8b signed in", needs=SIGN_IN_NEEDS, operations=("login",), selectors=SIGN_IN_SCR1
    ):
        sign_in_to_scr1(brun, bp)
        bp.page.wait_for_timeout(1000)
        checks()


def test_secrets_absent_from_evidence(
    browser_journey: BrowserRun, capsys: pytest.CaptureFixture[str], request: pytest.FixtureRequest
) -> None:
    brun = browser_journey
    run, bp = brun.run, brun.open(DESKTOP)
    state: dict[str, str] = {}
    with browser_step(
        run, J1, "9a sign in", needs=SIGN_IN_NEEDS, operations=("login",), selectors=SIGN_IN_SCR1
    ):
        sign_in_to_scr1(brun, bp)
        brun.screenshot(bp, "signed-in")
    with browser_step(run, J1, "9b cookie flags", needs=SIGN_IN_NEEDS):
        cookies = [c for c in bp.context.cookies() if c["name"] == "mhc_session"]
        assert len(cookies) == 1
        assert cookies[0]["httpOnly"] is True
        assert cookies[0]["sameSite"] == "Lax"
        assert cookies[0]["secure"] is False
        assert "mhc_session" not in bp.page.evaluate("document.cookie")
        state["cookie"] = cookies[0]["value"]
    with browser_step(run, J1, "9c secret values absent", needs=SIGN_IN_NEEDS):
        password, secret = run.secret_values()
        values = {"demo password": password, "session secret": secret, "mhc_session value": state["cookie"]}
        captured = capsys.readouterr()
        print(captured.out, end="")
        record = render_record(RecordData("AEA-58", sample_record_values(brun.session, run.collector)))
        places = {
            "server logs": run.logs.all_text(),
            "screenshot names": "\n".join(p.name for p in brun.shots_dir.glob("*")),
            "test id": request.node.nodeid,
            "record": record,
            "pytest output": captured.out + captured.err,
        }
        for label, value in values.items():
            hits = {where: text.count(value) for where, text in places.items()}
            assert sum(hits.values()) == 0, f"{label}: {hits}"
            found = len(run.files_containing(value))
            assert found == 0, f"{label}: {found} working-copy files"
        print("secret hits: 0 per value")
    with browser_step(
        run, J1, "9d show password never ticked", selectors=("login.show_password", *SIGN_IN_SELECTORS)
    ):
        other = brun.open(DESKTOP)
        other.page.goto("/login")
        fill_login(run, other, password=run.settings.demo_password.get_secret_value())
        assert locate(other.page, "login.show_password").is_checked() is False
        brun.screenshot(other, "login-filled")


def test_issued_db_unchanged(browser_journey: BrowserRun) -> None:
    brun = browser_journey
    run, bp = brun.run, brun.open(DESKTOP)
    start_mark = bp.net.mark()
    with browser_step(run, J1, "10a hash after signed-out loads"):
        bp.page.goto("/")
        bp.page.goto("/login")
        assert sha256_file(ISSUED_DB) == run.env.issued_sha256_before
        assert run.env.db_path.resolve() != ISSUED_DB.resolve()
        assert run.env.db_path.exists()
        print(f"issued DB sha256 {run.env.issued_sha256_before}")
    with browser_step(
        run,
        J1,
        "10b hash after sign-in and start",
        needs=CHAT_NEEDS,
        operations=("login", "startChatSession"),
        selectors=SIGN_IN_SCR1,
    ):
        sign_in_to_scr1(brun, bp)
        bp.net.wait_for(bp.page, "startChatSession", since=start_mark)
        assert sha256_file(ISSUED_DB) == run.env.issued_sha256_before
        print(f"issued DB sha256 {sha256_file(ISSUED_DB)}")


def test_browser_path_records(browser_journey: BrowserRun) -> None:
    brun = browser_journey
    run, bp = brun.run, brun.open(DESKTOP)
    state: dict[str, str] = {}
    with browser_step(run, J1, "11a page records signed out"):
        final = bp.page.goto("/")
        assert final is not None
        hop = first_hop(final)
        rid = hop.headers["x-request-id"]
        rec = run.logs.wait_for("request", lambda x: x["request_id"] == rid)
        assert (rec["route"], rec["status"], rec["caller_role"]) == ("spa_fallback", 303, "anonymous")
        rec = run.logs.wait_for("request", lambda x: x["request_id"] == final.headers["x-request-id"])
        assert (rec["route"], rec["status"]) == ("spa_fallback", 200)
        other = brun.open(DESKTOP)
        with other.page.expect_response(lambda x: "/assets/" in x.url) as info:
            other.page.goto("/login")
        asset_rid = info.value.headers["x-request-id"]
        rec = run.logs.wait_for("request", lambda x: x["request_id"] == asset_rid)
        assert (rec["route"], rec["status"], rec["caller_role"]) == ("/assets/{file}", 200, "anonymous")
        print("request records: 303 spa_fallback, 200 spa_fallback, 200 /assets/{file} (all anonymous)")
    with browser_step(
        run, J1, "11b auth_event ok", needs=SIGN_IN_NEEDS, operations=("login",), selectors=SIGN_IN_SCR1
    ):
        login = sign_in_to_scr1(brun, bp)
        state["session"] = login.session_id
        login_rid = login.login.header("x-request-id")
        ev = run.logs.wait_for("auth_event", lambda x: x["request_id"] == login_rid)
        assert ev["outcome"] == "ok"
        assert ev["session_id"] == login.session_id
    with browser_step(
        run,
        J1,
        "11c auth_event logged_out",
        needs=SIGN_IN_NEEDS,
        operations=("logout",),
        selectors=("shell.sign_out",),
    ):
        out = sign_out_via_shell(run, bp)
        out_rid = out.header("x-request-id")
        ev = run.logs.wait_for("auth_event", lambda x: x["request_id"] == out_rid)
        assert ev["outcome"] == "logged_out"
        assert ev["session_id"] == state["session"]
    with browser_step(
        run,
        J1,
        "11d conversation record",
        needs=CHAT_NEEDS,
        operations=("login", "startChatSession"),
        selectors=SIGN_IN_SCR1,
    ):
        mark = bp.net.mark()
        sign_in_to_scr1(brun, bp)
        ex = bp.net.wait_for(bp.page, "startChatSession", since=mark)
        assert ex.body is not None
        thread_id = str(json.loads(ex.body)["thread_id"])
        assert run.db.count("conversations", "thread_id = ?", (thread_id,)) == 1
        start_rid = ex.header("x-request-id")
        rec = run.logs.wait_for("request", lambda x: x["request_id"] == start_rid)
        assert (rec["status"], rec["caller_role"]) == (201, "customer")
        print(f"conversation record: request {rec['status']} customer, one conversations row")
    with browser_step(
        run,
        J1,
        "11e turn record",
        needs=TURN_NEEDS,
        operations=("submitTurn",),
        selectors=SEND_SELECTORS,
    ):
        sent = send_turn(brun, bp)
        assert run.db.count("turns", "turn_id = ?", (sent,)) == 1
        turn_ex = [e for e in bp.net.exchanges if e.operation_id == "submitTurn"][-1]
        turn_rid = turn_ex.header("x-request-id")
        rec = run.logs.wait_for("request", lambda x: x["request_id"] == turn_rid)
        assert (rec["status"], rec["caller_role"]) == (200, "customer")
        print(f"turn record: request {rec['status']} customer, one turns row")
