"""AEA-51 worked pairs through the HTTP API on the real graph: WP-1..WP-8, WP-4F, DANGER and NODANGER on the real app,
a disposable DB copy and a scripted model at the provider boundary. Every response is checked against the OpenAPI by the
client. Expected values come from policy texts and docs/data/worked-pairs.md.
"""

from __future__ import annotations

import itertools
import json
import time
from datetime import datetime
from typing import Any, cast
from zoneinfo import ZoneInfo

import pytest

from meridian.adapters.sqlite.repos_cases_state import DEMO_START
from meridian.domain.handoff import HandoffReason
from meridian.policy.handoff import PROMISE_TABLE, business_due
from meridian.policy.texts import TextId, render
from meridian.services.demo import format_clock
from meridian.web.routes.demo import CODE_GONE
from tests.fixtures.sqlite import ISSUED_DB
from tests.graph import worked_pair_scenarios as sc
from tests.integration.customer_api import Chat, blocks, inbox, login, open_chat, say
from tests.integration.customer_support import CustomerRun, RunOptions, open_customer_run, signals_of
from tests.journeys.support.db import sha256_file

CHI = ZoneInfo("America/Chicago")


def utc_iso(local: datetime) -> str:
    """A Chicago wall time as the stored UTC ISO string (the shape cases.due_at and promises.due_at use)."""
    return local.astimezone(ZoneInfo("UTC")).isoformat()


def when(stored: str) -> datetime:
    return datetime.fromisoformat(stored.replace("Z", "+00:00"))


def reply_text(resp: Any) -> str:
    return " ".join(str(b.get("text", "")) for b in blocks(resp))


def case_rows(run: CustomerRun, thread_id: str) -> list[dict[str, Any]]:
    return run.db.rows("SELECT * FROM cases WHERE thread_id = ? ORDER BY created_at, case_ref", (thread_id,))


def promise_for_case(run: CustomerRun, case_ref: str) -> dict[str, Any]:
    return run.db.one("SELECT * FROM promises WHERE case_ref = ?", (case_ref,))


def actions_of(run: CustomerRun, thread_id: str, kind: str | None = None) -> list[dict[str, Any]]:
    if kind is None:
        return run.db.rows("SELECT * FROM actions WHERE thread_id = ? ORDER BY id", (thread_id,))
    return run.db.rows(
        "SELECT * FROM actions WHERE thread_id = ? AND kind = ? ORDER BY id", (thread_id, kind)
    )


def checks_of(run: CustomerRun, turn_id: str, kind: str) -> list[dict[str, Any]]:
    return run.db.rows("SELECT * FROM check_events WHERE turn_id = ? AND check_kind = ?", (turn_id, kind))


def model_calls_in(run: CustomerRun, turn_id: str) -> int:
    return int(run.db.scalar("SELECT COUNT(*) FROM spend_ledger WHERE turn_id = ?", (turn_id,)))


def test_greeting_and_demo_date(request: pytest.FixtureRequest) -> None:
    """AC-5: CON-1 answers the fixed greeting (R-1) and the demo date label, with no model call."""
    with open_customer_run(request, RunOptions()) as run:
        opened = open_chat(run, login(run)).opened
        greeting = opened["greeting"]
        assert greeting["type"] == "text"
        assert greeting["text"] == render(TextId.GREETING)
        assert opened["demo_clock"]["label"] == format_clock(DEMO_START)[0]
        assert run.script.calls == ()


def test_wp1_membership_stale_twin(request: pytest.FixtureRequest) -> None:
    """AC-6: knowledge only; the archive twin never reaches the customer; the scripted $149 is removed by R-46."""
    with open_customer_run(request, RunOptions()) as run:
        result = sc.wp1(run)
        turn_id = result.turn_ids[0]
        text = reply_text(result.responses[0])
        assert sc.ARCHIVE_PRICE not in text
        assert "15%" in text
        assert not actions_of(run, result.thread_id)  # no identity action, no case_opened
        assert not case_rows(run, result.thread_id)
        lookups = run.db.rows("SELECT * FROM lookup_log WHERE thread_id = ?", (result.thread_id,))
        assert lookups and all(r["tool"] == "kb_search" for r in lookups)
        assert not any(p.startswith("archive/") for r in lookups for p in json.loads(r["passage_ids"]))
        cited = [src["file"] for b in blocks(result.responses[0], "text") for src in b["sources"]]
        assert cited, "the answer carries no citation"
        looked_up = {p.split("#")[0] for r in lookups for p in json.loads(r["passage_ids"])}
        assert set(cited) <= looked_up and not any(f.startswith("archive/") for f in cited)
        removals = [e for e in checks_of(run, turn_id, "fact") if e["result"] == "trimmed"]
        assert len(removals) == 1 and removals[0]["removed"] >= 1
        assert sc.ARCHIVE_PRICE not in json.dumps(removals[0])  # counts only, never the removed text
        assert run.script.problems() == ()


