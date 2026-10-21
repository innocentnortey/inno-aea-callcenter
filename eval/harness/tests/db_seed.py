"""Build seeded copies of the issued scheduling DB for the DB-copy check tests (AEA-24 plan 7.1).

Only a temporary copy is ever opened for writing. Rows to change are found by query, never by hard-coded values.
The demo clock for these tests is Fri 2026-10-16 10:00 Chicago, so a slot on or after FUTURE_DATE is never in the past.
"""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
from pathlib import Path

from eval.harness.tests.fixture_cases import ISSUED_DB

FUTURE_DATE = "2026-10-19"
CITY_ZONES = {
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
SKILL_FOR = {"hvac_repair": "hvac", "hvac_tune_up": "hvac", "plumbing": "plumbing", "estimate": "estimate"}


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_issued(dst: Path) -> Path:
    shutil.copy(ISSUED_DB, dst)
    return dst


class SeedBuilder:
    """Mutates one temporary copy of the issued DB; each method adds one kind of write and returns what it touched."""

    def __init__(self, copy: Path) -> None:
        assert copy != ISSUED_DB
        self.con = sqlite3.connect(copy)
        self.con.row_factory = sqlite3.Row
        self.used_slots: set[int] = set()

    def close(self) -> None:
        self.con.commit()
        self.con.close()

    def _slot(self, *, status: str, zone: str | None, service_type: str | None) -> sqlite3.Row:
        rows: list[sqlite3.Row] = self.con.execute(
            "SELECT s.*, t.skills FROM appointment_slots s JOIN technicians t ON t.tech_id = s.tech_id"
            " WHERE s.status = ? AND s.slot_date >= ? ORDER BY s.slot_id",
            (status, FUTURE_DATE),
        ).fetchall()
        for row in rows:
            if row["slot_id"] in self.used_slots:
                continue
            if zone is not None and row["zone"] != zone:
                continue
            if service_type is not None and row["service_type"] != service_type:
                continue
            if SKILL_FOR[row["service_type"]] not in row["skills"].split(","):
                continue
            self.used_slots.add(row["slot_id"])
            return row
        raise LookupError(f"no {status} slot for zone={zone} service={service_type}")

    def _customer(self, *, zone: str, tier: str | None = None, exclude: set[str] | None = None) -> str:
        for row in self.con.execute("SELECT * FROM customers ORDER BY customer_id"):
            if CITY_ZONES.get(row["city"].casefold().strip()) != zone:
                continue
            if tier is not None and row["membership_tier"] != tier:
                continue
            if exclude and row["customer_id"] in exclude:
                continue
            return str(row["customer_id"])
        raise LookupError(f"no customer in zone {zone} tier {tier}")

    def _book(self, slot_id: int, customer_id: str, *, mark_booked: bool = True) -> int:
        cur = self.con.execute(
            "INSERT INTO appointments (slot_id, customer_id, issue_description, created_at, status, is_warranty_visit)"
            " VALUES (?, ?, 'seeded for the harness test', '2026-10-16T10:00:00-05:00', 'scheduled', 0)",
            (slot_id, customer_id),
        )
        if mark_booked:
            self.con.execute("UPDATE appointment_slots SET status = 'booked' WHERE slot_id = ?", (slot_id,))
        assert cur.lastrowid is not None
        return int(cur.lastrowid)

    def valid_booking(self) -> int:
        slot = self._slot(status="open", zone="north", service_type="hvac_repair")
        return self._book(slot["slot_id"], self._customer(zone="north"))

    def out_of_zone_booking(self) -> int:
        slot = self._slot(status="open", zone="north", service_type="hvac_repair")
        return self._book(slot["slot_id"], self._customer(zone="south"))

    def reserved_slot_for_non_member(self) -> int:
        slot = self._slot(status="reserved_members", zone=None, service_type=None)
        customer = self._customer(zone=slot["zone"], tier="none")
        return self._book(slot["slot_id"], customer)

    def double_booking(self) -> int:
        """Two scheduled appointments on one open slot; returns the slot id."""
        slot = self._slot(status="open", zone="central", service_type="plumbing")
        first = self._customer(zone="central")
        second = self._customer(zone="central", exclude={first})
        self._book(slot["slot_id"], first)
        self._book(slot["slot_id"], second, mark_booked=False)
        return int(slot["slot_id"])

    def wrong_service_move(self) -> int:
        """Move an issued appointment (not id 1) to a slot of a different service type; returns the appointment id."""
        rows = self.con.execute(
            "SELECT a.appointment_id, a.slot_id AS old_slot, s.service_type AS old_type, c.city"
            " FROM appointments a JOIN appointment_slots s ON s.slot_id = a.slot_id"
            " JOIN customers c ON c.customer_id = a.customer_id WHERE a.appointment_id != 1 ORDER BY a.appointment_id"
        ).fetchall()
        for row in rows:
            zone = CITY_ZONES.get(row["city"].casefold().strip())
            if zone is None:
                continue
            for service_type in ("hvac_repair", "hvac_tune_up", "plumbing"):
                if service_type == row["old_type"]:
                    continue
                try:
                    slot = self._slot(status="open", zone=zone, service_type=service_type)
                except LookupError:
                    continue
                self.con.execute(
                    "UPDATE appointments SET slot_id = ? WHERE appointment_id = ?",
                    (slot["slot_id"], row["appointment_id"]),
                )
                self.con.execute(
                    "UPDATE appointment_slots SET status = 'booked' WHERE slot_id = ?", (slot["slot_id"],)
                )
                self.con.execute(
                    "UPDATE appointment_slots SET status = 'open' WHERE slot_id = ?", (row["old_slot"],)
                )
                return int(row["appointment_id"])
        raise LookupError("no appointment could be moved to a different service type")

    def cancel(self, appointment_id: int) -> None:
        self.con.execute(
            "UPDATE appointments SET status = 'cancelled' WHERE appointment_id = ?", (appointment_id,)
        )
