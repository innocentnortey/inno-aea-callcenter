"""J-9 (slice plan section 0a), AEA-40's part: the TURN_TIMEOUT, BUSY and RATE_LIMITED notices reach the user.

Level today: `mock-tested`. Real routes, real middleware and a real SQLite working copy through a TestClient; the
`run_graph`, `SpendGuard` and `DemoService` siblings are doubles; no server process, no browser, no model adapter.
The integrated tests (real server) are blocked by AEA-30 (demo clock, DemoService) and AEA-51 (reply composer,
graph) and are reported by the harness as blocked.
Each test asserts what the user sees (the notice and its actions) and what was stored (conversation, messages, turn).
"""

from __future__ import annotations

import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from meridian.web.deps import RATE_LIMITER
from meridian.web.middleware import LimitScope
from tests.api.chat_support import REFUSED, chat_env, post_turn
from tests.api.web_shell_support import assert_matches, make_client
from tests.journeys.support.run import JourneyRun
from tests.services.chat_doubles import (
    BlockingRunGraph,
    DeadlineRunGraph,
    ScriptedRunGraph,
    make_cmd,
    new_turn_id,
    text_payload,
)
from tests.services.chat_storage import (
    Collected,
    count_rows,
    customer_messages,
    messages_of,
    seed_thread,
    turn_row,
)

pytestmark = pytest.mark.journey

TURN_NEEDS = (
    "login_sessions",
    "session_service",
    "demo_service",
    "demo_clock",
    "reply_composer",
    "turn_service",
    "run_graph",
)


def test_j9_turn_timeout_notice_is_shown_and_retry_runs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """failure/refusal: a turn past its deadline shows TURN_TIMEOUT (try again, talk to a person); the retry runs."""
    holder: dict[str, DeadlineRunGraph] = {}
    graph = ScriptedRunGraph(lambda i, c: holder["deadline"](i, c))
    with chat_env(monkeypatch, tmp_path, graph=graph) as env, make_client(env.app) as client:
        holder["deadline"] = DeadlineRunGraph(env.store.uow)
        thread = seed_thread(env.store.uow, env.demo_session)
        turn_id = new_turn_id()

        first = post_turn(client, env.token, thread, text_payload("book the tune-up"), turn_id)

        assert first.status_code == 200
        assert_matches(first, "submitTurn")
        notice = first.json()["notice"]
        assert notice["code"] == "TURN_TIMEOUT"
        assert notice["actions"] == ["try_again", "talk_to_person"]
        assert notice["retry_turn_id"] == str(turn_id)
        assert [w["kind"] for w in first.json()["settled"]["actions"]] == ["booked"]
        row = turn_row(env.store, turn_id)
        assert (row.status, row.outcome, row.degrade_reason) == ("failed", "degraded_handoff", "timeout")
        assert len(customer_messages(env.store, thread, turn_id)) == 1
        assert [
            m for m in messages_of(env.store, thread) if m.role == "assistant" and m.turn_id == turn_id
        ] == []

        retry = post_turn(client, env.token, thread, text_payload("book the tune-up"), turn_id)  # "Try again"

        assert retry.status_code == 200 and retry.json()["notice"] is None
        assert turn_row(env.store, turn_id).status == "completed"
        assert len(customer_messages(env.store, thread, turn_id)) == 1