def test_wp2_invoice_after_code(request: pytest.FixtureRequest) -> None:
    """AC-7: locate by form; the code arrives only on CON-6; billed facts only after the code; a dispute opens P3."""
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        result = sc.wp2(run, client)
        opening, form, code, _read, dispute = result.responses
        thread_id = result.thread_id
        # nothing private before the code: no invoice lookup, no account card
        first_read = run.db.rows(
            "SELECT id FROM lookup_log WHERE thread_id = ? AND tool = 'read_invoices' ORDER BY id",
            (thread_id,),
        )
        assert first_read, "the invoice was read after the code"
        code_turn = result.turn_ids[2]
        before_code = run.db.rows(
            "SELECT * FROM lookup_log WHERE thread_id = ? AND turn_id IN (?, ?)",
            (thread_id, *result.turn_ids[:2]),
        )
        assert before_code == []
        assert not blocks(opening, "account_card") and not blocks(form, "account_card")
        # the code is shown on the inbox only
        chat = Chat(run=run, client=client, thread_id=thread_id, opened={})
        digits = [m["code"] for m in inbox(chat) if m.get("code")]
        assert digits
        assert all(d not in json.dumps([r.json() for r in result.responses]) for d in digits)
        verified = actions_of(run, thread_id, "verified")
        assert len(verified) == 1 and verified[0]["turn_id"] == code_turn
        card = blocks(code, "account_card")[0]
        assert card["invoice"]["invoice_id"] == "INV-204411"
        amounts = {line["description"]: line["amount"]["amount_cents"] for line in card["invoice"]["lines"]}
        assert sorted(amounts.values()) == [
            8900,
            14400,
            24500,
        ]  # as billed: the $144 dispatch line, never $149
        assert card["invoice"]["total"]["amount_cents"] == 47800
        # dispute: P3 billing_dispute with the policy promise and a reference
        [case] = case_rows(run, thread_id)
        assert (case["reason"], case["priority"]) == ("billing_dispute", "P3")
        promise = promise_for_case(run, case["case_ref"])
        assert promise["text"] == PROMISE_TABLE["R26.unstaffed"]
        assert promise["due_at"] == utc_iso(business_due(DEMO_START, 1))
        handoff = blocks(dispute, "handoff")[0]
        assert handoff["reference"] == case["case_ref"]
        assert run.script.problems() == ()


def test_wp3_booking_and_one_slot_concurrency(request: pytest.FixtureRequest) -> None:
    """AC-8: windows 56, 42, 58 and no Saturday; slot 56 booked; a racing second chat gets SLOT_TAKEN."""
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        result = sc.wp3_concurrent(run, client)
        windows = blocks(result.responses[2], "slot_card")[0]
        ids = [w["slot_id"] for day in windows["days"] for w in day["windows"]]
        assert ids == ["56", "42", "58"]
        assert all(
            day["date"] == "2026-10-19" for day in windows["days"]
        )  # Monday; there is no Saturday window
        picks = result.extra["picks"]
        booked = [k for k, r in picks.items() if blocks(r, "confirmation")]
        taken = [
            k for k, r in picks.items() if any(b.get("code") == "SLOT_TAKEN" for b in blocks(r, "error"))
        ]
        assert len(booked) == 1 and len(taken) == 1, {
            k: [b["type"] for b in blocks(r)] for k, r in picks.items()
        }
        confirmation = blocks(picks[booked[0]], "confirmation")[0]
        assert "waived" in confirmation["fee_line"] and "member" in confirmation["fee_line"]
        slot = run.db.one("SELECT status FROM appointment_slots WHERE slot_id = 56")
        assert slot["status"] != "open"
        booked_rows = run.db.rows(
            "SELECT * FROM actions WHERE kind = 'booked' AND record_id LIKE '%' ORDER BY id"
        )
        assert len(booked_rows) == 1
        assert run.db.count("appointments", "slot_id = 56 AND status = 'scheduled'") == 1
        assert sha256_file(ISSUED_DB) == run.env.issued_sha256_before


def _fee_bearing_checks(run: CustomerRun, result: sc.ScenarioResult, *, change: str) -> dict[str, Any]:
    """The assertions WP-4 and its cancel leg share: the write is refused and a P2 staff request opens."""
    thread_id = result.thread_id
    original = result.extra["original"]
    row = run.db.one(
        "SELECT status, slot_id FROM appointments WHERE appointment_id = ?", (result.extra["appointment_id"],)
    )
    assert (row["status"], row["slot_id"]) == ("scheduled", original["slot_id"])  # the row never changed
    assert not actions_of(run, thread_id, "moved") and not actions_of(run, thread_id, "cancelled")
    [case] = case_rows(run, thread_id)
    assert (case["reason"], case["priority"]) == ("fee_bearing_change", "P2")
    assert case["due_at"] == utc_iso(
        datetime(2026, 10, 16, 12, 0, tzinfo=CHI)
    )  # the window start, 12:00 today
    promise = promise_for_case(run, case["case_ref"])
    assert promise["text"] == PROMISE_TABLE["R26.unstaffed"]
    assert promise["due_at"] == utc_iso(datetime(2026, 10, 19, 19, 0, tzinfo=CHI))  # Mon Oct 19, 7:00 pm
    extra = json.loads(promise["extra_lines"])
    assert any("can't promise" in line for line in extra) and any("Phone support" in line for line in extra)
    block = blocks(result.responses[-1], "change_request")[0]
    assert block["change"] == change
    assert "$49" in block["fee_line"] and "stays" in block["original_stays_line"]
    assert block["extra_lines"] == extra
    code_turn = result.turn_ids[-1]
    removed = [e for e in checks_of(run, code_turn, "completion") if e["result"] == "trimmed"]
    assert len(removed) == 1 and removed[0]["removed"] >= 1
    return case


