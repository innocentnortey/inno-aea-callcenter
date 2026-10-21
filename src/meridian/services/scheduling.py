"""The only writer of slots and appointments (DO-2 section A.5): find windows, book, move, cancel, record a fee-bearing
change request; each write is one transaction (slot re-read + write + actions row + lookup_log row, DO-1 section 9).
Types: cases.md section 4 (CAS-17)."""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, time, timedelta
from typing import Final, Literal, cast
from zoneinfo import ZoneInfo

from pydantic import Field

from meridian.domain.actions import ActionKey, ActionKind, CompletedAction
from meridian.domain.common import CustomerId, MeridianModel, TurnId
from meridian.domain.records import FeeNote, MembershipTier, ServiceType, ShownSlot, Slot, Window, Zone
from meridian.domain.specialists import (
    ChangeRequestDraft,
    ConfirmationView,
    SchedulingSliceInputs,
    WriteResult,
)
from meridian.domain.tools import LookupEntry, ToolCallScope
from meridian.policy.booking import (
    NOT_SERVED_CITIES,
    fee_bearing,
    fee_note,
    hours_before,
    zone_for,
)
from meridian.policy.limits import BookingLimits
from meridian.policy.texts import TextId, format_usd, render
from meridian.ports.runtime import UnitOfWork, UnitOfWorkFactory

_CHICAGO: Final = ZoneInfo("America/Chicago")
_LATE_CHANGE_FEE_CENTS: Final = (
    4900  # [Source: pricing/2026_fee_schedule.pdf "Late cancellation (<24h) $49"].
)
#                                       Here because policy/booking.py's test bans the literal there.
_HORIZON_DAYS: Final = 60  # [A] how far ahead an open search looks (issued slots run 2026-10-16…11-05)
_FETCH: Final = 60  # [A] rows read per search before started windows and repeated (date, window) drop
_ALTERNATIVES: Final = 3  # [A] fresh windows offered with SlotTaken (= WindowQuery.limit default)
_ZIP_RE: Final = re.compile(r"[0-9]{5}(?:-[0-9]{4})?")
_STATE_SUFFIX_RE: Final = re.compile(r"(.*?)(?:,\s*|\s+)(?:tx|texas)")  # used with fullmatch only
_MAX_HINT_CHARS: Final = 64
_NOT_SERVED_KEYS: Final = frozenset(c.casefold() for c in NOT_SERVED_CITIES)
_log = logging.getLogger(__name__)


class WindowQuery(MeridianModel):
    zone_hint: str
    service_type: ServiceType
    member_tier: MembershipTier
    wanted_text: str = ""
    earliest: date | None = None
    latest: date | None = None
    window: Window | None = None
    limit: int = Field(default=3, ge=1, le=6)  # [A] cases §4


class WindowsFound(MeridianModel):
    zone: Zone
    windows: tuple[ShownSlot, ...]
    exact_fit: bool


class OutOfArea(MeridianModel):
    reason: Literal["not_served", "unknown_location"]


class SlotTaken(MeridianModel):
    slot_id: int
    alternatives: tuple[ShownSlot, ...]


class Refused(MeridianModel):
    code: Literal[
        "fee_bearing", "not_shown", "outside_service_area", "wrong_service_type", "booking_cap", "not_owned"
    ]
    hours_before: float | None = None


class CustomerTerms(MeridianModel):
    """AEA-28-internal (plan decision D-2): only agent/tools/scheduling.py reads it."""

    location: str  # the customer's ZIP on file when zone_for(zip) resolves it, else the city
    tier: MembershipTier


def _window_start(slot_date: date, window: Window) -> datetime:
    return datetime.combine(slot_date, time.fromisoformat(window[:5]), tzinfo=_CHICAGO)


def _out_of_area_reason(hint: str) -> Literal["not_served", "unknown_location"]:
    text = " ".join(hint.split()).casefold()
    if not text or len(text) > _MAX_HINT_CHARS:
        return "unknown_location"
    if _ZIP_RE.fullmatch(text):
        return "not_served"
    m = _STATE_SUFFIX_RE.fullmatch(text)
    if m:
        text = m.group(1)
    text = text.strip(" ,")
    return "not_served" if text in _NOT_SERVED_KEYS else "unknown_location"


def _customer_zone(zip_code: str, city: str) -> Zone | None:
    return zone_for(zip_code) or zone_for(city)


