"""FU-identity-plan (AEA-51 finding F-2): the start of an issued appointment window, in Chicago time."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import pytest

from meridian.policy.handoff import window_start_of


@pytest.mark.parametrize(
    ("window", "hour"), [("08:00-12:00", 8), ("12:00-16:00", 12), ("13:00-17:00", 13), ("16:00-19:00", 16)]
)
def test_issued_windows_start_in_chicago(window: str, hour: int) -> None:
    got = window_start_of(dt.date(2026, 10, 19), window)
    assert got == dt.datetime(2026, 10, 19, hour, 0, tzinfo=ZoneInfo("America/Chicago"))
    assert got.utcoffset() is not None


def test_unknown_window_raises() -> None:
    with pytest.raises(ValueError):
        window_start_of(dt.date(2026, 10, 19), "09:00-11:00")