def test_wp4_fee_bearing_never_written(request: pytest.FixtureRequest) -> None:
    """AC-9: move refused (fee_bearing); row unchanged; P2 with the promise and extra lines; 'I've moved it' removed."""
    with open_customer_run(request, RunOptions()) as run:
        result = sc.wp4(run)
        case = _fee_bearing_checks(run, result, change="move")
        text = reply_text(result.responses[-1])
        assert "moved it" not in text and "A representative will look" in text
        change = json.loads(case["change_request_json"])
        assert change["appointment_id"] == result.extra["appointment_id"] and change["change"] == "move"
        assert run.script.problems() == ()


def test_wp4_fee_bearing_cancel_never_written(request: pytest.FixtureRequest) -> None:
    """AC-35: the cancel leg: refused, rows unchanged, P2 staff request, the appointment stays, 0 cancelled actions."""
    with open_customer_run(request, RunOptions()) as run:
        result = sc.wp4_cancel(run)
        _fee_bearing_checks(run, result, change="cancel")
        assert "cancelled it" not in reply_text(result.responses[-1])
        assert run.db.count("actions", "kind = 'cancelled'") == 0


def test_wp4f_move_carries_to_next_turn(request: pytest.FixtureRequest) -> None:
    """AC-10: a fee-free move commits with actions(moved); 'Yes, please.' keeps 'Yes, it's moved: Monday ...'."""
    with open_customer_run(request, RunOptions()) as run:
        result = sc.wp4f(run)
        moved = actions_of(run, result.thread_id, "moved")
        assert len(moved) == 1
        appointment = run.db.one(
            "SELECT slot_id FROM appointments WHERE appointment_id = ?", (result.extra["appointment_id"],)
        )
        assert appointment["slot_id"] == result.extra["target_slot"]
        last = result.responses[-1]
        assert sc.MOVED_SENTENCE in reply_text(last)
        followup_turn = result.turn_ids[-1]
        assert all(
            e["removed"] == 0 for e in checks_of(run, followup_turn, "completion")
        )  # kept: settled has it
        settled_kinds = [a["kind"] for a in last.json()["settled"]["actions"]]
        assert "moved" in settled_kinds
        assert not case_rows(run, result.thread_id)


def test_wp5_co_alarm_safety_first(request: pytest.FixtureRequest) -> None:
    """AC-11: the KB instruction first and word for word, 0 model calls, P0 safety, no promise time, left open."""
    with open_customer_run(request, RunOptions()) as run:
        result = sc.wp5(run)
        first, second = result.responses
        safety = blocks(first)[0]
        assert safety["type"] == "safety" and safety["fixed_text"] is True
        assert safety["steps"][0].startswith("Leave the home immediately and call 911 or your gas utility")
        assert safety["case_priority"] == "P0"
        assert model_calls_in(run, result.turn_ids[0]) == 0
        assert (
            run.db.one("SELECT model_calls FROM turns WHERE turn_id = ?", (result.turn_ids[0],))[
                "model_calls"
            ]
            == 0
        )
        [case] = case_rows(run, result.thread_id)
        assert (case["reason"], case["priority"], case["due_at"]) == ("safety", "P0", None)
        assert promise_for_case(run, case["case_ref"])["due_at"] is None  # no follow-up time promised
        assert "leave a number" in safety["contact_line"]  # the contact line comes after, as an offer
        assert case["lifecycle"] not in (
            "resolved",
            "closed_unresolved",
        )  # a detail-free next turn leaves it open
        assert len(case_rows(run, result.thread_id)) == 1
        assert second.status_code == 200


def test_wp6_burning_three_branches(request: pytest.FixtureRequest) -> None:
    """AC-12: burning card first; yes -> WP-5 text + P0; not_sure -> cautious text, P1 + OD4.danger_review; no -> urgent
    booking offer and a P2 burning_ruled_out request."""
    with open_customer_run(request, RunOptions()) as run:
        yes = sc.wp6_yes(run)
        assert blocks(yes.responses[0])[0]["type"] == "burning_check"
        assert blocks(yes.responses[1])[0]["steps"][0].startswith("Leave the home immediately")
        [case] = case_rows(run, yes.thread_id)
        assert (case["reason"], case["priority"]) == ("safety", "P0")

        unsure = sc.wp6_not_sure(run)
        cautious = blocks(unsure.responses[1])[0]
        assert cautious["type"] == "conditional_safety" and "leave the home immediately" in cautious["text"]
        [case] = case_rows(run, unsure.thread_id)
        assert (case["reason"], case["priority"], case["rule_id"]) == (
            "burning_unclear",
            "P1",
            "R7.burning_unsure",
        )
        assert promise_for_case(run, case["case_ref"])["policy_row"] == "OD4.danger_review"

        no = sc.wp6_no(run)
        offered = blocks(no.responses[-2], "slot_card")
        assert offered, "the urgent booking offer is a slot card"
        [case] = case_rows(run, no.thread_id)
        assert (case["reason"], case["priority"]) == ("burning_ruled_out", "P2")
        assert blocks(no.responses[-1], "confirmation")
        assert run.script.problems() == ()


