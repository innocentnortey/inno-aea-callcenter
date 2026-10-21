"""J-9 (slice plan section 0a), AEA-40's part: the TURN_TIMEOUT, BUSY and RATE_LIMITED notices reach the user.

Level today: `mock-tested`. Real routes, real middleware and a real SQLite working copy through a TestClient; the
`run_graph`, `SpendGuard` and `DemoService` siblings are doubles; no server process, no browser, no model adapter.
The integrated step (real server, scripted model adapter) is blocked by AEA-57 (harness) and AEA-51 (the graph).
Each test asserts what the user sees (the notice and its actions) and what was stored (conversation, messages, turn).
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from tests.api.chat_support import REFUSED, chat_env, post_turn
from tests.api.web_shell_support import assert_matches, make_client
from tests.services.chat_doubles import (
    BlockingRunGraph,
    Collected,
    DeadlineRunGraph,
    ScriptedRunGraph,
    count_rows,
    customer_messages,
    make_cmd,
    messages_of,
    new_turn_id,
    seed_thread,
    text_payload,
    turn_row,
)

pytestmark = pytest.mark.journey


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


@pytest.mark.skip(
    reason="blocked by AEA-57 (harness) and AEA-51 (graph): integrated step, scripted model adapter"
)
def test_j9_notices_through_the_real_server_with_the_scripted_model() -> None:
    """The three notices through the real server process and the scripted model adapter (integrated level)."""
