"""AEA-40 capture and outcome checks: the real CON-1 and CON-2 entry points write the DO-6 records (AC-14, AC-21).

Drives `startChatSession` then `submitTurn` through the real app with a scripted `run_graph`, then reads the stored
`conversations`, `turns` and `check_events` rows back. The full CAP-1/CAP-2 with the real graph is AEA-51's.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from meridian.adapters.tracing_langfuse import NullTraceSink
from meridian.domain.tools import LookupEntry
from meridian.policy.limits import Limits
from meridian.ports.models import CallRecord
from meridian.services.ledger import LedgerService
from tests.api.chat_support import ChatEnv, chat_env, post_turn, start_session
from tests.api.web_shell_support import assert_matches, make_client
from tests.fakes import WORKED_PAIRS_NOW, InMemoryTraceSink
from tests.services.chat_doubles import (
    AGENT_VERSION,
    RaisingRunGraph,
    ScriptedRunGraph,
    answered_outcome,
    fixed_wall,
    handed_off_outcome,
    new_turn_id,
)
from tests.services.chat_storage import conversation, turn_row


def _call(cost: float) -> CallRecord:
    return CallRecord.model_validate(
        {
            "provider": "anthropic", "model": "claude-sonnet-test", "latency_ms": 1200, "input_tokens": 9000,
            "output_tokens": 700, "cache_read_tokens": 0, "cache_write_tokens": 0, "thinking_tokens": 0,
            "cost_usd": cost, "cost_source": "price_table", "status": "ok", "failure": None,
            "provider_request_id": None, "stop_reason": "end_turn", "role": "responder", "attempt": 1,
        }
    )  # fmt: skip


class _Probe:
    """A `run_graph` that, like the real graph, writes this turn's spend and lookup rows; it also peeks at its own row."""

    def __init__(self, holder: dict[str, ChatEnv]) -> None:
        self._holder = holder
        self.seen: list[tuple[str, str | None]] = []

    def __call__(self, turn_input: Any, context: Any) -> Any:
        env = self._holder["env"]
        row = turn_row(env.store, turn_input.turn_id)
        self.seen.append((row.status, row.outcome))  # the turn row exists on receipt, outcome still empty
        ledger = LedgerService(
            env.store.uow, wall_clock=fixed_wall, daily_cap_usd=Limits().spend.daily_cap_usd
        )
        ledger.record(_call(0.011), context.ids)
        ledger.record(_call(0.022), context.ids)
        with env.store.uow(write=True) as tx:
            for tool in ("search_knowledge", "lookup_invoice"):
                tx.core.lookup_log.append(
                    LookupEntry(
                        tool=tool,
                        record_ids=(),
                        passage_ids=(),
                        result_seen="ok",
                        message_id=turn_input.message_id,
                        turn_id=turn_input.turn_id,
                    )
                )
            tx.commit()
        return answered_outcome(turn_input.turn_id, context.now)


def test_con1_con2_records_written(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-14): CON-1 then CON-2 leave a conversation row, a finished turn row and two check events."""
    holder: dict[str, ChatEnv] = {}
    probe = _Probe(holder)
    with (
        chat_env(monkeypatch, tmp_path, graph=probe, with_session_service=True, trace=NullTraceSink()) as env,
        make_client(env.app) as client,
    ):
        holder["env"] = env
        started = start_session(client, env.token)
        thread = started.json()["thread_id"]
        turn_id = new_turn_id()

        sent = post_turn(
            client, env.token, thread, {"kind": "text", "text": "Why is my bill so high?"}, turn_id
        )

        assert started.status_code == 201 and sent.status_code == 200, sent.text
        assert_matches(started, "startChatSession")
        assert_matches(sent, "submitTurn")
        conv = conversation(env.store, thread)
        assert (conv.run_tag, conv.run_id, conv.agent_version, conv.outcome) == (
            "live",
            None,
            AGENT_VERSION,
            "open",
        )
        assert probe.seen == [("running", None)]  # on receipt: a `running` row with no outcome yet
        row = turn_row(env.store, turn_id)
        assert row.status == "completed"
        assert str(row.request_id) == sent.headers["X-Request-ID"]
        assert (row.sequence, row.received_at) == (1, WORKED_PAIRS_NOW)
        assert row.replied_at is not None and row.replied_at >= row.received_at
        assert isinstance(row.server_ms, int) and row.server_ms >= 0
        assert (row.gate_result, row.path, row.outcome, row.degrade_reason) == (
            "clear",
            "talk",
            "answered",
            None,
        )
        assert row.planner is not None
        assert (row.planner.model, row.planner.plan_mode, row.planner.plan_source, row.planner.topic) == (
            "jev-test",
            "talk",
            "planner",
            "billing",
        )
        assert row.specialists_run == ("knowledge",) and row.danger_raised is False
        assert (row.model_calls, row.input_tokens, row.output_tokens) == (2, 18000, 1400)
        assert row.cost_usd == pytest.approx(0.033)  # summed from the spend_ledger rows of this turn_id
        assert row.tool_calls == 2  # from the lookup_log rows of this turn_id
        assert (row.trace_id, row.trace_export) == (None, "off")  # NullTraceSink
        assert row.run_tag == "live" and row.agent_version == AGENT_VERSION
        assert json.loads(row.response) == sent.json()  # the stored body is what the client got
        with env.store.uow() as tx:
            events = tx.core.check_events.for_thread(conv.thread_id)
        assert [(e.check, e.result) for e in events] == [("gate", "pass"), ("fact", "pass")]


def test_trace_id_and_export_status_recorded(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-14): with a trace sink the turn row holds the span's trace id and the export status."""
    sink = InMemoryTraceSink(status="sent")
    with (
        chat_env(monkeypatch, tmp_path, trace=sink, with_session_service=True) as env,
        make_client(env.app) as client,
    ):
        thread = start_session(client, env.token).json()["thread_id"]
        turn_id = new_turn_id()
        assert (
            post_turn(client, env.token, thread, {"kind": "text", "text": "hello"}, turn_id).status_code
            == 200
        )

        row = turn_row(env.store, turn_id)

        assert len(sink.turns) == 1
        assert row.trace_id == sink.turns[0].trace_id
        assert row.trace_export == "sent"


