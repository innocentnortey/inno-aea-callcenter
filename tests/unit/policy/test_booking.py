"""AEA-13: policy/booking.py (zones, hours to a window, the 24-hour rule, the fee quote)."""

from __future__ import annotations

import ast
import csv
import logging
import re
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from meridian.domain.records import FeeNote
from meridian.policy import booking
from meridian.policy.booking import (
    LAKEWAY_ZIPS,
    MEMBER_ALLOWANCE_ROWS,
    NOT_SERVED_CITIES,
    SCHEDULE_FEES,
    fee_bearing,
    fee_note,
    hours_before,
    zone_for,
)
from meridian.policy.texts import TextId, format_usd, render

CHI = ZoneInfo("America/Chicago")
NOW = datetime(2026, 10, 16, 10, 0, tzinfo=CHI)  # the worked-pairs clock: Fri 2026-10-16 10:00
SERVICES = ("hvac_repair", "hvac_tune_up", "plumbing", "estimate")
TIERS = ("none", "standard", "plus")
SOURCE_PATH = Path(booking.__file__)
REPO = Path(__file__).resolve().parents[3]


def test_city_to_zone_schema_map() -> None:
    expected = {
        "Round Rock": "north",
        "Cedar Park": "north",
        "Pflugerville": "north",
        "Georgetown": "north",
        "Leander": "north",
        "Hutto": "north",
        "Austin": "central",
        "Kyle": "south",
        "Buda": "south",
    }
    for city, zone in expected.items():
        assert zone_for(city) == zone, city
        assert zone_for(city) in {"north", "central", "south"}


def test_zip_groups_to_zone() -> None:
    north = (
        "78664",
        "78665",
        "78681",
        "78613",
        "78641",
        "78645",
        "78660",
        "78634",
        "78626",
        "78628",
        "78633",
    )
    for z in north:
        assert zone_for(z) == "north", z
    for z in ("78640", "78610"):
        assert zone_for(z) == "south", z
    for z in ("78701", "78745", "78799"):
        assert zone_for(z) == "central", z


def test_new_april_2026_areas_central() -> None:
    for value in ("Dripping Springs", "78620", "Manor", "78653"):
        assert zone_for(value) == "central", value


def test_not_served_areas() -> None:
    for value in (
        "San Marcos",
        "Bastrop",
        "Elgin",
        "Lakeway",
        "78734",
        "78738",
        "Houston",
        "77002",
        "78701x",
    ):
        assert zone_for(value) is None, value
    assert NOT_SERVED_CITIES == frozenset({"San Marcos", "Bastrop", "Elgin", "Lakeway"})
    assert LAKEWAY_ZIPS == frozenset({"78734", "78738"})


