"""AEA-40: the customer chat routes (`startChatSession`, `getChatThread`, `submitTurn`) through the real app.

Real routes, real middleware (login gate, request ids), real `TurnService` / `SessionService` over a temp SQLite copy;
`run_graph`, `SpendGuard`, `DemoService` and the settled-view builder are doubles. Every response is checked against the
signed OpenAPI with `assert_response_matches` (through `assert_matches`). Acceptance criteria covered: AC-1, 2, 6, 7, 9,
11, 16, 18, 19 and the 409 / 401 / 404 / 410 statuses AC-22 lists. Part B tests (the CON-1 routes) wait for AEA-02b and
the AEA-03 follow-up.
"""

from __future__ import annotations

import datetime as dt
import logging
import uuid
from pathlib import Path
from typing import Any

import pytest

from meridian.domain.blocks import BurningCheckBlock, Option
from meridian.policy.limits import Limits
from meridian.policy.texts import TextId, render
from tests.api.chat_support import REFUSED, chat_env, get_thread, post_turn, start_session
from tests.api.web_shell_support import (
    assert_matches,
    error_body,
    make_client,
    rand_word,
    without_request_id,
)
from tests.fakes import WORKED_PAIRS_NOW
from tests.services.chat_doubles import (
    AGENT_VERSION,
    DeadlineRunGraph,
    RaisingRunGraph,
    ScriptedRunGraph,
    answered_outcome,
    choice_payload,
    code_payload,
    conversation,
    count_rows,
    customer_messages,
    handoff_block,
    has_person_key,
    history_text_id,
    human_controller,
    locate_form_payload,
    log_blob,
    messages_of,
    new_turn_id,
    seed_case,
    seed_person_request_turn,
    seed_takeover,
    seed_thread,
    synthetic,
    text_payload,
    turn_row,
)

QUESTION = "I got an invoice and I am not sure what it is for."


