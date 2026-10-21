"""AEA-05: typo-tolerant word rules (`gates/rules.py`). Expected values come from the plan, never from the module."""

from __future__ import annotations

import csv
import re
import uuid
from collections import Counter
from pathlib import Path

import pytest

from meridian.domain.handoff import HandoffReason
from meridian.domain.turn import RuleMatches, SafetyKind
from meridian.gates.rules import ALL_RULE_IDS, match_rules

REPO = Path(__file__).resolve().parents[3]
CALL_MAP = REPO / "docs" / "data" / "handoff-inventory-call-map.csv"
TRANSCRIPTS = REPO / "docs" / "data" / "issued" / "meridian_dataset" / "call_transcripts"
REVIEWED = Path(__file__).resolve().parent / "data" / "corpus_firings_reviewed.csv"

Labels = tuple[SafetyKind | None, bool, bool, bool, HandoffReason | None, bool]
NOTHING: Labels = (None, False, False, False, None, False)

_SAFETY_ID = {
    SafetyKind.GAS: "R5.gas",
    SafetyKind.CO: "R5.co",
    SafetyKind.SPARKS_SMOKE_FLAMES: "R5.sparks_smoke_flames",
    SafetyKind.BURNING_WITH_BREAKER: "R5.burning_with_breaker",
}


def _labels(m: RuleMatches) -> Labels:
    return (m.safety, m.burning_unclear, m.danger_words, m.person, m.policy_trigger, m.correction)


def test_wp5_co_alarm_is_co() -> None:
    for text in ("My carbon monoxide detector is going off.", "co alarm keeps going off"):
        m = match_rules(text)
        assert m.safety is SafetyKind.CO
        assert m.burning_unclear is False
        assert m.rule_ids == ("R5.co",)
        assert _labels(m) == (SafetyKind.CO, False, False, False, None, False)


def test_wp6_burning_smell_asks() -> None:
    m = match_rules("I need to schedule a service call. I smell something burning from the vents.")
    assert m.safety is None
    assert m.burning_unclear is True
    assert m.rule_ids == ("R7.burning_unclear",)


def test_wp7_refund_request() -> None:
    m = match_rules(
        "I want a full refund on the repair. It didn't fix anything and I had to call another company."
    )
    assert m.policy_trigger is HandoffReason.REFUND
    assert m.person is False
    assert m.rule_ids == ("R24.refund",)


_S, _H = SafetyKind, HandoffReason
# Expected labels by call-map category (each cites its source).
_EXPECTED: dict[str, Labels] = {
    "SAF-CO": (_S.CO, False, False, False, None, False),  # KB Immediate safety escalation
    "SAF-GAS": (_S.GAS, False, False, False, None, False),  # KB Immediate safety escalation
    "SAF-SPARK": (_S.SPARKS_SMOKE_FLAMES, False, False, False, None, False),  # KB Immediate safety escalation
    "SCH-BURNING": (None, True, False, False, None, False),  # R-7, D2
    "BILL-REFUND": (None, False, False, False, _H.REFUND, False),  # KB Supervisor escalation, R-24
    "BILL-DISPUTE": (None, False, False, False, _H.BILLING_DISPUTE, False),  # KB Supervisor escalation, R-24
    "COMPLAINT-CONDUCT": (None, False, False, True, _H.COMPLAINT_OR_MANAGER, False),  # R-2, PD-1
    "COMPLAINT-OPINION": (None, False, False, True, _H.COMPLAINT_OR_MANAGER, False),  # R-2, PD-1
    "COMPLAINT-REPEAT": (
        None,
        False,
        False,
        False,
        _H.COMPLAINT_OR_MANAGER,
        False,
    ),  # KB Supervisor escalation
    "COMMERCIAL": (None, False, False, False, _H.COMMERCIAL, False),  # KB Department redirects
}


def test_issued_templates_labelled() -> None:
    with CALL_MAP.open(encoding="utf-8", newline="") as fh:
        pairs = sorted({(r["initial"], r["template"]) for r in csv.DictReader(fh)})
    assert len(pairs) == 46
    bad = []
    for category, template in pairs:
        expected = _EXPECTED.get(
            category, NOTHING
        )  # every other category (BILL-DUP, MEM-CANCEL, ...) fires nothing
        if _labels(match_rules(template)) != expected:
            bad.append(category)
    assert not bad, f"templates mislabelled in categories: {sorted(set(bad))}"
    print("templates labelled: 46/46")


_SAFETY_CALLS = {
    "CALL-20260712-0046": SafetyKind.GAS,
    "CALL-20260728-0264": SafetyKind.GAS,
    "CALL-20260822-0185": SafetyKind.GAS,
    "CALL-20260721-0093": SafetyKind.CO,
    "CALL-20260805-0290": SafetyKind.CO,
    "CALL-20260816-0038": SafetyKind.CO,
    "CALL-20260822-0341": SafetyKind.CO,
    "CALL-20260905-0318": SafetyKind.CO,
    "CALL-20260717-0180": SafetyKind.SPARKS_SMOKE_FLAMES,
}


