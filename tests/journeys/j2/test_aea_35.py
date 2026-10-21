"""J-2 (slice plan §0a), AEA-35 steps: billing and warranty answers stay inside the specialist brakes and show the
source they used. Level today: mock-tested (real SpecialistRunner and SPECS; gateway, dispatcher and executors are
doubles; no server, no DB). The integrated steps (the answer's source on the real turn; the lookup_log rows in the
harness's DB copy) are blocked by AEA-51 (integrated customer path; it wires the graph that AEA-57's merged harness
drives and lands J-2). Synthetic values only.
"""

from __future__ import annotations

import pytest

from meridian.domain.common import CustomerId
from meridian.domain.specialists import AccountCapture
from meridian.domain.tools import ToolKind
from meridian.domain.turn import TaskIntent
from meridian.policy.limits import Brakes
from meridian.ports.models import ToolCall
from tests.fakes import FakeToolModel, InMemoryTraceSink
from tests.unit.agent.specialists._doubles import (
    INV_204411,
    WARRANTY,
    ScriptedDispatcher,
    ScriptedGateway,
    dispatched,
    make_runner,
    make_task,
    report_call,
    scope,
    step,
    tool_call,
    turn_ctx,
)

pytestmark = pytest.mark.journey


def test_j2_billing_answer_shows_invoice_source() -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel(
        [
            step(tool_call("c1", "read_invoices")),
            step(report_call("r1", summary="One unpaid invoice.")),
        ]
    )
    task = make_task("account", TaskIntent.READ_INVOICE, "I got an invoice and I'm not sure what it's for.")
    with turn_ctx(sink) as ctx:

        def handler(call: ToolCall):
            return dispatched(
                call,
                ctx,
                kind=ToolKind.ACCOUNT_READ,
                for_model={"invoices": [INV_204411.model_dump(mode="json")]},
                captured=AccountCapture(invoices=(INV_204411,), staff_notes=()),
                record_ids=("INV-204411",),
            )

        dispatcher = ScriptedDispatcher(handler)
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        result = runner.run(task, scope(ctx, customer_id=CustomerId("MHC-10002")), ctx)
    assert result.status == "read"
    assert result.invoices[0].invoice_id == "INV-204411"
    assert [line.amount_cents for line in result.invoices[0].lines] == [8900, 24500, 14400]
    assert result.tools[0].record_ids == ("INV-204411",)
    assert len(dispatcher.batches) <= Brakes().tool_rounds
    assert result.brake is None
    assert len(dispatcher.dispatched_calls) == len(result.tools) == 1


def test_j2_warranty_answer_shows_warranty_source() -> None:
    sink = InMemoryTraceSink()
    model = FakeToolModel(
        [
            step(tool_call("c1", "read_warranty")),
            step(report_call("r1", summary="Parts covered.")),
        ]
    )
    task = make_task("account", TaskIntent.READ_WARRANTY, "Is my system still under warranty?")
    with turn_ctx(sink) as ctx:

        def handler(call: ToolCall):
            return dispatched(
                call,
                ctx,
                kind=ToolKind.ACCOUNT_READ,
                for_model={"warranty": WARRANTY.model_dump(mode="json")},
                captured=AccountCapture(warranty=WARRANTY),
                record_ids=("customer:MHC-10002",),
            )

        dispatcher = ScriptedDispatcher(handler)
        runner = make_runner(ScriptedGateway(model), model, dispatcher, sink)
        result = runner.run(task, scope(ctx, customer_id=CustomerId("MHC-10002")), ctx)
    assert result.status == "read"
    assert result.warranty == WARRANTY
    assert result.tools[0].record_ids == ("customer:MHC-10002",)
    assert result.brake is None
