"""AEA-01 AC-3 and AC-4: every shared limit has its value and its source, and the set is frozen."""

from __future__ import annotations

import ast
import dataclasses
import operator
from pathlib import Path
from typing import Any

import pytest

import meridian.policy.limits as limits_mod
from meridian.policy.limits import Limits

ROWS: list[tuple[str, Any, str]] = [
    ("turn.deadline_s", 60, "SDQ-1; DO-4 §2"),
    ("turn.turn_deadline_ms", 60000, "api-con-mapping §0"),
    ("turn.still_working_after_ms", 10000, "api-con-mapping §0; SCR-1"),
    ("turn.browser_grace_s", 5, "DO-3 §2.3 rule 5"),
    ("turn.browser_give_up_after_ms", 65000, "api-con-mapping §0"),
    ("turn.max_message_chars", 2000, "api-con-mapping §0"),
    ("admission.max_in_flight", 30, "SDQ-9"),
    ("brakes.tasks_per_turn", 3, "code-design §4.1"),
    ("brakes.tool_rounds", 2, "graph-tools C-9"),
    ("brakes.sonnet_calls", 6, "models.md cross-topic 3"),
    ("identity.code_ttl_s", 600, "R-15"),
    ("identity.tries", 3, "R-15"),
    ("identity.max_sends", 3, "graph-tools C-9"),
    ("booking.max_per_conversation", 3, "code-design §4.1; R-41"),
    ("spend.daily_cap_usd", 30.0, "models.md §6; M-26"),
    ("web.chat_turns_per_thread_per_min", 20, "web.md §5"),
    ("web.chat_turns_per_session_per_min", 600, "web.md §5"),
    ("web.chat_turns_per_ip_per_min", 600, "web.md §5"),
    ("web.reads_per_session_per_min", 120, "web.md §5"),
    ("web.reads_per_ip_per_min", 240, "web.md §5"),
    ("web.login_rejects_per_ip", 10, "web.md §5"),
    ("web.login_reject_window_s", 600, "web.md §5"),
    ("web.resets_per_ip", 10, "web.md §5"),
    ("web.reset_window_s", 600, "web.md §5"),
    ("web.login_session_lifetime_s", 43_200, "web.md §5; WEB-5"),
    ("web.reset_wait_s", 5, "web.md §7"),
    ("context.window_turns", 10, "graph-core §7"),
    ("context.window_line_chars", 600, "graph-core §7"),
    ("context.window_total_chars", 8000, "graph-core §7"),
    ("context.planner_lines", 6, "graph-core §7; DO-4 §3"),
    ("context.planner_line_chars", 400, "graph-core §7; DO-4 §3"),
]
PROPERTIES = ("turn.turn_deadline_ms", "turn.browser_give_up_after_ms")


@pytest.mark.parametrize(("path", "expected", "source"), [pytest.param(*row, id=row[0]) for row in ROWS])
def test_values_match_their_sources(path: str, expected: Any, source: str) -> None:
    assert operator.attrgetter(path)(Limits()) == expected, f"{path} should be {expected} ({source})"


def test_every_field_has_a_source_case() -> None:
    covered = {row[0] for row in ROWS}
    limits = Limits()
    expected: set[str] = set(PROPERTIES)
    for part in dataclasses.fields(limits):
        for f in dataclasses.fields(getattr(limits, part.name)):
            expected.add(f"{part.name}.{f.name}")
    assert expected <= covered, f"fields without a source row: {sorted(expected - covered)}"


def test_frozen_and_single_literal() -> None:
    limits = Limits()
    for obj in (limits, *(getattr(limits, f.name) for f in dataclasses.fields(limits))):
        for f in dataclasses.fields(obj):
            with pytest.raises(dataclasses.FrozenInstanceError):
                setattr(obj, f.name, 1)
    assert limits.turn.turn_deadline_ms == limits.turn.deadline_s * 1000

    tree = ast.parse(Path(limits_mod.__file__).read_text(encoding="utf-8"))
    for node in tree.body:
        assert isinstance(node, ast.ImportFrom | ast.ClassDef | ast.Expr), ast.dump(node)[:60]
        assert not isinstance(node, ast.Assign | ast.AnnAssign)

    public = [
        n
        for n in dir(limits_mod)
        if not n.startswith("_")
        and getattr(getattr(limits_mod, n), "__module__", None) == limits_mod.__name__
    ]
    print("public names:", public)
    assert public
    assert all(isinstance(getattr(limits_mod, n), type) for n in public)