def test_corpus_firings_reviewed() -> None:
    expected: dict[tuple[str, int], tuple[str, ...]] = {}
    with REVIEWED.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            assert row["reason"].strip(), row["call_id"]
            expected[(row["call_id"], int(row["line_no"]))] = tuple(row["rule_ids"].split("+"))

    actual: dict[tuple[str, int], tuple[str, ...]] = {}
    safety_by_call: dict[str, set[SafetyKind]] = {}
    total = 0
    for path in sorted(TRANSCRIPTS.glob("*.txt")):
        for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.startswith("Customer:"):
                continue
            total += 1
            m = match_rules(line[len("Customer:") :].strip())
            if m.rule_ids:
                actual[(path.stem, no)] = m.rule_ids
            if m.safety is not None:
                safety_by_call.setdefault(path.stem, set()).add(m.safety)

    assert total == 2256
    missing = sorted(set(expected) - set(actual))
    unreviewed = sorted(set(actual) - set(expected))
    assert not missing and not unreviewed, f"missing={missing} unreviewed={unreviewed}"
    wrong = sorted(k for k in expected if expected[k] != actual[k])
    assert not wrong, f"rule ids differ at {wrong}"
    for call_id, kind in _SAFETY_CALLS.items():
        assert kind in safety_by_call.get(call_id, set()), call_id
    print(f"customer lines: {total}; safety calls: {len(_SAFETY_CALLS)}/9; reviewed firings: {len(expected)}")
    print(Counter(actual.values()))


_VARIANTS: list[tuple[str, str, SafetyKind, str, str]] = [
    # (case id, text, kind, varied dimension, clean source)
    ("gas-typo", "i smel gas near my furnce", SafetyKind.GAS, "typo", "SAF-GAS"),
    (
        "gas-mid",
        "Thanks for booking that. Also, I smell gas near my furnace now.",
        SafetyKind.GAS,
        "mid-chat",
        "SAF-GAS",
    ),
    ("gas-para", "there is a gas leak in the basement", SafetyKind.GAS, "paraphrase", "SAF-GAS"),
    ("gas-eggs", "smells like rotten eggs", SafetyKind.GAS, "paraphrase", "SAF-GAS"),
    ("gas-case", "I SMELL GAS NEAR MY FURNACE", SafetyKind.GAS, "case", "SAF-GAS"),
    ("gas-short", "gas smell by furnace", SafetyKind.GAS, "shorthand", "SAF-GAS"),
    ("co-typo", "my carbon monoxde detecter is going off", SafetyKind.CO, "typo", "SAF-CO"),
    (
        "co-mid",
        "ok the 2pm works. wait, my carbon monoxide detector just started going off",
        SafetyKind.CO,
        "mid-chat",
        "SAF-CO",
    ),
    ("co-para", "our monoxide alarm is sounding", SafetyKind.CO, "paraphrase", "SAF-CO"),
    ("co-case", "MY CARBON MONOXIDE DETECTOR IS GOING OFF", SafetyKind.CO, "case", "SAF-CO"),
    ("co-short", "co alarm keeps going off", SafetyKind.CO, "shorthand", "SAF-CO"),
    ("co-dots", "C.O. detector beeping", SafetyKind.CO, "shorthand", "SAF-CO"),
    (
        "spark-typo",
        "there are sprks coming from the outdoor unit",
        SafetyKind.SPARKS_SMOKE_FLAMES,
        "typo",
        "SAF-SPARK",
    ),
    (
        "spark-mid",
        "Before you look up my account, I just saw sparks coming out of the outdoor unit",
        SafetyKind.SPARKS_SMOKE_FLAMES,
        "mid-chat",
        "SAF-SPARK",
    ),
    (
        "spark-para",
        "flames are coming out of the furnace",
        SafetyKind.SPARKS_SMOKE_FLAMES,
        "paraphrase",
        "SAF-SPARK",
    ),
    (
        "spark-case",
        "THERE ARE SPARKS COMING FROM THE OUTDOOR UNIT",
        SafetyKind.SPARKS_SMOKE_FLAMES,
        "case",
        "SAF-SPARK",
    ),
    ("spark-short", "outdoor unit sparking", SafetyKind.SPARKS_SMOKE_FLAMES, "shorthand", "SAF-SPARK"),
    (
        "burn-typo",
        "i smell somthing burnign and the breker tripped",
        SafetyKind.BURNING_WITH_BREAKER,
        "typo",
        "synthetic",
    ),
    (
        "burn-mid",
        "Thursday is fine. Also there is a burning smell now and the breaker just tripped.",
        SafetyKind.BURNING_WITH_BREAKER,
        "mid-chat",
        "synthetic",
    ),
    (
        "burn-para",
        "there is an electrical burning odor and the circuit breaker keeps tripping",
        SafetyKind.BURNING_WITH_BREAKER,
        "paraphrase",
        "synthetic",
    ),
    (
        "burn-case",
        "I SMELL SOMETHING BURNING AND THE BREAKER TRIPPED",
        SafetyKind.BURNING_WITH_BREAKER,
        "case",
        "synthetic",
    ),
    ("burn-short", "burnt smell, breaker popped", SafetyKind.BURNING_WITH_BREAKER, "shorthand", "synthetic"),
]


