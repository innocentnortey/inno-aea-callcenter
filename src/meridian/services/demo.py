"""The one demo clock, simulated staffing and the forward-only clock advance (stage7/cases.md section 6; DO-3 4.4).

DemoClock reads the demo_state row, never the server clock (R-3). DemoService changes staffing and the clock, each in
one transaction with its demo_events row and its per-chat events. The four view types live in domain/views.py (AEA-02b).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, time, timedelta
from types import MappingProxyType
from typing import Final, Literal, Protocol, get_args
from zoneinfo import ZoneInfo

from pydantic import JsonValue

from meridian.adapters.sqlite.db import format_wall
from meridian.adapters.sqlite.rows import DemoEventRow, StreamEvent, thread_stream
from meridian.domain.common import Presence, RequestId
from meridian.domain.staff import DemoRole, StaffActor
from meridian.domain.views import ClockAdvanced, ClockView, StaffingChange, StaffingView
from meridian.policy.handoff import is_business_day
from meridian.policy.texts import TEXTS, TextId
from meridian.ports.runtime import UnitOfWork, UnitOfWorkFactory

__all__ = [
    "BUSINESS_MORNING",
    "CLOCK_STEPS",
    "STAFFING_CHANGED_OFF_LINE",
    "STAFFING_LABELS",
    "STAFFING_MODES",
    "ClockAdvanced",
    "ClockStep",
    "ClockView",
    "DeferredCases",
    "DemoClock",
    "DemoService",
    "LiveQueueConverter",
    "StaffingChange",
    "StaffingView",
    "format_clock",
    "next_demo_time",
]

_CHICAGO: Final = ZoneInfo("America/Chicago")
BUSINESS_MORNING: Final = time(
    7, 0
)  # [Source: OpenAPI advanceDemoClock "next business morning (Mon 7:00 am)"]

ClockStep = Literal["plus_1h", "plus_4h", "next_business_morning"]  # = OpenAPI ClockAdvanceRequest.step
CLOCK_STEPS: Final[tuple[str, ...]] = get_args(ClockStep)
STAFFING_MODES: Final[tuple[str, ...]] = get_args(Presence)

STAFFING_LABELS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "nobody_online": "Nobody online",  # [Source: OpenAPI Staffing.label; SCREEN_SPECS line 30]
        "simulated_on_shift": "Simulated staff on shift (demo)",  # same sources
    }
)
# Provisional copy (plan R-4): the specs give only the "on" line; this matches apps/web's dev fixture "staffing-off".
STAFFING_CHANGED_OFF_LINE: Final = "Staffing changed: nobody online."

_DAYS: Final = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS: Final = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _utc_now() -> datetime:  # default wall clock for demo_events.at_wall ONLY; DemoClock never calls it.
    return datetime.now(UTC)


def format_clock(dt: datetime) -> tuple[str, str]:
    """(label, date_label): the ONE formatter for CON-1, CON-8 and clock_changed."""
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("format_clock needs a tz-aware datetime")
    local = dt.astimezone(_CHICAGO)
    hour12 = local.hour % 12 or 12
    ampm = "am" if local.hour < 12 else "pm"
    date_part = f"{_DAYS[local.weekday()]} {_MONTHS[local.month - 1]} {local.day}, {local.year}"
    return (f"{date_part} · {hour12}:{local.minute:02d} {ampm}", f"{date_part} (demo date)")


def next_demo_time(old: datetime, step: ClockStep) -> datetime:
    """The demo time after one step; pure, always strictly later than `old`."""
    if step not in CLOCK_STEPS:
        raise ValueError("unknown clock step")
    if old.tzinfo is None or old.utcoffset() is None:
        raise ValueError("next_demo_time needs a tz-aware datetime")
    if step == "next_business_morning":
        day = old.astimezone(_CHICAGO).date() + timedelta(days=1)
        while not is_business_day(day):
            day += timedelta(days=1)
        return datetime.combine(day, BUSINESS_MORNING, tzinfo=_CHICAGO)
    hours = 1 if step == "plus_1h" else 4
    return (old.astimezone(UTC) + timedelta(hours=hours)).astimezone(_CHICAGO)


class DemoClock:
    """The Clock every service and node receives: the demo_state row, in America/Chicago (R-3)."""

    def __init__(self, uow: UnitOfWorkFactory) -> None:
        self._uow = uow

    def now(self) -> datetime:
        with self._uow() as tx:
            row = tx.cases.demo_state.get()
        return row.demo_now.astimezone(_CHICAGO)


class LiveQueueConverter(Protocol):
    """The ONE CaseService method DemoService calls (stage7/cases section 5)."""

    def convert_live_queued(self, now: datetime, tx: UnitOfWork | None = None) -> int: ...


class DeferredCases:
    """The case service, looked up when a shift ends rather than when the container builds.

    case_service is bound only once AEA-29 / AEA-51 land; resolving it at build time would stop every app start until
    then. An unbound case service fails the shift end (and rolls it back), never the boot.
    """

    def __init__(self, resolve: Callable[[], LiveQueueConverter]) -> None:
        self._resolve = resolve

    def convert_live_queued(self, now: datetime, tx: UnitOfWork | None = None) -> int:
        return self._resolve().convert_live_queued(now, tx)


def _banner(mode: str) -> str | None:
    return TEXTS[TextId.STAFFING_BANNER] if mode == "simulated_on_shift" else None


def _event_speaker() -> dict[str, JsonValue]:
    return {"kind": "event", "display_name": None}


class DemoService:
    """Staffing and the demo clock (stage7/cases section 6, CAS-18)."""

    def __init__(
        self,
        uow: UnitOfWorkFactory,
        clock: DemoClock,
        cases: LiveQueueConverter,
        *,
        wall_clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._cases = cases
        self._wall_clock = wall_clock

    def presence(self, tx: UnitOfWork | None = None) -> Presence:
        if tx is not None:
            return tx.cases.demo_state.get().staffing
        with self._uow() as own:
            return own.cases.demo_state.get().staffing

    def staffing(self) -> StaffingView:
        mode = self.presence()
        return StaffingView(mode=mode, label=STAFFING_LABELS[mode], banner=_banner(mode))

    def clock_view(self) -> ClockView:
        now = self._clock.now()
        label, date_label = format_clock(now)
        return ClockView(now=now, label=label, date_label=date_label)

    def set_staffing(self, mode: Presence, *, request_id: RequestId, role: DemoRole) -> StaffingChange:
        if mode not in STAFFING_MODES:
            raise ValueError("unknown staffing mode")
        with self._uow(write=True) as tx:
            state = tx.cases.demo_state.get()
            now = state.demo_now.astimezone(_CHICAGO)
            before = state.staffing
            if before == mode:
                return StaffingChange(mode=mode, label=STAFFING_LABELS[mode], converted_cases=0)
            tx.cases.demo_state.set_staffing(mode)
            converted = 0
            if before == "simulated_on_shift" and mode == "nobody_online":
                converted = self._cases.convert_live_queued(now, tx)
            line = (
                TEXTS[TextId.STAFFING_CHANGED_ON_SHIFT]
                if mode == "simulated_on_shift"
                else STAFFING_CHANGED_OFF_LINE
            )
            for thread_id in tx.core.conversations.open_thread_ids():
                tx.core.events.append(
                    thread_stream(thread_id),
                    StreamEvent(
                        type="staffing_changed",
                        at=now,
                        payload={
                            "speaker": _event_speaker(),
                            "staffing": {
                                "mode": mode,
                                "label": STAFFING_LABELS[mode],
                                "banner": _banner(mode),
                            },
                            "line": line,
                        },
                    ),
                )
            tx.cases.demo_events.insert(
                DemoEventRow(
                    demo_event_id=str(uuid.uuid4()),
                    at_wall=self._wall_clock(),
                    kind="staffing_changed",
                    step=None,
                    mode=mode,
                    demo_before=before,
                    demo_after=mode,
                    became_overdue=None,
                    converted_cases=converted,
                    request_id=str(request_id),
                    role=role.value,
                )
            )
            tx.commit()
        return StaffingChange(mode=mode, label=STAFFING_LABELS[mode], converted_cases=converted)

    def advance_clock(self, step: ClockStep, *, actor: StaffActor, request_id: RequestId) -> ClockAdvanced:
        if step not in CLOCK_STEPS:
            raise ValueError("unknown clock step")
        with self._uow(write=True) as tx:
            old = tx.cases.demo_state.get().demo_now.astimezone(_CHICAGO)
            new = next_demo_time(old, step)
            if new <= old:
                raise RuntimeError("clock step did not move forward")
            tx.cases.demo_state.set_now(new)
            became = sum(
                1 for c in tx.cases.cases.list_open() if c.due_at is not None and old <= c.due_at < new
            )
            label, date_label = format_clock(new)
            for thread_id in tx.core.conversations.open_thread_ids():
                tx.core.events.append(
                    thread_stream(thread_id),
                    StreamEvent(
                        type="clock_changed",
                        at=new,
                        payload={
                            "speaker": _event_speaker(),
                            "demo_clock": {"now": new.isoformat(), "label": label, "date_label": date_label},
                        },
                    ),
                )
            tx.cases.demo_events.insert(
                DemoEventRow(
                    demo_event_id=str(uuid.uuid4()),
                    at_wall=self._wall_clock(),
                    kind="clock_advanced",
                    step=step,
                    mode=None,
                    demo_before=format_wall(old),
                    demo_after=format_wall(new),
                    became_overdue=became,
                    converted_cases=None,
                    request_id=str(request_id),
                    role=actor.role.value,
                )
            )
            tx.commit()
        return ClockAdvanced(now=new, label=label, became_overdue=became)