def test_wp4_two_hours_before(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    fake_now = datetime(2030, 1, 1, tzinfo=CHI)

    class SpyDatetime(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> datetime:  # type: ignore[override]
            calls.append("now")
            return fake_now

        @classmethod
        def utcnow(cls) -> datetime:  # type: ignore[override]
            calls.append("utcnow")
            return fake_now

        @classmethod
        def today(cls) -> datetime:  # type: ignore[override]
            calls.append("today")
            return fake_now

    class SpyDate(date):
        @classmethod
        def today(cls) -> date:  # type: ignore[override]
            calls.append("date.today")
            return date(2030, 1, 1)

    monkeypatch.setattr(booking, "datetime", SpyDatetime)
    monkeypatch.setattr(booking, "date", SpyDate)
    assert hours_before(NOW, date(2026, 10, 16), "12:00-16:00") == 2.0
    started = datetime(2026, 10, 16, 13, 0, tzinfo=CHI)
    assert hours_before(started, date(2026, 10, 16), "12:00-16:00") == -1.0
    assert calls == []


def test_fee_bearing_boundary() -> None:
    assert fee_bearing(2.0) is True
    assert fee_bearing(-1.0) is True
    far = hours_before(NOW, date(2026, 10, 22), "08:00-12:00")
    assert far == 142.0
    assert fee_bearing(far) is False
    assert fee_bearing(24.0) is False
    exactly = hours_before(datetime(2026, 10, 16, 12, 0, tzinfo=CHI), date(2026, 10, 17), "12:00-16:00")
    assert exactly == 24.0
    assert fee_bearing(exactly) is False


def test_fee_note_by_tier() -> None:
    for s in ("hvac_repair", "plumbing"):
        got = fee_note(s, "none")
        assert isinstance(got, FeeNote)
        assert got == FeeNote(
            service_type=s,
            tier="none",
            fee_row="Diagnostic visit",
            amount_cents=8900,
            waived=False,
            line="Standard diagnostic fee: $89",
        )
        for t in ("standard", "plus"):
            member = fee_note(s, t)
            assert member.fee_row == "Diagnostic visit"
            assert member.amount_cents == 0
            assert member.waived is True
            assert member.line == render(TextId.FEE_DIAGNOSTIC_WAIVED, amount="$89")
    for t in TIERS:
        est = fee_note("estimate", t)  # type: ignore[arg-type]
        assert est.fee_row is None
        assert est.amount_cents == 0
        assert est.waived is False
        assert est.line == render(TextId.FEE_ESTIMATE_FREE)


def _int_constants(tree: ast.AST) -> list[int]:
    return [
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, int) and not isinstance(n.value, bool)
    ]


def test_schedule_fees_single_source() -> None:
    assert {k: dict(v) for k, v in SCHEDULE_FEES.items()} == {
        "Diagnostic visit": {"none": 8900, "standard": 0, "plus": 0},
        "After-hours dispatch": {"none": 14900, "standard": 0, "plus": 0},
        "Seasonal tune-up": {"none": 12900, "standard": 0, "plus": 0},
    }
    assert MEMBER_ALLOWANCE_ROWS == frozenset({"Seasonal tune-up"})
    for s in SERVICES:
        for t in TIERS:
            note = fee_note(s, t)  # type: ignore[arg-type]
            if note.fee_row is not None:
                assert note.amount_cents == SCHEDULE_FEES[note.fee_row][t]  # type: ignore[index]
    ints = _int_constants(ast.parse(SOURCE_PATH.read_text("utf-8")))
    assert ints.count(8900) == 1
    assert ints.count(12900) == 1
    assert ints.count(14900) == 1
    assert not {89, 129, 49, 79, 4900, 7900} & set(ints)
    with pytest.raises(TypeError):
        SCHEDULE_FEES["Diagnostic visit"]["none"] = 1  # type: ignore[index]


def test_fee_note_never_charged_or_waived() -> None:
    for s in SERVICES:
        for t in TIERS:
            line = fee_note(s, t).line  # type: ignore[arg-type]
            cf = line.casefold()
            assert "charg" not in cf
            assert "$79" not in line
            assert "$49" not in line
            assert not ("late" in cf and "waiv" in cf)


def test_unknown_location_not_logged(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    assert zone_for("Zyxwvut Hollow QX") is None
    assert zone_for("99999") is None
    assert "Zyxwvut" not in caplog.text
    assert "99999" not in caplog.text


def test_booking_module_is_pure(monkeypatch: pytest.MonkeyPatch) -> None:
    source = SOURCE_PATH.read_text("utf-8")
    allowed = {
        "__future__",
        "re",
        "collections.abc",
        "datetime",
        "types",
        "typing",
        "zoneinfo",
        "meridian.policy.texts",
    }
    forbidden = (
        "meridian.services",
        "meridian.agent",
        "meridian.adapters",
        "meridian.web",
        "meridian.ports",
        "meridian.gates",
        "meridian.config",
    )
    names: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    for name in names:
        assert name in allowed or name.startswith("meridian.domain."), name
        assert not name.startswith(forbidden), name
    for token in (".now(", ".today(", "utcnow", "time.time", "open(", "logging"):
        assert token not in source, token

    recorded: list[TextId] = []
    real_render = render

    def spy(text_id: TextId, /, **values: str) -> str:
        recorded.append(text_id)
        return real_render(text_id, **values)

    monkeypatch.setattr(booking, "render", spy)
    for s in SERVICES:
        for t in TIERS:
            fee_note(s, t)  # type: ignore[arg-type]
    assert len(recorded) == 12


def test_fee_note_tune_up_and_estimate() -> None:
    none = fee_note("hvac_tune_up", "none")
    assert none.fee_row == "Seasonal tune-up"
    assert none.amount_cents == 12900
    assert none.waived is False
    assert none.line == render(TextId.FEE_TUNE_UP, amount="$129")
    for t in ("standard", "plus"):
        member = fee_note("hvac_tune_up", t)
        assert member.amount_cents == 0
        assert member.waived is True
        assert member.line == render(TextId.FEE_TUNE_UP_INCLUDED, amount="$129")
    for t in TIERS:
        est = fee_note("estimate", t)  # type: ignore[arg-type]
        assert (est.fee_row, est.amount_cents, est.waived) == (None, 0, False)


def test_fee_line_rendered_with_format_usd(monkeypatch: pytest.MonkeyPatch) -> None:
    renders: list[tuple[TextId, dict[str, str]]] = []
    usd: list[int] = []
    real_render, real_usd = render, format_usd

    def render_spy(text_id: TextId, /, **values: str) -> str:
        renders.append((text_id, dict(values)))
        return real_render(text_id, **values)

    def usd_spy(cents: int) -> str:
        usd.append(cents)
        return real_usd(cents)

    monkeypatch.setattr(booking, "render", render_spy)
    monkeypatch.setattr(booking, "format_usd", usd_spy)
    cases: list[tuple[str, str, TextId, dict[str, str], list[int]]] = [
        ("hvac_repair", "none", TextId.FEE_STANDARD_DIAGNOSTIC, {"amount": "$89"}, [8900]),
        ("plumbing", "none", TextId.FEE_STANDARD_DIAGNOSTIC, {"amount": "$89"}, [8900]),
        ("hvac_repair", "standard", TextId.FEE_DIAGNOSTIC_WAIVED, {"amount": "$89"}, [8900]),
        ("plumbing", "plus", TextId.FEE_DIAGNOSTIC_WAIVED, {"amount": "$89"}, [8900]),
        ("hvac_tune_up", "none", TextId.FEE_TUNE_UP, {"amount": "$129"}, [12900]),
        ("hvac_tune_up", "standard", TextId.FEE_TUNE_UP_INCLUDED, {"amount": "$129"}, [12900]),
        ("hvac_tune_up", "plus", TextId.FEE_TUNE_UP_INCLUDED, {"amount": "$129"}, [12900]),
        ("estimate", "none", TextId.FEE_ESTIMATE_FREE, {}, []),
        ("estimate", "standard", TextId.FEE_ESTIMATE_FREE, {}, []),
    ]
    for service, tier, text_id, kwargs, cents in cases:
        renders.clear()
        usd.clear()
        fee_note(service, tier)  # type: ignore[arg-type]
        assert renders == [(text_id, kwargs)], (service, tier)
        assert usd == cents, (service, tier)
    assert re.search(r"\$[0-9]", SOURCE_PATH.read_text("utf-8")) is None
    assert format_usd(8900) == "$89"


def test_worked_pairs_wp3_wp4() -> None:
    # WP-4: MHC-57204, Austin, tune-up today 12:00-16:00, clock Fri 2026-10-16 10:00.
    assert zone_for("Austin") == "central"
    h = hours_before(NOW, date(2026, 10, 16), "12:00-16:00")
    assert h == 2.0
    assert fee_bearing(h) is True
    # WP-4F: the same customer, visit 2026-10-22 08:00-12:00.
    assert fee_bearing(hours_before(NOW, date(2026, 10, 22), "08:00-12:00")) is False
    # WP-3: MHC-10001, Round Rock, standard member, hvac_repair: waived, not the transcript's $89.
    assert zone_for("Round Rock") == "north"
    assert zone_for("78664") == "north"
    n = fee_note("hvac_repair", "standard")
    assert n.waived is True
    assert n.amount_cents == 0
    assert n.line != "Standard diagnostic fee: $89"


def test_zone_for_normalises_input() -> None:
    for value in ("  austin ", "AUSTIN", "Austin, TX", "Austin TX", "austin, texas", "78701-1234"):
        assert zone_for(value) == "central", value
    assert zone_for("round  rock") == "north"
    for value in ("78734-0001", "Lakeway, TX", "", "   ", "a" * 65):
        assert zone_for(value) is None, value
    assert zone_for(78701) is None  # type: ignore[arg-type]


def test_hours_before_rejects_naive_now_and_bad_window() -> None:
    with pytest.raises(ValueError):
        hours_before(datetime(2026, 10, 16, 10, 0), date(2026, 10, 16), "12:00-16:00")
    for window in ("noon-4pm", "25:00-26:00"):
        with pytest.raises(ValueError) as excinfo:
            hours_before(NOW, date(2026, 10, 16), window)  # type: ignore[arg-type]
        assert "noon" not in str(excinfo.value)


def test_hours_before_is_timezone_safe() -> None:
    utc_now = datetime(2026, 10, 16, 15, 0, tzinfo=UTC)  # 10:00 in Chicago (CDT)
    assert hours_before(utc_now, date(2026, 10, 16), "12:00-16:00") == 2.0
    # DST ends 2026-11-01: 12:00 CDT on Oct 31 to 12:00 CST on Nov 1 is 25 real hours.
    assert hours_before(datetime(2026, 10, 31, 12, 0, tzinfo=CHI), date(2026, 11, 1), "12:00-16:00") == 25.0


def test_issued_customers_city_and_zip_agree() -> None:
    path = REPO / "docs/data/issued/meridian_dataset/scheduling_db/customers.csv"
    rows = 0
    mismatches = 0
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows += 1
            by_zip, by_city = zone_for(row["zip"]), zone_for(row["city"])
            if by_zip is None or by_zip != by_city:
                mismatches += 1
    assert rows > 0
    assert mismatches == 0


def test_fee_note_rejects_unknown_service_or_tier() -> None:
    bad_fns: list[tuple[Callable[[], object], str, str]] = [
        (lambda: fee_note("duct_cleaning", "none"), "unknown service type", "duct_cleaning"),  # type: ignore[arg-type]
        (lambda: fee_note("hvac_repair", "gold"), "unknown tier", "gold"),  # type: ignore[arg-type]
    ]
    for call, match, value in bad_fns:
        with pytest.raises(ValueError, match=match) as excinfo:
            call()
        assert value not in str(excinfo.value)