def test_wp6_no_due_is_booked_window_start(request: pytest.FixtureRequest) -> None:
    with open_customer_run(request, RunOptions()) as run:
        no = sc.wp6_no(run)
        [case] = case_rows(run, no.thread_id)
        booked = run.db.one(
            "SELECT s.slot_date, s.window FROM actions a "
            "JOIN appointment_slots s ON s.slot_id = a.record_id WHERE a.thread_id = ? AND a.kind = 'booked'",
            (no.thread_id,),
        )
        start = datetime.fromisoformat(f"{booked['slot_date']}T{booked['window'][:5]}:00").replace(tzinfo=CHI)
        assert case["due_at"] == utc_iso(start)


def test_wp6_no_unverified_still_opens_p2(request: pytest.FixtureRequest) -> None:
    with open_customer_run(request, RunOptions()) as run:
        no = sc.wp6_no(run, verified_first=False)
        [case] = case_rows(run, no.thread_id)
        assert (case["reason"], case["priority"]) == ("burning_ruled_out", "P2")


def test_wp7_refund_handoff_and_brief(request: pytest.FixtureRequest) -> None:
    """AC-13 and PA-5: refund P3, the exact promise and 'I can't promise an outcome.', due Tue Oct 20 7:00 pm, the
    reference appended by code; the brief's amount is removed and a fabricated quote never reaches the stored brief."""
    with open_customer_run(request, RunOptions()) as run:
        result = sc.wp7(run)
        [response] = result.responses
        [case] = case_rows(run, result.thread_id)
        assert (case["reason"], case["priority"]) == ("refund", "P3")
        promise = promise_for_case(run, case["case_ref"])
        assert promise["text"] == PROMISE_TABLE["R26.refund"]
        assert promise["due_at"] == utc_iso(datetime(2026, 10, 20, 19, 0, tzinfo=CHI))
        assert render(TextId.PROMISE_REFUND_NO_OUTCOME) in json.loads(promise["extra_lines"])
        handoff = blocks(response, "handoff")[0]
        assert handoff["reference"] == case["case_ref"] and handoff["variant"] == "refund"
        assert handoff["followup_chooser"] is not None  # the email-or-phone question
        brief_row = run.db.one("SELECT brief_json FROM case_briefs WHERE case_ref = ?", (case["case_ref"],))
        stored = brief_row["brief_json"]
        assert result.extra["refund_amount"] not in stored  # the scripted amount is in no record: removed
        quote_events = [
            e for e in checks_of(run, result.turn_ids[0], "brief_quote") if e["result"] == "trimmed"
        ]
        assert len(quote_events) == 1 and quote_events[0]["removed"] >= 1
        assert (
            result.extra["sentinel_quote"] not in stored
        )  # PA-5: a fabricated quote never reaches the stored brief
        fact_events = [
            e for e in checks_of(run, result.turn_ids[0], "brief_fact") if e["result"] == "trimmed"
        ]
        assert fact_events, "the unsupported amount in the open decision should be flagged"
        assert run.script.problems() == ()


def test_wp8_no_false_completion(request: pytest.FixtureRequest) -> None:
    """AC-14: code first; the renewal date read with a lookup row; 'Done, auto-renew is off' removed; P3 request."""
    with open_customer_run(request, RunOptions()) as run:
        result = sc.wp8(run)
        thread_id = result.thread_id
        assert actions_of(run, thread_id, "verified")
        lookups = run.db.rows(
            "SELECT * FROM lookup_log WHERE thread_id = ? AND tool = 'read_membership'", (thread_id,)
        )
        assert lookups, "the renewal date was read with a lookup row"
        final = result.responses[-1]
        assert "auto-renew is off" not in reply_text(final)
        assert blocks(final, "account_card")[0]["membership"]["renewal_date"] == "2026-11-03"
        removed = [e for e in checks_of(run, result.turn_ids[-1], "completion") if e["result"] == "trimmed"]
        assert len(removed) == 1
        [case] = case_rows(run, thread_id)
        assert (case["reason"], case["rule_id"]) == ("membership_cancel", "D4.membership_cancel")
        assert promise_for_case(run, case["case_ref"])["text"] == PROMISE_TABLE["R26.unstaffed"]
        assert blocks(final, "handoff")[0]["reference"] == case["case_ref"]


