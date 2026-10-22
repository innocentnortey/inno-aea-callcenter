"""The customer-facing split of a stored promise (UXR-19) for the chat cards and the settled panel.

The screen joins "{promise_text}, {due_label}. {extra_lines}" (UI_CONTRACTS UXR-19; OpenAPI HandoffBlock.promise_text).
`Promise.text` keeps the policy-table string word for word, placeholders included (DO-4 section 7), so the composer
splits it here. Every word comes from `policy/texts.py`; this module types none. Pure: no I/O, no clock, no model.
"""

from __future__ import annotations

from typing import Final, NamedTuple

from meridian.domain.handoff import Promise
from meridian.policy.handoff import PROMISE_TABLE
from meridian.policy.texts import TEXTS, TextId, render

__all__ = ["UNSTAFFED_DUE", "UNSTAFFED_LEAD", "PromiseWire", "promise_wire"]

_DUE_FIELD: Final = "{due_label}"
_UNSTAFFED: Final = TEXTS[TextId.PROMISE_UNSTAFFED]
_REFUND_ROW: Final = "R26.refund"


class PromiseWire(NamedTuple):
    """The promise fields of HandoffBlock, SettledRequest and ChangeRequestBlock."""

    promise_text: str
    due_label: str | None
    extra_lines: tuple[str, ...]


def _split_unstaffed(template: str) -> tuple[str, str]:
    """(lead, due template) with lead + ", " + due + ". " + REFERENCE_LINE == template; else RuntimeError."""
    tail = ". " + TEXTS[TextId.REFERENCE_LINE]
    if not template.endswith(tail):
        raise RuntimeError("compose_promise: PROMISE_UNSTAFFED no longer ends with the reference line")
    head = template[: -len(tail)]
    if not head.endswith(_DUE_FIELD):
        raise RuntimeError(
            "compose_promise: PROMISE_UNSTAFFED no longer ends its first part with the due label"
        )
    cut = head.rfind(", ", 0, head.index(_DUE_FIELD))
    if cut < 0:
        raise RuntimeError("compose_promise: PROMISE_UNSTAFFED has no ', ' before the due label")
    lead, due = head[:cut], head[cut + 2 :]
    if "{" in lead or "}" in lead or due.count("{") != 1:
        raise RuntimeError("compose_promise: PROMISE_UNSTAFFED does not fit '{lead}, {due}. {reference}'")
    return lead, due


_SPLIT: Final = _split_unstaffed(_UNSTAFFED)
UNSTAFFED_LEAD: Final[str] = _SPLIT[0]  # "No representative is online right now. ... within 1 business day"
UNSTAFFED_DUE: Final[str] = _SPLIT[1]  # "by {due_label}"

if any("{" in text or "}" in text for text in PROMISE_TABLE.values() if text != _UNSTAFFED):
    raise RuntimeError("compose_promise: a promise row other than R26.unstaffed has a placeholder")


def promise_wire(promise: Promise, case_ref: str) -> PromiseWire:
    """The three wire fields for one stored promise; the screen's join gives the fixed sentence word for word."""
    reference = render(TextId.REFERENCE_LINE, case_ref=case_ref)
    if promise.text == _UNSTAFFED:
        due = None if promise.due_label is None else UNSTAFFED_DUE.replace(_DUE_FIELD, promise.due_label)
        return PromiseWire(UNSTAFFED_LEAD, due, (reference, *promise.extra_lines))
    if promise.policy_row == _REFUND_ROW:
        return PromiseWire(promise.text, None, (*promise.extra_lines, reference))
    return PromiseWire(promise.text, None, tuple(promise.extra_lines))
