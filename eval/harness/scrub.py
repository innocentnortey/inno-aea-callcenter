"""Known-secret and PII scrubbing, and the fail-closed leak check (AC-11, AC-21)."""

from __future__ import annotations

import re
from typing import Final

CARD_RX: Final = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
PHONE_RX: Final = re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)")
EMAIL_RX: Final = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
CODE_RX: Final = re.compile(r"(?<!\d)\d{6}(?!\d)")


class LeakDetected(Exception):
    """A known secret is in an output. The message never contains the value."""


def _value_rx(value: str) -> re.Pattern[str]:
    body = re.escape(value)
    if value.isdigit():
        body = rf"(?<!\d){body}(?!\d)"
    return re.compile(body, re.IGNORECASE)


class Scrubber:
    def __init__(self) -> None:
        self._values: dict[str, re.Pattern[str]] = {}

    def add(self, value: str | None) -> None:
        if value is None or len(value.strip()) < 4:
            return
        if value not in self._values:
            self._values[value] = _value_rx(value)

    def known_count(self) -> int:
        return len(self._values)

    def _patterns(self) -> list[re.Pattern[str]]:
        return [self._values[v] for v in sorted(self._values, key=len, reverse=True)]

    def scrub(self, text: str) -> str:
        for rx in self._patterns():
            text = rx.sub("[redacted]", text)
        text = CARD_RX.sub("[card]", text)
        text = PHONE_RX.sub("[phone]", text)
        text = EMAIL_RX.sub("[email]", text)
        return CODE_RX.sub("[code]", text)

    def assert_absent(self, text: str, *, where: str) -> None:
        for rx in self._patterns():
            if rx.search(text):
                raise LeakDetected(f"known secret in {where}")
