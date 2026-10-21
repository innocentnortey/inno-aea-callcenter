"""Typo-tolerant word rules for the gates (AEA-05, DO-3 section 4.1).

`match_rules(text)` answers which fixed rule a message matches (safety, burning, danger words, a request for a
person, a policy trigger, a correction) and decides nothing else. It normalises the text, corrects near-miss
spellings of a fixed keyword list token by token, then runs fixed regular expressions, ignoring a match that a
negation word just before it (same clause) cancels. Pure: no I/O, no logging, no clock.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final

from meridian.domain.handoff import HandoffReason
from meridian.domain.turn import RuleMatches, SafetyKind

# --- Rule ids (stable codes only, never message text) ---

_SAFETY_IDS: Final[dict[SafetyKind, str]] = {
    SafetyKind.GAS: "R5.gas",
    SafetyKind.CO: "R5.co",
    SafetyKind.SPARKS_SMOKE_FLAMES: "R5.sparks_smoke_flames",
    SafetyKind.BURNING_WITH_BREAKER: "R5.burning_with_breaker",
}
_POLICY_IDS: Final[dict[HandoffReason, str]] = {
    HandoffReason.REFUND: "R24.refund",
    HandoffReason.BILLING_DISPUTE: "R24.billing_dispute",
    HandoffReason.COMPLAINT_OR_MANAGER: "R24.complaint_or_manager",
    HandoffReason.LEGAL_OR_CHARGEBACK: "R24.legal_or_chargeback",
    HandoffReason.COMMERCIAL: "R24.commercial",
}
RULE_ID_BURNING_UNCLEAR: Final = "R7.burning_unclear"
RULE_ID_DANGER_WORDS: Final = "R8.danger_words"
RULE_ID_PERSON: Final = "R2.person"
RULE_ID_CORRECTION: Final = "OD6.correction"
ALL_RULE_IDS: Final[frozenset[str]] = frozenset(
    {
        *_SAFETY_IDS.values(),
        *_POLICY_IDS.values(),
        RULE_ID_BURNING_UNCLEAR,
        RULE_ID_DANGER_WORDS,
        RULE_ID_PERSON,
        RULE_ID_CORRECTION,
    }
)

# --- Word sets for typo tolerance ---

_NEGATIONS: Final = frozenset(
    {
        "no",
        "not",
        "dont",
        "doesnt",
        "didnt",
        "isnt",
        "arent",
        "wasnt",
        "werent",
        "hasnt",
        "havent",
        "never",
        "without",
        "nobody",
        "cant",
        "cannot",
    }
)
_WINDOW_STOPS: Final = frozenset({"|", "but", "though", "although", "however"})
# Keywords a near-miss token is corrected TO (all 6+ letters):
_FUZZY_TARGETS: Final = frozenset(
    """
carbon monoxide detector detectors alarming sparks sparking sparked smoking flames flaming burning scorched scorching
breaker breakers tripped tripping rotten breathe breathing unconscious fainted heatstroke emergency person somebody
someone representative operator supervisor manager refund refunded reimburse reimbursed reimbursement lawyer lawyers
attorney lawsuit chargeback dispute disputing overcharged overcharge complaint complain unprofessional commercial
warehouse rooftop misunderstood incorrect""".split()
)
# Tokens never corrected: short exact keywords, and real words one edit away from a target:
_KEEP_AS_IS: Final = frozenset(
    """
