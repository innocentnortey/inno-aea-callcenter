"""J-2 (slice plan 0a; WP-2, WP-1), extended by AEA-38.

Level today: mock-tested (real facts, responder and checks nodes through AEA-21's `timed_node`, the real
`ModelGateway` over a scripted `FakeStructuredModel`, the real `ReplyComposer`, on a temp SQLite copy of the issued DB;
no server, no route). The integrated steps (CON-2 on AEA-57's harness with the scripted model) are blocked by AEA-40
(`startChatSession`, `submitTurn`) and AEA-51 (`run_graph`, `reply_composer`; it lands J-2).
"""

from __future__ import annotations

import functools
import hashlib
from typing import cast

import pytest

from meridian.agent.graph import NodeFn, timed_node
from meridian.agent.nodes import reply
from meridian.agent.nodes.compose import ReplyComposer
from meridian.domain.blocks import TextBlock
from meridian.domain.state import ChatLine
from meridian.domain.turn import ResponderDraft
from tests.fakes import FakeStructuredModel
from tests.fixtures.sqlite import ISSUED_DB, temp_sqlite
from tests.journeys.support.run import JourneyRun
from tests.unit.agent.nodes.reply_fixtures import (
    NOW,
    STAFF_NOTE_TEXT,
    TURN_4,
    WP2_KEPT,
    WP2_LOOKUP_TEXT,
    WP2_QUESTION,
    account_read,
    deps,
    gateway,
    knowledge_answered,
    run,
    seed,
    state,
    turn_ctx,
    turn_input,
    wp2_draft,
)

pytestmark = pytest.mark.journey

_NEEDS = ("session_service", "turn_service", "run_graph", "reply_composer")
_OPERATIONS = ("startChatSession", "submitTurn")


def test_j2_wp2_reply_keeps_billed_amounts_mock() -> None:
    before = hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest()
    with temp_sqlite() as store:
        ids = seed(
            store,
            customer=[(TURN_4, WP2_QUESTION)],
            lookups=[(TURN_4, 0, WP2_LOOKUP_TEXT, ("INV-204411",))],
        )
        fake = FakeStructuredModel([ResponderDraft(text=wp2_draft())])
        gw, _ = gateway(responder=fake)
        d = deps(uow=store.uow, gw=gw)
        ctx = turn_ctx()
        rt = run(ctx)
        st = state(
            turn_input=turn_input(message_id=ids[0], text=WP2_QUESTION),
            chat_window=[ChatLine(speaker="customer", text=WP2_QUESTION, turn_id=TURN_4, at=NOW)],
            specialist_results=[account_read(), knowledge_answered()],
        )
        for name, fn in (("facts", reply.facts), ("responder", reply.responder), ("checks", reply.checks)):
            node = timed_node(name, cast(NodeFn, functools.partial(fn, deps=d)), d)
            st = st.model_copy(update=dict(node(st, rt)))
        out = ReplyComposer().compose(st, ctx)
    assert st.checked is not None
    assert st.checked.text == WP2_KEPT
    assert [(e.check, e.result) for e in st.checked.events] == [("completion", "pass"), ("fact", "trimmed")]
    assert st.checked.removals[0].reason == "not_in_evidence"
    chips = [b for b in out.blocks if isinstance(b, TextBlock) and b.text == WP2_KEPT]
    assert len(chips) == 1
    assert [s.file for s in chips[0].sources] == ["faq/customer_faq.md"]
    banned = "$" + "149"
    assert banned not in out.model_dump_json()
    assert all(banned not in e.model_dump_json() for e in st.checked.events)
    assert len(fake.requests) == 1
    sent = fake.requests[0]
    assert STAFF_NOTE_TEXT not in sent.system_dynamic + sent.user
    assert hashlib.sha256(ISSUED_DB.read_bytes()).hexdigest() == before


def test_j2_wp2_invoice_turn_through_con2(journey: JourneyRun) -> None:
    with journey.step(
        "J-2",
        "reply 1 WP-2 invoice turn: billed $89 / $245 / $144 with a source chip, no $149, "
        "completion and fact check_events stored",
        needs=_NEEDS,
        operations=_OPERATIONS,
    ):
        pytest.skip("J-2 WP-2 body is written when AEA-51 lands the scripted graph outputs (AEA-38 plan R-8)")


def test_j2_wp1_cites_current_membership_document(journey: JourneyRun) -> None:
    with journey.step(
        "J-2",
        "reply 2 WP-1 answer cites membership/comfort_club_overview.md, never archive/comfort_club_overview.md",
        needs=_NEEDS,
        operations=_OPERATIONS,
    ):
        pytest.skip("J-2 WP-1 body is written when AEA-51 lands the scripted graph outputs (AEA-38 plan R-8)")
