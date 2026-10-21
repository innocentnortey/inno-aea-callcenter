"""AEA-51 failure paths through the real graph and the real ledger: spend caps, brakes, model and tool errors, the turn
deadline, an idempotent resend, no DB transaction across a model call, and CON-4/CON-5 never limited."""

from __future__ import annotations

import json
import uuid
from typing import Any

import pytest

from meridian.config import SONNET_MODEL
from meridian.domain.common import CallRecord, ProviderFailureKind, Role
from meridian.domain.turn import TurnIds
from meridian.policy.texts import TextId, render
from meridian.web.container import Key
from tests.fakes import ScriptedFailure, provider_call
from tests.graph import worked_pair_scenarios as sc
from tests.integration.customer_api import blocks, open_chat, say, submit
from tests.integration.customer_support import CustomerRun, RunOptions, Stall, open_customer_run, write_probe


def seed_day_total(run: CustomerRun, thread_id: str, usd: float = 30.0) -> None:
    """Spend the day's cap through the real LedgerService (PD-10)."""
    call = provider_call(provider="anthropic", model=SONNET_MODEL, cost_usd=usd)
    ids = TurnIds.model_validate(
        {
            "thread_id": thread_id,
            "turn_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),
            "run_tag": "live",
            "run_id": None,
            "agent_version": run.settings.agent_version,
        }
    )
    run.container.get(Key[Any]("ledger")).record(
        CallRecord.from_provider(call, role=Role.RESPONDER, attempt=1), ids
    )


def turn_of(run: CustomerRun, response: Any) -> dict[str, Any]:
    return run.db.one("SELECT * FROM turns WHERE turn_id = ?", (response.json()["turn_id"],))


def ask_kb(run: CustomerRun, *, responder_entry: Any = None, **overrides: Any) -> None:
    entries: dict[Any, Any] = {
        Role.PLANNER: sc.planner(knowledge="yes", topic="membership"),
        Role.CLASSIFIER: sc.NORMAL,
        Role.RESPONDER: responder_entry
        if responder_entry is not None
        else sc.responder("Members save 15% on repairs."),
    }
    entries.update(overrides)
    if Role.SPECIALIST not in entries:
        entries[Role.SPECIALIST] = sc.kb_steps(run, sc.WP1_QUERY, "Members save 15% on repairs.")
    run.steps.set_step(entries)


def test_spend_caps(request: pytest.FixtureRequest) -> None:
    """AC-24: at the day's cap a text turn gets SPEND_CAP_REACHED with no model call and CON-4 still opens a case; a
    scripted provider spend cap trips that provider's circuit and the next turn makes no Anthropic call."""
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        chat = open_chat(run, client)
        seed_day_total(run, chat.thread_id)
        run.steps.set_step({})
        mark = len(run.script.calls)
        capped = say(chat, "Do members get a discount on repairs?")
        assert capped.json()["notice"]["code"] == "SPEND_CAP_REACHED"
        assert run.steps.calls_since(mark) == ()
        row = turn_of(run, capped)
        assert (row["outcome"], row["degrade_reason"], row["trace_export"]) == (
            "degraded_handoff",
            "spend_cap",
            "off",
        )
        person = client.call(
            "POST",
            f"/api/chat/sessions/{chat.thread_id}/handoff",
            operation_id="requestPerson",
            body={"turn_id": str(uuid.uuid4())},
        )
        assert person.status_code == 200 and person.json()["result"] == "case_created"
        assert run.db.count("cases", "thread_id = ?", (chat.thread_id,)) == 1

    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        chat = open_chat(run, client)
        ask_kb(run, responder_entry=ScriptedFailure(kind=ProviderFailureKind.PROVIDER_SPEND_CAP))
        tripped = say(chat, "Do members get a discount on repairs?")
        row = turn_of(run, tripped)
        assert (row["outcome"], row["degrade_reason"], row["trace_export"]) == (
            "degraded_handoff",
            "spend_cap",
            "off",
        )
        ledger = run.container.get(Key[Any]("ledger"))
        assert ledger.open_circuits() == ("anthropic",)
        mark = len(run.script.calls)
        ask_kb(run)
        again = say(chat, "Do members get a discount on repairs?")
        row = turn_of(run, again)
        assert (row["outcome"], row["degrade_reason"]) == ("degraded_handoff", "spend_cap")
        used = {c.role for c in run.steps.calls_since(mark)}
        assert not used & {
            Role.SPECIALIST,
            Role.RESPONDER,
            Role.BRIEF,
            Role.PLANNER_FALLBACK,
        }  # no Anthropic call
        assert used <= {Role.PLANNER, Role.CLASSIFIER}


