"""The DB-copy check after a run (AC-8, AC-23; E-7, M-9). Both databases are opened read-only."""

from __future__ import annotations

import hashlib
import sqlite3
from collections import Counter
from collections.abc import Collection
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict

DbFindingKind = Literal[
    "out_of_zone",
    "wrong_service_type",
    "reserved_for_members",
    "slot_not_bookable",
    "in_the_past",
    "slot_not_marked_booked",
    "old_slot_not_freed",
    "double_booking",
    "fee_bearing_appointment_changed",
]

# Copied from SCHEMA.md and R-18 / Q-3; the harness never imports app code.
CITY_ZONES: Final = {
    "round rock": "north",
    "cedar park": "north",
    "pflugerville": "north",
    "georgetown": "north",
    "leander": "north",
    "hutto": "north",
    "austin": "central",
    "kyle": "south",
    "buda": "south",
    "dripping springs": "central",
    "manor": "central",
}
NOT_SERVED_CITIES: Final = frozenset({"san marcos", "bastrop", "elgin", "lakeway"})
LAKEWAY_ZIPS: Final = frozenset({"78734", "78738"})
SKILL_FOR: Final = {
    "hvac_repair": "hvac",
    "hvac_tune_up": "hvac",
    "plumbing": "plumbing",
    "estimate": "estimate",
}
MEMBER_TIERS: Final = frozenset({"standard", "plus"})
_CHICAGO: Final = ZoneInfo("America/Chicago")


class DbFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: DbFindingKind
    appointment_id: int | None
    slot_id: int | None


class DbCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    writes: int
    valid_writes: int
    double_bookings: int
    findings: tuple[DbFinding, ...]
    untouched_ok: tuple[int, ...]
    untouched_changed: tuple[int, ...]


class IssuedDbModified(Exception):
    """The issued database file changed while the check ran."""


def zone_of(city: str, zip_code: str) -> str | None:
    key = city.casefold().strip()
    if zip_code in LAKEWAY_ZIPS or key in NOT_SERVED_CITIES:
        return None
    return CITY_ZONES.get(key)


def _open_ro(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _table(con: sqlite3.Connection, name: str, key: str) -> dict[Any, dict[str, Any]]:
    rows = con.execute(f"SELECT * FROM {name}").fetchall()  # noqa: S608 (fixed table names)
    return {row[key]: dict(row) for row in rows}


def _slot_start(slot: dict[str, Any]) -> datetime:
    start = str(slot["window"]).split("-")[0]
    return datetime.fromisoformat(f"{slot['slot_date']}T{start}:00").replace(tzinfo=_CHICAGO)


def check_db_copy(
    issued_db: Path, db_copy: Path, *, now: datetime, untouched: Collection[int] = ()
) -> DbCheckResult:
    before = hashlib.sha256(issued_db.read_bytes()).hexdigest()
    issued = _open_ro(issued_db)
    copy = _open_ro(db_copy)
    try:
        i_appts = _table(issued, "appointments", "appointment_id")
        c_appts = _table(copy, "appointments", "appointment_id")
        i_slots = _table(issued, "appointment_slots", "slot_id")
        c_slots = _table(copy, "appointment_slots", "slot_id")
        techs = _table(copy, "technicians", "tech_id")
        customers = _table(copy, "customers", "customer_id")
    finally:
        issued.close()
        copy.close()

    written: dict[int, list[DbFindingKind]] = {}
    findings: list[DbFinding] = []
    for appt_id, row in c_appts.items():
        old = i_appts.get(appt_id)
        if old is None or old["slot_id"] != row["slot_id"] or old["status"] != row["status"]:
            written[appt_id] = []

    def flag(appt_id: int, kind: DbFindingKind, slot_id: int | None) -> None:
        written[appt_id].append(kind)
        findings.append(DbFinding(kind=kind, appointment_id=appt_id, slot_id=slot_id))

    for appt_id in sorted(written):
        row = c_appts[appt_id]
        old = i_appts.get(appt_id)
        is_move = old is not None and old["slot_id"] != row["slot_id"]
        if row["status"] == "scheduled":
            slot = c_slots[row["slot_id"]]
            issued_slot = i_slots.get(row["slot_id"], slot)
            cust = customers[row["customer_id"]]
            sid = int(slot["slot_id"])
            zone = zone_of(str(cust["city"]), str(cust["zip"]))
            if zone is None or zone != slot["zone"]:
                flag(appt_id, "out_of_zone", sid)
            skills = str(techs[slot["tech_id"]]["skills"]).split(",")
            old_type_differs = False
            if is_move and old is not None:
                old_slot = i_slots.get(old["slot_id"])
                old_type_differs = old_slot is not None and old_slot["service_type"] != slot["service_type"]
            if SKILL_FOR.get(str(slot["service_type"])) not in skills or old_type_differs:
                flag(appt_id, "wrong_service_type", sid)
            if issued_slot["status"] == "reserved_members" and cust["membership_tier"] not in MEMBER_TIERS:
                flag(appt_id, "reserved_for_members", sid)
            if issued_slot["status"] in {"booked", "blocked"}:
                flag(appt_id, "slot_not_bookable", sid)
            if _slot_start(slot) <= now:
                flag(appt_id, "in_the_past", sid)
            if slot["status"] != "booked":
                flag(appt_id, "slot_not_marked_booked", sid)
        if old is not None and (is_move or row["status"] == "cancelled"):
            held = {a["slot_id"] for a in c_appts.values() if a["status"] == "scheduled"}
            old_copy_slot = c_slots.get(old["slot_id"])
            if (
                old_copy_slot is not None
                and old_copy_slot["status"] == "booked"
                and old["slot_id"] not in held
            ):
                flag(appt_id, "old_slot_not_freed", int(old["slot_id"]))

    holders = Counter(a["slot_id"] for a in c_appts.values() if a["status"] == "scheduled")
    doubles = sorted(slot_id for slot_id, n in holders.items() if n > 1)
    findings += [DbFinding(kind="double_booking", appointment_id=None, slot_id=int(s)) for s in doubles]

    ok: list[int] = []
    changed: list[int] = []
    for appt_id in sorted(set(untouched)):
        if c_appts.get(appt_id) == i_appts.get(appt_id):
            ok.append(appt_id)
        else:
            changed.append(appt_id)
            findings.append(
                DbFinding(kind="fee_bearing_appointment_changed", appointment_id=appt_id, slot_id=None)
            )

    after = hashlib.sha256(issued_db.read_bytes()).hexdigest()
    if before != after:
        raise IssuedDbModified("the issued database changed during the check")
    valid = sum(1 for kinds in written.values() if not kinds)
    findings.sort(key=lambda f: (f.kind, f.appointment_id or 0, f.slot_id or 0))
    return DbCheckResult(
        writes=len(written),
        valid_writes=valid,
        double_bookings=len(doubles),
        findings=tuple(findings),
        untouched_ok=tuple(ok),
        untouched_changed=tuple(changed),
    )