def test_j9_busy_notice_when_30_turns_are_running(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure/refusal: with 30 turns in flight the next customer gets BUSY and the person key; no model call."""
    blocking = BlockingRunGraph()
    with chat_env(monkeypatch, tmp_path, graph=blocking) as env, make_client(env.app) as client:
        threads = [seed_thread(env.store.uow, env.demo_session) for _ in range(31)]
        collected = Collected()
        workers = []
        for thread in threads[:30]:
            cmd = make_cmd(thread, text_payload("hello"), demo_session=env.demo_session)
            worker = threading.Thread(
                target=collected.run, args=(lambda c=cmd: env.turn_service.run_turn(c),)
            )
            worker.start()
            workers.append(worker)
        try:
            for _ in range(30):
                assert blocking.entered.acquire(timeout=10)
            turn_id = new_turn_id()

            busy = post_turn(client, env.token, threads[30], text_payload("one more"), turn_id)

            assert busy.status_code == 200, busy.text
            assert_matches(busy, "submitTurn")
            notice = busy.json()["notice"]
            assert notice["code"] == "BUSY" and notice["actions"] == ["talk_to_person"]
            assert blocking.calls == 30
            row = turn_row(env.store, turn_id)
            assert (row.outcome, row.degrade_reason) == ("degraded_handoff", "rate_limit")
        finally:
            blocking.release.set()
            for worker in workers:
                worker.join(timeout=10)
        assert not collected.errors


def test_j9_rate_limited_notice_then_normal_turn(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure/refusal: a refused rate-limit verdict shows RATE_LIMITED with the person key, never a 429; later turns run."""
    with chat_env(monkeypatch, tmp_path) as env, make_client(env.app) as client:
        thread = seed_thread(env.store.uow, env.demo_session)
        env.verdict.verdict = REFUSED
        turn_id = new_turn_id()

        refused = post_turn(client, env.token, thread, text_payload("hello"), turn_id)

        assert refused.status_code == 200
        assert_matches(refused, "submitTurn")
        assert refused.json()["notice"]["code"] == "RATE_LIMITED"
        assert refused.json()["notice"]["actions"] == ["talk_to_person"]
        assert env.graph.calls == []
        assert count_rows(env.store, "messages", "role = 'customer'") == 0
        env.verdict.verdict = None
        ok = post_turn(client, env.token, thread, text_payload("hello"), turn_id)
        assert ok.status_code == 200 and ok.json()["notice"] is None
        assert len(env.graph.calls) == 1


def test_j9_rate_limited_through_the_real_server(journey: JourneyRun) -> None:
    """integrated (AC-15): the real limiter refuses the 21st turn on a thread with a RATE_LIMITED notice, never 429."""
    with journey.step(
        "J-9",
        "AEA-40 RATE_LIMITED through the real limiter",
        needs=TURN_NEEDS,
        operations=("login", "startChatSession", "submitTurn"),
    ):
        signed = journey.login()
        thread_id = signed.client.call("POST", "/api/chat/sessions", operation_id="startChatSession").json()[
            "thread_id"
        ]
        limit = journey.container.limits.web.chat_turns_per_thread_per_min
        # With the real graph bound each turn takes ~0.3 s, so the per-minute thread bucket refills while 21 turns run
        # and the 21st is never refused (AEA-51 merge gate). Spend limit - 3 tokens of this thread's bucket on the same
        # real limiter and clock first, so the HTTP loop below still crosses the cap through the real server.
        # Chosen by Innocent, 2026-10-22 ("go with A"); a frozen-clock harness (option B) is a follow-up.
        limiter = journey.container.get(RATE_LIMITER)
        now = (journey.clock() if journey.clock is not None else datetime.now(UTC)).timestamp()
        for _ in range(limit - 3):
            assert limiter.check(LimitScope.THREAD, thread_id, now, family="turn").allowed
        codes: list[str | None] = []
        last_turn = ""
        for n in range(limit + 1):
            last_turn = str(uuid.uuid4())
            r = signed.client.call(
                "POST",
                f"/api/chat/sessions/{thread_id}/turns",
                operation_id="submitTurn",
                body={"turn_id": last_turn, "payload": {"kind": "text", "text": f"message {n}"}},
            )
            assert r.status_code == 200
            codes.append((r.json()["notice"] or {}).get("code"))
            if codes[-1] == "RATE_LIMITED":
                break
        assert codes[-1] == "RATE_LIMITED" and "RATE_LIMITED" not in codes[:-1]
        notice = r.json()["notice"]
        assert notice["actions"] == ["talk_to_person"] and notice["retry_turn_id"] is None
        row = journey.db.one("SELECT * FROM turns WHERE turn_id = ?", (last_turn,))
        assert (row["status"], row["outcome"], row["degrade_reason"]) == (
            "failed",
            "degraded_handoff",
            "rate_limit",
        )
        assert journey.db.count("messages", "turn_id = ?", (last_turn,)) == 0


@pytest.mark.skip(
    reason="blocked-on AEA-51 and an AEA-57 follow-up (a scripted entry that holds a provider call): "
    "TURN_TIMEOUT and BUSY through the real server; mock-tested above"
)
def test_j9_timeout_and_busy_through_the_real_server() -> None:
    """TURN_TIMEOUT and BUSY through the real server process and the scripted model adapter (integrated level)."""