flame spark smoke alarm burnt burned carton manage managed manages layer layers trapped spares flakes flares burying
burping""".split()
)
# Explicit misspellings and shorthand for short words (looked up before anything else):
_TYPOS: Final[dict[str, str]] = {
    "c0": "co",
    "gass": "gas",
    "smel": "smell",
    "smeel": "smell",
    "smelt": "smell",
    "egs": "eggs",
    "eggz": "eggs",
    "alrm": "alarm",
    "alram": "alarm",
    "alarn": "alarm",
    "smoek": "smoke",
    "smok": "smoke",
    "smkoe": "smoke",
    "fier": "fire",
    "waht": "what",
    "wat": "what",
    "aksed": "asked",
    "askd": "asked",
    "asekd": "asked",
    "siad": "said",
    "wrnog": "wrong",
    "worng": "wrong",
    "wrogn": "wrong",
    "thta": "that",
    "taht": "that",
    "tahts": "thats",
    "nto": "not",
    "humna": "human",
    "hunam": "human",
    "speek": "speak",
    "spek": "speak",
    "tlak": "talk",
    "breker": "breaker",
}


def _index_targets(targets: frozenset[str]) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, list[str]] = {}
    for word in sorted(targets):
        grouped.setdefault(word[:2], []).append(word)
    return {prefix: tuple(words) for prefix, words in grouped.items()}


_TARGETS_BY_PREFIX: Final[dict[str, tuple[str, ...]]] = _index_targets(_FUZZY_TARGETS)
_APOSTROPHES: Final = str.maketrans({"‘": "'", "’": "'", "ʼ": "'", "`": "'"})

# --- Patterns (over normalised text) ---

_GAS: Final = r"\b(smell|smells|smelling|smelled|whiff|odor|odour)\b(?: [a-z0-9]+){0,3}? gas\b|\bgas (smell|smells|odor|odour|leak|leaks|leaking)\b|\bgas is leaking\b|\bleak(ing|s)? gas\b|\brotten eggs?\b|\b(sulfur|sulphur)\b"
_CO: Final = r"\bcarbon monoxide\b|\bmonoxide\b|\bco2? (alarm|alarms|alarming|detector|detectors|monitor|monitors|sensor)\b|\bco is (going off|beeping|alarming)\b"
_FIRE: Final = r"\b(spark|sparks|sparking|sparked|smoke|smoking|smoked|flames|flaming|on fire|caught fire|catching fire)\b|\bflame\b(?! (sensor|rod|rectifier))|\bfire\b(?! (up|ups|place|places|wood|works|department))"
_BURNING: Final = r"\b(burning|burnt|burned|scorch|scorched|scorching|melting)\b(?! (out|up|hot))"
_BREAKER_TRIPPED: Final = r"\bbreakers? (has |have |keeps |keep |was |were |is |just |had )?(tripped|tripping|trips|trip|flipped|popped|blew|blown)\b|\b(tripped|tripping|trip|flipped|popped|blew) (the |a |my |our |a few |two |some )?(circuit )?breakers?\b|\b(tripped|blown) (circuit )?breakers?\b"
_BREAKER_UNSURE: Final = (
    r"\b(if|whether|maybe|might have|may have)( the| a| my| our| any)?( circuit)? breakers?\b"
)
_DANGER: Final = r"\b(in danger|cant breathe|cannot breathe|can not breathe|trouble breathing|not breathing|passed out|unconscious|fainted|heatstroke|heat stroke|medical emergency)\b"
_PERSON: Final = r"\b(talk|speak|chat) (to|with) (a |an |the |some )?(someone|somebody|real|actual|live|human|humans|person|people|agent|representative|rep|staff|employee|operator)\b|\b(connect|transfer|put) me (to|with|through)\b|\btransfer me\b|\b(real|actual|live) (person|human|agent|representative|rep|people)\b|\b(want|need|get|like|request|prefer)\b(?: [a-z]+){0,2} (a |an )?(human|representative|operator)\b|\b(can|could|will|would|please|have) (someone|somebody|a person|a human|a rep|a representative) (call|phone|text) me\b|\b(want|need|like) (someone|somebody|a person) to (call|phone) me\b|^(operator|agent|representative|rep|human|person|a human|a person)( please)?( \|)?$"
_MANAGER: Final = r"\b(talk|speak|chat|complain|escalate this|escalate it) (to|with) (a |an |the |your |some )?(manager|supervisor|boss|owner)\b|\b(want|need|get|like|request|see|demand)\b(?: [a-z]+){0,2} (manager|supervisor)\b|(?<!im )(?<!am )(?<!was )(?<!as )\b(your|a) (manager|supervisor)\b|\b(someone|somebody|person|anyone) in charge\b|^(manager|supervisor)( please)?( \|)?$"
_LEGAL: Final = r"\b(lawyer|lawyers|attorney|attorneys|lawsuit|legal action|chargeback|charge back|small claims|better business bureau|bbb|suing|sued)\b|\b(going to|gonna|will|ill|could|can|might|want to|plan to|about to) sue\b|\bsue (you|meridian|your company|the company|them|your business)\b"
_REFUND: Final = r"\b(refund|refunds|refunded|money back|reimburse|reimbursed|reimbursement)\b"
_DISPUTE: Final = r"\bnot what i agreed\b|\bovercharg\w*|\bcharged (me )?(wrong|too much|for something|for work|for parts)\b|\bwrong (amount|charge|price|total)\b|\b(dispute|disputing)\b|\bdont (owe|agree)\b|\btake (that|it|the fee|the charge) off\b|\bshouldnt have to pay\b|\b(bill|invoice|charge|fee|price|total) (is|was|looks|seems) (wrong|too high)\b"
_COMPLAINT: Final = r"\b(rude|tracked mud|unprofessional|disrespectful|ripped off|scam|second opinion|shoddy|sloppy work|poor workmanship|bad workmanship)\b|\bcalled (two|three|four|five|2|3|4|5|several|multiple|many) times\b|\b(nobody|no one|noone)( has| have| ever| even)* (called|call|got|gotten) (me )?back\b|\bnever (called|call|got|gotten) (me )?back\b|\b(file|make|lodge|register) a complaint\b|\bwant to complain\b|\bcomplain about\b"
_COMMERCIAL: Final = r"\b(commercial|strip (center|mall|plaza)|shopping (center|mall|plaza)|rooftop units?|rtus?|office (building|park|space)|warehouse|retail (space|store|building))\b"
_CORRECTION: Final = r"\bthats not what i (asked|said|meant|wanted|was asking)\b|\bnot what i (asked|meant)\b|\b(no|nope|but|again)( \|)? i (said|meant|asked)\b|\b(thats|that is|that was|this is|you are|youre|your) (wrong|incorrect|not right|not correct)\b|\byou (misunderstood|misheard|got it wrong|got that wrong|have it wrong|are not listening|arent listening|re not listening)\b|\bi (didnt|did not) (ask|say|mean) (that|this|for that|about that)\b|\b(wrong answer|not my question|you didnt answer my question)\b"

_GAS_RX: Final[re.Pattern[str]] = re.compile(_GAS)
_CO_RX: Final[re.Pattern[str]] = re.compile(_CO)
_FIRE_RX: Final[re.Pattern[str]] = re.compile(_FIRE)
_BURNING_RX: Final[re.Pattern[str]] = re.compile(_BURNING)
_BREAKER_TRIPPED_RX: Final[re.Pattern[str]] = re.compile(_BREAKER_TRIPPED)
_BREAKER_UNSURE_RX: Final[re.Pattern[str]] = re.compile(_BREAKER_UNSURE)
_DANGER_RX: Final[re.Pattern[str]] = re.compile(_DANGER)
_PERSON_RX: Final[re.Pattern[str]] = re.compile(_PERSON)
_MANAGER_RX: Final[re.Pattern[str]] = re.compile(_MANAGER)
_LEGAL_RX: Final[re.Pattern[str]] = re.compile(_LEGAL)
_REFUND_RX: Final[re.Pattern[str]] = re.compile(_REFUND)
_DISPUTE_RX: Final[re.Pattern[str]] = re.compile(_DISPUTE)
_COMPLAINT_RX: Final[re.Pattern[str]] = re.compile(_COMPLAINT)
_COMMERCIAL_RX: Final[re.Pattern[str]] = re.compile(_COMMERCIAL)
_CORRECTION_RX: Final[re.Pattern[str]] = re.compile(_CORRECTION)

# --- Helpers ---


def _within_one_edit(a: str, b: str) -> bool:
    """True when the optimal-string-alignment distance of a and b is at most one."""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if la == lb:
        diffs = [i for i in range(la) if a[i] != b[i]]
        if len(diffs) == 1:
            return True
        return (
            len(diffs) == 2
            and diffs[1] == diffs[0] + 1
            and a[diffs[0]] == b[diffs[1]]
            and a[diffs[1]] == b[diffs[0]]
        )
    if abs(la - lb) != 1:
        return False
    longer, shorter = (a, b) if la > lb else (b, a)
    return any(longer[:i] + longer[i + 1 :] == shorter for i in range(len(longer)))


def _canonical(token: str) -> str:
    if token in _TYPOS:
        return _TYPOS[token]
    if token in _FUZZY_TARGETS or token in _KEEP_AS_IS or len(token) < 5:
        return token
    hits = [k for k in _TARGETS_BY_PREFIX.get(token[:2], ()) if _within_one_edit(token, k)]
    return hits[0] if len(hits) == 1 else token


def _normalise(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).translate(_APOSTROPHES).lower().replace("'", "")
    t = re.sub(r"\b([a-z])\.([a-z])\.?(?![a-z])", r"\1\2", t)
    t = re.sub(r"\b([a-z])/([a-z])\b", r"\1\2", t)
    t = re.sub(r"[.?!,;:\n\r]+", " | ", t)
    t = re.sub(r"[^a-z0-9| ]+", " ", t)
    t = re.sub(r"([a-z])\1{2,}", r"\1\1", t)
    return " ".join(tok if tok == "|" else _canonical(tok) for tok in t.split())


def _negated(t: str, start: int) -> bool:
    toks = t[:start].split()
    cut = 0
    for i in range(len(toks) - 1, -1, -1):
        if toks[i] in _WINDOW_STOPS:
            cut = i + 1
            break
    return any(w in _NEGATIONS for w in toks[cut:][-3:])


def _fires(pattern: re.Pattern[str], t: str) -> bool:
    return any(not _negated(t, m.start()) for m in pattern.finditer(t))


# --- Public function ---


def match_rules(text: str) -> RuleMatches:
    """Which fixed word rules does this message match? Pure; never raises on any string."""
    t = _normalise(text)
    burning = _fires(_BURNING_RX, t)
    tripped = _fires(_BREAKER_TRIPPED_RX, t) and _BREAKER_UNSURE_RX.search(t) is None

    safety: SafetyKind | None
    if _fires(_GAS_RX, t):
        safety = SafetyKind.GAS
    elif _fires(_CO_RX, t):
        safety = SafetyKind.CO
    elif _fires(_FIRE_RX, t):
        safety = SafetyKind.SPARKS_SMOKE_FLAMES
    elif burning and tripped:
        safety = SafetyKind.BURNING_WITH_BREAKER
    else:
        safety = None

    burning_unclear = burning and safety is None
    danger_words = _fires(_DANGER_RX, t)
    manager = _fires(_MANAGER_RX, t)
    person = manager or _fires(_PERSON_RX, t)

    policy: HandoffReason | None
    if _fires(_LEGAL_RX, t):
        policy = HandoffReason.LEGAL_OR_CHARGEBACK
    elif _fires(_REFUND_RX, t):
        policy = HandoffReason.REFUND
    elif _fires(_DISPUTE_RX, t):
        policy = HandoffReason.BILLING_DISPUTE
    elif manager or _fires(_COMPLAINT_RX, t):
        policy = HandoffReason.COMPLAINT_OR_MANAGER
    elif _fires(_COMMERCIAL_RX, t):
        policy = HandoffReason.COMMERCIAL
    else:
        policy = None

    correction = _fires(_CORRECTION_RX, t)

    ids: list[str] = []
    if safety is not None:
        ids.append(_SAFETY_IDS[safety])
    if burning_unclear:
        ids.append(RULE_ID_BURNING_UNCLEAR)
    if danger_words:
        ids.append(RULE_ID_DANGER_WORDS)
    if person:
        ids.append(RULE_ID_PERSON)
    if policy is not None:
        ids.append(_POLICY_IDS[policy])
    if correction:
        ids.append(RULE_ID_CORRECTION)

    return RuleMatches(
        safety=safety,
        burning_unclear=burning_unclear,
        danger_words=danger_words,
        person=person,
        policy_trigger=policy,
        rule_ids=tuple(ids),
        correction=correction,
    )
