"""AEA-30 AC-6 / PA-5: the one clock formatter."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from meridian.adapters.sqlite.repos_cases import DEMO_START
from meridian.services.demo import format_clock
from tests.fakes.clock import CHICAGO


def chi(y: int, m: int, d: int, h: int, mi: int = 0) -> datetime:
    return datetime(y, m, d, h, mi, tzinfo=CHICAGO)


def test_format_clock_demo_start() -> None:
    assert format_clock(DEMO_START) == ("Fri Oct 16, 2026 · 10:00 am", "Fri Oct 16, 2026 (demo date)")


def test_format_clock_examples() -> None:
    assert format_clock(chi(2026, 10, 16, 14, 20))[0] == "Fri Oct 16, 2026 · 2:20 pm"
    assert format_clock(chi(2026, 10, 19, 7, 0)) == (
        "Mon Oct 19, 2026 · 7:00 am",
        "Mon Oct 19, 2026 (demo date)",
    )
    assert format_clock(chi(2026, 10, 19, 12, 0))[0].endswith("· 12:00 pm")
    assert format_clock(chi(2026, 10, 19, 0, 0))[0].endswith("· 12:00 am")
    assert format_clock(datetime(2026, 10, 19, 12, 0, tzinfo=UTC))[0] == "Mon Oct 19, 2026 · 7:00 am"


def test_format_clock_refuses_naive() -> None:
    with pytest.raises(ValueError):
        format_clock(datetime(2026, 10, 16, 10, 0))