@pytest.mark.parametrize(("text", "kind"), [(v[1], v[2]) for v in _VARIANTS], ids=[v[0] for v in _VARIANTS])
def test_safety_variants(text: str, kind: SafetyKind) -> None:
    m = match_rules(text)
    assert m.safety is kind
    assert m.burning_unclear is False
    assert m.rule_ids[0] == _SAFETY_ID[kind]


def test_safety_variant_grid_is_complete() -> None:
    dims = ("typo", "mid-chat", "paraphrase", "case", "shorthand")
    grid = Counter((v[2], v[3]) for v in _VARIANTS)
    for kind in SafetyKind:
        if kind in _SAFETY_ID:
            for dim in dims:
                assert grid[(kind, dim)] >= 1, f"{kind.value} x {dim}"
    for kind in _SAFETY_ID:
        print(kind.value, {d: grid[(kind, d)] for d in dims})
    assert len(_VARIANTS) == 22


def test_burning_paths() -> None:
    m = match_rules("I smell something burning and the breaker tripped.")
    assert m.safety is SafetyKind.BURNING_WITH_BREAKER and m.burning_unclear is False
    m = match_rules("I smell something burning and I see smoke.")
    assert m.safety is SafetyKind.SPARKS_SMOKE_FLAMES and m.burning_unclear is False
    m = match_rules("I need to schedule a service call. I smell something burning from the vents.")
    assert m.safety is None and m.burning_unclear is True


@pytest.mark.parametrize(
    "text",
    [
        "I don't know if the breaker tripped, but something smells burnt.",
        "I smell something burning but the breaker has not tripped.",
    ],
    ids=["breaker-unknown", "breaker-denied"],
)
def test_burning_breaker_unknown_or_denied_still_asks(text: str) -> None:
    m = match_rules(text)
    assert m.safety is None
    assert m.burning_unclear is True


@pytest.mark.parametrize(
    "text",
    [
        "My AC isn't cooling.",
        "the furnace wont kick on",
        "the ac runs but the air is warm",
        "my thermostat is blank",
        "the water heater pilot light keeps going out",
        "my mother is 88 and it's 95 degrees in here",
    ],
    ids=["wp3", "furnace", "ac-warm", "thermostat", "pilot", "danger-no-words"],
)
def test_comfort_reports_do_not_fire(text: str) -> None:
    m = match_rules(text)
    assert _labels(m) == NOTHING
    assert m.rule_ids == ()


@pytest.mark.parametrize(
    "text",
    [
        "Someone in the house is in danger",
        "My son can't breathe",
        "She cannot breathe",
        "He is having trouble breathing",
        "My father is not breathing",
        "My mom passed out",
        "My husband is unconscious",
        "Grandpa fainted",
        "I think she has heat stroke",
        "heatstroke",
        "This is a medical emergency",
    ],
)
def test_explicit_danger_phrases(text: str) -> None:
    m = match_rules(text)
    assert m.danger_words is True
    assert m.safety is None
    assert m.rule_ids == ("R8.danger_words",)


@pytest.mark.parametrize(
    "text",
    [
        "can I talk to a person",
        "I want to speak to a human",
        "connect me to a live agent",
        "representative please",
        "agent",
        "transfer me",
        "can someone call me back",
        "is this a real person?",
    ],
)
def test_person_requests(text: str) -> None:
    m = match_rules(text)
    assert m.person is True
    assert m.policy_trigger is None
    assert m.rule_ids == ("R2.person",)


@pytest.mark.parametrize(
    "text",
    [
        "I want to talk to a manager",
        "can I speak to your supervisor",
        "let me talk to someone in charge",
        "is your manager around",
    ],
)
def test_manager_requests_set_person_and_policy(text: str) -> None:
    m = match_rules(text)
    assert m.person is True
    assert m.policy_trigger is HandoffReason.COMPLAINT_OR_MANAGER
    assert m.rule_ids == ("R2.person", "R24.complaint_or_manager")


