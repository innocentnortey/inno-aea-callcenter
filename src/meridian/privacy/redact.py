"""One redaction function, five profiles (AEA-04, stage7/data.md section 1).

`redact(text, profile)` masks card-like numbers, six-digit codes, phones, emails, street lines, introduced names
and customer/invoice IDs according to the profile; LOG keeps only the length. It is pure (no I/O, no state),
standard library only, and idempotent: no placeholder token matches any pattern again. Names are found by
introduction patterns only (DAT-1, option A): "my name is ...", "this is ...", "I'm ...".
"""

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TypeAlias

__all__ = [
    "Redacted",
    "RedactionKind",
    "RedactionProfile",
    "Redactor",
    "UnknownRedactionProfile",
    "redact",
]


class RedactionKind(StrEnum):
    CARD = "card"
    CODE = "code"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    NAME = "name"
    CUSTOMER_ID = "customer_id"
    INVOICE_ID = "invoice_id"
    FREE_TEXT = "free_text"  # LOG only


class RedactionProfile(StrEnum):
    STORE = "store"
    SONNET = "sonnet"
    JEV = "jev"
    TRACE = "trace"
    LOG = "log"


@dataclass(frozen=True)
class Redacted:
    text: str  # the redacted text; LOG: ""
    replaced: Mapping[RedactionKind, int]  # how many values of each kind were replaced; never a value
    length: int  # len(input); the only thing LOG keeps

    def __repr__(self) -> str:
        counts = ", ".join(f"{kind}: {count}" for kind, count in self.replaced.items())
        return f"Redacted(length={self.length}, replaced={{{counts}}})"


class UnknownRedactionProfile(ValueError):
    """The profile is not one of the five; the message never holds the text."""


Redactor: TypeAlias = Callable[[str, RedactionProfile], Redacted]

# CARD: 13-19 digits, single spaces or dashes between digits, no checksum, not glued to other digits.
_CARD = r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)"
# EMAIL: bounded local part and domain labels so a long run of letters cannot make the scan quadratic.
_EMAIL = (
    r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9-]{1,63}(?:\.[A-Za-z0-9-]{1,63}){0,8}\.[A-Za-z]{2,24}(?![A-Za-z0-9-])"
)
# PHONE: US 10-digit forms with an optional +1/1 prefix.
_PHONE = r"(?<![\d+])(?:\+?1[ .-]?)?(?:\(\d{3}\)[ ]?|\d{3}[ .-]?)\d{3}[ .-]?\d{4}(?!\d)"
_STREET_ABBR = r"(?i:st|ave|rd|dr|ln|blvd|ct|cir|trl|pkwy|hwy|ter|cv|pl)"
_STREET_FULL = (
    r"(?:Street|Avenue|Road|Drive|Lane|Boulevard|Court|Circle|Trail|Parkway|Highway|Terrace|Cove|Place|Way|Pass"
    r"|Loop|Run|Path|Bend|Point|Row|Square|Crossing)"
)
_STREET_WORD = r"(?:\d{1,3}(?:st|nd|rd|th)|[A-Za-z][A-Za-z'’-]*)"
# ADDRESS: house number, optional direction, one to three street-name words, a suffix, an optional unit.
_ADDRESS = (
    r"(?<![\w$.,:/#-])\d{1,6}[ \t]+"
    r"(?:(?:[NSEW]|North|South|East|West)\.?[ \t]+)?"
    r"(?:" + _STREET_WORD + r"[ \t]+){1,3}"
    r"(?:" + _STREET_ABBR + r"|" + _STREET_FULL + r")(?![A-Za-z])\.?"
    r"(?:,?[ \t]+(?i:apt|apartment|unit|suite|ste)\.?[ \t]*#?[A-Za-z0-9-]+|,?[ \t]*#[ \t]*[A-Za-z0-9-]+)?"
)
# CODE: exactly six digits not touching another digit, not after INV-, $, or digit plus . or ,.
_CODE = r"(?<!\d)(?<![Ii][Nn][Vv]-)(?<!\$)(?<!\d[.,])\d{6}(?!\d|[.,-]\d)"
# CUSTOMER_ID / INVOICE_ID: any case; MHC-C-0007 case references never match.
_CUSTOMER_ID = r"\b(?i:MHC)-\d{5}\b"
_INVOICE_ID = r"\b(?i:INV)-\d{6}\b"
_NAME_WORD = r"[A-Z](?:[a-z]+(?:[A-Z][a-z]+)?|['’][A-Z][a-z]+)(?:-[A-Z][a-z]+)?"
# NAME: an introduction, then one to three capitalised words; the introduction stays, the brand is not a name.
_NAME = (
    r"(?P<intro>\b(?i:my[ \t]+name[ \t]+is|my[ \t]+name['’]s|name[ \t]+is|this[ \t]+is|i[ \t]+am|i['’]m)[ \t]+)"
    r"(?!Meridian\b)"
    r"(?P<name>" + _NAME_WORD + r"(?:[ \t]+" + _NAME_WORD + r"){0,2})(?![A-Za-z'’-])"
)