# -- AC-1: CON-1 startChatSession (Part B) -----------------------------------------------------------------------
def test_start_session_fixed_greeting_no_model(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-1): 201 with the fixed greeting, demo clock, staffing and limits; no model; one conversation row."""
    with chat_env(monkeypatch, tmp_path, with_session_service=True) as env, make_client(env.app) as client:
        response = start_session(client, env.token)

        assert response.status_code == 201, response.text
        assert_matches(response, "startChatSession")
        body = response.json()
        assert body["greeting"]["text"] == render(TextId.GREETING)
        assert body["greeting"]["type"] == "text"
        assert body["greeting"]["speaker"]["kind"] == "assistant"
        assert body["demo_clock"]["date_label"] == "Fri Oct 16, 2026 (demo date)"
        assert body["staffing"]["mode"] == "nobody_online"
        assert body["controller"] == {"kind": "ai", "display_name": None}
        assert body["settled"]["actions"] == []
        assert body["events"]["last_event_id"] == 0
        assert (
            body["limits"]
            == {
                "turn_deadline_ms": Limits().turn.turn_deadline_ms,
                "still_working_after_ms": 10000,
                "browser_give_up_after_ms": 65000,
                "max_message_chars": 2000,
            }
            == {
                "turn_deadline_ms": 60000,
                "still_working_after_ms": 10000,
                "browser_give_up_after_ms": 65000,
                "max_message_chars": 2000,
            }
        )
        thread = body["thread_id"]
        assert env.graph.calls == []  # no model, no graph
        row = conversation(env.store, thread)
        assert row.demo_session == env.demo_session
        assert (row.run_tag, row.run_id, row.outcome, row.controller.kind) == ("live", None, "open", "ai")
        assert row.agent_version == AGENT_VERSION
        messages = messages_of(env.store, thread)
        assert [(m.role, m.turn_id, m.text) for m in messages] == [
            ("assistant", None, render(TextId.GREETING))
        ]
        assert count_rows(env.store, "conversations") == 1
        for table in ("turns", "events", "lookup_log", "spend_ledger"):
            assert count_rows(env.store, table) == 0


def test_start_session_tags_eval_runs_and_leaves_others_live(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """invariant (AC-1, CAP-7): the run tag and run id come from the eval key; a run without it is `live`."""
    with chat_env(monkeypatch, tmp_path, with_session_service=True) as env, make_client(env.app) as client:
        tagged = start_session(
            client,
            env.token,
            extra_headers={"X-Meridian-Eval-Key": env.eval_key, "X-Meridian-Run-Id": "run-abc"},
        )
        wrong = start_session(client, env.token, extra_headers={"X-Meridian-Eval-Key": rand_word(18, "bad")})
        plain = start_session(client, env.token)

        for response in (tagged, wrong, plain):
            assert response.status_code == 201
            assert_matches(response, "startChatSession")
        tagged_row = conversation(env.store, tagged.json()["thread_id"])
        assert (tagged_row.run_tag, tagged_row.run_id) == ("eval", "run-abc")
        for response in (wrong, plain):
            row = conversation(env.store, response.json()["thread_id"])
            assert (row.run_tag, row.run_id) == ("live", None)


# -- AC-2: ownership, redaction, ended threads (Part B) ----------------------------------------------------------
def test_get_thread_redacted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """negative (AC-2): a card number typed by the customer comes back as '[card number removed]', never as digits."""
    syn = synthetic()
    typed = f"my card is {syn.card} ok"
    with chat_env(monkeypatch, tmp_path, with_session_service=True) as env, make_client(env.app) as client:
        thread = start_session(client, env.token).json()["thread_id"]
        sent = post_turn(client, env.token, thread, text_payload(typed))
        assert sent.status_code == 200, sent.text

        response = get_thread(client, env.token, thread)

        assert response.status_code == 200, response.text
        assert_matches(response, "getChatThread")
        turns = response.json()["turns"]
        customer = [t for t in turns if t["speaker"]["kind"] == "customer"]
        assert [t["text"] for t in customer] == ["my card is [card number removed] ok"]
        for needle in syn.needles():
            assert needle not in response.text
        stored = customer_messages(env.store, thread)
        assert [m.text for m in stored] == ["my card is [card number removed] ok"]


def test_thread_not_found_identical_for_malformed_unknown_and_foreign(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """failure/refusal (AC-2): malformed, unknown and another session's thread give the identical 404."""
    with chat_env(monkeypatch, tmp_path, with_session_service=True) as env, make_client(env.app) as client:
        foreign = seed_thread(env.store.uow, str(env.other_session().session_id))
        mine = seed_thread(env.store.uow, env.demo_session)
        ids = ["not-a-thread-id", str(uuid.uuid4()), str(foreign)]

        responses = [get_thread(client, env.token, thread_id) for thread_id in ids]

        for response in responses:
            error_body(response, 404, "SESSION_NOT_FOUND")
            assert_matches(response, "getChatThread")
        bodies = [without_request_id(r) for r in responses]
        assert bodies[0] == bodies[1] == bodies[2]
        assert get_thread(client, env.token, mine).status_code == 200  # the owner still reads it


def test_submit_turn_other_threads_are_refused_and_run_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """failure/refusal (AC-2, web.md section 4): submitTurn takes the same ownership gate; no model, no row."""
    with chat_env(monkeypatch, tmp_path) as env, make_client(env.app) as client:
        foreign = seed_thread(env.store.uow, str(env.other_session().session_id))
        ids = ["not-a-thread-id", str(uuid.uuid4()), str(foreign)]

        responses = [post_turn(client, env.token, thread_id, text_payload("hello")) for thread_id in ids]

        for response in responses:
            error_body(response, 404, "SESSION_NOT_FOUND")
            assert_matches(response, "submitTurn")
        assert (
            without_request_id(responses[0])
            == without_request_id(responses[1])
            == without_request_id(responses[2])
        )
        assert env.graph.calls == []
        assert count_rows(env.store, "turns") == 0
        assert customer_messages(env.store, foreign) == []


