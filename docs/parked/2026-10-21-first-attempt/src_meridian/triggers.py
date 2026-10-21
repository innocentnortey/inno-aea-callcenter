"""Deterministic message checks that run before any model step (PRD R-2, R-5, R-7, R-8; D2, D5, OD-4)."""
from __future__ import annotations

import re
from dataclasses import dataclass

SAFETY_INSTRUCTION = (
    "Please leave the home now and call 911 or your gas utility from outside. "
    "Don't flip any light switches, open windows near the furnace, or restart any equipment."
)

_GAS = r"\b(smell(s|ing)?\s+(of\s+)?gas|gas\s+(smell|leak|odor|odour)|rotten[- ]?eggs?|natural gas)\b"
_CO = r"\b(carbon monoxide|co\s+(alarm|detector|monitor)|co2? detector|monoxide)\b"
_FIRE = r"\b(sparks?|sparking|smoke|smoking unit|flames?|on fire|fire)\b"
_BURNING = r"\b(burning|burnt|scorch(ed|ing)?)\b"
_BREAKER_TRIPPED = r"\b(breakers?\s+(has\s+|have\s+|keeps?\s+|was\s+|were\s+)?(tripped|tripping|trips|flipped|popped)|tripped\s+(the\s+)?breakers?)\b"
_BREAKER_NO = r"\b(no|not|didn'?t|hasn'?t|haven'?t)\b[^.?!]{0,30}\b(trip|tripped|breaker)"
_URGENT = (r"\b(no heat|heat(ing)? (is )?(not working|out|broken)|furnace (won'?t|isn'?t|doesn'?t|will not) "
           r"(turn on|kick on|start|work)|not heating|no (cool(ing)?|a/?c|air)|a/?c (is )?(not|isn'?t) (cooling|working)|"
           r"isn'?t cooling|not cooling|blowing (warm|hot)|air is warm|leak(ing|s)?|flood(ing|ed)?|burst pipe|"
           r"water (is )?(pooling|everywhere|coming|running|pouring))\b")
_PERSON = (r"\b(talk|speak|chat)\s+(to|with)\s+(a|an|the|someone|somebody|real|human|live|person|people|agent|"
           r"representative|rep|manager|supervisor)|\b(real|live)\s+(person|human|agent)\b|\bhuman\b|"
           r"\brepresentative\b|\b(a|your|the)\s+manager\b|\bsupervisor\b|someone in charge")
_REFUND = r"\brefund"
_DISPUTE = (r"(not what i agreed|overcharg|charged (me )?(wrong|too much|for something)|wrong (amount|charge)|"
            r"dispute|don'?t (owe|agree)|take (that|it|the fee) off|shouldn'?t have to pay)")
_COMPLAINT = (r"\b(rude|tracked mud|unprofessional|called (three|3|several|multiple) times|nobody (has )?called me back|"
              r"never called back|second opinion|ripped off|scam)\b")
_LEGAL = r"\b(lawyer|attorney|sue|lawsuit|chargeback|better business bureau|bbb)\b"
_COMMERCIAL = r"\b(commercial|strip (center|mall)|rooftop units?|office building|warehouse|my business|tenants)\b"


@dataclass
class Signals:
    safety: bool = False
    safety_kind: str = ""
    burning_unclear: bool = False
    urgent_comfort: bool = False
    wants_person: bool = False
    escalation: str = ""  # refund | billing_dispute | complaint | legal_or_chargeback | commercial


def check(text: str) -> Signals:
    t = text.lower()
    s = Signals()
    burning = re.search(_BURNING, t) is not None
    tripped = re.search(_BREAKER_TRIPPED, t) is not None and re.search(_BREAKER_NO, t) is None
    if re.search(_GAS, t):
        s.safety, s.safety_kind = True, "gas"
    elif re.search(_CO, t):
        s.safety, s.safety_kind = True, "co"
    elif re.search(_FIRE, t) and not re.search(r"\b(no|not|don'?t see|without)\b[^.?!]{0,20}" + _FIRE, t):
        s.safety, s.safety_kind = True, "sparks_smoke_flames"
    elif burning and tripped:
        s.safety, s.safety_kind = True, "burning_with_breaker"
    elif burning:
        s.burning_unclear = True
    if not s.safety and re.search(_URGENT, t):
        s.urgent_comfort = True
    if re.search(_PERSON, t):
        s.wants_person = True
    for name, rx in (("legal_or_chargeback", _LEGAL), ("refund", _REFUND), ("billing_dispute", _DISPUTE),
                     ("complaint", _COMPLAINT), ("commercial", _COMMERCIAL)):
        if re.search(rx, t):
            s.escalation = name
            break
    return s