def test_spend_cap_safety_still_answered(request: pytest.FixtureRequest) -> None:
    """AC-24 (safety half): at the cap a carbon monoxide message still gets the instruction and a P0 case, with no model
    call. (AEA-40-F1 merged: the deterministic safety gate runs before the cap check.)"""
    with open_customer_run(request, RunOptions()) as run:
        chat = open_chat(run, run.login().client)
        seed_day_total(run, chat.thread_id)
        run.steps.set_step({})
        mark = len(run.script.calls)
        response = say(chat, sc.CO_TEXT)
        first = blocks(response)[0]
        assert first["type"] == "safety" and first["steps"][0].startswith("Leave the home immediately")
        assert response.json()["notice"] is None
        assert run.steps.calls_since(mark) == ()
        [case] = run.db.rows("SELECT * FROM cases WHERE thread_id = ?", (chat.thread_id,))
        assert (case["reason"], case["priority"]) == ("safety", "P0")


def _check_degraded(run: CustomerRun, response: Any, reason: str, *, thread_id: str) -> dict[str, Any]:
    row = turn_of(run, response)
    assert (row["outcome"], row["degrade_reason"]) == ("degraded_handoff", reason)
    conversation = run.db.one("SELECT outcome FROM conversations WHERE thread_id = ?", (thread_id,))
    assert conversation["outcome"] != "ai_resolved"  # a degraded conversation is never counted as resolved
    return row


