"""R-46 checks: pure code that guards the model's words (AEA-15; DO-3 section 4.1, DO-4 section 10).

Completion claims are checked against ``Settled`` (the whole conversation, SDQ-8 option A), numbers, dates,
times, IDs and amounts against an ``EvidenceSet``, and brief quotes against the text the model was shown
(GRN-3). Only whole sentences (or whole quotes) are removed; nothing is rewritten or appended. This module
builds no check event and logs nothing: removed values never leave the result.
"""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Mapping, Sequence
from typing import Final, Literal

from meridian.domain.actions import ActionKind, CompletedAction, Settled
from meridian.domain.common import MeridianModel
from meridian.domain.handoff import BriefExtraction, Quote, SourceRef
from meridian.domain.state import ChatLine
from meridian.domain.tools import LookupRow
from meridian.domain.turn import CheckResult, Claim, EvidenceSet, Removal, TurnFacts

# ---------------------------------------------------------------------------------------------------------
# Sentences (PD-11)
# ---------------------------------------------------------------------------------------------------------

_BOUNDARY: Final = re.compile(r"[.!?]+[\"'”’)\]]*(?=\s|$)|\n")
_NO_SPLIT: Final = re.compile(
    r"(?i)(?:\b(?:a\.m|p\.m|e\.g|i\.e|mr|mrs|ms|dr|st|vs|approx|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\.)$"
)


def _sentences(text: str) -> list[tuple[int, int]]:
    """Spans of the non-blank sentences of ``text``, in order, trimmed of outer whitespace."""
    pos = 0
    raw: list[tuple[int, int]] = []
    for m in _BOUNDARY.finditer(text):
        if m.group() == "\n":
            end = m.start()
        elif m.group() == "." and _NO_SPLIT.search(text[max(0, m.start() - 8) : m.end()]):
            continue
        else:
            end = m.end()
        if text[pos:end].strip():
            raw.append((pos, end))
        pos = m.end()
    if text[pos:].strip():
        raw.append((pos, len(text)))
    spans: list[tuple[int, int]] = []
    for start, end in raw:
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        spans.append((start, end))
    return spans


def _rejoin(text: str, spans: Sequence[tuple[int, int]], removed: set[int]) -> str:
    """The kept sentences, joined the way the original gap between them was."""
    out = ""
    previous_end: int | None = None
    for index, (start, end) in enumerate(spans):
        if index in removed:
            continue
        if previous_end is not None:
            gap = text[previous_end:start]
            out += "\n\n" if "\n\n" in gap else "\n" if "\n" in gap else " "
        out += text[start:end]
        previous_end = end
    return out.strip()


# ---------------------------------------------------------------------------------------------------------
# Completion lexicon (PD-2, PD-3, PD-4)
# ---------------------------------------------------------------------------------------------------------

COMPLETION_WORDS: Final[dict[ActionKind, tuple[str, ...]]] = {
    ActionKind.BOOKED: (
        "booked",
        "i've scheduled",
        "i have scheduled",
        "we've scheduled",
        "we have scheduled",
        "has been scheduled",
        "have been scheduled",
        "is now scheduled",
    ),
    ActionKind.MOVED: ("moved", "rescheduled"),
    ActionKind.CANCELLED: ("cancelled", "canceled"),
    ActionKind.CHANGE_REQUEST_SENT: (
        "sent your change request",
        "sent a change request",
        "sent the change request",
        "change request has been sent",
        "change request is sent",
        "recorded your change request",
        "logged your change request",
        "passed your change request",
    ),
    ActionKind.CASE_OPENED: (
        "opened a case",
        "created a case",
        "created a request",
        "case is open",
        "case has been opened",
        "case has been created",
        "request has been created",
    ),
    ActionKind.FOLLOWUP_SAVED: (
        "saved your email",
        "saved your phone",
        "saved your number",
        "saved your contact",
        "saved how to reach you",
        "saved your preference",
    ),
    ActionKind.VERIFIED: (
        "you're verified",
        "you are verified",
        "you've been verified",
        "you have been verified",
        "verified your identity",
        "identity is verified",
        "identity has been verified",
        "identity is confirmed",
        "confirmed your identity",
    ),
}
GENERIC_COMPLETION_WORDS: Final[tuple[str, ...]] = (
    "done",
    "all set",
    "taken care of",
    "sorted",
    "finished",
    "completed",
    "that's handled",
)
# Claims no tool can back (no tool refunds or switches off auto-renew): they never pass.
UNBACKED_COMPLETION_WORDS: Final[tuple[str, ...]] = (
    "refunded",
    "turned off",
    "switched off",
    "auto-renew is off",
    "auto-renewal is off",
    "auto-renew is now off",
    "auto-renewal is now off",
    "e-mailed",
)
_NOT_A_CLAIM_BEFORE: Final = frozenset(
    {
        "not",
        "no",
        "never",
        "cant",
        "cannot",
        "couldnt",
        "wont",
        "wouldnt",
        "isnt",
        "wasnt",
        "arent",
        "werent",
        "hasnt",
        "havent",
        "hadnt",
        "didnt",
        "dont",
        "doesnt",
        "if",
        "once",
        "until",
        "unless",
        "when",
        "whether",
        "before",
        "after",
        "will",
        "would",
        "can",
        "could",
        "should",
        "shall",
        "may",
        "might",
        "want",
        "wants",
        "need",
        "needs",
    }
)
_CLAUSE_MARK: Final = re.compile(r"[,;:()—–]|\s-\s")
_WORD: Final = re.compile(r"[a-z]+(?:['’][a-z]+)?")


