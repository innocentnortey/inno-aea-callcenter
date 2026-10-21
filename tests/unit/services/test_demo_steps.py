"""AEA-30 PA-3: pure step math for the demo clock."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import cast

import pytest

from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.services.demo import CLOCK_STEPS, ClockStep, next_demo_time
from tests.fakes.clock import CHICAGO


def chi(y: int, m: int, d: int, h: int, mi: int = 0) -> datetime:
    return datetime(y, m, d, h, mi, tzinfo=CHICAGO)


def test_steps_from_examples() -> None:
    cases = [
        (DEMO_START, "plus_1h", chi(2026, 10, 16, 11)),
        (DEMO_START, "plus_4h", chi(2026, 10, 16, 14)),
        (DEMO_START, "next_business_morning", chi(2026, 10, 19, 7)),
        (chi(2026, 11, 25, 10), "next_business_morning", chi(2026, 11, 30, 7)),
        (chi(2026, 10, 17, 15), "next_business_morning", chi(2026, 10, 19, 7)),
        (chi(2026, 10, 19, 6), "next_business_morning", chi(2026, 10, 20, 7)),
    ]
    for start, step, expected in cases:
        got = next_demo_time(start, cast(ClockStep, step))
        assert got == expected
        assert got.tzinfo is not None
        assert getattr(got.tzinfo, "key", None) == "America/Chicago"


def test_plus_hours_is_elapsed_time_across_dst() -> None:
    start = chi(2026, 11, 1, 0, 30)
    after = next_demo_time(next_demo_time(start, "plus_1h"), "plus_1h")
    assert after.astimezone(UTC) - start.astimezone(UTC) == timedelta(hours=2)


def test_every_step_moves_forward() -> None:
    days = [datetime(2026, 10, d).date() for d in range(16, 20)] + [
        datetime(2026, 11, d).date() for d in range(25, 31)
    ]
    for day in days:
        for hour in range(24):
            start = chi(day.year, day.month, day.day, hour)
            for step in CLOCK_STEPS:
                assert next_demo_time(start, cast(ClockStep, step)) > start


def test_unknown_step_raises() -> None:
    with pytest.raises(ValueError):
        next_demo_time(DEMO_START, cast(ClockStep, "minus_1h"))