def test_brake_and_deadline(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-25: a brake, a model error, a tool error and the deadline each end as a degraded handoff with its reason; a
    resent turn after a committed write does not repeat the write."""
    with open_customer_run(request, RunOptions()) as run:
        chat = open_chat(run, run.login().client)
        queries = ("member discount", "plan price", "plan perks")
        ask_kb(
            run,
            **{
                Role.SPECIALIST: tuple(
                    sc.step(sc.tool(sc.TOOLS["kb_search"], {"query": q}, f"call-{i}"))
                    for i, q in enumerate(queries)
                )
            },
        )
        braked = say(chat, "Do members get a discount on repairs?")
        _check_degraded(run, braked, "brake", thread_id=chat.thread_id)
        assert blocks(braked, "handoff") or blocks(braked, "failure_offer")
        assert run.db.count("cases", "thread_id = ? AND reason = 'ai_failure'", (chat.thread_id,)) == 1

        failing = open_chat(run, chat.client)
        ask_kb(run, **{Role.SPECIALIST: ScriptedFailure(kind=ProviderFailureKind.SERVER, http_status=500)})
        errored = say(failing, "Do members get a discount on repairs?")
        _check_degraded(run, errored, "model_error", thread_id=failing.thread_id)
        assert errored.json()["settled"] is not None

        # idempotency: the pick turn commits a move; the same turn_id answers the same body and writes once
        move_chat, _, card, target, row = sc.wp4f_prepare(run, chat.client)
        app_id = int(row["appointment_id"])
        run.steps.set_step(
            {
                Role.SPECIALIST: sc.scheduling_steps(
                    sc.tool(
                        sc.TOOLS["move"],
                        sc.MoveVisitArgs(appointment_id=app_id, new_slot_id=target).model_dump(),
                    )
                ),
                Role.RESPONDER: sc.responder("Done, your visit is moved."),
            }
        )
        turn_id = str(uuid.uuid4())
        payload = {"kind": "choice", "card_id": card, "option": str(target)}
        first = submit(move_chat, payload, turn_id=turn_id)
        again = submit(move_chat, payload, turn_id=turn_id)
        assert first.json() == again.json()
        assert run.db.count("actions", "thread_id = ? AND kind = 'moved'", (move_chat.thread_id,)) == 1

    # (c) a tool error: a booking refused by the tool (a slot nobody showed) leaves the scheduling task failed without a
    # provider failure, which is a tool_error degrade. An empty index never raises to the customer either (below).
    with open_customer_run(request, RunOptions()) as run:
        booking, _shown, card = sc.wp3_prepare(run, run.login().client)
        run.steps.set_step(
            {
                Role.SPECIALIST: sc.scheduling_steps(
                    sc.tool(
                        sc.TOOLS["book"],
                        sc.BookVisitArgs(slot_id=999_999, issue="AC not cooling").model_dump(),
                    )
                ),
                Role.RESPONDER: sc.responder("I could not complete that booking."),
            }
        )
        refused = sc.pick(booking, card, "56")
        row = _check_degraded(run, refused, "tool_error", thread_id=booking.thread_id)
        assert row["tool_calls"] == 1
        assert blocks(refused, "handoff") or blocks(refused, "failure_offer")
        assert not run.db.count("actions", "thread_id = ? AND kind = 'booked'", (booking.thread_id,))

    with open_customer_run(request, RunOptions(index="empty")) as run:
        chat = open_chat(run, run.login().client)
        ask_kb(
            run,
            **{
                Role.SPECIALIST: sc.no_source_steps(sc.WP1_QUERY),
                Role.RESPONDER: sc.responder("I don't have that."),
            },
        )
        silent = say(chat, "Do members get a discount on repairs?")
        assert silent.status_code == 200 and blocks(silent, "no_info")[0]["person_key"] is True
        assert (
            run.db.one("SELECT result_seen FROM lookup_log WHERE thread_id = ?", (chat.thread_id,))[
                "result_seen"
            ]
            == "failed"
        )

    # (d) the deadline: a 3-second turn deadline and a specialist call that stalls for 4 seconds. The gateway enforces the
    # budget when the next call starts, so the responder that follows is halted with the deadline reason.
    with open_customer_run(request, RunOptions(deadline_s=3), monkeypatch=monkeypatch) as run:
        chat = open_chat(run, run.login().client)
        ask_kb(run, **{Role.SPECIALIST: Stall(4.0)})
        slow = say(chat, "Do members get a discount on repairs?")
        body = slow.json()
        assert body["notice"]["code"] == "TURN_TIMEOUT" and body["notice"]["retry_turn_id"] == body["turn_id"]
        assert [b["code"] for b in blocks(slow, "notice")] == ["TURN_TIMEOUT"]
        assert body["notice"]["actions"] == ["try_again", "talk_to_person"]
        row = turn_of(run, slow)
        assert (row["outcome"], row["degrade_reason"]) == ("degraded_handoff", "timeout")
        conversation = run.db.one("SELECT outcome FROM conversations WHERE thread_id = ?", (chat.thread_id,))
        assert conversation["outcome"] != "ai_resolved"


def test_no_transaction_across_model_calls(request: pytest.FixtureRequest) -> None:
    """AC-28 (DO-3 section 2.3 rule 1): a write probe with busy_timeout 0 succeeds inside every scripted model call of
    the dev set, so no DB transaction is open across a model call."""
    with open_customer_run(request, RunOptions()) as run:
        failures: list[str] = []
        run.steps.probe = write_probe(run.env.db_path, failures)
        sc.run_dev_set(run)
        calls = len(run.script.calls)
        print(f"model calls probed: {calls}")
        assert calls > 0
        assert failures == []


def test_person_request_never_limited(request: pytest.FixtureRequest) -> None:
    """AC-45: with the spend cap reached and every read bucket exhausted, CON-4 still opens a case and CON-5 is never
    answered 429."""
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        chat = open_chat(run, client)
        seed_day_total(run, chat.thread_id)
        statuses = []
        for _ in range(300):
            statuses.append(client.call("GET", "/api/demo/staffing", operation_id="getStaffing").status_code)
            if statuses[-1] == 429:
                break
        assert statuses[-1] == 429, "the read bucket never ran out"
        person = client.call(
            "POST",
            f"/api/chat/sessions/{chat.thread_id}/handoff",
            operation_id="requestPerson",
            body={"turn_id": str(uuid.uuid4())},
        )
        assert person.status_code == 200 and person.json()["result"] == "case_created"
        [case] = run.db.rows("SELECT * FROM cases WHERE thread_id = ?", (chat.thread_id,))
        assert run.db.count("promises", "case_ref = ?", (case["case_ref"],)) == 1
        saved = client.call(
            "PUT",
            f"/api/chat/sessions/{chat.thread_id}/follow-up",
            operation_id="saveFollowUp",
            body={"channel": "email", "destination": "general", "window": "any"},
        )
        assert saved.status_code == 200
        assert render(TextId.GREETING)  # the texts module is the single source of customer sentences
        assert json.dumps(saved.json())
