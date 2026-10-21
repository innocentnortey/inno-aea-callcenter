"""Booking repository: appointment_slots, appointments, technicians (AEA-28 body; AEA-02 shell; cases.md section 4.1)."""

from __future__ import annotations

import datetime as dt
import sqlite3
from typing import Any, Literal

from meridian.adapters.sqlite.db import StorageError, integrity_errors, last_row_id
from meridian.domain.common import CustomerId
from meridian.domain.records import Appointment, ServiceType, Slot, Window, Zone
from meridian.domain.specialists import AppointmentView

_SEARCH_SQL = (
    'SELECT slot_id, slot_date, "window", tech_id, zone, service_type, status FROM appointment_slots '
    "WHERE zone = ? AND service_type = ? "
    "AND (status = 'open' OR (? = 1 AND status = 'reserved_members')) "
    'AND slot_date BETWEEN ? AND ? AND (? IS NULL OR "window" = ?) '
    'ORDER BY slot_date, "window", slot_id LIMIT ?'
)


def _slot(r: tuple[Any, ...]) -> Slot:
    return Slot.model_validate(
        {
            "slot_id": r[0],
            "slot_date": r[1],
            "window": r[2],
            "tech_id": r[3],
            "zone": r[4],
            "service_type": r[5],
            "status": r[6],
        }
    )


def _appointment(r: tuple[Any, ...]) -> Appointment:
    return Appointment.model_validate(
        {
            "appointment_id": r[0],
            "slot_id": r[1],
            "customer_id": r[2],
            "issue_description": r[3] if r[3] is not None else "",
            "created_at": r[4],
            "status": r[5],
            "is_warranty_visit": bool(r[6]),
        }
    )


class SlotsRepo:
    """appointment_slots; = tx.booking.slots (cases.md 4.1)."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def search(
        self,
        zone: Zone,
        service_type: ServiceType,
        *,
        member: bool,
        earliest: dt.date,
        latest: dt.date,
        window: Window | None,
        limit: int,
    ) -> tuple[Slot, ...]:
        rows = self._conn.execute(
            _SEARCH_SQL,
            (
                zone,
                service_type,
                1 if member else 0,
                earliest.isoformat(),
                latest.isoformat(),
                window,
                window,
                limit,
            ),
        ).fetchall()
        return tuple(_slot(r) for r in rows)

    def get_for_update(self, slot_id: int) -> Slot | None:
        row = self._conn.execute(
            'SELECT slot_id, slot_date, "window", tech_id, zone, service_type, status '
            "FROM appointment_slots WHERE slot_id = ?",
            (slot_id,),
        ).fetchone()
        return None if row is None else _slot(row)

    def set_status(
        self, slot_id: int, status: Literal["open", "booked", "reserved_members", "blocked"]
    ) -> None:
        with integrity_errors("appointment_slots"):
            cur = self._conn.execute(
                "UPDATE appointment_slots SET status = ? WHERE slot_id = ?", (status, slot_id)
            )
        if cur.rowcount == 0:
            raise StorageError("appointment_slots", "no row")


class AppointmentsRepo:
    """appointments; = tx.booking.appointments (cases.md 4.1)."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(
        self, slot_id: int, customer_id: CustomerId, issue_description: str, created_at: dt.date
    ) -> int:
        with integrity_errors("appointments"):
            cur = self._conn.execute(
                "INSERT INTO appointments (slot_id, customer_id, issue_description, created_at, status, "
                "is_warranty_visit) VALUES (?, ?, ?, ?, 'scheduled', 0)",
                (slot_id, str(customer_id), issue_description, created_at.isoformat()),
            )
        return last_row_id(cur, "appointments")

    def get(self, appointment_id: int) -> Appointment | None:
        row = self._conn.execute(
            "SELECT appointment_id, slot_id, customer_id, issue_description, created_at, status, is_warranty_visit "
            "FROM appointments WHERE appointment_id = ?",
            (appointment_id,),
        ).fetchone()
        return None if row is None else _appointment(row)

    def for_customer(self, customer_id: CustomerId) -> tuple[Appointment, ...]:
        rows = self._conn.execute(
            "SELECT a.appointment_id, a.slot_id, a.customer_id, a.issue_description, a.created_at, a.status, "
            "a.is_warranty_visit FROM appointments a JOIN appointment_slots s ON s.slot_id = a.slot_id "
            "WHERE a.customer_id = ? AND a.status = 'scheduled' "
            'ORDER BY s.slot_date, s."window", a.appointment_id',
            (str(customer_id),),
        ).fetchall()
        return tuple(_appointment(r) for r in rows)

    def views_for_customer(self, customer_id: CustomerId) -> tuple[AppointmentView, ...]:
        rows = self._conn.execute(
            'SELECT a.appointment_id, s.slot_date, s."window", s.service_type, t.name, a.is_warranty_visit '
            "FROM appointments a JOIN appointment_slots s ON s.slot_id = a.slot_id "
            "LEFT JOIN technicians t ON t.tech_id = s.tech_id "
            "WHERE a.customer_id = ? AND a.status = 'scheduled' "
            'ORDER BY s.slot_date, s."window", a.appointment_id',
            (str(customer_id),),
        ).fetchall()
        return tuple(
            AppointmentView.model_validate(
                {
                    "appointment_id": r[0],
                    "date": r[1],
                    "window": r[2],
                    "service_type": r[3],
                    "technician": r[4],
                    "is_warranty_visit": bool(r[5]),
                }
            )
            for r in rows
        )

    def move(self, appointment_id: int, new_slot_id: int) -> None:
        with integrity_errors("appointments"):
            cur = self._conn.execute(
                "UPDATE appointments SET slot_id = ? WHERE appointment_id = ?", (new_slot_id, appointment_id)
            )
        if cur.rowcount == 0:
            raise StorageError("appointments", "no row")

    def set_status(
        self, appointment_id: int, status: Literal["scheduled", "completed", "cancelled", "no_show"]
    ) -> None:
        with integrity_errors("appointments"):
            cur = self._conn.execute(
                "UPDATE appointments SET status = ? WHERE appointment_id = ?", (status, appointment_id)
            )
        if cur.rowcount == 0:
            raise StorageError("appointments", "no row")


class TechniciansRepo:
    """technicians; = tx.booking.technicians (cases.md 4.1)."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def name(self, tech_id: int) -> str | None:
        row = self._conn.execute("SELECT name FROM technicians WHERE tech_id = ?", (tech_id,)).fetchone()
        return None if row is None else str(row[0])


class BookingRepos:
    """Scheduling reads and booking writes over the unit of work's one connection (body AEA-28, cases.md section 4.1)."""

    slots: SlotsRepo
    appointments: AppointmentsRepo
    technicians: TechniciansRepo

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.slots = SlotsRepo(conn)
        self.appointments = AppointmentsRepo(conn)
        self.technicians = TechniciansRepo(conn)
