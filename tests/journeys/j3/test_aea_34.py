"""J-3 step (slice plan 0a; WP-4F): the follow-up turn after a move loads the completed action, controller and
identity from the working copy, and the settled panel the customer sees names the new window. Level today:
mock-tested (real load_context through AEA-21's timed_node and ReplyComposer on a temp SQLite copy of the issued DB;
no server, no model; the move is seeded as the scheduling service writes it). Integrated level blocked by AEA-51 (it
binds the harness's run_graph need and lands J-3 with the reply text); AEA-57's harness is on main."""

from __future__ import annotations

import dataclasses
import functools
import hashlib
from datetime import date, timedelta
from typing import cast

import pytest
from langgraph.runtime import Runtime

from meridian.agent.graph import NodeFn, timed_node
from meridian.agent.nodes.compose import ReplyComposer
from meridian.agent.nodes.load_context import load_context
from meridian.domain.actions import Settled
from meridian.domain.state import LoadContextUpdate
from tests.fakes import InMemoryTraceSink
from tests.fixtures.sqlite import ISSUED_DB, temp_sqlite
from tests.unit.agent.nodes.load_context_fixtures import (
    DEMO_START,
    count_rows,
    make_ctx,
    make_deps,
    make_state,
    seed_wp4f,
)

pytestmark = pytest.mark.journey

_FOLLOWUP = "Great, so I'm all set for Monday?"


def test_j3_followup_turn_remembers_the_move() -> None:
    issued_hash_before = hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest()
    with temp_sqlite() as store:
        thread, turn3, turn4 = seed_wp4f(store)
        tables = ("actions", "messages", "turns")
        before = {name: count_rows(store, name) for name in tables}
        now = DEMO_START + timedelta(minutes=5)
        # Turn 2's checkpoint: turn 3's was lost when the process died after the move committed.
        state = make_state(
            thread,
            turn4,
            now=now,
            text=_FOLLOWUP,
            settled=Settled(actions=(), open_case=None, read_at=DEMO_START),
        )
        sink = InMemoryTraceSink()
        deps, touched = make_deps(store.uow, trace=sink)
        ctx0 = make_ctx(thread, turn4, now=now)
        with sink.turn(ctx0.ids) as span:
            ctx = dataclasses.replace(ctx0, span=span)
            wrapped = timed_node(
                "load_context", cast(NodeFn, functools.partial(load_context, deps=deps)), deps
            )
            update = cast(LoadContextUpdate, wrapped(state, Runtime(context=ctx)))
            assert [n.name for n in sink.spans_for(span).nodes] == ["load_context"]

        # What the user sees: the settled panel names the new window.
        view = ReplyComposer().settled_view(update["settled"], update["identity"], update["controller"])
        assert view.visit is not None
        assert view.visit.date == date(2026, 10, 19)
        assert view.visit.window_label == "8:00 am – 12:00 pm"
        assert view.visit.status == "moved"
        assert view.identity.status == "verified"
        assert view.replying.kind == "ai"
        moved = [w for w in view.actions if w.kind == "moved"]
        assert len(moved) == 1 and "Oct 19" in moved[0].summary
        window = update["chat_window"]
        assert window[-1].text == _FOLLOWUP
        assert any("it's moved" in line.text for line in window)

        # What is stored: the node wrote nothing; the one action row is turn 3's; the issued file is untouched.
        assert {name: count_rows(store, name) for name in tables} == before
        with store.uow() as tx:
            rows = tx.core.actions.for_thread(thread)
        assert len(rows) == 1 and rows[0].key.turn_id == turn3
        assert touched == []
    assert hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest() == issued_hash_before


def test_j3_followup_reply_names_new_window_integrated() -> None:
    pytest.skip(
        "blocked-on AEA-51: the follow-up turn's reply naming the new window, through submitTurn on AEA-57's harness "
        "(run_graph not bound until AEA-51 lands J-3)"
    )
