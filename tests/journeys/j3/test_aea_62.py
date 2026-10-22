"""AEA-62, J-3 (`J-BOOK`) in Chrome on the production build: WP-3 booking to confirmation, reload with a follow-up turn
that remembers the booking (R-45, WP-4F turn-4 shape), and an old card that writes nothing. Level: integrated with a
scripted model. Blocked steps name their owner and are never passed.

This file also holds the identity helpers (verification in the chat) that j2, j6 and j8 use; j2 imports them
function-locally because this file imports j2 at module level.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass, field
from typing import Any

import pytest

from meridian.agent.tools.account import READ_INVOICES_NAME, ReadInvoicesArgs
from meridian.agent.tools.scheduling import BOOK_VISIT_NAME, FIND_WINDOWS_NAME, BookVisitArgs, FindWindowsArgs
from meridian.domain.common import InvoiceId, Role
from meridian.domain.specialists import AccountReport, SchedulingReport
from meridian.policy.texts import TextId, render
from tests.fixtures.sqlite import ISSUED_DB
from tests.journeys.browser.network import ApiExchange
from tests.journeys.browser.pages import PHONE, BrowserPage, BrowserRun
from tests.journeys.browser.selectors import locate, locate_by, locate_in
from tests.journeys.browser.steps import SIGN_IN_SELECTORS, browser_step
from tests.journeys.j1.test_aea_57 import TURN_NEEDS
from tests.journeys.j2.test_aea_62 import (
    CHAT_SELECTORS,
    IDENTITY_SELECTORS,
    NORMAL,
    VERIFY_NEEDS,
    Factory,
    Table,
    Turn,
    assert_turn_records,
    blocks_of,
    browser_run,
    card_shot,
    expect_turn,
    open_chat,
    page_post,
    page_text,
    planner,
    report,
    responder,
    say,
    second_tab,
    step,
    tool,
)
from tests.journeys.support.db import sha256_file
from tests.journeys.support.run import JourneyRun

pytest_plugins = ("tests.journeys.browser.plugin",)
pytestmark = pytest.mark.journey

J3 = "J-3"


# ---------------------------------------------------------------------------------------------------------------
# AEA-62 identity helpers (shared)
# ---------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Verified:  # values for the AC-16 scans; never printed
    customer_id: str
    opening: Turn
    code_turn: Turn
    inbox: ApiExchange  # the listDemoInbox exchange (AC-17, WF-3)
    phone: str = field(repr=False)
    code: str = field(repr=False)


def customer_contact(run: JourneyRun, customer_id: str) -> tuple[str, str]:
    row = run.db.one("SELECT name, phone FROM customers WHERE customer_id = ?", (customer_id,))
    return str(row["name"]), str(row["phone"])  # never printed


def submit_locate(
    run: JourneyRun,
    bp: BrowserPage,
    customer_id: str,
    *,
    previous: Turn,
    table: Table,
    must: Collection[Role],
) -> Turn:
    prompt = blocks_of(previous.body, "locate_prompt")[-1]
    assert ["name", "phone"] in prompt["field_sets"]
    card = locate(bp.page, "chat.block.locate_prompt").last
    name, phone = customer_contact(run, customer_id)

    def send() -> None:
        locate_in(card, "card.locate.name").fill(name)
        locate_in(card, "card.locate.phone").fill(phone)
        locate_in(card, "card.locate.submit").click()

    return expect_turn(run, bp, table=table, must=must, send=send)


def read_code_from_inbox(run: JourneyRun, bp: BrowserPage) -> tuple[str, ApiExchange]:
    """SCR-2 in a second tab; no screenshot while it is open. WF-3 is asserted in AC-17 only."""
    tab = second_tab(bp)
    mark = bp.net.mark()
    tab.page.goto("/demo/inbox")
    locate(tab.page, "screen.scr2").wait_for()
    ex = bp.net.wait_for(tab.page, "listDemoInbox", since=mark)
    assert ex.status == 200 and ex.body is not None
    active = [m for m in json.loads(ex.body)["messages"] if m["status"] == "active"]
    newest = max(active, key=lambda m: m["at"])
    shown = locate_in(locate(tab.page, "inbox.message.active").first, "inbox.code").inner_text().strip()
    assert shown == newest["code"], "SCR-2 shows a different code than listDemoInbox returned"
    tab.page.close()
    return shown, ex


def verify_in_chat(
    run: JourneyRun,
    bp: BrowserPage,
    customer_id: str,
    ending: str,
    *,
    opening: str,
    opening_table: Table,
    code_table: Table,
    code_must: Collection[Role],
    code_by_marker: Mapping[str, Table] | None = None,
    before_code: Callable[[], None] | None = None,
) -> Verified:
    talk: Table = {Role.PLANNER: opening_table[Role.PLANNER], Role.CLASSIFIER: NORMAL}
    t1 = say(run, bp, opening, table=opening_table, must={Role.PLANNER, Role.CLASSIFIER})
    assert blocks_of(t1.body, "locate_prompt")
    sent: Table = {**talk, Role.RESPONDER: responder("Thanks, I sent a code.")}
    t2 = submit_locate(run, bp, customer_id, previous=t1, table=sent, must=set())
    assert blocks_of(t2.body, "code_prompt")
    card = locate(bp.page, "chat.block.code_prompt").last
    assert f"Code sent to the phone on record, ending in {ending}" in card.inner_text()
    if before_code is not None:
        before_code()
    code, inbox = read_code_from_inbox(run, bp)

    def send() -> None:
        locate_in(card, "card.code.input").fill(code)
        locate_in(card, "card.code.submit").click()

    t3 = expect_turn(
        run, bp, table={**talk, **code_table}, by_marker=code_by_marker, must=code_must, send=send
    )
    assert render(TextId.VERIFIED) in locate(bp.page, "chat.entry.assistant").last.inner_text()
    _, phone = customer_contact(run, customer_id)
    return Verified(customer_id, t1, t3, inbox, phone, code)


BILLING_TEXT = "I got an invoice, INV-204411, and I'm not sure what it's for."
BILLING_OPENING: Table = {
    Role.PLANNER: planner(account="invoice", topic="billing"),
    Role.CLASSIFIER: NORMAL,
    Role.RESPONDER: responder("I can explain that invoice once I've confirmed your account."),
}
INVOICE_REPLY = (
    "Invoice INV-204411 has three lines as billed: a diagnostic visit, $89.00; a contactor replacement, $245.00; "
    "and an after-hours dispatch, $144.00. The total is $478.00, due November 1, 2026."
)
BILLING_CODE: Table = {
    Role.SPECIALIST: (
        step(
            tool(
                READ_INVOICES_NAME,
                ReadInvoicesArgs(invoice_number=InvoiceId("INV-204411")).model_dump(mode="json"),
            )
        ),
        step(
            report(
                AccountReport,
                summary="Invoice INV-204411 lists a diagnostic visit, a contactor replacement and an after-hours dispatch.",
            )
        ),
    ),
    Role.RESPONDER: responder(INVOICE_REPLY),
}
INVOICE_VALUES = ("$478.00", "$245.00", "$144.00", "$89.00")


def billing_through_code(run: JourneyRun, bp: BrowserPage) -> Verified:
    def nothing_yet() -> None:
        text = page_text(bp.page)
        assert [s for s in INVOICE_VALUES if s in text] == [], (
            "an invoice value is on the page before the code"
        )

    return verify_in_chat(
        run,
        bp,
        "MHC-10002",
        "02",
        opening=BILLING_TEXT,
        opening_table=BILLING_OPENING,
        code_table=BILLING_CODE,
        code_must={Role.SPECIALIST, Role.RESPONDER},
        before_code=nothing_yet,
    )


# ---------------------------------------------------------------------------------------------------------------
# J-3 booking (WP-3)
# ---------------------------------------------------------------------------------------------------------------
BOOK_TEXT = (
    "I need to schedule a service call. My AC isn't cooling. This Saturday if possible, 4 to 7, after work."
)
BOOKED_REPLY = "You're booked for Monday, October 19, 8:00 am to 12:00 pm with Marta Kowalski."
FOLLOW_REPLY = "Yes, you're booked: Monday, October 19, 8:00 am to 12:00 pm with Marta Kowalski."
WANTED = "This Saturday if possible, 4 to 7, after work."
BOOK_SELECTORS = (
    "chat.block.slot_card",
    "card.slot.window_by_id",
    "card.slot.continue",
    "chat.block.confirmation",
)


@dataclass
class Booking:
    thread_id: str
    booking: Turn
    appointment_id: int
    counts: dict[str, Any]


def counts_of(run: JourneyRun, tid: str) -> dict[str, Any]:
    return {
        "appointments": run.db.count("appointments", "customer_id = ?", ("MHC-10001",)),
        "booked": run.db.count("actions", "thread_id = ? AND kind = 'booked'", (tid,)),
        "slot56": run.db.scalar("SELECT status FROM appointment_slots WHERE slot_id = 56"),
        "slot58": run.db.scalar("SELECT status FROM appointment_slots WHERE slot_id = 58"),
    }


def book_slot_56(brun: BrowserRun) -> Booking:
    run = brun.run
    bp = brun.open(PHONE)
    with browser_step(
        run,
        J3,
        "6a sign in and chat",
        needs=TURN_NEEDS,
        operations=("login", "startChatSession"),
        selectors=(*SIGN_IN_SELECTORS, "screen.scr1"),
    ):
        _, tid = open_chat(run, bp)
    with browser_step(
        run,
        J3,
        "6b ask, locate, code",
        needs=VERIFY_NEEDS,
        operations=("submitTurn", "listDemoInbox"),
        selectors=(*CHAT_SELECTORS, *IDENTITY_SELECTORS, "chat.block.slot_card"),
    ):
        windows = FindWindowsArgs(service_type="hvac_repair", wanted_text=WANTED).model_dump(mode="json")
        v = verify_in_chat(
            run,
            bp,
            "MHC-10001",
            "01",
            opening=BOOK_TEXT,
            opening_table={
                Role.PLANNER: planner(scheduling="book_new", topic="booking"),
                Role.CLASSIFIER: NORMAL,
                Role.RESPONDER: responder("I can look for a time once I've confirmed your account."),
            },
            code_table={
                Role.SPECIALIST: (
                    step(tool(FIND_WINDOWS_NAME, windows)),
                    step(
                        report(
                            SchedulingReport,
                            appointment_id=0,
                            wanted_time="Saturday 4 to 7 pm",
                            note="AC not cooling",
                        )
                    ),
                ),
                Role.RESPONDER: responder(
                    "There's no Saturday evening window, so here are the earliest repair windows."
                ),
            },
            code_must={Role.SPECIALIST, Role.RESPONDER},
        )
        assert not blocks_of(v.opening.body, "safety") and not blocks_of(v.opening.body, "emergency_line")
        assert run.db.count("cases", "thread_id = ?", (tid,)) == 0
        card = blocks_of(v.code_turn.body, "slot_card")[-1]
        mon = {w["slot_id"]: w for d in card["days"] if d["date"] == "2026-10-19" for w in d["windows"]}
        assert {"56", "42", "58"} <= set(mon)
        assert (
            mon["56"]["technician"] == "Marta Kowalski" and mon["56"]["window_label"] == "8:00 am – 12:00 pm"
        )
        assert mon["42"]["technician"] == "Ray Mendoza" and mon["58"]["technician"] == "Marta Kowalski"
        assert not [d for d in card["days"] if d["date"] == "2026-10-17"], "a Saturday window is offered"
        shown = locate(bp.page, "chat.block.slot_card").last.inner_text()
        assert all(t in shown for t in ("8:00 am – 12:00 pm", "Marta Kowalski", "Ray Mendoza"))
        print("offered windows:", [(k, w["window_label"], w["technician"]) for k, w in mon.items()])
    with browser_step(
        run,
        J3,
        "6c pick 8-12",
        needs=TURN_NEEDS,
        operations=("submitTurn",),
        selectors=(*BOOK_SELECTORS, "settled.visit"),
    ):
        card_el = locate(bp.page, "chat.block.slot_card").last

        def send() -> None:
            locate_by(card_el, "card.slot.window_by_id", "56").click()
            locate_in(card_el, "card.slot.continue").click()

        book = BookVisitArgs(slot_id=56, issue="AC not cooling").model_dump()
        booking = expect_turn(
            run,
            bp,
            table={
                Role.PLANNER: planner(scheduling="book_new", topic="booking"),
                Role.CLASSIFIER: NORMAL,
                Role.SPECIALIST: (
                    step(tool(BOOK_VISIT_NAME, book)),
                    step(report(SchedulingReport, appointment_id=0, wanted_time="", note="booked")),
                ),
                Role.RESPONDER: responder(BOOKED_REPLY),
            },
            must={Role.RESPONDER},
            send=send,
        )
        assert render(TextId.BOOKED) in page_text(bp.page)
        conf = locate(bp.page, "chat.block.confirmation").last.inner_text()
        assert all(t in conf for t in ("Your visit", "Booked", "8:00 am → 12:00 pm", "Marta Kowalski"))
        assert "October 19" in conf or "Oct 19" in conf
        api = blocks_of(booking.body, "confirmation")[-1]
        assert api["date"] == "2026-10-19" and api["fee_line"] in conf and "waived" in api["fee_line"].lower()
        assert re.search(r"\$89(\.00)?\s+(is\s+)?due|amount due", page_text(bp.page), re.I) is None
        assert "Marta Kowalski" in locate(bp.page, "settled.visit").inner_text()
        visit = booking.body["settled"]["visit"]
        assert visit["appointment_id"] == api["appointment_id"] and visit["status"] == "booked"
        assert run.db.scalar("SELECT status FROM appointment_slots WHERE slot_id = 56") != "open"
        assert (
            run.db.count(
                "appointments", "customer_id = ? AND slot_id = ? AND status = 'scheduled'", ("MHC-10001", 56)
            )
            == 1
        )
        booked = run.db.rows("SELECT * FROM actions WHERE thread_id = ? AND kind = 'booked'", (tid,))
        assert len(booked) == 1 and booked[0]["turn_id"] == booking.turn_id
        assert run.db.count("lookup_log", "thread_id = ? AND tool = ?", (tid, FIND_WINDOWS_NAME)) >= 1
        assert run.db.count("cases", "thread_id = ?", (tid,)) == 0
        before, after = run.env.issued_sha256_before, sha256_file(ISSUED_DB)
        assert after == before, "the issued DB changed"
        counts = counts_of(run, tid)
        print(f"booked actions {len(booked)}; counts {counts}; issued hashes equal")
        card_shot(brun, bp, "chat.block.confirmation", "confirmation-card")
    return Booking(tid, booking, int(api["appointment_id"]), counts)


def reload_thread(bp: BrowserPage, tid: str) -> ApiExchange:
    mark = bp.net.mark()
    bp.page.reload()
    read = bp.net.wait_for(bp.page, "getChatThread", since=mark)
    assert read.status == 200 and read.path.endswith("/" + tid)
    assert "startChatSession" not in bp.net.operations(mark)
    return read


def test_j3_book_to_confirmation(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J3) as (brun, _):
        b = book_slot_56(brun)
        with browser_step(brun.run, J3, "6d records"):
            assert_turn_records(brun.run, b.thread_id)


def test_j3_reload_and_follow_up_remembers(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J3) as (brun, _):
        run = brun.run
        b = book_slot_56(brun)
        bp, tid = brun.pages[0], b.thread_id
        with browser_step(
            run,
            J3,
            "7a reload",
            needs=TURN_NEEDS,
            operations=("getChatThread",),
            selectors=(
                "chat.entry",
                "chat.block.text",
                "chat.entry.customer",
                "chat.block.confirmation",
                "settled.visit",
            ),
        ):
            read = reload_thread(bp, tid)
            data = json.loads(read.body or b"{}")
            first = locate_in(locate(bp.page, "chat.entry").first, "chat.block.text").first
            assert first.inner_text().strip() == render(TextId.GREETING)
            assert data["turns"][0]["turn_id"] == "greeting"
            assert locate(bp.page, "chat.entry.customer").count() >= 3
            assert locate(bp.page, "chat.block.confirmation").count() >= 1
            assert "Marta Kowalski" in locate(bp.page, "settled.visit").inner_text()
            assert data["settled"]["visit"]["appointment_id"] == b.appointment_id
        with browser_step(
            run, J3, "7b follow-up", needs=TURN_NEEDS, operations=("submitTurn",), selectors=CHAT_SELECTORS
        ):
            t = say(
                run,
                bp,
                "Yes, please.",
                table={
                    Role.PLANNER: planner(topic="booking"),
                    Role.CLASSIFIER: NORMAL,
                    Role.RESPONDER: responder(FOLLOW_REPLY),
                },
                must={Role.PLANNER, Role.CLASSIFIER, Role.RESPONDER},
            )
            last = locate_in(locate(bp.page, "chat.entry.assistant").last, "chat.block.text").first
            assert last.inner_text().strip() == FOLLOW_REPLY
            c = run.db.one(
                "SELECT * FROM check_events WHERE turn_id = ? AND check_kind = 'completion'", (t.turn_id,)
            )
            assert c["result"] == "pass" and c["removed"] == 0
            assert run.db.count("check_events", "turn_id = ? AND result = 'trimmed'", (t.turn_id,)) == 0
            booked_id = int(
                run.db.scalar("SELECT record_id FROM actions WHERE thread_id = ? AND kind = 'booked'", (tid,))
            )
            assert t.body["settled"]["visit"]["appointment_id"] == booked_id
            assert t.body["settled"]["identity"]["status"] == "verified"
            assert counts_of(run, tid) == b.counts
            print(", ".join(bp.net.operations()), "|", FOLLOW_REPLY, "|", b.counts, counts_of(run, tid))


def test_j3_old_card_writes_nothing(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J3) as (brun, _):
        run = brun.run
        b = book_slot_56(brun)
        bp, tid = brun.pages[0], b.thread_id
        with browser_step(run, J3, "8z reload", needs=TURN_NEEDS, operations=("getChatThread",)):
            reload_thread(bp, tid)
        with browser_step(run, J3, "8a replay booking turn", needs=TURN_NEEDS, operations=("submitTurn",)):
            assert b.booking.exchange.request_body is not None
            r = page_post(bp, f"/api/chat/sessions/{tid}/turns", json.loads(b.booking.exchange.request_body))
            assert r["status"] == 200 and json.loads(r["text"])["turn_id"] == b.booking.turn_id
            assert counts_of(run, tid) == b.counts
        with browser_step(
            run,
            J3,
            "8b old card",
            needs=TURN_NEEDS,
            operations=("submitTurn",),
            selectors=("chat.block.slot_card", "card.slot.window_by_id", "card.slot.continue"),
        ):
            card = locate(bp.page, "chat.block.slot_card").first
            w = locate_by(card, "card.slot.window_by_id", "58")
            if not w.is_enabled() or w.get_attribute("aria-disabled") == "true":
                print("old card disabled after reload")
            else:

                def send() -> None:
                    w.click()
                    locate_in(card, "card.slot.continue").click()

                expect_turn(
                    run,
                    bp,
                    table={
                        Role.PLANNER: planner(topic="booking"),
                        Role.CLASSIFIER: NORMAL,
                        Role.RESPONDER: responder("Your visit stays on Monday morning."),
                    },
                    must=set(),
                    send=send,
                )
            after = counts_of(run, tid)
            assert after == b.counts and after["slot58"] == "open" and after["booked"] == 1
            print("counts before", b.counts, "after", after)
