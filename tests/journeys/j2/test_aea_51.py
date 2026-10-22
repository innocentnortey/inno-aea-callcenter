"""J-2 (slice plan section 0a), AEA-51 steps: grounded answers that are never stale. Real app, real graph and index,
scripted model at the provider boundary (level: integrated with a scripted model)."""

from __future__ import annotations

import json

import pytest

from tests.graph import worked_pair_scenarios as sc
from tests.integration.customer_api import blocks
from tests.integration.customer_support import RunOptions, open_customer_run

pytestmark = pytest.mark.journey

J2 = "J-2"
CHAT = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
TURN = (*CHAT, "turn_service", "run_graph")
IDENTITY = (*TURN, "identity_service", "handoff_service")
OPS = ("login", "startChatSession", "submitTurn")


def test_j2_grounded_answers_never_stale(request: pytest.FixtureRequest) -> None:
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        with run.step(J2, "1 membership answer from a current file", needs=TURN, operations=OPS):
            answer = sc.wp1(run, client)
            [response] = answer.responses
            cited = [src["file"] for b in blocks(response, "text") for src in b["sources"]]
            assert cited and not any(f.startswith("archive/") for f in cited)
            lookups = run.db.rows(
                "SELECT passage_ids FROM lookup_log WHERE thread_id = ?", (answer.thread_id,)
            )
            assert lookups and not any(
                p.startswith("archive/") for r in lookups for p in json.loads(r["passage_ids"])
            )
            assert sc.ARCHIVE_PRICE not in " ".join(str(b.get("text", "")) for b in blocks(response))
            print(f"step 1: cited={sorted(set(cited))} lookups={len(lookups)}")
        with run.step(J2, "2 invoice facts after the code", needs=IDENTITY, operations=OPS):
            invoice = sc.wp2(run, client)
            card = blocks(invoice.responses[2], "account_card")[0]
            assert card["invoice"]["invoice_id"] == "INV-204411"
            assert run.db.count("actions", "thread_id = ? AND kind = 'verified'", (invoice.thread_id,)) == 1
            assert (
                run.db.count("lookup_log", "thread_id = ? AND tool = 'read_invoices'", (invoice.thread_id,))
                >= 1
            )
            print(f"step 2: invoice={card['invoice']['invoice_id']} lines={len(card['invoice']['lines'])}")
