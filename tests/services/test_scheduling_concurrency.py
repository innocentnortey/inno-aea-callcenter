"""AEA-28 AC-6 (E-7): two writers racing for one slot, each on its own connection and the real busy timeout."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date

import pytest

from meridian.adapters.sqlite.db import SqliteUnitOfWorkFactory
from meridian.domain.actions import ActionKind
from meridian.domain.specialists import WriteResult
from meridian.domain.tools import ToolCallScope
from meridian.policy.limits import Limits
from meridian.services.scheduling import Refused, SchedulingService, SlotTaken
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.scheduling_helpers import LINDA, entry, issued_sha256, key, raw, scope, thread, turn

_REPEATS = 20


@pytest.fixture
def store() -> Iterator[TempStore]:
    with temp_sqlite() as s:
        yield s


@pytest.fixture(scope="module", autouse=True)
def issued_unchanged() -> Iterator[None]:
    before = issued_sha256()
    yield
    assert issued_sha256() == before


def test_one_slot_two_bookers(store: TempStore) -> None:
    with store.uow() as tx:
        slots = [
            s.slot_id
            for s in tx.booking.slots.search(
                "north",
                "hvac_repair",
                member=False,
                earliest=date(2026, 10, 17),
                latest=date(2026, 12, 31),
                window=None,
                limit=_REPEATS,
            )
        ]
    assert len(slots) == _REPEATS
    doubles = 0
    for i, slot in enumerate(slots):
        svcs = [SchedulingService(SqliteUnitOfWorkFactory(store.db_path), Limits().booking) for _ in range(2)]
        scopes = [scope(store, thread(100 + 2 * i + j), turn(1), LINDA, {slot}) for j in range(2)]
        barrier = threading.Barrier(2)

        def book(
            j: int,
            slot: int = slot,
            svcs: list[SchedulingService] = svcs,
            scopes: list[ToolCallScope] = scopes,
            barrier: threading.Barrier = barrier,
        ) -> WriteResult | SlotTaken | Refused:
            sc = scopes[j]
            barrier.wait()
            return svcs[j].book(key(sc, ActionKind.BOOKED, str(slot)), sc, slot, "AC not cooling", entry(sc))

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(book, (0, 1)))
        wrote = [r for r in results if isinstance(r, WriteResult)]
        taken = [r for r in results if isinstance(r, SlotTaken)]
        assert (len(wrote), len(taken)) == (1, 1)
        with closing(raw(store)) as c:
            n = int(c.execute("SELECT COUNT(*) FROM appointments WHERE slot_id = ?", (slot,)).fetchone()[0])
        if n != 1:
            doubles += 1
    print(f"double bookings: {doubles} / {_REPEATS}")
    assert doubles == 0