def test_eval_key_tags_runs_and_live_is_the_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-14, CAP-7): a run with the eval key is tagged `eval` (conversation and turn), one without it `live`."""
    with chat_env(monkeypatch, tmp_path, with_session_service=True) as env, make_client(env.app) as client:
        headers = {"X-Meridian-Eval-Key": env.eval_key, "X-Meridian-Run-Id": "run-xyz"}
        tagged = start_session(client, env.token, extra_headers=headers).json()["thread_id"]
        tagged_turn, live_turn = new_turn_id(), new_turn_id()
        post_turn(
            client, env.token, tagged, {"kind": "text", "text": "hello"}, tagged_turn, extra_headers=headers
        )
        live = start_session(client, env.token).json()["thread_id"]
        post_turn(client, env.token, live, {"kind": "text", "text": "hello"}, live_turn)

        assert (turn_row(env.store, tagged_turn).run_tag, turn_row(env.store, tagged_turn).run_id) == (
            "eval",
            "run-xyz",
        )
        assert (turn_row(env.store, live_turn).run_tag, turn_row(env.store, live_turn).run_id) == (
            "live",
            None,
        )
        assert conversation(env.store, tagged).run_tag == "eval"
        assert conversation(env.store, live).run_tag == "live"


# -- AC-21 through the route ------------------------------------------------------------------------------------
def test_conversation_outcome_via_submit_turn(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-21): the stored conversation outcome after each scripted step, sent through submitTurn."""
    graph = ScriptedRunGraph(
        lambda i, c: answered_outcome(i.turn_id, c.now, closed=True),
        lambda i, c: answered_outcome(i.turn_id, c.now, closed=False),
        lambda i, c: handed_off_outcome(i.turn_id, c.now),
        lambda i, c: answered_outcome(i.turn_id, c.now, closed=True),
    )
    with (
        chat_env(monkeypatch, tmp_path, graph=graph, with_session_service=True) as env,
        make_client(env.app) as client,
    ):
        thread = start_session(client, env.token).json()["thread_id"]

        def send(text: str) -> None:
            response = post_turn(client, env.token, thread, {"kind": "text", "text": text})
            assert response.status_code == 200, response.text
            assert_matches(response, "submitTurn")

        send("what is this charge?")
        assert conversation(env.store, thread).outcome == "ai_resolved"
        send("one more question")
        assert (
            conversation(env.store, thread).outcome == "open"
        )  # reopened by the message; a task is still open
        send("I want to speak to someone about a refund")
        assert conversation(env.store, thread).outcome == "handed_off"
        send("thanks")
        assert conversation(env.store, thread).outcome == "handed_off"  # a later answered turn leaves it

    with (
        chat_env(
            monkeypatch, tmp_path / "second", graph=RaisingRunGraph(), with_session_service=True
        ) as env2,
        make_client(env2.app) as client2,
    ):
        thread2 = start_session(client2, env2.token).json()["thread_id"]
        response = post_turn(client2, env2.token, thread2, {"kind": "text", "text": "hello"})
        assert response.status_code == 200
        assert conversation(env2.store, thread2).outcome == "open"  # a degraded_handoff turn leaves it open