def test_danger_emergency_first(request: pytest.FixtureRequest) -> None:
    """AC-15: DANGER through the raise-only classifier: the emergency number first, P1 danger, nothing before it."""
    with open_customer_run(request, RunOptions()) as run:
        result = sc.danger(run)
        [response] = result.responses
        assert blocks(response)[0]["type"] == "emergency_line"
        assert len(blocks(response)) == 1
        turn = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (result.turn_ids[0],))
        assert (turn["gate_result"], turn["outcome"]) == ("danger", "safety_reply")
        [case] = case_rows(run, result.thread_id)
        assert (case["reason"], case["priority"]) == ("danger", "P1")
        assert promise_for_case(run, case["case_ref"])["policy_row"] == "OD4.danger_review"
        assert {c.role.value for c in run.script.calls} == {"classifier", "planner"}


def test_nodanger_and_model_fallbacks(request: pytest.FixtureRequest) -> None:
    """AC-16: NODANGER is not raised; a classifier error-in-200 leaves the rules standing; the planner falls back once;
    when both planners fail the customer gets an ai_failure handoff (degrade_reason model_error)."""
    with open_customer_run(request, RunOptions()) as run:
        normal = sc.nodanger(run)
        turn = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (normal.turn_ids[0],))
        assert turn["danger_raised"] == 0 and not case_rows(run, normal.thread_id)

        broken = sc.nodanger_classifier_fails(run)
        [event] = checks_of(run, broken.turn_ids[0], "classifier")
        assert event["result"] == "fallback"
        assert not case_rows(run, broken.thread_id)
        assert any(sig["name"] == "classifier_fallback" for sig in signals_of(run.logs))

        fell_back = sc.planner_fallback(run)
        turn = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (fell_back.turn_ids[0],))
        assert turn["planner_fallback_used"] == 1 and turn["outcome"] == "acted"

        failed = sc.planners_fail(run)
        turn = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (failed.turn_ids[0],))
        assert (turn["outcome"], turn["degrade_reason"]) == ("degraded_handoff", "model_error")
        [case] = case_rows(run, failed.thread_id)
        assert (case["reason"], case["priority"]) == ("ai_failure", "P3")
        assert HandoffReason.AI_FAILURE.value == case["reason"]
        assert run.script.problems() == ()


def _normalised_blocks(resp: Any) -> str:
    """The reply blocks with the ids and times that legitimately differ replaced, for byte comparison."""
    cleaned = [{**b, "block_id": "<id>", "at": "<at>"} for b in resp.json()["blocks"]]
    return json.dumps(cleaned, sort_keys=True)


def test_wf1_identity_failure_reveals_nothing(request: pytest.FixtureRequest) -> None:
    """AC-34: no match and a real name with another phone give byte-identical blocks; no account value leaks."""
    with open_customer_run(request, RunOptions()) as run:
        result = sc.identity_failures(run)
        cases = result.extra["cases"]
        unknown, wrong_phone = cases["no_match"][1], cases["real_name_other_phone"][1]
        assert _normalised_blocks(unknown) == _normalised_blocks(wrong_phone)
        row = run.db.one("SELECT * FROM customers WHERE customer_id = 'MHC-10001'")
        seen = json.dumps([r.json() for rs in cases.values() for r in rs[1:]])
        for value in (
            row["phone"],
            str(row["email"]),
            str(row["service_address"]),
            row["membership_renewal_date"],
        ):
            assert value not in seen
        for label in ("no_match", "real_name_other_phone"):
            ident = run.db.one(
                "SELECT status, customer_id FROM identity_threads WHERE thread_id = ?",
                (result.extra["threads"][label],),
            )
            assert ident["status"] == "not_verified" and ident["customer_id"] is None
        locked = run.db.one(
            "SELECT status FROM identity_threads WHERE thread_id = ?",
            (result.extra["threads"]["wrong_codes"],),
        )
        assert locked["status"] == "locked"
        assert not actions_of(run, result.thread_id, "verified")


def test_wf1_three_wrong_codes_open_identity_unverified(request: pytest.FixtureRequest) -> None:
    with open_customer_run(request, RunOptions()) as run:
        result = sc.identity_failures(run)
        [case] = case_rows(run, result.thread_id)
        assert (case["reason"], case["priority"]) == ("identity_unverified", "P3")


def test_estimate_books_comfort_advisor(request: pytest.FixtureRequest) -> None:
    """AC-36: only estimate slots are offered; the booking names the Comfort Advisor."""
    with open_customer_run(request, RunOptions()) as run:
        result = sc.estimate(run)
        card = blocks(result.responses[2], "slot_card")[0]
        slot_ids = [int(w["slot_id"]) for day in card["days"] for w in day["windows"]]
        assert slot_ids
        kinds = {
            run.db.one("SELECT service_type FROM appointment_slots WHERE slot_id = ?", (i,))["service_type"]
            for i in slot_ids
        }
        assert kinds == {"estimate"}
        confirmation = blocks(result.responses[-1], "confirmation")[0]
        assert confirmation["technician"].startswith("Comfort Advisor")
        booked = actions_of(run, result.thread_id, "booked")
        assert len(booked) == 1