def _phone_hint(match: re.Match[str]) -> str:
    return f"[phone ending {re.sub(r'\D', '', match.group(0))[-2:]}]"


def _name_token(match: re.Match[str]) -> str:
    return match.group("intro") + "[name]"


@dataclass(frozen=True)
class _Rule:
    kind: RedactionKind
    pattern: re.Pattern[str]
    replace: str | Callable[[re.Match[str]], str]


_CARD_RULE = _Rule(RedactionKind.CARD, re.compile(_CARD), "[card number removed]")
_EMAIL_RULE = _Rule(RedactionKind.EMAIL, re.compile(_EMAIL), "[email]")
_PHONE_FULL_RULE = _Rule(RedactionKind.PHONE, re.compile(_PHONE), "[phone]")
_PHONE_HINT_RULE = _Rule(RedactionKind.PHONE, re.compile(_PHONE), _phone_hint)
_ADDRESS_RULE = _Rule(RedactionKind.ADDRESS, re.compile(_ADDRESS), "[address]")
_CODE_RULE = _Rule(RedactionKind.CODE, re.compile(_CODE), "[code]")
_CUSTOMER_ID_RULE = _Rule(RedactionKind.CUSTOMER_ID, re.compile(_CUSTOMER_ID), "[customer id]")
_INVOICE_ID_RULE = _Rule(RedactionKind.INVOICE_ID, re.compile(_INVOICE_ID), "[invoice id]")
_NAME_RULE = _Rule(RedactionKind.NAME, re.compile(_NAME), _name_token)

# The profile matrix (data.md section 1), rules in the fixed order. LOG has no entry: it drops the text.
_RULES_BY_PROFILE: Mapping[RedactionProfile, tuple[_Rule, ...]] = MappingProxyType(
    {
        RedactionProfile.STORE: (_CARD_RULE, _CODE_RULE),
        RedactionProfile.SONNET: (_CARD_RULE, _EMAIL_RULE, _PHONE_HINT_RULE, _ADDRESS_RULE, _CODE_RULE),
        RedactionProfile.JEV: (
            _CARD_RULE,
            _EMAIL_RULE,
            _PHONE_FULL_RULE,
            _ADDRESS_RULE,
            _CODE_RULE,
            _CUSTOMER_ID_RULE,
            _INVOICE_ID_RULE,
            _NAME_RULE,
        ),
        RedactionProfile.TRACE: (
            _CARD_RULE,
            _EMAIL_RULE,
            _PHONE_HINT_RULE,
            _ADDRESS_RULE,
            _CODE_RULE,
            _NAME_RULE,
        ),
    }
)

_PROFILE_BY_VALUE: Mapping[str, RedactionProfile] = MappingProxyType({p.value: p for p in RedactionProfile})
_PROFILE_SHAPE = re.compile(r"[a-z_]{1,16}")


def _describe_profile(profile: object) -> str:
    expected = ", ".join(p.value for p in RedactionProfile)
    if isinstance(profile, str) and _PROFILE_SHAPE.fullmatch(profile):
        shown = repr(str(profile))
    else:
        shown = f"<{type(profile).__name__}>"
    return f"profile: unknown_redaction_profile (expected one of {expected}; got {shown})"


def redact(text: str, profile: RedactionProfile) -> Redacted:
    resolved = _PROFILE_BY_VALUE.get(profile) if isinstance(profile, str) else None
    if resolved is None:
        raise UnknownRedactionProfile(_describe_profile(profile))
    if not isinstance(text, str):
        raise TypeError(f"text: invalid_type (expected str, got {type(text).__name__})")
    if resolved is RedactionProfile.LOG:
        free_text: dict[RedactionKind, int] = {RedactionKind.FREE_TEXT: 1} if text else {}
        return Redacted(text="", replaced=MappingProxyType(free_text), length=len(text))
    out = text
    counts: dict[RedactionKind, int] = {}
    for rule in _RULES_BY_PROFILE[resolved]:
        out, n = rule.pattern.subn(rule.replace, out)
        if n:
            counts[rule.kind] = counts.get(rule.kind, 0) + n
    return Redacted(text=out, replaced=MappingProxyType(counts), length=len(text))