def _phrase_rx(phrase: str) -> re.Pattern[str]:
    parts: list[str] = []
    for ch in phrase:
        if ch == "'":
            parts.append("['’]?")
        elif ch == " ":
            parts.append(r"\s+")
        elif ch == "-":
            parts.append(r"[-\s]?")
        else:
            parts.append(re.escape(ch))
    return re.compile(r"(?<!\w)" + "".join(parts) + r"(?!\w)", re.IGNORECASE)


_KIND_RX: Final[tuple[tuple[ActionKind, re.Pattern[str]], ...]] = tuple(
    (kind, _phrase_rx(phrase)) for kind, phrases in COMPLETION_WORDS.items() for phrase in phrases
)
_GENERIC_RX: Final[tuple[re.Pattern[str], ...]] = tuple(_phrase_rx(p) for p in GENERIC_COMPLETION_WORDS)
_UNBACKED_RX: Final[tuple[re.Pattern[str], ...]] = tuple(_phrase_rx(p) for p in UNBACKED_COMPLETION_WORDS)


def _suppressed(sentence: str, start: int) -> bool:
    """True when a negation, condition, modal or wish word sits just before ``start`` in the same clause."""
    before = sentence[:start]
    cut = max((m.end() for m in _CLAUSE_MARK.finditer(before)), default=0)
    words = [w.replace("'", "").replace("’", "") for w in _WORD.findall(before[cut:].lower())]
    return any(w in _NOT_A_CLAIM_BEFORE for w in words[-4:])


# ---------------------------------------------------------------------------------------------------------
# Fact claims (PD-6)
# ---------------------------------------------------------------------------------------------------------

_YEARLESS_YEAR: Final = 4

_ID_RX: Final = re.compile(r"\b(?:INV-[0-9]{6}|MHC-C-[0-9]{4}|MHC-[0-9]{5})\b", re.I)
_ISO_DATE_RX: Final = re.compile(r"\b([0-9]{4})-([0-9]{2})-([0-9]{2})\b")
_AMOUNT_RX: Final = re.compile(r"\$\s?([0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.([0-9]{2}))?(?![0-9])")
_MERIDIEM: Final = r"(a\.?\s?m\.?|p\.?\s?m\.?)(?![a-z])"
_TIME_RANGE_RX: Final = re.compile(
    r"\b([0-9]{1,2})(?::([0-5][0-9]))?\s*(?:-|–|—|to)\s*([0-9]{1,2})(?::([0-5][0-9]))?\s*" + _MERIDIEM, re.I
)
_TIME_12_RX: Final = re.compile(r"\b([0-9]{1,2})(?::([0-5][0-9]))?\s*" + _MERIDIEM, re.I)
_TIME_24_RX: Final = re.compile(r"\b([01]?[0-9]|2[0-3]):([0-5][0-9])\b")
_TIME_WORD_RX: Final = re.compile(r"\b(noon|midday|midnight)\b", re.I)
_MONTH_DATE_RX: Final = re.compile(
    r"\b(january|february|march|april|may|june|july|august|september|october|november|december"
    r"|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\.?\s+([0-9]{1,2})(?:st|nd|rd|th)?"
    r"(?:,?\s+([0-9]{4}))?(?![0-9])",
    re.I,
)
_SLASH_DATE_RX: Final = re.compile(r"\b([0-9]{1,2})/([0-9]{1,2})(?:/([0-9]{4}|[0-9]{2}))?\b")
_NUMBER_RX: Final = re.compile(r"(?<![\w.,])[0-9]+(?:[.,][0-9]+)*(?![0-9])")

