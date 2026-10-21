"""LedgerService: record every model-call attempt's cost and stop model use at a cap (stage7/models.md §6).

Our cap (allow_turn) is checked by TurnService before a turn (MOD-11). A provider's own cap is a per-provider circuit
held in memory and released only by a successful probe (MOD-13).
"""

from __future__ import annotations

import datetime as dt
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, Protocol, cast, get_args, runtime_checkable
from zoneinfo import ZoneInfo

from meridian.adapters.sqlite.repos_spend import SpendRow
from meridian.domain.common import ProviderFailure, ProviderFailureKind, ProviderName
from meridian.domain.turn import TurnIds
from meridian.policy.limits import TurnLimits
from meridian.ports.models import CallRecord
from meridian.ports.runtime import UnitOfWorkFactory

__all__ = ["CallAdmission", "LedgerService", "SpendGuard"]

_log = logging.getLogger(__name__)

_DAY_ZONE: Final = "America/Chicago"  # the spend day (UX-3 CON-19; DO-3 C-12)
_CAP_KINDS: Final = frozenset({ProviderFailureKind.PROVIDER_SPEND_CAP, ProviderFailureKind.OUR_SPEND_LIMIT})
_PROVIDERS: Final = cast(tuple[ProviderName, ...], get_args(ProviderName))  # ("anthropic", "openrouter_jev")
_PROBE_LOST_AFTER_S: Final = float(TurnLimits().deadline_s)  # a probe in flight longer than one turn is lost


class CallAdmission(StrEnum):
    ALLOW = "allow"
    PROBE = "probe"
    REFUSE = "refuse"


@runtime_checkable
class SpendGuard(Protocol):
    def allow_turn(self) -> bool: ...


@dataclass
class _Circuit:
    tripped_at: float  # monotonic seconds
    probe_started: float | None = None


class LedgerService:
    """Writes one spend row per model-call attempt; answers the daily cap and per-provider circuit questions."""

    def __init__(
        self,
        uow: UnitOfWorkFactory,
        *,
        wall_clock: Callable[[], dt.datetime],
        daily_cap_usd: float,
        probe_after_s: float = 600.0,
        monotonic: Callable[[], float] = time.monotonic,
        probe_lost_after_s: float = _PROBE_LOST_AFTER_S,
    ) -> None:
        if daily_cap_usd < 0:
            raise ValueError("daily_cap_usd must be >= 0")
        if probe_after_s <= 0 or probe_lost_after_s <= 0:
            raise ValueError("probe intervals must be > 0")
        self._uow = uow
        self._wall_clock = wall_clock
        self._cap = daily_cap_usd
        self._probe_after_s = probe_after_s
        self._probe_lost_after_s = probe_lost_after_s
        self._monotonic = monotonic
        self._zone = ZoneInfo(_DAY_ZONE)
        self._circuits: dict[ProviderName, _Circuit] = {}
        self._lock = threading.Lock()

    def _now(self) -> dt.datetime:
        now = self._wall_clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("wall clock returned a naive datetime")
        return now.astimezone(dt.UTC)

    def record(self, call: CallRecord, ids: TurnIds) -> None:
        row = SpendRow.model_validate({**call.model_dump(), **ids.model_dump(), "recorded_at": self._now()})
        with self._uow(write=True) as tx:
            tx.spend.append(row)
            tx.commit()

    def _day_bounds_utc(self, now: dt.datetime) -> tuple[dt.datetime, dt.datetime]:
        local = now.astimezone(self._zone)
        start = dt.datetime.combine(local.date(), dt.time(0), tzinfo=self._zone)
        end = dt.datetime.combine(local.date() + dt.timedelta(days=1), dt.time(0), tzinfo=self._zone)
        return start.astimezone(dt.UTC), end.astimezone(dt.UTC)

    def spend_today(self) -> float:
        start, end = self._day_bounds_utc(self._now())
        with self._uow() as tx:
            return tx.spend.total_between(start, end)

    def allow_turn(self) -> bool:
        return self.spend_today() < self._cap

    def trip_provider_cap(self, failure: ProviderFailure) -> None:
        if failure.kind not in _CAP_KINDS:
            return
        with self._lock:
            self._circuits[failure.provider] = _Circuit(tripped_at=self._monotonic())
        _log.warning(
            "provider_circuit_open provider=%s failure_kind=%s", failure.provider, failure.kind.value
        )

    def admit_call(self, provider: ProviderName) -> CallAdmission:
        with self._lock:
            c = self._circuits.get(provider)
            if c is None:
                return CallAdmission.ALLOW
            now = self._monotonic()
            if now - c.tripped_at < self._probe_after_s:
                return CallAdmission.REFUSE
            if c.probe_started is not None and now - c.probe_started <= self._probe_lost_after_s:
                return CallAdmission.REFUSE
            lost = c.probe_started is not None
            c.probe_started = now
        if lost:
            _log.warning("provider_circuit_probe_lost provider=%s", provider)
        _log.info("provider_circuit_probe provider=%s", provider)
        return CallAdmission.PROBE

    def close_provider_cap(self, provider: ProviderName) -> None:
        with self._lock:
            removed = self._circuits.pop(provider, None)
        if removed is not None:
            _log.info("provider_circuit_closed provider=%s", provider)

    def open_circuits(self) -> tuple[ProviderName, ...]:
        with self._lock:
            return tuple(p for p in _PROVIDERS if p in self._circuits)

    def models_disabled(self) -> bool:
        return bool(self.open_circuits()) or not self.allow_turn()