def test_wf1_quick_checks_offered_never_required(request: pytest.FixtureRequest) -> None:
    """AC-37: quick checks are offered once on a non-urgent repair booking; declining books straight away; none on
    WP-5 or DANGER; the offer never marks the conversation resolved."""
    with open_customer_run(request, RunOptions()) as run:
        result = sc.quick_checks(run)
        offer, declined, booked = result.responses[-3:]
        assert len(blocks(offer, "quick_checks")) == 1
        offer_turn = result.extra["offer_turn"]
        offered_lookups = run.db.rows(
            "SELECT * FROM lookup_log WHERE turn_id = ? AND tool = 'kb_search'", (offer_turn,)
        )
        assert len(offered_lookups) == 1  # the one qc- search, never a model-requested one
        assert any(
            p.startswith("faq/troubleshooting_before_you_call.md")
            for p in json.loads(offered_lookups[0]["passage_ids"])
        )
        assert result.extra["conversation_after_offer"] != "ai_resolved"
        assert not blocks(declined, "quick_checks")  # offered once
        assert blocks(declined, "slot_card")
        assert blocks(booked, "confirmation")
        assert run.db.count("lookup_log", "thread_id = ? AND tool = 'kb_search'", (result.thread_id,)) == 1

        co = sc.wp5(run)
        urgent = sc.urgent_no_heat(run)
        for none in (co, urgent):
            assert not any(blocks(r, "quick_checks") for r in none.responses)
            assert run.db.count("lookup_log", "thread_id = ?", (none.thread_id,)) == 0


def test_wf1_no_source_and_warranty(request: pytest.FixtureRequest) -> None:
    """AC-38: an off-corpus question gets a no-current-source reply and a person offer with 0 citations; the warranty
    after the code names the install date and the term sentence word for word."""
    from meridian.agent.tools.account import WARRANTY_TERM_SENTENCE

    with open_customer_run(request, RunOptions()) as run:
        silent = sc.no_source(run)
        [response] = silent.responses
        assert blocks(response, "no_info")[0]["person_key"] is True
        assert not any(b["sources"] for b in blocks(response, "text"))
        assert not blocks(response, "source_chip")
        assert reply_text(response).count("I don't have that information") >= 1

        owner = sc.warranty(run)
        card = blocks(owner.responses[-1], "account_card")[0]
        assert card["kind"] == "warranty" and card["warranty"]["install_date"] == "2025-11-30"
        assert card["warranty"]["sentence"] == WARRANTY_TERM_SENTENCE


def test_wf1_staffing_and_no_live_queue(request: pytest.FixtureRequest) -> None:
    """AC-39: staffing is nobody_online after start and nothing over the dev set is live-queued; after CON-7 a handoff is
    live-queued with the R26.staffed text."""
    from tests.integration.customer_api import set_staffing

    with open_customer_run(request, RunOptions()) as run:
        results = sc.run_dev_set(run)
        client = run.clients[0]
        opened = open_chat(run, client).opened
        assert opened["staffing"]["mode"] == "nobody_online"
        assert run.db.count("cases", "lifecycle = 'live_queued'") == 0
        assert run.db.count("promises", "live_queued = 1") == 0
        assert all(r.status_code == 200 for res in results for r in res.responses)
        set_staffing(client, "simulated_on_shift")
        live = sc.wp7(run, client)
        [case] = case_rows(run, live.thread_id)
        assert case["lifecycle"] == "live_queued"
        promise = promise_for_case(run, case["case_ref"])
        assert promise["policy_row"] == "R26.staffed" and promise["text"] == PROMISE_TABLE["R26.staffed"]
        assert promise["live_queued"] == 1


def test_wf3_code_expiry_follows_demo_clock(request: pytest.FixtureRequest) -> None:
    """AC-40: CON-8 plus_1h expires the code on the demo clock (seconds of wall time); CON-6 lists it expired without
    the code; entering it answers CODE_EXPIRED."""
    from tests.integration.customer_api import (
        advance_clock,
        newest_code,
        say,
        send_code,
        send_form,
        switch_role,
    )

    with open_customer_run(request, RunOptions(with_clock=True)) as run:
        client = run.login().client
        chat = open_chat(run, client)
        run.steps.set_step(
            {
                sc.Role.CLASSIFIER: sc.NORMAL,
                sc.Role.PLANNER: sc.planner(account="invoice", topic="billing"),
                sc.Role.RESPONDER: sc.responder("I need to find your record first."),
            }
        )
        opened = say(chat, "What is my invoice for?")
        row = run.db.one("SELECT * FROM customers WHERE customer_id = 'MHC-10001'")
        run.steps.set_step({sc.Role.RESPONDER: sc.responder("Thanks, I sent a code.")})
        sent = send_form(
            chat,
            blocks(opened, "locate_prompt")[0]["card_id"],
            {"name": str(row["name"]), "phone": str(row["phone"])},
        )
        code = newest_code(chat)
        started = time.monotonic()
        switch_role(client, "supervisor")
        advance_clock(client, "plus_1h")
        switch_role(client, "customer")
        assert time.monotonic() - started < 60  # wall seconds, not an hour
        messages = inbox(chat)
        expired = [m for m in messages if m["status"] == "expired"]
        assert expired and all(m["code"] == CODE_GONE and code not in json.dumps(m) for m in expired)
        run.steps.set_step({sc.Role.RESPONDER: sc.responder("That code has expired.")})
        late = send_code(chat, sc.card_id_of(sent, "code_prompt"), code)
        assert any(b.get("code") == "CODE_EXPIRED" for b in blocks(late, "error"))
        assert blocks(late, "code_prompt")[0]["state"] == "expired"
        assert not actions_of(run, chat.thread_id, "verified")


