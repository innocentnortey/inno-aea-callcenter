"""AEA-24 AC-8: the DB-copy check (E-7, M-9) on temporary copies of the issued SQLite."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from eval.harness.tests.db_seed import SeedBuilder, copy_issued, sha256_of
from eval.harness.tests.fixture_cases import ISSUED_DB

NOW = datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))


def _kinds(result: Any) -> set[str]:
    return {f.kind for f in result.findings}


def test_db_copy_check_rules(tmp_path: Path) -> None:
    """invariant: the check flags each seeded rule break, passes a valid write, never writes the issued file."""
    from eval.harness.dbcheck import check_db_copy

    issued_hash = sha256_of(ISSUED_DB)

    clean = copy_issued(tmp_path / "clean.sqlite")
    result = check_db_copy(ISSUED_DB, clean, now=NOW, untouched=[1])
    assert result.writes == 0
    assert result.findings == ()
    assert result.double_bookings == 0
    assert result.untouched_ok == (1,)
    assert result.untouched_changed == ()

    valid_only = copy_issued(tmp_path / "valid.sqlite")
    builder = SeedBuilder(valid_only)
    valid_id = builder.valid_booking()
    builder.close()
    result = check_db_copy(ISSUED_DB, valid_only, now=NOW, untouched=[1])
    assert (result.writes, result.valid_writes) == (1, 1), f"valid appointment {valid_id} must pass"
    assert result.findings == ()

    bad = copy_issued(tmp_path / "bad.sqlite")
    builder = SeedBuilder(bad)
    builder.valid_booking()
    out_of_zone_id = builder.out_of_zone_booking()
    moved_id = builder.wrong_service_move()
    reserved_id = builder.reserved_slot_for_non_member()
    double_slot = builder.double_booking()
    builder.close()
    result = check_db_copy(ISSUED_DB, bad, now=NOW, untouched=[1])
    kinds = _kinds(result)
    assert {"out_of_zone", "wrong_service_type", "reserved_for_members", "double_booking"} <= kinds
    by_kind = {f.kind: f for f in result.findings}
    assert by_kind["out_of_zone"].appointment_id == out_of_zone_id
    assert by_kind["wrong_service_type"].appointment_id == moved_id
    assert by_kind["reserved_for_members"].appointment_id == reserved_id
    assert by_kind["double_booking"].slot_id == double_slot
    assert result.double_bookings == 1
    assert result.writes == 6
    assert 1 <= result.valid_writes <= result.writes - 3
    assert result.untouched_ok == (1,)

    assert sha256_of(ISSUED_DB) == issued_hash


def test_fee_bearing_appointment_changed_is_flagged(tmp_path: Path) -> None:
    """invariant: WP-4's appointment 1 changed on the copy is reported, not hidden."""
    from eval.harness.dbcheck import check_db_copy

    copy = copy_issued(tmp_path / "changed.sqlite")
    builder = SeedBuilder(copy)
    builder.cancel(1)
    builder.close()
    result = check_db_copy(ISSUED_DB, copy, now=NOW, untouched=[1])
    assert result.untouched_changed == (1,)
    assert result.untouched_ok == ()
    assert "fee_bearing_appointment_changed" in _kinds(result)


def test_zone_of_rules() -> None:
    """boundary: out-of-area cities and the Lakeway zips have no zone; city matching is case and space blind."""
    from eval.harness.dbcheck import zone_of

    assert zone_of("Round Rock", "78664") == "north"
    assert zone_of("  KYLE ", "78640") == "south"
    assert zone_of("Austin", "78745") == "central"
    assert zone_of("Austin", "78734") is None
    assert zone_of("Lakeway", "78734") is None
    assert zone_of("San Marcos", "78666") is None
    assert zone_of("Nowhere", "00000") is None
