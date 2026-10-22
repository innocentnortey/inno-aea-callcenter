"""AEA-62, J-6 (`J-ESC`) in Chrome on the production build: WP-7 refund request becomes a handoff card, a case in
the staff queue (SCR-5) and a case view with its eight-section brief and promise (SCR-6); WP-8 cancel-membership
as a second case with no false completion. Level: integrated with a scripted model. Blocked steps name their owner
and are never passed.

This file also holds `switch_role`, which j8 imports.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit

import pytest

from meridian.agent.tools.account import READ_MEMBERSHIP_NAME, ReadMembershipArgs
from meridian.agent.tools.knowledge import KB_SEARCH_NAME, KbSearchArgs
from meridian.domain.common import Role
from meridian.domain.handoff import BRIEF_TITLES, HandoffReason, Quote
from meridian.domain.specialists import AccountReport, KnowledgeReport, ReportedPoint
from meridian.policy.handoff import PROMISE_TABLE, STAFF_GUIDANCE_FOR
from meridian.policy.texts import TextId, render
from tests.journeys.browser.network import ApiExchange
from tests.journeys.browser.pages import DESKTOP, PHONE, BrowserPage, BrowserRun
from tests.journeys.browser.selectors import locate, locate_by, locate_in
from tests.journeys.browser.steps import SIGN_IN_SELECTORS, BrowserLogin, browser_step
from tests.journeys.j1.test_aea_57 import TURN_NEEDS
from tests.journeys.j2.test_aea_62 import (
    ACCOUNT_MARKER,
    CHAT_SELECTORS,
    CHI,
    HANDOFF_NEEDS,
    IDENTITY_SELECTORS,
    KNOWLEDGE_MARKER,
    NORMAL,
    SEED_REFS,
    STAFF_NEEDS,
    VERIFY_NEEDS,
    Factory,
    Turn,
    assert_no_excluded,
    assert_turn_records,
    blocks_of,
    brief,
    browser_run,
    card_shot,
    next_message_id,
    open_chat,
    page_text,
    planner,
    report,
    responder,
    say,
    step,
    tool,
    top_passage,
)
from tests.journeys.j3.test_aea_62 import verify_in_chat
from tests.journeys.support.db import issued_rows
from tests.journeys.support.run import JourneyRun

pytest_plugins = ("tests.journeys.browser.plugin",)
pytestmark = pytest.mark.journey

J6 = "J-6"
REFUND_TEXT = "I want a full refund on the repair. It didn't fix anything and I had to call another company."
STAFF_SELECTORS = ("shell.role.representative", "screen.scr5", "queue.row", "queue.row_by_ref")


def switch_role(run: JourneyRun, bp: BrowserPage, role: str) -> ApiExchange:
    mark = bp.net.mark()
    locate(bp.page, f"shell.role.{role}").click()
    ex = bp.net.wait_for(bp.page, "switchRole", since=mark)
    assert ex.status == 200
    return ex


@dataclass(frozen=True)
class RefundCase:
    bp: BrowserPage
    thread_id: str
    ref: str
    turn: Turn
    login: BrowserLogin


def refund_case(brun: BrowserRun) -> RefundCase:
    run = brun.run
    bp = brun.open(PHONE)
    with browser_step(
        run,
        J6,
        "9a sign in and chat",
        needs=TURN_NEEDS,
        operations=("login", "startChatSession"),
        selectors=(*SIGN_IN_SELECTORS, "screen.scr1"),
    ):
        login, tid = open_chat(run, bp)
    with browser_step(
        run,
        J6,
        "9b refund",
        needs=HANDOFF_NEEDS,
        operations=("submitTurn",),
        selectors=(*CHAT_SELECTORS, "chat.block.handoff", "settled.request"),
    ):
        msg_id = next_message_id(run)
        quotes = [
            Quote(message_id=msg_id, text=q)
            for q in ("It didn't fix anything", "I had to call another company")
        ]
        t = say(
            run,
            bp,
            REFUND_TEXT,
            table={
                Role.PLANNER: planner(handoff="refund", topic="billing"),
                Role.CLASSIFIER: NORMAL,
                Role.RESPONDER: responder("I'm sorry the repair didn't fix the problem."),
                Role.BRIEF: brief(
                    needs=[Quote(message_id=msg_id, text="I want a full refund on the repair.")],
                    claims=quotes,
                    open_decision="Decide between a refund, a warranty recall, or neither.",
                ),
            },
            must={Role.PLANNER, Role.CLASSIFIER, Role.RESPONDER, Role.BRIEF},
        )
        stored_id = run.db.scalar(
            "SELECT id FROM messages WHERE turn_id = ? AND role = 'customer'", (t.turn_id,)
        )
        assert stored_id == msg_id, (
            "the message id prediction is wrong (plan error: report it, keep the quotes)"
        )
        h = blocks_of(t.body, "handoff")[-1]
        m = re.fullmatch(r"MHC-C-(\d{4})", h["reference"])
        assert m and int(m.group(1)) >= 9
        assert h["promise_text"] == PROMISE_TABLE["R26.refund"]
        assert render(TextId.PROMISE_REFUND_NO_OUTCOME) in h["extra_lines"]
        assert t.body["settled"]["request"]["reference"] == h["reference"]
    return RefundCase(bp, tid, str(h["reference"]), t, login)


def open_queue(brun: BrowserRun, rc: RefundCase) -> ApiExchange:
    """Switch to Representative on a desktop viewport and return the getQueue exchange."""
    run, bp = brun.run, rc.bp
    bp.page.set_viewport_size({"width": DESKTOP.width, "height": DESKTOP.height})
    mark = bp.net.mark()
    switch_role(run, bp, "representative")
    q = bp.net.wait_for(bp.page, "getQueue", since=mark)
    assert q.status == 200 and urlsplit(bp.page.url).path == "/staff/queue"
    locate(bp.page, "screen.scr5").wait_for()
    return q


def test_j6_refund_handoff_in_chat(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J6) as (brun, _):
        run = brun.run
        rc = refund_case(brun)
        tid, ref, t = rc.thread_id, rc.ref, rc.turn
        with browser_step(run, J6, "9c card and stored", selectors=("chat.block.handoff", "settled.request")):
            text = locate(rc.bp.page, "chat.block.handoff").last.inner_text()
            promise, limit = PROMISE_TABLE["R26.refund"], render(TextId.PROMISE_REFUND_NO_OUTCOME)
            for needed in (ref, promise, limit, "Tue Oct 20 · 7:00 pm", render(TextId.FOLLOWUP_LEGEND)):
                assert needed in text, f"handoff card lacks {needed!r}"
            assert text.index(promise) < text.index(limit)
            assert ref in locate(rc.bp.page, "settled.request").inner_text()
            c = run.db.one("SELECT * FROM cases WHERE thread_id = ?", (tid,))
            assert c["case_ref"] == ref and c["reason"] == "refund" and c["priority"] == "P3"
            assert datetime.fromisoformat(c["due_at"]) == datetime(2026, 10, 20, 19, 0, tzinfo=CHI)
            p = run.db.one("SELECT * FROM promises WHERE case_ref = ?", (ref,))
            assert p["text"] == promise and p["status"] == "open"
            assert run.db.count("case_events", "case_ref = ? AND kind = 'case_opened'", (ref,)) == 1
            ev = run.db.rows("SELECT payload FROM events WHERE stream = ? AND type = 'case_created'", (tid,))
            assert len(ev) == 1 and json.loads(ev[0]["payload"])["case_ref"] == ref
            assert run.db.scalar("SELECT outcome FROM turns WHERE turn_id = ?", (t.turn_id,)) == "handed_off"
            assert (
                run.db.scalar("SELECT outcome FROM conversations WHERE thread_id = ?", (tid,)) == "handed_off"
            )
            print("handoff card:", text.replace("\n", " | "), "| case", dict(c), "| promise", dict(p))
            brun.screenshot(rc.bp, "handoff-card")
        with browser_step(run, J6, "9d records"):
            assert_turn_records(run, tid)


def test_j6_case_in_staff_queue(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J6) as (brun, _):
        run = brun.run
        rc = refund_case(brun)
        bp, ref = rc.bp, rc.ref
        with browser_step(
            run,
            J6,
            "10a switch",
            needs=STAFF_NEEDS,
            operations=("switchRole", "getQueue"),
            selectors=STAFF_SELECTORS,
        ):
            before = run.db.one("SELECT session_id, role FROM staff_sessions")
            events_before = run.db.count("case_events")
            q = open_queue(brun, rc)
            assert "Riley · demo representative" in page_text(bp.page)
            rows = json.loads(q.body or b"{}")["needs_my_action"]
            refs = [r["reference"] for r in rows]
            assert refs[0] == "MHC-C-0008" and set(SEED_REFS) | {ref} <= set(refs)
            mine = next(r for r in rows if r["reference"] == ref)
            assert mine["priority"] == {"level": "P3", "word": "Standard"} and mine["owner"] is None
            row = locate_by(bp.page, "queue.row_by_ref", ref).inner_text()
            for needed in ("P3 · Standard", ref, mine["reason"], "Unowned", "Tue Oct 20 · 7:00 pm"):
                assert needed in row, f"queue row lacks {needed!r}"
            first = locate(bp.page, "queue.row").first.inner_text()
            assert "MHC-C-0008" in first and "P0 · Safety" in first
            assert locate(bp.page, "queue.row").count() >= 5
            after = run.db.one("SELECT session_id, role FROM staff_sessions")
            assert after["session_id"] == before["session_id"] and before["role"] == "customer"
            assert after["role"] == "representative"
            assert run.db.count("case_events") == events_before
            print("queue order", refs, "| role", before["role"], "->", after["role"])
            brun.screenshot(bp, "scr5")


def test_j6_case_view_brief_and_promise(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J6, index=True) as (brun, _):
        run = brun.run
        rc = refund_case(brun)
        bp, ref = rc.bp, rc.ref
        with browser_step(
            run,
            J6,
            "11x switch",
            needs=STAFF_NEEDS,
            operations=("switchRole", "getQueue"),
            selectors=STAFF_SELECTORS,
        ):
            open_queue(brun, rc)
        with browser_step(
            run,
            J6,
            "11a open case",
            needs=STAFF_NEEDS,
            operations=("getCase",),
            selectors=(
                "queue.row_by_ref",
                "screen.scr6",
                "case.root",
                "case.owner",
                "case.promise",
                "case.promise.open",
                "brief.section_by_number",
                "brief.heading",
                "brief.item.tag",
                "case.sources_tab",
                "case.source_by_id",
            ),
        ):
            version_before = run.db.scalar("SELECT version FROM cases WHERE case_ref = ?", (ref,))
            events_before = run.db.count("case_events", "case_ref = ?", (ref,))
            mark = bp.net.mark()
            locate_by(bp.page, "queue.row_by_ref", ref).click()
            g = bp.net.wait_for(bp.page, "getCase", since=mark)
            assert g.status == 200 and urlsplit(bp.page.url).path == f"/staff/cases/{ref}"
            d = json.loads(g.body or b"{}")
            assert "Unassigned, nobody owns it yet" in locate(bp.page, "case.owner").inner_text()
            promise = locate(bp.page, "case.promise.open")
            assert promise.is_visible() and PROMISE_TABLE["R26.refund"] in promise.inner_text()
            assert "Open" in promise.inner_text()
            for n in range(1, 9):
                heading = locate_in(locate_by(bp.page, "brief.section_by_number", str(n)), "brief.heading")
                assert heading.inner_text().strip() == BRIEF_TITLES[n - 1]
            sec4 = locate_by(bp.page, "brief.section_by_number", "4")
            assert "Customer says · not checked" in locate_in(sec4, "brief.item.tag").first.inner_text()
            for quote in ("It didn't fix anything", "I had to call another company"):
                assert quote in sec4.inner_text()
            heads = d["brief"]["headings"]
            assert [h["title"] for h in heads] == list(BRIEF_TITLES)
            claims = [i["text"] for i in heads[3]["items"] if i["kind"] == "claim"]
            assert "It didn't fix anything" in claims and "I had to call another company" in claims
            lead = STAFF_GUIDANCE_FOR[HandoffReason.REFUND][0]
            guide = [i for i in heads[6]["items"] if i["kind"] == "fact" and i["text"].startswith(lead)]
            assert len(guide) == 1 and guide[0]["source_ids"]
            by_id = {s["source_id"]: s for s in d["sources"]}
            assert by_id[guide[0]["source_ids"][0]]["audience"] == "staff_only"
            ids = {s for h in heads for i in h["items"] for s in i["source_ids"]}
            assert ids <= set(by_id) and d["promise"]["status"] == "open"
            locate(bp.page, "case.sources_tab").click()
            for sid in sorted(ids):
                assert locate_by(bp.page, "case.source_by_id", sid).is_visible()
            stored = json.loads(
                run.db.scalar("SELECT brief_json FROM case_briefs WHERE case_ref = ?", (ref,))
            )
            s_heads = stored["headings"]
            assert [h["title"] for h in s_heads] == list(BRIEF_TITLES)
            for s_head, w_head in zip(s_heads, heads, strict=True):
                assert [i["kind"] for i in s_head["items"]] == [i["kind"] for i in w_head["items"]]
            for idx in (1, 3):
                assert [i["text"] for i in s_heads[idx]["items"]] == [i["text"] for i in heads[idx]["items"]]
            assert run.db.scalar("SELECT version FROM cases WHERE case_ref = ?", (ref,)) == version_before
            assert run.db.count("case_events", "case_ref = ?", (ref,)) == events_before
            print("headings", [h["title"] for h in heads], "| claims", claims, "| sources", sorted(ids))
            brun.screenshot(bp, "case-brief")


CANCEL_QUERY = "cancel Comfort Club membership auto-renewal"
CANCEL_TEXT = "I want to cancel my Comfort Club membership."
CANCEL_CLAIM = "Done, auto-renew is off."
MEMBERSHIP_READ = (
    step(tool(READ_MEMBERSHIP_NAME, ReadMembershipArgs().model_dump())),
    step(report(AccountReport, summary="Read the membership record.")),
)


def test_j6_membership_cancel_honest_limit(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J6, index=True) as (brun, _):
        run = brun.run
        bp = brun.open(PHONE)
        with browser_step(
            run,
            J6,
            "12a sign in and chat",
            needs=TURN_NEEDS,
            operations=("login", "startChatSession"),
            selectors=(*SIGN_IN_SELECTORS, "screen.scr1"),
        ):
            _, tid = open_chat(run, bp)
        with browser_step(
            run,
            J6,
            "12b verify with a membership question",
            needs=VERIFY_NEEDS,
            operations=("submitTurn", "listDemoInbox"),
            selectors=(*CHAT_SELECTORS, *IDENTITY_SELECTORS, "chat.block.account_card"),
        ):
            v = verify_in_chat(
                run,
                bp,
                "MHC-10001",
                "01",
                opening="What does my membership include?",
                opening_table={
                    Role.PLANNER: planner(account="membership", topic="membership"),
                    Role.CLASSIFIER: NORMAL,
                    Role.RESPONDER: responder("I need to find your record first."),
                },
                code_table={
                    Role.SPECIALIST: MEMBERSHIP_READ,
                    Role.RESPONDER: responder("Here is your membership."),
                },
                code_must={Role.SPECIALIST, Role.RESPONDER},
            )
            mem = [b for b in blocks_of(v.code_turn.body, "account_card") if b["kind"] == "membership"]
            assert mem and mem[-1]["membership"]["renewal_date"] == "2026-11-03"
            assert locate(bp.page, "chat.block.account_card").last.is_visible()
            assert (
                run.db.count(
                    "lookup_log", "turn_id = ? AND tool = ?", (v.code_turn.turn_id, READ_MEMBERSHIP_NAME)
                )
                >= 1
            )
        with browser_step(
            run,
            J6,
            "12c cancel",
            needs=HANDOFF_NEEDS,
            operations=("submitTurn",),
            selectors=(*CHAT_SELECTORS, "chat.block.handoff"),
        ):
            msg = next_message_id(run)
            kp = top_passage(run, CANCEL_QUERY)
            knowledge = {
                Role.SPECIALIST: (
                    step(tool(KB_SEARCH_NAME, KbSearchArgs(query=CANCEL_QUERY).model_dump())),
                    step(
                        report(
                            KnowledgeReport,
                            points=[
                                ReportedPoint(
                                    text="Auto-renewal can be cancelled before the renewal date.",
                                    passage_id=kp.passage_id,
                                )
                            ],
                            answered=True,
                        )
                    ),
                )
            }
            t = say(
                run,
                bp,
                CANCEL_TEXT,
                table={
                    Role.PLANNER: planner(
                        account="membership", handoff="membership_cancel", topic="membership"
                    ),
                    Role.CLASSIFIER: NORMAL,
                    Role.RESPONDER: responder(
                        "I can't switch off auto-renewal from this chat. " + CANCEL_CLAIM
                    ),
                    Role.BRIEF: brief(
                        needs=[Quote(message_id=msg, text=CANCEL_TEXT)],
                        claims=[],
                        open_decision="Switch off auto-renewal before the renewal date.",
                    ),
                },
                by_marker={KNOWLEDGE_MARKER: knowledge, ACCOUNT_MARKER: {Role.SPECIALIST: MEMBERSHIP_READ}},
                must={Role.PLANNER, Role.CLASSIFIER, Role.SPECIALIST, Role.RESPONDER, Role.BRIEF},
            )
            stored_id = run.db.scalar(
                "SELECT id FROM messages WHERE turn_id = ? AND role = 'customer'", (t.turn_id,)
            )
            assert stored_id == msg, (
                "the message id prediction is wrong (plan error: report it, keep the quote)"
            )
            text = page_text(bp.page)
            assert (
                "I can't switch off auto-renewal from this chat." in text
                and "Done, auto-renew is off" not in text
            )
            card = locate(bp.page, "chat.block.handoff").last.inner_text()
            assert "A representative will get back to you within 1 business day" in card
            c = run.db.one("SELECT * FROM cases WHERE thread_id = ?", (tid,))
            assert c["reason"] == "membership_cancel" and c["priority"] == "P3"
            assert run.db.count("promises", "case_ref = ?", (c["case_ref"],)) == 1
            trimmed = "turn_id = ? AND check_kind = 'completion' AND result = 'trimmed'"
            assert run.db.count("check_events", trimmed, (t.turn_id,)) >= 1
            assert (
                run.db.count("lookup_log", "turn_id = ? AND tool = ?", (t.turn_id, READ_MEMBERSHIP_NAME)) >= 1
            )
            assert_no_excluded(run, tid)
            row = [r for r in run.db.table_rows("customers") if r[0] == "MHC-10001"]
            assert [r for r in issued_rows("customers") if r[0] == "MHC-10001"] == row
            card_shot(brun, bp, "chat.block.handoff", "cancel-handoff")
        with browser_step(
            run,
            J6,
            "12d in the queue",
            needs=STAFF_NEEDS,
            operations=("switchRole", "getQueue"),
            selectors=("shell.role.representative", "queue.row_by_ref"),
        ):
            bp.page.set_viewport_size({"width": DESKTOP.width, "height": DESKTOP.height})
            switch_role(run, bp, "representative")
            assert "P3 · Standard" in locate_by(bp.page, "queue.row_by_ref", c["case_ref"]).inner_text()
        with browser_step(run, J6, "12e records"):
            assert_turn_records(run, tid)