def test_chat_routes_need_a_session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure/refusal (AC-22): all three routes answer 401 without a session cookie, valid against the OpenAPI."""
    with chat_env(monkeypatch, tmp_path, with_session_service=True) as env, make_client(env.app) as client:
        thread = seed_thread(env.store.uow, env.demo_session)
        responses = {
            "startChatSession": client.post("/api/chat/sessions"),
            "getChatThread": client.get(f"/api/chat/sessions/{thread}"),
            "submitTurn": client.post(
                f"/api/chat/sessions/{thread}/turns",
                json={"turn_id": str(uuid.uuid4()), "payload": {"kind": "text", "text": "hi"}},
            ),
        }
        for operation_id, response in responses.items():
            error_body(response, 401, "UNAUTHENTICATED")
            assert_matches(response, operation_id)
        assert env.graph.calls == []
        assert count_rows(env.store, "conversations") == 1  # only the seeded one


def test_ended_thread_410(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure/refusal (AC-2): this session's ended thread is 410 SESSION_ENDED with the reason, on both thread routes."""
    with chat_env(monkeypatch, tmp_path, with_session_service=True) as env, make_client(env.app) as client:
        thread = seed_thread(env.store.uow, env.demo_session)
        with env.store.uow(write=True) as tx:
            tx.core.reset.clear_demo_tables(
                "reset-test-1", ended_at=dt.datetime(2026, 10, 21, 15, 0, tzinfo=dt.UTC)
            )
            tx.commit()
        ended = conversation(env.store, thread)
        assert ended.reason  # the stored end reason

        got = get_thread(client, env.token, thread)
        sent = post_turn(client, env.token, thread, text_payload("hello"))

        for response, operation in ((got, "getChatThread"), (sent, "submitTurn")):
            body = error_body(response, 410, "SESSION_ENDED")
            assert body["error"]["details"]["reason"] == ended.reason
            assert_matches(response, operation)
        assert env.graph.calls == []


# -- AC-6: rate limit notice -------------------------------------------------------------------------------------
def test_rate_limited_notice_then_same_turn_runs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure/refusal (AC-6): a refused verdict gives 200 + RATE_LIMITED, no model; the same turn_id runs once allowed."""
    with chat_env(monkeypatch, tmp_path) as env, make_client(env.app) as client:
        thread = seed_thread(env.store.uow, env.demo_session)
        turn_id = new_turn_id()
        env.verdict.verdict = REFUSED

        refused = post_turn(client, env.token, thread, text_payload("hello"), turn_id)

        assert refused.status_code == 200, refused.text
        assert_matches(refused, "submitTurn")
        notice = refused.json()["notice"]
        assert notice["code"] == "RATE_LIMITED"
        assert notice["actions"] == ["talk_to_person"]
        assert notice["retry_turn_id"] is None
        assert env.graph.calls == []
        row = turn_row(env.store, turn_id)
        assert (row.status, row.gate_result, row.path, row.outcome, row.degrade_reason) == (
            "failed",
            "clear",
            "degraded",
            "degraded_handoff",
            "rate_limit",
        )

        env.verdict.verdict = None  # the bucket refilled
        again = post_turn(client, env.token, thread, text_payload("hello"), turn_id)

        assert again.status_code == 200
        assert_matches(again, "submitTurn")
        assert again.json()["notice"] is None
        assert len(env.graph.calls) == 1
        assert turn_row(env.store, turn_id).status == "completed"


# -- AC-7: deadline and exception through the route --------------------------------------------------------------
def test_timeout_and_exception_notices_via_submit_turn(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """failure/refusal (AC-7): a DEADLINE halt and a raising graph are both HTTP 200 with `settled`, never a 500."""
    marker = RaisingRunGraph.MARKER
    holder: dict[str, Any] = {}

    def boom(turn_input: Any, context: Any) -> Any:
        raise RuntimeError("scripted graph failure " + marker)

    graph = ScriptedRunGraph(lambda i, c: holder["deadline"](i, c), boom)
    with chat_env(monkeypatch, tmp_path, graph=graph) as env, make_client(env.app) as client:
        holder["deadline"] = DeadlineRunGraph(env.store.uow)
        thread = seed_thread(env.store.uow, env.demo_session)
        first_turn, second_turn = new_turn_id(), new_turn_id()

        timed_out = post_turn(client, env.token, thread, text_payload("book the tune-up"), first_turn)
        failed = post_turn(client, env.token, thread, text_payload("hello"), second_turn)

        for response in (timed_out, failed):
            assert response.status_code == 200, response.text
            assert_matches(response, "submitTurn")
            assert "settled" in response.json()
        body = timed_out.json()
        assert body["notice"]["code"] == "TURN_TIMEOUT"
        assert body["notice"]["actions"] == ["try_again", "talk_to_person"]
        assert body["notice"]["retry_turn_id"] == str(first_turn)
        assert [w["kind"] for w in body["settled"]["actions"]] == ["booked"]
        assert has_person_key(_blocks(failed.json()))
        for turn_id in (first_turn, second_turn):
            row = turn_row(env.store, turn_id)
            assert (row.status, row.outcome) == ("failed", "degraded_handoff")
        assert turn_row(env.store, first_turn).degrade_reason == "timeout"
        assert marker not in failed.text


def _blocks(body: dict[str, Any]) -> list[Any]:
    """Blocks of a response body as simple objects exposing `person_key` / `code` / `type`."""

    class _B:
        def __init__(self, data: dict[str, Any]) -> None:
            self.person_key = data.get("person_key", False)
            self.code = data.get("code")
            self.type = data.get("type")

    return [_B(b) for b in body["blocks"]]


# -- AC-3 over the wire ------------------------------------------------------------------------------------------
def test_running_turn_409_via_submit_turn(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-3): a resend while the turn runs is 409 TURN_IN_PROGRESS with retry_after_ms 2000; nothing runs."""
    from tests.services.chat_doubles import make_cmd, turn_ids_of

    with chat_env(monkeypatch, tmp_path) as env, make_client(env.app) as client:
        thread = seed_thread(env.store.uow, env.demo_session)
        turn_id = new_turn_id()
        cmd = make_cmd(thread, text_payload("hello"), turn_id=turn_id)
        with env.store.uow(write=True) as tx:
            tx.core.turns.begin(turn_ids_of(cmd), WORKED_PAIRS_NOW)
            tx.commit()

        response = post_turn(client, env.token, thread, text_payload("hello"), turn_id)

        body = error_body(response, 409, "TURN_IN_PROGRESS")
        assert body["error"]["details"] == {"retry_after_ms": 2000}
        assert_matches(response, "submitTurn")
        assert env.graph.calls == []


