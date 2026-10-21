"""FixedClock (AEA-11; stage7/data.md section 8a, DAT-32)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

CHICAGO = ZoneInfo("America/Chicago")
# [Source: docs/data/worked-pairs.md header "Friday 2026-10-16, 10:00"]; same instant as cases.md DEMO_START
WORKED_PAIRS_NOW = datetime(2026, 10, 16, 10, 0, tzinfo=CHICAGO)


class FixedClock:
    """A Clock that never moves. `advanced` returns a new clock (R-G-9: no setters)."""

    def __init__(self, at: datetime = WORKED_PAIRS_NOW) -> None:
        if at.tzinfo is None or at.utcoffset() is None:
            raise ValueError("FixedClock needs a tz-aware datetime (R-3)")
        if not isinstance(at.tzinfo, ZoneInfo) or at.tzinfo.key != "America/Chicago":
            raise ValueError("FixedClock needs America/Chicago (R-3)")
        self._at = at

    def now(self) -> datetime:
        return self._at

    def advanced(self, by: timedelta) -> FixedClock:
        return FixedClock((self._at.astimezone(UTC) + by).astimezone(CHICAGO))

    def __repr__(self) -> str:
        return f"FixedClock({self._at.isoformat()})"