@pytest.mark.parametrize(
    "text",
    [
        "I spoke to a representative yesterday",
        "I need a person to come out and fix my AC",
        "I'm a manager at a bank",
        "don't need a human, just book me",
    ],
)
def test_not_a_person_request(text: str) -> None:
    assert match_rules(text).person is False


def test_manage_strip_center_is_commercial_not_person() -> None:
    m = match_rules("i manage a 12 unit strip center")
    assert m.person is False
    assert m.policy_trigger is HandoffReason.COMMERCIAL


@pytest.mark.parametrize(
    "text",
    [
        "that's not what I asked",
        "thats not waht i asked",
        "that's wrong",
        "thats wrnog",
        "no, I said Thursday",
        "no, i siad thursday",
    ],
)
def test_correction_phrases(text: str) -> None:
    m = match_rules(text)
    assert m.correction is True
    assert m.rule_ids == ("OD6.correction",)
    assert _labels(m) == (None, False, False, False, None, True)


@pytest.mark.parametrize("text", ["no", "No.", "no thanks", "not sure", "yes", "Yes please", "nope"])
def test_plain_replies_are_not_corrections(text: str) -> None:
    m = match_rules(text)
    assert m.correction is False
    assert m.rule_ids == ()


def test_rule_matches_hold_no_text() -> None:
    sentinel = "zq" + uuid.uuid4().hex[:12]
    m = match_rules(f"I smell gas near my furnace {sentinel} and I want a refund")
    assert m.rule_ids
    assert sentinel not in m.model_dump_json()
    assert sentinel not in repr(m)
    for rid in m.rule_ids:
        assert sentinel not in rid
        assert re.fullmatch(r"(R\d+|OD\d+)\.[a-z_]+", rid)
        assert rid in ALL_RULE_IDS
    assert len(ALL_RULE_IDS) == 13
    assert all(re.fullmatch(r"(R\d+|OD\d+)\.[a-z_]+", rid) for rid in ALL_RULE_IDS)


@pytest.mark.parametrize(
    ("text", "policy", "correction"),
    [
        ("I'm going to call my lawyer", HandoffReason.LEGAL_OR_CHARGEBACK, False),
        ("I want to file a chargeback", HandoffReason.LEGAL_OR_CHARGEBACK, False),
        ("I want a refund or I'll call my lawyer", HandoffReason.LEGAL_OR_CHARGEBACK, False),
        (
            "The tech quoted me $252 and the invoice says $312. That's not what I agreed to.",
            HandoffReason.BILLING_DISPUTE,
            False,
        ),
        ("I think I got charged twice", None, False),
        ("the tech was rude", HandoffReason.COMPLAINT_OR_MANAGER, False),
        ("do you guys do commercial work?", HandoffReason.COMMERCIAL, False),
        ("I want to cancel my comfort club membership", None, False),
        ("This is Sue Miller", None, False),
    ],
)
def test_policy_triggers(text: str, policy: HandoffReason | None, correction: bool) -> None:
    m = match_rules(text)
    assert m.policy_trigger is policy
    assert m.correction is correction
    if text == "the tech was rude":
        assert m.person is False
    if policy is None:
        assert _labels(m) == NOTHING


@pytest.mark.parametrize(
    "text",
    [
        "I don't smell gas",
        "there are no sparks",
        "no one is in danger",
        "no burning smell",
        "I don't want a refund",
        "I don't need to talk to a person",
    ],
)
def test_negated_mentions_do_not_fire(text: str) -> None:
    assert _labels(match_rules(text)) == NOTHING


def test_negation_ends_at_comma() -> None:
    assert match_rules("No, there are sparks").safety is SafetyKind.SPARKS_SMOKE_FLAMES


@pytest.mark.parametrize(
    "text",
    [
        "the fan keeps turning",
        "the burst pipe is leaking",
        "I spoke to the tech",
        "the top layer of insulation",
        "the tech dripped water",
        "the flame sensor needs cleaning",
        "the furnace won't fire up",
        "the motor burned out",
        "it's burning up in here",
    ],
)
def test_typo_correction_does_not_overreach(text: str) -> None:
    assert _labels(match_rules(text)) == NOTHING


@pytest.mark.parametrize(
    "text", ["", "   ", "[card number removed]", "[code]", "[code entered]", "[details submitted]"]
)
def test_empty_and_placeholder_text_fire_nothing(text: str) -> None:
    m = match_rules(text)
    assert _labels(m) == NOTHING
    assert m.rule_ids == ()


def test_rule_id_order() -> None:
    m = match_rules("I smell gas and my dad can't breathe, let me talk to a manager, that's wrong")
    assert m.rule_ids == (
        "R5.gas",
        "R8.danger_words",
        "R2.person",
        "R24.complaint_or_manager",
        "OD6.correction",
    )