_MONTHS: Final = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3, "apr": 4, "april": 4,
    "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7, "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10, "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}  # fmt: skip

FactKind = Literal["number", "date", "time", "id", "amount"]


def _norm_number(s: str) -> str:
    s = s.replace(",", "")
    ip, _, fp = s.partition(".")
    ip = ip.lstrip("0") or "0"
    fp = fp.rstrip("0")
    return f"{ip}.{fp}" if fp else ip


def _meridiem(captured: str) -> str:
    return "am" if captured.lower().replace(".", "").replace(" ", "").startswith("a") else "pm"


def _minutes(h: int, mm: str | None, meridiem: str) -> int:
    return (h % 12 + (12 if meridiem == "pm" else 0)) * 60 + int(mm or 0)


def _to_24(h: int, mm: str | None, meridiem: str) -> str | None:
    if not 1 <= h <= 12:
        return None
    total = _minutes(h, mm, meridiem)
    return f"{total // 60:02d}:{total % 60:02d}"


def _valid_date(year: int | None, month: int, day: int) -> bool:
    try:
        dt.date(year or _YEARLESS_YEAR, month, day)
    except ValueError:
        return False
    return True


def _fact_claims(text: str, offset: int = 0) -> list[Claim]:
    """Every id, date, amount, time and number of ``text``; each character belongs to at most one claim."""
    taken: list[tuple[int, int]] = []
    found: list[Claim] = []

    def free(start: int, end: int) -> bool:
        return all(end <= ts or start >= te for ts, te in taken)

    def take(kind: FactKind, start: int, end: int, value: str) -> None:
        taken.append((start, end))
        found.append(Claim(kind=kind, span=(offset + start, offset + end), value=value))

    for m in _ID_RX.finditer(text):
        if free(m.start(), m.end()):
            take("id", m.start(), m.end(), m.group().upper())

    for m in _ISO_DATE_RX.finditer(text):
        if free(m.start(), m.end()) and _valid_date(int(m.group(1)), int(m.group(2)), int(m.group(3))):
            take("date", m.start(), m.end(), f"{m.group(1)}-{m.group(2)}-{m.group(3)}")

    for m in _AMOUNT_RX.finditer(text):
        if free(m.start(), m.end()):
            cents = int(m.group(1).replace(",", "")) * 100 + int(m.group(2) or 0)
            take("amount", m.start(), m.end(), str(cents))

    for m in _TIME_RANGE_RX.finditer(text):
        h1, h2 = int(m.group(1)), int(m.group(3))
        if not (1 <= h1 <= 12 and 1 <= h2 <= 12) or not free(m.start(), m.end()):
            continue
        second_meridiem = _meridiem(m.group(5))
        first_meridiem = second_meridiem
        if _minutes(h1, m.group(2), first_meridiem) > _minutes(h2, m.group(4), second_meridiem):
            first_meridiem = "am" if second_meridiem == "pm" else "pm"
        first = _to_24(h1, m.group(2), first_meridiem)
        second = _to_24(h2, m.group(4), second_meridiem)
        if first is None or second is None:
            continue
        first_end = m.end(2) if m.group(2) else m.end(1)
        take("time", m.start(1), first_end, first)
        take("time", m.start(3), m.end(), second)

    for m in _TIME_12_RX.finditer(text):
        if free(m.start(), m.end()):
            value = _to_24(int(m.group(1)), m.group(2), _meridiem(m.group(3)))
            if value is not None:
                take("time", m.start(), m.end(), value)

    for m in _TIME_24_RX.finditer(text):
        if free(m.start(), m.end()):
            take("time", m.start(), m.end(), f"{int(m.group(1)):02d}:{m.group(2)}")

    for m in _TIME_WORD_RX.finditer(text):
        if free(m.start(), m.end()):
            take("time", m.start(), m.end(), "00:00" if m.group().lower() == "midnight" else "12:00")

    for m in _MONTH_DATE_RX.finditer(text):
        month, day = _MONTHS[m.group(1).lower()], int(m.group(2))
        year = int(m.group(3)) if m.group(3) else None
        if free(m.start(), m.end()) and _valid_date(year, month, day):
            value = f"{year:04d}-{month:02d}-{day:02d}" if year else f"--{month:02d}-{day:02d}"
            take("date", m.start(), m.end(), value)

    for m in _SLASH_DATE_RX.finditer(text):
        month, day = int(m.group(1)), int(m.group(2))
        year = None
        if m.group(3):
            year = int(m.group(3)) if len(m.group(3)) == 4 else 2000 + int(m.group(3))
        if free(m.start(), m.end()) and _valid_date(year, month, day):
            value = f"{year:04d}-{month:02d}-{day:02d}" if year else f"--{month:02d}-{day:02d}"
            take("date", m.start(), m.end(), value)

    for m in _NUMBER_RX.finditer(text):
        if free(m.start(), m.end()):
            take("number", m.start(), m.end(), _norm_number(m.group()))

    return sorted(found, key=lambda c: c.span[0])


