"""J-9 (slice plan section 0a), AEA-51 steps: the failure states a customer can reach through the real server: a model
error, the spend cap, the turn deadline, a busy server and the per-thread rate limit. Each step asserts the notice or
blocks the customer sees and the stored turn row. Real app, real graph and DB copy; scripted model at the provider
boundary. (tests/journeys/j9/test_aea_40.py has its own integrated test, skipped for its owner to unskip.)"""

from __future__ import annotations

import threading
import uuid
from typing import Any

import pytest

from meridian.config import SONNET_MODEL
from meridian.domain.common import CallRecord, ProviderFailureKind, Role
from meridian.domain.turn import TurnIds
from tests.fakes import ScriptedFailure, provider_call
from tests.graph import worked_pair_scenarios as sc
from tests.integration.customer_api import blocks, open_chat, say
from tests.integration.customer_support import CustomerRun, RunOptions, Stall, open_customer_run

pytestmark = pytest.mark.journey

J9 = "J-9"
NEEDS = (
    "login_sessions",
    "session_service",
    "demo_service",
    "demo_clock",
    "reply_composer",
    "turn_service",
    "run_graph",
    "handoff_service",
    "rate_limiter",
    "ledger",
)
OPS = ("login", "startChatSession", "submitTurn")
QUESTION = "Do members get a discount on repairs?"


def stored(run: CustomerRun, response: Any) -> dict[str, Any]:
    return run.db.one("SELECT * FROM turns WHERE turn_id = ?", (response.json()["turn_id"],))


def kb_turn(run: CustomerRun, **overrides: Any) -> None:
    entries: dict[Any, Any] = {
        Role.PLANNER: sc.planner(knowledge="yes", topic="membership"),
        Role.CLASSIFIER: sc.NORMAL,
        Role.SPECIALIST: sc.kb_steps(run, sc.WP1_QUERY, "Members save 15% on repairs."),
        Role.RESPONDER: sc.responder("Members save 15% on repairs."),
    }
    entries.update(overrides)
    run.steps.set_step(entries)


def test_j9_failure_states(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    with open_customer_run(request, RunOptions(deadline_s=3), monkeypatch=monkeypatch) as run:
        client = run.login().client
        with run.step(J9, "1 a model error is a handoff offer, not a crash", needs=NEEDS, operations=OPS):
            chat = open_chat(run, client)
            kb_turn(
                run, **{Role.SPECIALIST: ScriptedFailure(kind=ProviderFailureKind.SERVER, http_status=500)}
            )
            failed = say(chat, QUESTION)
            row = stored(run, failed)
            assert (row["outcome"], row["degrade_reason"]) == ("degraded_handoff", "model_error")
            assert blocks(failed, "handoff") or blocks(failed, "failure_offer")
            print(f"step 1: outcome={row['outcome']} reason={row['degrade_reason']}")
        with run.step(J9, "3 a slow turn times out with a way forward", needs=NEEDS, operations=OPS):
            # the turn deadline is 3 s in this run: the test replaced the container's Limits factory (PD-9)
            slow_chat = open_chat(run, client)
            kb_turn(run, **{Role.SPECIALIST: Stall(4.0)})
            slow = say(slow_chat, QUESTION)
            body = slow.json()
            assert (
                body["notice"]["code"] == "TURN_TIMEOUT"
                and body["notice"]["retry_turn_id"] == body["turn_id"]
            )
            assert body["notice"]["actions"] == ["try_again", "talk_to_person"]
            row = stored(run, slow)
            assert (row["outcome"], row["degrade_reason"]) == ("degraded_handoff", "timeout")
            print(f"step 3: notice={body['notice']['code']} actions={body['notice']['actions']}")
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        with run.step(J9, "2 the spend cap stops the model, not the person", needs=NEEDS, operations=OPS):
            chat = open_chat(run, client)
            ids = TurnIds.model_validate(
                {
                    "thread_id": chat.thread_id,
                    "turn_id": str(uuid.uuid4()),
                    "request_id": str(uuid.uuid4()),
                    "run_tag": "live",
                    "run_id": None,
                    "agent_version": run.settings.agent_version,
                }
            )
            call = provider_call(provider="anthropic", model=SONNET_MODEL, cost_usd=30.0)
            run.container.get(sc.Key("ledger")).record(
                CallRecord.from_provider(call, role=Role.RESPONDER, attempt=1), ids
            )
            mark = len(run.script.calls)
            capped = say(chat, QUESTION)
            assert capped.json()["notice"]["code"] == "SPEND_CAP_REACHED"
            assert run.steps.calls_since(mark) == ()
            row = stored(run, capped)
            assert (row["outcome"], row["degrade_reason"]) == ("degraded_handoff", "spend_cap")
            print(f"step 2: notice={capped.json()['notice']['code']} model_calls=0")

    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        with run.step(J9, "4 a busy server says so", needs=NEEDS, operations=OPS):
            chats = [open_chat(run, client) for _ in range(31)]
            kb_turn(run, **{Role.RESPONDER: Stall(2.0)})
            barrier = threading.Barrier(31)
            answers: dict[int, Any] = {}

            def go(index: int) -> None:
                barrier.wait()
                answers[index] = say(chats[index], QUESTION)

            threads = [threading.Thread(target=go, args=(i,)) for i in range(31)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=120)
            assert len(answers) == 31
            busy = [
                r for r in answers.values() if r.json()["notice"] and r.json()["notice"]["code"] == "BUSY"
            ]
            assert busy, "at least one of 31 simultaneous turns should be answered BUSY (30 may run at once)"
            row = stored(run, busy[0])
            assert (row["outcome"], row["degrade_reason"]) == ("degraded_handoff", "rate_limit")
            print(f"step 4: busy_answers={len(busy)} of 31")
        with run.step(J9, "5 the per-thread rate limit says slow down", needs=NEEDS, operations=OPS):
            chat = open_chat(run, client)
            # a safety message is never rate limited, so the turns are ordinary talk turns that call the scripted model
            run.steps.set_step(
                {
                    Role.CLASSIFIER: sc.NORMAL,
                    Role.PLANNER: sc.planner(),
                    Role.RESPONDER: sc.responder("You're welcome."),
                }
            )
            # the bucket holds 20 turns and refills over a minute, so the limit lands a little after the 20th turn
            last = None
            sent = 0
            for turn_number in range(1, 61):
                sent = turn_number
                last = say(chat, "ok thanks")
                if last.json()["notice"]:
                    break
            assert last is not None and sent > 20 and last.json()["notice"]["code"] == "RATE_LIMITED"
            row = stored(run, last)
            assert (row["outcome"], row["degrade_reason"]) == ("degraded_handoff", "rate_limit")
            print(f"step 5: notice={last.json()['notice']['code']} on turn {sent}")
