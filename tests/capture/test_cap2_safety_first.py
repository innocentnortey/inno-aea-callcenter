"""CAP-2 (WF-1 safety): the safety reply comes before any model, lookup or identity step. Spans are read in start order;
the case rows and the stored turn show the same order."""

from __future__ import annotations

from typing import Any

import pytest

from tests.graph import worked_pair_scenarios as sc
from tests.integration.customer_support import (
    RunOptions,
    build_capture_sink,
    finished_spans,
    open_customer_run,
)
from tests.unit.adapters._tracing_doubles import close_all, trace_hex


def spans_of_turn(spans: list[Any], trace_id: str) -> list[Any]:
    return [s for s in spans if trace_hex(s) == trace_id]


def test_wp5_no_model_span_before_safety(request: pytest.FixtureRequest) -> None:
    """AC-21 (WP-5): no model_call span, no tool span, no lookup and no identity row: a P0 case exists and the safety card
    was the first block."""
    registry: list[Any] = []
    sink, exporter = build_capture_sink(registry)
    try:
        with open_customer_run(request, RunOptions(trace=sink)) as run:
            result = sc.wp5(run)
            row = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (result.turn_ids[0],))
            names = [s.name for s in spans_of_turn(finished_spans(sink, exporter), row["trace_id"])]
            assert not [n for n in names if n.startswith(("model_call:", "tool:"))], names
            assert (row["gate_result"], row["outcome"], row["model_calls"]) == ("safety", "safety_reply", 0)
            [case] = run.db.rows("SELECT * FROM cases WHERE thread_id = ?", (result.thread_id,))
            assert (case["reason"], case["priority"]) == ("safety", "P0")
            assert run.db.count("lookup_log", "thread_id = ?", (result.thread_id,)) == 0
            assert (
                run.db.count(
                    "identity_threads", "thread_id = ? AND status != 'not_checked'", (result.thread_id,)
                )
                == 0
            )
            first = result.responses[0].json()["blocks"][0]
            assert first["type"] == "safety"
    finally:
        close_all(registry)


def test_danger_only_routing_spans(request: pytest.FixtureRequest) -> None:
    """AC-21 (DANGER): the only model spans before the emergency reply are the planner's and the classifier's; there is
    no tool span; a P1 case exists; nothing was looked up and nobody was identified first."""
    registry: list[Any] = []
    sink, exporter = build_capture_sink(registry)
    try:
        with open_customer_run(request, RunOptions(trace=sink)) as run:
            result = sc.danger(run)
            row = run.db.one("SELECT * FROM turns WHERE turn_id = ?", (result.turn_ids[0],))
            spans = spans_of_turn(finished_spans(sink, exporter), row["trace_id"])
            names = [s.name for s in spans]
            models = sorted(n for n in names if n.startswith("model_call:"))
            assert models == ["model_call:classifier", "model_call:planner"]
            assert not [n for n in names if n.startswith("tool:")]
            [case] = run.db.rows("SELECT * FROM cases WHERE thread_id = ?", (result.thread_id,))
            assert (case["reason"], case["priority"]) == ("danger", "P1")
            assert run.db.count("lookup_log", "thread_id = ?", (result.thread_id,)) == 0
            assert (
                run.db.count(
                    "identity_threads", "thread_id = ? AND status != 'not_checked'", (result.thread_id,)
                )
                == 0
            )
    finally:
        close_all(registry)