def test_three_task_turn_under_recursion_limit(request: pytest.FixtureRequest) -> None:
    """AC-29: one message with a membership question, an invoice question and a booking completes under limit 25."""
    with open_customer_run(request, RunOptions()) as run:
        result = sc.three_tasks(run)
        final = result.responses[-1]
        turn = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (result.turn_ids[-1],))
        assert turn["outcome"] in ("answered", "acted") and turn["degrade_reason"] is None
        assert sorted(json.loads(turn["specialists_run"])) == ["account", "knowledge", "scheduling"]
        tools = {
            r["tool"]
            for r in run.db.rows("SELECT tool FROM lookup_log WHERE thread_id = ?", (result.thread_id,))
        }
        assert {"kb_search", "read_invoices", "find_windows"} <= tools
        assert not checks_of(run, result.turn_ids[-1], "brake")
        assert final.json()["notice"] is None
        assert run.script.problems() == ()
        assert run.container.get(sc.Key("compiled_graph")).config["recursion_limit"] == 25


def test_restart_between_write_and_checkpoint(request: pytest.FixtureRequest, tmp_path: Any) -> None:
    """AC-26: the business write commits, the checkpoint write is dropped, the process restarts: the next turn still sees
    the move, because `settled` is read from the actions table and not from the checkpoint."""
    import shutil

    from tests.integration.customer_support import (
        customer_environment,
        fastembed_offline,
        require_index,
        serve_customer_run,
    )
    from tests.journeys.support.client import JourneyClient
    from tests.journeys.support.logtap import tap_logs
    from tests.journeys.support.server import socket_guard

    options = RunOptions()
    with socket_guard() as guard, tap_logs() as logs, fastembed_offline():
        with customer_environment(index_dir=require_index(), eval_key=None) as env:
            data = env.data_dir
            backup = tmp_path / "checkpoints-before-the-move"
            backup.mkdir()
            kwargs: dict[str, Any] = {"guard": guard, "logs": logs, "eval_key": None}
            # server 1: sign in, ask to move, see the windows; the checkpoint now holds the open task
            with serve_customer_run(request, env, options, **kwargs) as s1:
                client = s1.login().client
                chat, _, card, target, row = sc.wp4f_prepare(s1, client)
                cookie = client.cookie()
                assert cookie
                thread_id = chat.thread_id
                appointment_id = int(row["appointment_id"])
            for path in data.glob("checkpoints.sqlite*"):
                shutil.copy2(path, backup / path.name)
            assert (backup / "checkpoints.sqlite").exists()

            def reconnect(run: CustomerRun) -> Chat:
                again = JourneyClient(run.base_url)
                run.clients.append(again)
                again._http.cookies.set("mhc_session", cookie)
                return Chat(run=run, client=again, thread_id=thread_id, opened={})

            # server 2: the pick commits the move
            with serve_customer_run(request, env, options, **kwargs) as s2:
                picked = sc.wp4f_pick(s2, reconnect(s2), card, target, appointment_id)
                assert blocks(picked, "confirmation")
                assert len(actions_of(s2, thread_id, "moved")) == 1
            # the checkpoint write is dropped: put the pre-pick checkpoint files back
            for path in data.glob("checkpoints.sqlite*"):
                path.unlink()
            for path in backup.iterdir():
                shutil.copy2(path, data / path.name)
            # server 3: the follow-up turn still sees the move
            with serve_customer_run(request, env, options, **kwargs) as s3:
                follow = sc.wp4f_followup(s3, reconnect(s3), str(row["service_type"]), appointment_id)
                turn_id = follow.json()["turn_id"]
                assert sc.MOVED_SENTENCE in reply_text(follow)
                assert all(e["removed"] == 0 for e in checks_of(s3, turn_id, "completion"))
                stored = [a["kind"] for a in actions_of(s3, thread_id)]
                assert (
                    [a["kind"] for a in follow.json()["settled"]["actions"]].count("moved")
                    == stored.count("moved")
                    == 1
                )
    assert guard.blocked == []


def _prefix(call: Any) -> str:
    """The stable part of a request: the system text for a choice, the system prefix for the other two."""
    request = call.request
    return str(request.system if hasattr(request, "system") else request.system_prefix)