# ---------------------------------------------------------------------------------------------------------
# check_completion (PD-1, PD-5)
# ---------------------------------------------------------------------------------------------------------

_APPT_KINDS: Final = frozenset(
    {ActionKind.BOOKED, ActionKind.MOVED, ActionKind.CANCELLED, ActionKind.CHANGE_REQUEST_SENT}
)
_CASE_KINDS: Final = frozenset({ActionKind.CASE_OPENED, ActionKind.FOLLOWUP_SAVED})
_APPT_REF: Final = re.compile(r"\bappointment\s+(?:#\s*|no\.?\s*|number\s+)?([0-9]+)(?![0-9:])", re.I)
_CASE_REF: Final = re.compile(r"\bMHC-C-[0-9]{4}\b", re.I)
_CUSTOMER_REF: Final = re.compile(r"\bMHC-[0-9]{5}\b", re.I)


def _month_day(value: str) -> str:
    if value.startswith("--"):
        return f"md:{value[2:]}"
    day = dt.date.fromisoformat(value)
    return f"md:{day.month:02d}-{day.day:02d}"


def _named_refs(kind: ActionKind, sentence: str) -> frozenset[str]:
    """The records the sentence names, as comparable references."""
    if kind in _APPT_KINDS:
        refs = {"appointment:" + str(int(m.group(1))) for m in _APPT_REF.finditer(sentence)}
        refs |= {_month_day(c.value) for c in _fact_claims(sentence) if c.kind == "date"}
        return frozenset(refs)
    if kind in _CASE_KINDS:
        return frozenset("case:" + m.group().upper() for m in _CASE_REF.finditer(sentence))
    if kind is ActionKind.VERIFIED:
        return frozenset("customer:" + m.group().upper() for m in _CUSTOMER_REF.finditer(sentence))
    return frozenset()


def _action_refs(action: CompletedAction, settled: Settled) -> frozenset[str]:
    refs: set[str] = set()
    for key, prefix in (("case", "case:"), ("customer", "customer:")):
        if key in action.records:
            refs.add(prefix + action.records[key].upper())
    if "appointment" in action.records:
        appt = action.records["appointment"]
        refs.add("appointment:" + (str(int(appt)) if appt.isdigit() else appt))
        related = [b for b in settled.actions if b.records.get("appointment") == appt]
        for x in (action, *related):
            for d in (x.before, x.after):
                if d is not None and "date" in d:
                    try:
                        day = dt.date.fromisoformat(d["date"])
                    except ValueError:
                        continue
                    refs.add(f"md:{day.month:02d}-{day.day:02d}")
    return frozenset(refs)


def _backed(kind: ActionKind, sentence: str, settled: Settled) -> bool:
    actions = [a for a in settled.actions if a.kind == kind]
    if not actions:
        return False
    named = _named_refs(kind, sentence)
    if not named:
        return True
    return any(named <= _action_refs(a, settled) for a in actions)


def check_completion(text: str, settled: Settled) -> CheckResult:
    """Remove every sentence that claims something done with no matching stored action (R-46)."""
    spans = _sentences(text)
    removed: set[int] = set()
    removals: list[Removal] = []
    for i, (s, e) in enumerate(spans):
        sentence = text[s:e]
        found: list[tuple[Claim, str, bool]] = []
        for kind, rx in _KIND_RX:
            for m in rx.finditer(sentence):
                if not _suppressed(sentence, m.start()):
                    claim = Claim(
                        kind="completion",
                        span=(s + m.start(), s + m.end()),
                        value=m.group(),
                        action_kind=kind,
                    )
                    found.append((claim, "specific", _backed(kind, sentence, settled)))
        for rx in _UNBACKED_RX:
            for m in rx.finditer(sentence):
                if not _suppressed(sentence, m.start()):
                    claim = Claim(kind="completion", span=(s + m.start(), s + m.end()), value=m.group())
                    found.append((claim, "unbacked", False))
        specific_passes = any(p for _, g, p in found if g == "specific")
        for rx in _GENERIC_RX:
            for m in rx.finditer(sentence):
                if not _suppressed(sentence, m.start()):
                    claim = Claim(kind="completion", span=(s + m.start(), s + m.end()), value=m.group())
                    found.append((claim, "generic", specific_passes))
        failing = sorted((c for c, _, p in found if not p), key=lambda c: c.span[0])
        if failing:
            removed.add(i)
            removals.append(Removal(claim=failing[0], reason="no_completed_action"))
    if not removals:
        return CheckResult(text=text, removals=(), passed=True)
    return CheckResult(text=_rejoin(text, spans, removed), removals=tuple(removals), passed=False)