def test_completed_turn_resent_is_byte_identical(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-3): the same turn_id returns the stored response body unchanged and runs nothing."""
    with chat_env(monkeypatch, tmp_path) as env, make_client(env.app) as client:
        thread = seed_thread(env.store.uow, env.demo_session)
        turn_id = new_turn_id()

        first = post_turn(client, env.token, thread, text_payload(QUESTION), turn_id)
        again = post_turn(client, env.token, thread, text_payload(QUESTION), turn_id)

        assert first.status_code == again.status_code == 200
        assert_matches(first, "submitTurn")
        assert again.content == first.content
        assert len(env.graph.calls) == 1


# -- AC-9: validation errors name the field, never the value -----------------------------------------------------
def test_validation_error_hides_value(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """negative (AC-9): a bad code and an over-long text are 400 VALIDATION_ERROR with field and constraint, no value."""
    caplog.set_level(logging.DEBUG)
    bad_code = "12ab56"
    too_long = "zq" * 1000 + "z"  # 2001 characters
    assert len(too_long) == 2001
    with chat_env(monkeypatch, tmp_path) as env, make_client(env.app) as client:
        thread = seed_thread(env.store.uow, env.demo_session)
        responses = [
            post_turn(client, env.token, thread, code_payload(bad_code)),
            post_turn(client, env.token, thread, text_payload(too_long)),
            post_turn(client, env.token, thread, text_payload("")),
        ]

        for response in responses:
            body = error_body(response, 400, "VALIDATION_ERROR")
            assert_matches(response, "submitTurn")
            assert body["error"]["field"], body
            assert body["error"]["constraint"], body
        assert bad_code not in responses[0].text
        assert "zqzqzq" not in responses[1].text
        assert bad_code not in log_blob(caplog) and "zqzqzq" not in log_blob(caplog)
        assert env.graph.calls == []
        assert customer_messages(env.store, thread) == []
        assert count_rows(env.store, "turns") == 0


# -- AC-11: customer message side effects over the wire ----------------------------------------------------------
def test_customer_message_event_via_submit_turn(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-11): a submitTurn on a human-controlled thread leaves the message row and one customer_message event."""
    with chat_env(monkeypatch, tmp_path) as env, make_client(env.app) as client:
        controller = human_controller("MHC-C-0042")
        thread = seed_thread(env.store.uow, env.demo_session, controller=controller)
        turn_id = new_turn_id()

        response = post_turn(client, env.token, thread, text_payload("are you still there?"), turn_id)

        assert response.status_code == 200, response.text
        assert_matches(response, "submitTurn")
        assert len(customer_messages(env.store, thread, turn_id)) == 1
        assert (
            count_rows(env.store, "events", "stream = 'case:MHC-C-0042' AND type = 'customer_message'") == 1
        )
        assert count_rows(env.store, "events", "stream = ?", (str(thread),)) == 0
        wall = conversation(env.store, thread).last_customer_wall_at
        assert wall is not None and wall.utcoffset() == dt.timedelta(0)


