"""AEA-02 AC-9 and AC-19: CheckEvent builders, gate_result table, TurnBudget."""

from __future__ import annotations

import time

import pytest

from meridian.domain.common import Halt, HaltReason, ProviderFailure, ProviderFailureKind, TurnId
from meridian.domain.turn import (
    CheckEvent,
    DangerAssessment,
    GateDecision,
    GateKind,
    Removal,
    RuleMatches,
    TurnBudget,
)

TURN = TurnId("6f1c1d7e-3a0b-4c55-9e1a-0d3b5c7a9e21")


def _rules(*rule_ids: str) -> RuleMatches:
    return RuleMatches(
        safety=None,
        burning_unclear=False,
        danger_words=False,
        person=False,
        policy_trigger=None,
        rule_ids=rule_ids,
        correction=False,
    )


def _gate(kind: GateKind, answer: str | None = None, rule_ids: tuple[str, ...] = ()) -> GateDecision:
    return GateDecision.model_validate({"kind": kind, "rules": _rules(*rule_ids), "burning_answer": answer})


def _removal(kind: str) -> Removal:
    return Removal.model_validate(
        {"claim": {"kind": kind, "span": (0, 1), "value": "v"}, "reason": "not_in_evidence"}
    )


def test_check_event_builders() -> None:
    clean = CheckEvent.from_check("fact", TURN, ())
    assert (clean.result, clean.removed, clean.claim_kinds, clean.codes) == ("pass", 0, (), ())
    trimmed = CheckEvent.from_check(
        "completion", TURN, [_removal("time"), _removal("amount"), _removal("time")]
    )
    assert (trimmed.result, trimmed.removed, trimmed.claim_kinds) == ("trimmed", 3, ("amount", "time"))
    fallback = CheckEvent.from_check("brief_fact", TURN, [_removal("id")], fallback=True)
    assert fallback.result == "fallback"

    assert CheckEvent.from_gate(TURN, _gate(GateKind.FREE_TEXT)).result == "pass"
    assert CheckEvent.from_gate(TURN, _gate(GateKind.FREE_TEXT, rule_ids=("r1",))).result == "fired"
    fired = CheckEvent.from_gate(TURN, _gate(GateKind.SAFETY, rule_ids=("r1",)))
    assert (fired.result, fired.codes) == ("fired", ("safety", "r1"))

    failure = ProviderFailure(
        kind=ProviderFailureKind.TIMEOUT,
        provider="openrouter_jev",
        http_status=None,
        retry_after_s=None,
        retryable=True,
        provider_request_id=None,
    )
    fell_back = CheckEvent.from_danger(TURN, DangerAssessment(label="normal", raised=False, failure=failure))
    assert (fell_back.result, fell_back.codes) == ("fallback", ("fallback", "timeout"))
    raised = CheckEvent.from_danger(TURN, DangerAssessment(label="danger", raised=True, failure=None))
    assert (raised.result, raised.codes) == ("raised", ("danger",))
    assert (
        CheckEvent.from_danger(TURN, DangerAssessment(label="normal", raised=False, failure=None)).result
        == "pass"
    )

    braked = CheckEvent.from_halt(TURN, Halt(reason=HaltReason.BRAKE_TASKS, node="plan_join", elapsed_ms=5))
    assert (braked.check, braked.result, braked.codes) == ("brake", "fired", ("brake_tasks", "plan_join"))
    for reason in (HaltReason.DEADLINE, HaltReason.SPEND_CAP, HaltReason.PROVIDER_SPEND_CAP):
        with pytest.raises(ValueError, match="no brake event"):
            CheckEvent.from_halt(TURN, Halt(reason=reason, node="n", elapsed_ms=1))


def test_gate_result_mapping() -> None:
    for kind in (GateKind.CODE_ENTRY, GateKind.LOCATE, GateKind.CARD_CHOICE, GateKind.FREE_TEXT):
        assert _gate(kind).gate_result() == "clear"


_TABLE = [
    (GateKind.SAFETY, None, "safety"),
    (GateKind.AI_PAUSED, None, "ai_paused"),
    (GateKind.BURNING_ASK, None, "burning_unclear"),
    (GateKind.BURNING_ANSWER, "yes", "safety"),
    (GateKind.BURNING_ANSWER, "unsure", "burning_unclear"),
    (GateKind.BURNING_ANSWER, "no", "clear"),
    (GateKind.DANGER_RULE, None, "danger"),
    (GateKind.PERSON, None, "person_requested"),
    (GateKind.CODE_ENTRY, None, "clear"),
    (GateKind.LOCATE, None, "clear"),
    (GateKind.CARD_CHOICE, None, "clear"),
    (GateKind.FREE_TEXT, None, "clear"),
]


@pytest.mark.parametrize(("kind", "answer", "expected"), _TABLE)
def test_gate_result_table(kind: GateKind, answer: str | None, expected: str) -> None:
    print(f"{kind.value:16} {answer or '-':7} -> {expected}")
    assert _gate(kind, answer).gate_result() == expected


def test_gate_table_covers_every_kind() -> None:
    assert {kind for kind, _, _ in _TABLE} == set(GateKind)


def test_burning_answer_needs_an_answer() -> None:
    with pytest.raises(ValueError, match="needs burning_answer"):
        _gate(GateKind.BURNING_ANSWER).gate_result()


def test_turn_budget_timeout_for() -> None:
    now = time.monotonic()
    plenty = TurnBudget(started=now, deadline=now + 60)
    assert plenty.timeout_for(8.0) == 8.0
    short = TurnBudget(started=now, deadline=now + 3.0)
    result = short.timeout_for(8.0)
    assert result is not None
    assert 1.0 <= result <= 3.0
    spent = TurnBudget(started=now - 60, deadline=now - 1)
    assert spent.remaining() == 0.0
    assert spent.timeout_for(8.0) is None
    nearly = TurnBudget(started=now, deadline=now + 0.5)
    assert nearly.timeout_for(8.0) is None
    assert nearly.timeout_for(8.0, min_call_s=0.1) is not None