# ---------------------------------------------------------------------------------------------------------
# build_evidence (PD-8, PD-9, PD-10)
# ---------------------------------------------------------------------------------------------------------

_SKIP_KEYS: Final = frozenset(
    {
        "score",
        "confidence",
        "probabilities",
        "thread_id",
        "turn_id",
        "request_id",
        "task_id",
        "opened_turn",
        "shown_turn",
        "message_id",
        "tool_call_id",
        "run_id",
        "key",
        "version",
        "passage_id",
        "passage_ids",
        "quick_checks",
        "at",
        "read_at",
    }
)


class _Collector:
    def __init__(self) -> None:
        self.amounts: set[int] = set()
        self.dates: set[dt.date] = set()
        self.times: set[str] = set()
        self.ids: set[str] = set()
        self.numbers: set[str] = set()
        self.sources: dict[str, SourceRef] = {}

    def add(self, kind: FactKind, value: str, source: SourceRef) -> None:
        if kind == "amount":
            cents = int(value)
            self.amounts.add(cents)
            if cents % 100 == 0:
                self.add("number", str(cents // 100), source)
        elif kind == "date":
            if value.startswith("--"):
                day = dt.date(_YEARLESS_YEAR, int(value[2:4]), int(value[5:7]))
            else:
                day = dt.date.fromisoformat(value)
            self.dates.add(day)
            self.add("number", str(day.day), source)
        elif kind == "time":
            self.times.add(value)
            self.add("number", str(int(value[:2]) % 12 or 12), source)
        elif kind == "id":
            self.ids.add(value)
        else:
            self.numbers.add(value)
        self.sources.setdefault(f"{kind}:{value}", source)

    def add_text(self, text: str, source: SourceRef) -> None:
        for c in _fact_claims(text):
            self.add(c.kind, c.value, source)  # type: ignore[arg-type]

    def walk(self, value: object, key: str, source: SourceRef) -> None:
        if key in _SKIP_KEYS or value is None or isinstance(value, bool):
            return
        if isinstance(value, str):
            self.add_text(value, source)
        elif isinstance(value, int):
            self.add("amount" if key.endswith("_cents") else "number", str(value), source)
        elif isinstance(value, float):
            self.add("number", _norm_number(f"{value:.2f}"), source)
        elif isinstance(value, dt.datetime):
            self.add("date", value.date().isoformat(), source)
            self.add("time", f"{value.hour:02d}:{value.minute:02d}", source)
        elif isinstance(value, dt.date):
            self.add("date", value.isoformat(), source)
        elif isinstance(value, MeridianModel):
            self.walk(value.model_dump(mode="python"), key, source)
        elif isinstance(value, Mapping):
            for k, v in value.items():
                self.walk(v, str(k), source)
        elif isinstance(value, (list, tuple, set, frozenset)):
            for v in value:
                self.walk(v, key, source)


def _action_source(action: CompletedAction) -> SourceRef:
    return SourceRef(
        kind="action", ref=f"{action.key.kind.value}:{action.key.record_id}:{action.key.turn_id}"
    )


def build_evidence(
    facts: TurnFacts,
    settled: Settled,
    lookups: Sequence[LookupRow],
    chat: Sequence[ChatLine] | None = None,
) -> EvidenceSet:
    """What may be stated: this turn's facts, stored actions and lookup rows; the chat only when passed."""
    col = _Collector()
    for row in lookups:
        ref = SourceRef(kind="lookup_log", ref=str(row.id))
        col.walk(row.record_ids, "record_ids", ref)
        col.walk(row.result_seen, "result_seen", ref)
    for a in settled.actions:
        col.walk(a.model_dump(mode="python"), "action", _action_source(a))
    if settled.open_case is not None:
        case = settled.open_case
        col.walk(
            case.model_dump(mode="python"),
            "open_case",
            SourceRef(kind="action", ref=f"case_opened:{case.case_ref}"),
        )
    for name in type(facts).model_fields:
        if name in _SKIP_KEYS:
            continue
        value = getattr(facts, name)
        if name == "writes_this_turn":
            for a in value:
                col.walk(a.model_dump(mode="python"), "action", _action_source(a))
        elif name == "handoff" and value is not None:
            col.walk(value.action.model_dump(mode="python"), "action", _action_source(value.action))
            col.walk(
                value.model_dump(mode="python", exclude={"action"}),
                "handoff",
                SourceRef(kind="action", ref=f"case_opened:{value.case.case_ref}"),
            )
        elif name == "passages":
            for p in value:
                col.walk(
                    p.model_dump(mode="python"),
                    "passage",
                    SourceRef(kind="policy_row", ref=str(p.passage_id)),
                )
        elif name == "points":
            for k in value:
                col.walk(
                    k.model_dump(mode="python"),
                    "point",
                    SourceRef(kind="policy_row", ref=str(k.passage_id)),
                )
        else:
            col.walk(value, name, SourceRef(kind="rule", ref=f"turn_facts.{name}"))
    if chat is not None:
        for index, line in enumerate(chat):
            chat_ref = str(line.turn_id) if line.turn_id is not None else f"line:{index}"
            col.add_text(line.text, SourceRef(kind="message", ref=chat_ref))
    return EvidenceSet(
        amounts_cents=frozenset(col.amounts),
        dates=frozenset(col.dates),
        times=frozenset(col.times),
        ids=frozenset(col.ids),
        numbers=frozenset(col.numbers),
        sources=dict(col.sources),
    )


# ---------------------------------------------------------------------------------------------------------
# check_facts, check_quotes
# ---------------------------------------------------------------------------------------------------------


def _supported(claim: Claim, ev: EvidenceSet) -> bool:
    if claim.kind == "amount":
        return int(claim.value) in ev.amounts_cents
    if claim.kind == "date":
        if claim.value.startswith("--"):
            month, day = int(claim.value[2:4]), int(claim.value[5:7])
            return any(d.month == month and d.day == day for d in ev.dates)
        full = dt.date.fromisoformat(claim.value)
        return full in ev.dates or dt.date(_YEARLESS_YEAR, full.month, full.day) in ev.dates
    if claim.kind == "time":
        return claim.value in ev.times
    if claim.kind == "id":
        return claim.value in ev.ids
    return claim.value in ev.numbers


def check_facts(text: str, evidence: EvidenceSet) -> CheckResult:
    """Remove every sentence holding a number, date, time, ID or amount the evidence lacks (R-46, R-28)."""
    spans = _sentences(text)
    removed: set[int] = set()
    removals: list[Removal] = []
    for i, (s, e) in enumerate(spans):
        bad = [c for c in _fact_claims(text[s:e], offset=s) if not _supported(c, evidence)]
        if bad:
            removed.add(i)
            removals.append(Removal(claim=bad[0], reason="not_in_evidence"))
    if not removals:
        return CheckResult(text=text, removals=(), passed=True)
    return CheckResult(text=_rejoin(text, spans, removed), removals=tuple(removals), passed=False)


class QuoteCheck(MeridianModel):
    """GRN-3: the brief quotes that passed (original order) and the removals of those that did not."""

    needs: tuple[Quote, ...]
    claims: tuple[Quote, ...]
    removals: tuple[Removal, ...]
    passed: bool


def check_quotes(extraction: BriefExtraction, shown: Mapping[int, str]) -> QuoteCheck:
    """A quote passes only as an exact substring of the message the model was shown (GRN-3, PD-12)."""
    kept_needs: list[Quote] = []
    kept_claims: list[Quote] = []
    removals: list[Removal] = []
    for target, quotes in ((kept_needs, extraction.needs), (kept_claims, extraction.claims)):
        for q in quotes:
            if q.text != "" and q.message_id in shown and q.text in shown[q.message_id]:
                target.append(q)
            else:
                claim = Claim(kind="quote", span=(0, len(q.text)), value=str(q.message_id))
                removals.append(Removal(claim=claim, reason="quote_not_found"))
    return QuoteCheck(
        needs=tuple(kept_needs),
        claims=tuple(kept_claims),
        removals=tuple(removals),
        passed=not removals,
    )