# -- AC-16 / AC-18: history over the wire (Part B) ---------------------------------------------------------------
def test_get_thread_full_history(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-16): getChatThread returns the whole conversation in order, valid, with unique ids."""
    with chat_env(monkeypatch, tmp_path, with_session_service=True) as env, make_client(env.app) as client:
        thread = start_session(client, env.token).json()["thread_id"]
        turn_id = new_turn_id()
        sent = post_turn(client, env.token, thread, text_payload(QUESTION), turn_id)
        assert sent.status_code == 200
        shift = handoff_block("MHC-C-0042", WORKED_PAIRS_NOW + dt.timedelta(minutes=6))
        takeover = seed_takeover(
            env.store.uow,
            _tid(thread),
            WORKED_PAIRS_NOW + dt.timedelta(minutes=5),
            step=dt.timedelta(seconds=1),
            shift_end=shift,
        )

        response = get_thread(client, env.token, thread)

        assert response.status_code == 200, response.text
        assert_matches(response, "getChatThread")
        body = response.json()
        turns = body["turns"]
        assert [t["speaker"]["kind"] for t in turns] == [
            "assistant",
            "customer",
            "assistant",
            "event",
            "event",
            "representative",
            "event",
            "assistant",
        ]
        assert turns[0]["turn_id"] == "greeting" and turns[0]["blocks"][0]["type"] == "text"
        assert turns[1]["text"] == QUESTION and turns[1]["turn_id"] == str(turn_id)
        assert turns[2]["turn_id"] == str(turn_id) and turns[2]["blocks"][0]["type"] == "text"
        assert turns[3]["speaker"] == {"kind": "event", "display_name": None}
        assert (
            turns[3]["text"] == takeover.lines["joined"]
            and turns[3]["turn_id"] == f"evt-{takeover.joined_id}"
        )
        assert turns[5]["speaker"] == {"kind": "representative", "display_name": "Riley"}
        assert (
            turns[5]["text"] == takeover.riley_text
            and turns[5]["turn_id"] == f"msg-{takeover.riley_message_id}"
        )
        assert (
            turns[7]["blocks"][0]["type"] == "handoff"
            and turns[7]["turn_id"] == f"evt-{takeover.shift_end_id}"
        )
        others = [
            t["turn_id"]
            for t in turns
            if t["turn_id"] == "greeting" or t["turn_id"].startswith(("msg-", "evt-"))
        ]
        assert len(others) == len(turns) - 2 and len(set(others)) == len(
            others
        )  # ids unique apart from the turn pair
        assert body["last_event_id"] == takeover.newest_event_id
        assert body["state"] == "open"
        assert body["staffing"]["mode"] == "nobody_online"
        assert body["demo_clock"]["date_label"] == "Fri Oct 16, 2026 (demo date)"


def test_thread_history_includes_greeting_staff_and_event_lines(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """invariant (AC-18): after a live takeover a reload returns every line in order, with last_event_id the newest."""
    with chat_env(monkeypatch, tmp_path, with_session_service=True) as env, make_client(env.app) as client:
        thread_id = _tid(start_session(client, env.token).json()["thread_id"])
        turn_id = new_turn_id()
        assert post_turn(client, env.token, thread_id, text_payload(QUESTION), turn_id).status_code == 200
        seed_case(env.store.uow, thread_id, "MHC-C-0042")
        block = handoff_block("MHC-C-0042", WORKED_PAIRS_NOW)
        request_turn = seed_person_request_turn(env.store.uow, thread_id, block)
        takeover = seed_takeover(env.store.uow, thread_id, WORKED_PAIRS_NOW, staffing_change=True)

        response = get_thread(client, env.token, thread_id)

        assert response.status_code == 200, response.text
        assert_matches(response, "getChatThread")
        body = response.json()
        turns = body["turns"]
        shape = [
            (
                t["speaker"]["kind"],
                t["speaker"]["display_name"],
                None if t["speaker"]["kind"] == "assistant" else t["text"],
            )
            for t in turns
        ]
        assistant_name = turns[0]["speaker"]["display_name"]
        assert shape == [
            ("assistant", assistant_name, None),
            ("customer", None, QUESTION),
            ("assistant", assistant_name, None),
            ("customer", None, "Talk to a person"),
            ("assistant", assistant_name, None),
            ("event", None, "Riley (demo representative) has joined."),
            ("event", None, takeover.lines["paused"]),
            ("representative", "Riley", takeover.riley_text),
            ("event", None, takeover.lines["resumed"]),
            ("event", None, takeover.lines["staffing"]),
        ]
        assert turns[0]["turn_id"] == "greeting"
        assert turns[3]["turn_id"] == turns[4]["turn_id"] == str(request_turn)
        assert turns[4]["blocks"][0]["type"] == "handoff"
        assert turns[4]["blocks"][0]["reference"] == "MHC-C-0042"
        assert body["last_event_id"] == takeover.newest_event_id


# -- AC-19: history rows read like the live rows (Part B + AEA-03 follow-up) -------------------------------------
def test_history_display_texts(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-19): code 'Code entered', form 'Details sent', choice the option's label; stored rows stay redacted."""
    code_text = render(history_text_id("HISTORY_CODE_ENTERED"))
    form_text = render(history_text_id("HISTORY_DETAILS_SENT"))
    assert (code_text, form_text) == ("Code entered", "Details sent")
    syn = synthetic()
    first_turn = new_turn_id()
    card_id = f"burn-{first_turn}"

    def with_card(turn_input: Any, context: Any) -> Any:
        outcome = answered_outcome(turn_input.turn_id, context.now)
        card = BurningCheckBlock(
            block_id=f"blk-{turn_input.turn_id}-2",
            speaker=outcome.reply.blocks[0].speaker,
            at=context.now,
            card_id=card_id,
            options=(
                Option(option="yes", label="Yes, I smell burning", disabled=False, reason=None),
                Option(option="no", label="No smell", disabled=False, reason=None),
            ),
            answered=None,
            question="Do you smell burning?",
        )
        reply = outcome.reply.model_copy(update={"blocks": (*outcome.reply.blocks, card)})
        return outcome.model_copy(update={"reply": reply})

    with (
        chat_env(monkeypatch, tmp_path, graph=ScriptedRunGraph(with_card), with_session_service=True) as env,
        make_client(env.app) as client,
    ):
        thread = start_session(client, env.token).json()["thread_id"]
        sent = [
            post_turn(client, env.token, thread, text_payload("my furnace smells odd"), first_turn),
            post_turn(client, env.token, thread, choice_payload(card_id, "yes")),
            post_turn(client, env.token, thread, choice_payload("slots-7", "maybe")),
            post_turn(client, env.token, thread, code_payload(syn.code)),
            post_turn(client, env.token, thread, locate_form_payload("Zqname Testperson", syn.phone)),
        ]
        assert [r.status_code for r in sent] == [200] * 5, [r.text for r in sent]

        response = get_thread(client, env.token, thread)

        assert_matches(response, "getChatThread")
        customer = [t for t in response.json()["turns"] if t["speaker"]["kind"] == "customer"]
        assert [t["text"] for t in customer] == [
            "my furnace smells odd",
            "Yes, I smell burning",  # the label of the option, from the card it answered
            "maybe",  # that card is not in the thread: the stored option string
            code_text,
            form_text,
        ]
        for needle in (*syn.needles(), "[code entered]", "[details submitted]"):
            assert needle not in response.text
        stored = {m.kind: m.text for m in customer_messages(env.store, thread) if m.kind in ("code", "form")}
        assert stored == {
            "code": "[code entered]",
            "form": "[details submitted]",
        }  # stored rows stay redacted


def _tid(value: str) -> Any:
    from pydantic import TypeAdapter

    from meridian.domain.common import ThreadId

    return TypeAdapter(ThreadId).validate_python(value)
