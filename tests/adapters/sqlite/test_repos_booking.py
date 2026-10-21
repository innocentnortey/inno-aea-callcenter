"""AEA-28 AC-14 and PA-6: the booking repositories over the temp working copy."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator

import pytest

from meridian.adapters.sqlite.db import StorageError
from meridian.adapters.sqlite.migrate import restore_working_copy
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.scheduling_helpers import LINDA, issued_sha256


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


@pytest.fixture(scope="module", autouse=True)
def issued_unchanged() -> Iterator[None]:
    before = issued_sha256()
    yield
    assert issued_sha256() == before


def test_for_customer_and_next_id(store: TempStore) -> None:
    with store.uow() as tx:
        appts = tx.booking.appointments.for_customer(LINDA)
        assert [(a.appointment_id, a.slot_id, a.status) for a in appts] == [(159, 159, "scheduled")]
        views = tx.booking.appointments.views_for_customer(LINDA)
        assert [(v.date, v.window, v.technician) for v in views] == [
            (dt.date(2026, 10, 22), "08:00-12:00", "Marta Kowalski")
        ]
    with store.uow(write=True) as tx:
        assert tx.booking.appointments.insert(56, LINDA, "synthetic", dt.date(2026, 10, 16)) == 160
        tx.commit()
    with store.uow(write=True) as tx:
        restore_working_copy(tx, issued_path=store.issued_path)
        tx.commit()
    with store.uow(write=True) as tx:
        assert tx.booking.appointments.insert(56, LINDA, "synthetic", dt.date(2026, 10, 16)) == 160
        tx.commit()


def test_search_filters_and_orders(store: TempStore) -> None:
    d19, d20, d21 = dt.date(2026, 10, 19), dt.date(2026, 10, 20), dt.date(2026, 10, 21)
    with store.uow() as tx:
        s = tx.booking.slots
        rows = s.search("north", "hvac_repair", member=False, earliest=d19, latest=d20, window=None, limit=10)
        assert [r.slot_id for r in rows] == [56, 42, 57, 58, 91, 72]
        assert all(r.status == "open" for r in rows)
        rows = s.search(
            "north", "hvac_repair", member=False, earliest=d19, latest=d20, window="12:00-16:00", limit=10
        )
        assert [r.slot_id for r in rows] == [42, 57, 72]
        member = s.search(
            "north", "hvac_repair", member=True, earliest=d21, latest=d21, window=None, limit=10
        )
        assert 110 in [r.slot_id for r in member]
        guest = s.search(
            "north", "hvac_repair", member=False, earliest=d21, latest=d21, window=None, limit=10
        )
        assert 110 not in [r.slot_id for r in guest]
        two = s.search("north", "hvac_repair", member=False, earliest=d19, latest=d20, window=None, limit=2)
        assert len(two) == 2


def test_writes_on_unknown_rows_raise(store: TempStore) -> None:
    with store.uow(write=True) as tx:
        b = tx.booking
        with pytest.raises(StorageError):
            b.slots.set_status(99999, "open")
        with pytest.raises(StorageError):
            b.appointments.move(99999, 56)
        with pytest.raises(StorageError):
            b.appointments.set_status(99999, "cancelled")
        assert b.appointments.get(99999) is None
        assert b.technicians.name(99999) is None
