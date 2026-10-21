"""Booking rules: zone lookup, hours to a window, the 24-hour rule and the fee quote (AEA-13).

Pure module (DO-3 section 2.1): no I/O, no clock read, no log output. Every customer sentence comes from
``meridian.policy.texts``; this module types no wording and no dollar figure.

Sources: issued ``scheduling_db/SCHEMA.md`` (zone map, windows), KB ``policies/service_area.md`` (ZIP groups,
updated 2026-04-01), the 2026 fee schedule, ``docs/design/contracts/stage7/cases.md`` section 2 and
``graph-tools.md`` section 4. Callers: ``services/scheduling.py`` and ``agent/tools/scheduling.py`` (AEA-28),
``agent/tools/account.py`` (AEA-27).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import UTC, date, datetime, time
from types import MappingProxyType
from typing import Final, Literal
from zoneinfo import ZoneInfo

from meridian.domain.records import FeeNote, ServiceType, Window, Zone
from meridian.policy.texts import TextId, format_usd, render

__all__ = [
    "LAKEWAY_ZIPS",
    "MEMBER_ALLOWANCE_ROWS",
    "NOT_SERVED_CITIES",
    "SCHEDULE_FEES",
    "fee_bearing",
    "fee_note",
    "hours_before",
    "zone_for",
]

# The one owner of every scheduled fee amount, in cents (graph-tools section 4, C-3, R-G-3). Keys are the invoice
# line wording. The member columns are 0 here; for the allowance rows below that 0 means "included", not "free".
SCHEDULE_FEES: Final[Mapping[str, Mapping[Literal["none", "standard", "plus"], int]]] = MappingProxyType(
    {
        "Diagnostic visit": MappingProxyType({"none": 8900, "standard": 0, "plus": 0}),
        "After-hours dispatch": MappingProxyType({"none": 14900, "standard": 0, "plus": 0}),
        "Seasonal tune-up": MappingProxyType({"none": 12900, "standard": 0, "plus": 0}),
    }
)
MEMBER_ALLOWANCE_ROWS: Final[frozenset[str]] = frozenset({"Seasonal tune-up"})

_CHICAGO: Final = ZoneInfo("America/Chicago")
_TIERS: Final[frozenset[str]] = frozenset({"none", "standard", "plus"})

# [Source: KB policies/service_area.md]
NOT_SERVED_CITIES: Final[frozenset[str]] = frozenset({"San Marcos", "Bastrop", "Elgin", "Lakeway"})
# [A] CAS-8: both are 787xx, so this specific exclusion wins over "Austin: 787xx (all)". Replaced by a check of
# the full USPS list for Lakeway at Stage 9.
LAKEWAY_ZIPS: Final[frozenset[str]] = frozenset({"78734", "78738"})

_CITY_ZONES: Final[Mapping[str, Zone]] = MappingProxyType(
    {
        # SCHEMA.md "Zone mapping (city -> zone)"
        "round rock": "north",
        "cedar park": "north",
        "pflugerville": "north",
        "georgetown": "north",
        "leander": "north",
        "hutto": "north",
        "austin": "central",
        "kyle": "south",
        "buda": "south",
        # Q-3 (Innocent 2026-10-20): newly served April 2026, configured here, never an edit to SCHEMA.md
        "dripping springs": "central",
        "manor": "central",
    }
)
_SERVICE_AREA_ZIPS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        # KB policies/service_area.md (updated 2026-04-01); each group keyed by a city in _CITY_ZONES
        "round rock": ("78664", "78665", "78681"),
        "cedar park": ("78613", "78641", "78645"),  # "Cedar Park / Leander" (both north)
        "pflugerville": ("78660", "78634"),  # "Pflugerville / Hutto" (both north)
        "georgetown": ("78626", "78628", "78633"),
        "kyle": ("78640", "78610"),  # "Kyle / Buda" (both south)
        "dripping springs": ("78620",),
        "manor": ("78653",),
    }
)
_ZIP_ZONES: Final[Mapping[str, Zone]] = MappingProxyType(
    {z: _CITY_ZONES[city] for city, zips in _SERVICE_AREA_ZIPS.items() for z in zips}
)
_AUSTIN_ZIP_PREFIX: Final = "787"  # service_area.md "Austin: 787xx (all)"
_NOT_SERVED_KEYS: Final[frozenset[str]] = frozenset(c.casefold() for c in NOT_SERVED_CITIES)
_ZIP_RE: Final = re.compile(r"(\d{5})(?:-\d{4})?")
_STATE_SUFFIX_RE: Final = re.compile(r"(.*?)(?:,\s*|\s+)(?:tx|texas)")  # used with fullmatch only
_MAX_LOCATION_CHARS: Final = 64
_WINDOW_RE: Final = re.compile(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})")


def zone_for(city_or_zip: str) -> Zone | None:
    """Zone of a served city or ZIP; ``None`` when not served or unknown. Never raises and never records the input."""
    if not isinstance(city_or_zip, str):
        return None
    text = " ".join(city_or_zip.split())
    if text == "" or len(text) > _MAX_LOCATION_CHARS:
        return None
    m = _ZIP_RE.fullmatch(text)
    if m is not None:
        zip5 = m.group(1)
        if zip5 in LAKEWAY_ZIPS:
            return None
        if zip5 in _ZIP_ZONES:
            return _ZIP_ZONES[zip5]
        if zip5.startswith(_AUSTIN_ZIP_PREFIX):
            return "central"
        return None
    key = text.casefold()
    s = _STATE_SUFFIX_RE.fullmatch(key)
    if s is not None:
        key = s.group(1)
    key = key.strip(" ,")
    if key in _NOT_SERVED_KEYS:
        return None
    return _CITY_ZONES.get(key)


def _window_start(slot_date: date, window: str) -> datetime:
    m = _WINDOW_RE.fullmatch(window)
    if m is None:
        raise ValueError("hours_before: window must look like HH:MM-HH:MM")
    return datetime.combine(slot_date, time(int(m.group(1)), int(m.group(2))), tzinfo=_CHICAGO)


def hours_before(now: datetime, slot_date: date, window: Window) -> float:
    """Real elapsed hours from the injected demo clock to the window start; negative once it has started."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("hours_before: now must be timezone-aware (the demo clock)")
    start = _window_start(slot_date, window)
    # Subtract in UTC: two aware values on the same zone object would otherwise subtract wall-clock time and
    # miss a DST change between them.
    return (start.astimezone(UTC) - now.astimezone(UTC)).total_seconds() / 3600.0