def test_turn_two_plus_prompt_and_state(request: pytest.FixtureRequest) -> None:
    """AC-27 (rule context-management-multi-turn 3): the stable prefix of every role is identical and complete on the
    first, second and fifth turns that reach it; the window obeys its caps; no tool output is in messages or the window;
    'what about Monday?' resolves against the open booking task."""
    long_text = "My question is about the plan. " * 61  # about 1,900 characters
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        chat = open_chat(run, client)
        know = {
            sc.Role.CLASSIFIER: sc.NORMAL,
            sc.Role.PLANNER: sc.planner(knowledge="yes", topic="membership"),
        }
        first, second = sc.kb_steps(run, sc.WP1_QUERY, "Members save 15% on repairs.")
        passage_text = sc.top_passage(run, sc.WP1_QUERY).text
        texts = [
            "Do members get a discount on repairs?",
            "Do members get a discount on repairs?",
            long_text + "Do members get a discount on repairs?",
            "Do members get a discount on repairs?",
        ]
        marks: list[int] = []
        for text in texts:
            marks.append(len(run.script.calls))
            run.steps.set_step(
                {
                    **know,
                    sc.Role.SPECIALIST: (first, second),
                    sc.Role.RESPONDER: sc.responder("Members save 15% on repairs."),
                }
            )
            say(chat, text)
        marks.append(len(run.script.calls))
        # turn 5: a booking message; the planner opens the booking task, which waits on identity
        run.steps.set_step(
            {
                sc.Role.CLASSIFIER: sc.NORMAL,
                sc.Role.PLANNER: sc.BOOKING_PLAN,
                sc.Role.RESPONDER: sc.responder("I need to find your record first."),
            }
        )
        opening = say(chat, "I need to book a repair")
        marks.append(len(run.script.calls))
        per_turn = [run.script.calls[a:b] for a, b in itertools.pairwise(marks)]
        for role in (sc.Role.PLANNER, sc.Role.CLASSIFIER, sc.Role.RESPONDER):
            prefixes = [
                {_prefix(c) for c in calls if c.role is role}
                for calls in (per_turn[0], per_turn[1], per_turn[4])
            ]
            assert all(len(p) == 1 for p in prefixes), role
            assert prefixes[0] == prefixes[1] == prefixes[2], f"the {role.value} prefix changed between turns"
            assert next(iter(prefixes[0])).strip()
        specialist_prefixes = [
            {_prefix(c) for c in calls if c.role is sc.Role.SPECIALIST} for calls in per_turn[:4]
        ]
        assert (
            all(len(p) == 1 for p in specialist_prefixes)
            and len({next(iter(p)) for p in specialist_prefixes}) == 1
        )

        # the window: caps on turns, characters per line and in total
        responder_calls = [c for c in run.script.calls if c.role is sc.Role.RESPONDER]
        window = str(cast(Any, responder_calls[3].request).user)
        recent = window.split("RECENT CHAT:\n", 1)[1].split("\n\nLATEST CUSTOMER MESSAGE:", 1)[0].split("\n")
        assert len(recent) <= 20
        assert max(len(line) for line in recent) <= 600 + len("customer: ")
        assert sum(len(line) for line in recent) <= 8_000
        assert any(len(line) > 500 for line in recent), (
            "the 1,900-character message should still appear, cut to 600"
        )
        # no tool output in messages or in any model-facing window
        marker = passage_text.strip().splitlines()[0][:40]
        assert marker
        stored = " ".join(
            r["text"] for r in run.db.rows("SELECT text FROM messages WHERE thread_id = ?", (chat.thread_id,))
        )
        assert marker not in stored
        for call in run.script.calls:
            if call.role in (sc.Role.PLANNER, sc.Role.RESPONDER, sc.Role.CLASSIFIER):
                assert marker not in json.dumps(
                    call.request.model_dump(exclude={"output_model"}), default=str
                )

        # verify through the form and code, then the follow-up resolves against the open task
        find = sc.scheduling_steps(
            sc.tool(
                sc.TOOLS["find_windows"],
                sc.FindWindowsArgs(service_type="hvac_repair").model_dump(mode="json"),
            )
        )
        sc.locate_and_code(
            run,
            chat,
            "MHC-10001",
            opening,
            after_code={sc.Role.SPECIALIST: find, sc.Role.RESPONDER: sc.responder("Here are the windows.")},
        )
        monday = sc.scheduling_steps(
            sc.tool(
                sc.TOOLS["find_windows"],
                sc.FindWindowsArgs(service_type="hvac_repair", wanted_text="Monday").model_dump(mode="json"),
            )
        )
        run.steps.set_step(
            {
                sc.Role.CLASSIFIER: sc.NORMAL,
                sc.Role.PLANNER: sc.planner(topic="booking"),
                sc.Role.SPECIALIST: monday,
                sc.Role.RESPONDER: sc.responder("Here are the Monday windows."),
            }
        )
        mark = len(run.script.calls)
        follow = say(chat, "what about Monday?")
        planner_call = next(c for c in run.script.calls[mark:] if c.role is sc.Role.PLANNER)
        assert cast(Any, planner_call.request).state["flags"]["open_task"] == "scheduling"
        cards = blocks(follow, "slot_card")
        assert cards and any(day["date"] == "2026-10-19" for day in cards[0]["days"])  # a Monday
        assert run.script.problems() == ()