def _visit_dict(slot: Slot, technician: str) -> dict[str, str]:
    return {
        "date": slot.slot_date.isoformat(),
        "window": slot.window,
        "technician": technician,
        "service_type": slot.service_type,
    }


def _after_visit(slot: Slot, technician: str, fee: FeeNote) -> dict[str, str]:
    return _visit_dict(slot, technician) | {"fee_line": fee.line}


def _change_fee_line(hours: float) -> str:
    if fee_bearing(hours):
        return render(TextId.FEE_APPLIES, amount=format_usd(_LATE_CHANGE_FEE_CENTS))
    return render(TextId.FREE_CHANGE_NOTE)


def _today(now: datetime) -> date:
    return now.astimezone(_CHICAGO).date()


class SchedulingService:
    """Each method opens and commits its own transaction."""

    def __init__(self, uow: UnitOfWorkFactory, booking: BookingLimits) -> None:
        self._uow = uow
        self._booking = booking

    # -- private readers --------------------------------------------------------------------------------------

    def _technician(self, tx: UnitOfWork, tech_id: int) -> str:
        name = tx.booking.technicians.name(tech_id)
        if name is None:
            raise RuntimeError("technician row missing")
        return name

    def _shown(self, tx: UnitOfWork, slot: Slot, shown_turn: TurnId) -> ShownSlot:
        return ShownSlot(
            slot_id=slot.slot_id,
            date=slot.slot_date,
            window=slot.window,
            technician=self._technician(tx, slot.tech_id),
            service_type=slot.service_type,
            zone=slot.zone,
            member_reserved=(slot.status == "reserved_members"),
            shown_turn=shown_turn,
        )

    @staticmethod
    def _bookable(slot: Slot, member: bool, now: datetime) -> bool:
        open_to_caller = slot.status == "open" or (member and slot.status == "reserved_members")
        return open_to_caller and hours_before(now, slot.slot_date, slot.window) > 0

    def _windows(
        self,
        tx: UnitOfWork,
        *,
        zone: Zone,
        service_type: ServiceType,
        member: bool,
        earliest: date,
        latest: date,
        window: Window | None,
        now: datetime,
        shown_turn: TurnId,
        limit: int,
        skip: set[tuple[date, str]],
        skip_slot: int | None = None,
    ) -> list[ShownSlot]:
        rows = tx.booking.slots.search(
            zone, service_type, member=member, earliest=earliest, latest=latest, window=window, limit=_FETCH
        )
        result: list[ShownSlot] = []
        for s in rows:
            if len(result) >= limit:
                break
            if s.slot_id == skip_slot:
                continue
            if hours_before(now, s.slot_date, s.window) <= 0:
                continue
            k = (s.slot_date, s.window)
            if k in skip:
                continue
            skip.add(k)
            result.append(self._shown(tx, s, shown_turn))
        return result

    def _alternatives(
        self, tx: UnitOfWork, slot: Slot, member: bool, scope: ToolCallScope, taken_slot_id: int
    ) -> tuple[ShownSlot, ...]:
        today = _today(scope.now)
        return tuple(
            self._windows(
                tx,
                zone=slot.zone,
                service_type=slot.service_type,
                member=member,
                earliest=today,
                latest=today + timedelta(days=_HORIZON_DAYS),
                window=None,
                now=scope.now,
                shown_turn=scope.ids.turn_id,
                limit=_ALTERNATIVES,
                skip=set(),
                skip_slot=taken_slot_id,
            )
        )

    @staticmethod
    def _find_replay(tx: UnitOfWork, key: ActionKey) -> CompletedAction | None:
        return next((a for a in tx.core.actions.for_thread(key.thread_id) if a.key == key), None)

    def _owned_visit(
        self, tx: UnitOfWork, scope: ToolCallScope, appointment_id: int
    ) -> tuple[int, Slot] | None:
        """The verified customer's scheduled appointment (its id and current slot), else None."""
        appt = tx.booking.appointments.get(appointment_id)
        if appt is None or appt.customer_id != scope.customer_id or appt.status != "scheduled":
            return None
        slot = tx.booking.slots.get_for_update(appt.slot_id)
        return None if slot is None else (appt.appointment_id, slot)

    def _replay_result(
        self, tx: UnitOfWork, scope: ToolCallScope, existing: CompletedAction
    ) -> WriteResult | ChangeRequestDraft:
        cust = tx.core.reads.customer(scope.customer_id) if scope.customer_id is not None else None
        tier: MembershipTier = cust.membership_tier if cust is not None else "none"
        if existing.kind is ActionKind.CHANGE_REQUEST_SENT:
            after = existing.after or {}
            appt_id = int(existing.records["appointment"])
            slot_id = int(existing.records["slot"])
            slot = tx.booking.slots.get_for_update(slot_id)
            if slot is None:
                raise RuntimeError("slot row missing")
            change = cast(Literal["move", "cancel"], after["change"])
            h = hours_before(scope.now, slot.slot_date, slot.window)
            return ChangeRequestDraft(
                appointment_id=appt_id,
                change=change,
                wanted_text=after["wanted_text"],
                windows_shown=tuple(sorted(scope.shown_slot_ids)),
                hours_before=h,
                window_start=_window_start(slot.slot_date, slot.window),
            )
        d = (existing.before if existing.kind is ActionKind.CANCELLED else existing.after) or {}
        return WriteResult(
            action=existing,
            confirmation=ConfirmationView.model_validate(
                {
                    "date": d["date"],
                    "window": d["window"],
                    "technician": d["technician"],
                    "fee_note": fee_note(cast(ServiceType, d["service_type"]), tier),
                }
            ),
        )

    def _outcome(self, op: str, outcome: str, scope: ToolCallScope) -> None:
        _log.info("scheduling_write op=%s outcome=%s turn_id=%s", op, outcome, scope.ids.turn_id)

    def _refuse(self, op: str, scope: ToolCallScope, code: str, hours: float | None = None) -> Refused:
        self._outcome(op, f"refused:{code}", scope)
        return Refused(code=cast(Literal["fee_bearing"], code), hours_before=hours)

    def _store(self, tx: UnitOfWork, action: CompletedAction, lookup: LookupEntry) -> CompletedAction:
        stored = tx.core.actions.record(action)
        tx.core.lookup_log.append(lookup)
        tx.commit()
        return stored

    # -- reads ------------------------------------------------------------------------------------------------

    def find_windows(
        self, query: WindowQuery, now: datetime, *, shown_turn: TurnId
    ) -> WindowsFound | OutOfArea:
        zone = zone_for(query.zone_hint)
        if zone is None:
            return OutOfArea(reason=_out_of_area_reason(query.zone_hint))
        member = query.member_tier != "none"
        today = _today(now)
        fit_from = max(query.earliest or today, today)
        fit_to = query.latest or (fit_from + timedelta(days=_HORIZON_DAYS))
        with self._uow() as tx:
            seen: set[tuple[date, str]] = set()
            fit = (
                []
                if fit_to < fit_from
                else self._windows(
                    tx,
                    zone=zone,
                    service_type=query.service_type,
                    member=member,
                    earliest=fit_from,
                    latest=fit_to,
                    window=query.window,
                    now=now,
                    shown_turn=shown_turn,
                    limit=query.limit,
                    skip=seen,
                )
            )
            rest = (
                []
                if len(fit) >= query.limit
                else self._windows(
                    tx,
                    zone=zone,
                    service_type=query.service_type,
                    member=member,
                    earliest=today,
                    latest=today + timedelta(days=_HORIZON_DAYS),
                    window=None,
                    now=now,
                    shown_turn=shown_turn,
                    limit=query.limit - len(fit),
                    skip=seen,
                )
            )
        _log.info("scheduling_search zone=%s windows=%d exact_fit=%s", zone, len(fit) + len(rest), bool(fit))
        return WindowsFound(zone=zone, windows=tuple(fit + rest), exact_fit=bool(fit))

    def slice_inputs(self, customer_id: CustomerId) -> SchedulingSliceInputs:
        with self._uow() as tx:
            cust = tx.core.reads.customer(customer_id)
            if cust is None:
                return SchedulingSliceInputs(zone=None, member=False, appointments=())
            return SchedulingSliceInputs(
                zone=_customer_zone(cust.zip, cust.city),
                member=cust.membership_tier != "none",
                appointments=tx.booking.appointments.views_for_customer(customer_id),
            )

    def customer_terms(self, customer_id: CustomerId) -> CustomerTerms | None:
        with self._uow() as tx:
            cust = tx.core.reads.customer(customer_id)
            if cust is None:
                return None
            location = cust.zip if zone_for(cust.zip) is not None else cust.city
            return CustomerTerms(location=location, tier=cust.membership_tier)

    # -- writes -----------------------------------------------------------------------------------------------

    def book(
        self, key: ActionKey, scope: ToolCallScope, slot_id: int, issue: str, lookup: LookupEntry
    ) -> WriteResult | SlotTaken | Refused:
        customer_id = scope.customer_id
        if customer_id is None:
            return self._refuse("book", scope, "not_owned")
        with self._uow(write=True) as tx:
            existing = self._find_replay(tx, key)
            if existing is not None:
                self._outcome("book", "replayed", scope)
                replay = self._replay_result(tx, scope, existing)
                if isinstance(replay, WriteResult):
                    return replay
            if slot_id not in scope.shown_slot_ids:
                return self._refuse("book", scope, "not_shown")
            cust = tx.core.reads.customer(customer_id)
            if cust is None:
                return self._refuse("book", scope, "not_owned")
            tier = cust.membership_tier
            member = tier != "none"
            zone = _customer_zone(cust.zip, cust.city)
            booked = sum(
                1 for a in tx.core.actions.for_thread(scope.ids.thread_id) if a.kind is ActionKind.BOOKED
            )
            if booked >= self._booking.max_per_conversation:
                return self._refuse("book", scope, "booking_cap")
            slot = tx.booking.slots.get_for_update(slot_id)
            if slot is None:
                return self._refuse("book", scope, "not_shown")
            if zone is None or slot.zone != zone:
                return self._refuse("book", scope, "outside_service_area")
            if not self._bookable(slot, member, scope.now):
                self._outcome("book", "slot_taken", scope)
                return SlotTaken(
                    slot_id=slot_id, alternatives=self._alternatives(tx, slot, member, scope, slot_id)
                )
            tx.booking.slots.set_status(slot_id, "booked")
            appt_id = tx.booking.appointments.insert(slot_id, customer_id, issue, _today(scope.now))
            tech = self._technician(tx, slot.tech_id)
            fee = fee_note(slot.service_type, tier)
            action = CompletedAction(
                key=key,
                kind=ActionKind.BOOKED,
                records={"appointment": str(appt_id), "slot": str(slot_id)},
                before=None,
                after=_after_visit(slot, tech, fee),
                at=scope.now,
            )
            stored = self._store(tx, action, lookup)
        self._outcome("book", "written", scope)
        return WriteResult(
            action=stored,
            confirmation=ConfirmationView(
                date=slot.slot_date, window=slot.window, technician=tech, fee_note=fee
            ),
        )

    def move(
        self, key: ActionKey, scope: ToolCallScope, appointment_id: int, new_slot_id: int, lookup: LookupEntry
    ) -> WriteResult | SlotTaken | Refused:
        customer_id = scope.customer_id
        if customer_id is None:
            return self._refuse("move", scope, "not_owned")
        with self._uow(write=True) as tx:
            existing = self._find_replay(tx, key)
            if existing is not None:
                self._outcome("move", "replayed", scope)
                replay = self._replay_result(tx, scope, existing)
                if isinstance(replay, WriteResult):
                    return replay
            cust = tx.core.reads.customer(customer_id)
            if cust is None:
                return self._refuse("move", scope, "not_owned")
            tier = cust.membership_tier
            member = tier != "none"
            zone = _customer_zone(cust.zip, cust.city)
            visit = self._owned_visit(tx, scope, appointment_id)
            if visit is None:
                return self._refuse("move", scope, "not_owned")
            old = visit[1]
            h = hours_before(scope.now, old.slot_date, old.window)
            if fee_bearing(h):
                return self._refuse("move", scope, "fee_bearing", h)
            if new_slot_id not in scope.shown_slot_ids:
                return self._refuse("move", scope, "not_shown")
            new = tx.booking.slots.get_for_update(new_slot_id)
            if new is None:
                return self._refuse("move", scope, "not_shown")
            if zone is None or new.zone != zone:
                return self._refuse("move", scope, "outside_service_area")
            if new.service_type != old.service_type:
                return self._refuse("move", scope, "wrong_service_type")
            if not self._bookable(new, member, scope.now):
                self._outcome("move", "slot_taken", scope)
                return SlotTaken(
                    slot_id=new_slot_id, alternatives=self._alternatives(tx, new, member, scope, new_slot_id)
                )
            tx.booking.slots.set_status(old.slot_id, "open")
            tx.booking.slots.set_status(new.slot_id, "booked")
            tx.booking.appointments.move(appointment_id, new.slot_id)
            before = _visit_dict(old, self._technician(tx, old.tech_id))
            tech = self._technician(tx, new.tech_id)
            fee = fee_note(new.service_type, tier)
            action = CompletedAction(
                key=key,
                kind=ActionKind.MOVED,
                records={
                    "appointment": str(appointment_id),
                    "slot": str(new.slot_id),
                    "old_slot": str(old.slot_id),
                },
                before=before,
                after=_after_visit(new, tech, fee),
                at=scope.now,
            )
            stored = self._store(tx, action, lookup)
        self._outcome("move", "written", scope)
        return WriteResult(
            action=stored,
            confirmation=ConfirmationView(
                date=new.slot_date, window=new.window, technician=tech, fee_note=fee
            ),
        )

    def cancel(
        self, key: ActionKey, scope: ToolCallScope, appointment_id: int, lookup: LookupEntry
    ) -> WriteResult | Refused:
        customer_id = scope.customer_id
        if customer_id is None:
            return self._refuse("cancel", scope, "not_owned")
        with self._uow(write=True) as tx:
            existing = self._find_replay(tx, key)
            if existing is not None:
                self._outcome("cancel", "replayed", scope)
                replay = self._replay_result(tx, scope, existing)
                if isinstance(replay, WriteResult):
                    return replay
            cust = tx.core.reads.customer(customer_id)
            if cust is None:
                return self._refuse("cancel", scope, "not_owned")
            visit = self._owned_visit(tx, scope, appointment_id)
            if visit is None:
                return self._refuse("cancel", scope, "not_owned")
            slot = visit[1]
            h = hours_before(scope.now, slot.slot_date, slot.window)
            if fee_bearing(h):
                return self._refuse("cancel", scope, "fee_bearing", h)
            tx.booking.appointments.set_status(appointment_id, "cancelled")
            tx.booking.slots.set_status(slot.slot_id, "open")
            tech = self._technician(tx, slot.tech_id)
            action = CompletedAction(
                key=key,
                kind=ActionKind.CANCELLED,
                records={"appointment": str(appointment_id), "slot": str(slot.slot_id)},
                before=_visit_dict(slot, tech),
                after=None,
                at=scope.now,
            )
            stored = self._store(tx, action, lookup)
        self._outcome("cancel", "written", scope)
        return WriteResult(
            action=stored,
            confirmation=ConfirmationView(
                date=slot.slot_date,
                window=slot.window,
                technician=tech,
                fee_note=fee_note(slot.service_type, cust.membership_tier),
            ),
        )

    def request_change(
        self,
        key: ActionKey,
        scope: ToolCallScope,
        appointment_id: int,
        change: Literal["move", "cancel"],
        wanted_text: str,
        lookup: LookupEntry,
    ) -> ChangeRequestDraft | Refused:
        if scope.customer_id is None:
            return self._refuse("request_change", scope, "not_owned")
        with self._uow(write=True) as tx:
            existing = self._find_replay(tx, key)
            if existing is not None:
                self._outcome("request_change", "replayed", scope)
                replay = self._replay_result(tx, scope, existing)
                if isinstance(replay, ChangeRequestDraft):
                    return replay
            visit = self._owned_visit(tx, scope, appointment_id)
            if visit is None:
                return self._refuse("request_change", scope, "not_owned")
            slot = visit[1]
            h = hours_before(scope.now, slot.slot_date, slot.window)
            draft = ChangeRequestDraft(
                appointment_id=appointment_id,
                change=change,
                wanted_text=wanted_text,
                windows_shown=tuple(sorted(scope.shown_slot_ids)),
                hours_before=h,
                window_start=_window_start(slot.slot_date, slot.window),
            )
            action = CompletedAction(
                key=key,
                kind=ActionKind.CHANGE_REQUEST_SENT,
                records={"appointment": str(appointment_id), "slot": str(slot.slot_id)},
                before=_visit_dict(slot, self._technician(tx, slot.tech_id)),
                after={"change": change, "wanted_text": wanted_text, "fee_line": _change_fee_line(h)},
                at=scope.now,
            )
            self._store(tx, action, lookup)
        self._outcome("request_change", "written", scope)
        return draft