def fee_bearing(hours: float) -> bool:
    # Fee schedule "Late cancellation (<24h)"; CAS-6: exactly 24.0 hours is free, a started or past window is not.
    return hours < 24.0


_FEE_ROW_FOR: Final[Mapping[str, str | None]] = MappingProxyType(
    {
        "hvac_repair": "Diagnostic visit",  # CAS-7 / fee schedule "Diagnostic visit"
        "plumbing": "Diagnostic visit",  # CAS-7: no service restriction on the diagnostic row
        "hvac_tune_up": "Seasonal tune-up",  # R-G-3
        "estimate": None,  # services/service_catalog.md "Free in-home estimate"
    }
)
_PAY_TEXT: Final[Mapping[str, TextId]] = MappingProxyType(
    {
        "Diagnostic visit": TextId.FEE_STANDARD_DIAGNOSTIC,
        "Seasonal tune-up": TextId.FEE_TUNE_UP,
    }
)
_WAIVED_TEXT: Final[Mapping[str, TextId]] = MappingProxyType(
    {
        "Diagnostic visit": TextId.FEE_DIAGNOSTIC_WAIVED,
        "Seasonal tune-up": TextId.FEE_TUNE_UP_INCLUDED,
    }
)


def fee_note(service_type: ServiceType, tier: Literal["none", "standard", "plus"]) -> FeeNote:
    """The visit fee for a service type and the verified tier (``"none"`` when unverified, R-14).

    No waiver or discount beyond the tier column (D3 = DEC-2); the late-change fee is never handled here.
    """
    if service_type not in _FEE_ROW_FOR:
        raise ValueError("fee_note: unknown service type")
    if tier not in _TIERS:
        raise ValueError("fee_note: unknown tier")
    fee_row = _FEE_ROW_FOR[service_type]
    if fee_row is None:
        return FeeNote(
            service_type=service_type,
            tier=tier,
            fee_row=None,
            amount_cents=0,
            waived=False,
            line=render(TextId.FEE_ESTIMATE_FREE),
        )
    amount = SCHEDULE_FEES[fee_row][tier]
    waived = amount == 0
    if waived:
        line = render(_WAIVED_TEXT[fee_row], amount=format_usd(SCHEDULE_FEES[fee_row]["none"]))
    else:
        line = render(_PAY_TEXT[fee_row], amount=format_usd(amount))
    return FeeNote(
        service_type=service_type,
        tier=tier,
        fee_row=fee_row,
        amount_cents=amount,
        waived=waived,
        line=line,
    )
