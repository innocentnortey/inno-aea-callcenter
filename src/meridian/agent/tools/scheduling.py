"""Scheduling executors (graph-tools.md sections 1-3, C-7): scheduling_tools() binds five tools to one
SchedulingService; nothing registers itself. Model-facing results carry ids, dates, windows, technician names and fee
lines only (audit D-11)."""

from __future__ import annotations

from datetime import date
from typing import Final, Literal

from pydantic import Field, JsonValue

from meridian.domain.actions import ActionKey, ActionKind
from meridian.domain.common import LLMFacing, ToolErrorCode, ToolKind
from meridian.domain.records import MembershipTier, ServiceType, Window
from meridian.domain.specialists import SchedulingCapture
from meridian.domain.tools import LookupEntry, ToolCallScope, ToolDef, ToolError, ToolResult
from meridian.policy.booking import fee_bearing, fee_note, hours_before
from meridian.services.scheduling import (
    OutOfArea,
    Refused,
    SchedulingService,
    SlotTaken,
    WindowQuery,
)

FIND_WINDOWS_NAME: Final = "find_windows"
BOOK_VISIT_NAME: Final = "book_visit"
MOVE_VISIT_NAME: Final = "move_visit"
CANCEL_VISIT_NAME: Final = "cancel_visit"
REQUEST_VISIT_CHANGE_NAME: Final = "request_visit_change"

_FIND_DESCRIPTION: Final = (
    "Search open visit windows for one service type. Returns up to 3 windows (slot_id, date, window, technician), "
    "whether the requested day or time fits, and the fee line for this customer. Windows are shown, not held. "
    "Use before book_visit or move_visit. Before the customer is verified, pass the city or ZIP they gave; after "
    "verification the address on file is used. Do not use to look up the customer's existing visits: they are in "
    "your task slice."
)
_BOOK_DESCRIPTION: Final = (
    "Book one window the customer picked from the windows shown in this conversation (slot_id from find_windows). "
    "Returns the confirmation: date, window, technician and fee line. Needs a verified customer. Do not use to "
    "change an existing visit: use move_visit."
)
_MOVE_DESCRIPTION: Final = (
    "Move the customer's existing visit (appointment_id from your task slice) to a window shown by find_windows, "
    "only when the visit is more than 24 hours away. Returns the new confirmation. If it returns fee_bearing, do "
    "not retry: use request_visit_change. Do not use for a new booking: use book_visit."
)
_CANCEL_DESCRIPTION: Final = (
    "Cancel the customer's existing visit (appointment_id from your task slice) when it is more than 24 hours away. "
    "Returns the cancelled visit. If it returns fee_bearing, do not retry: use request_visit_change with change "
    "'cancel'."
)
_CHANGE_DESCRIPTION: Final = (
    "Record a staff change request for a visit inside 24 hours of its window, after move_visit or cancel_visit "
    "returned fee_bearing. Records the wanted time and the windows shown (not held); the visit stays as booked "
    "until a representative confirms. Do not use when the visit is more than 24 hours away: use move_visit or "
    "cancel_visit."
)


class FindWindowsArgs(LLMFacing):
    service_type: ServiceType = Field(description="hvac_repair, hvac_tune_up, plumbing or estimate")
    zone_hint: str | None = Field(
        default=None,
        max_length=64,
        description="City or 5-digit ZIP the customer gave; ignored once verified",
    )
    earliest: date | None = Field(default=None, description="First day the customer can do, if they said one")
    latest: date | None = Field(default=None, description="Last day the customer can do, if they said one")
    window: Window | None = Field(default=None, description="The window the customer asked for, if any")
    wanted_text: str = Field(default="", max_length=200, description="The customer's words about when")


class BookVisitArgs(LLMFacing):
    slot_id: int = Field(ge=1, description="slot_id of a window returned by find_windows")
    issue: str = Field(
        min_length=1, max_length=300, description="What the customer needs fixed, in their words"
    )


class MoveVisitArgs(LLMFacing):
    appointment_id: int = Field(ge=1, description="appointment_id of the visit from your task slice")
    new_slot_id: int = Field(ge=1, description="slot_id of a window returned by find_windows")


class CancelVisitArgs(LLMFacing):
    appointment_id: int = Field(ge=1, description="appointment_id of the visit from your task slice")


class RequestVisitChangeArgs(LLMFacing):
    appointment_id: int = Field(ge=1, description="appointment_id of the visit from your task slice")
    change: Literal["move", "cancel"] = Field(description="move or cancel")
    wanted_text: str = Field(
        default="", max_length=200, description="When the customer would like the visit instead"
    )


def _entry(scope: ToolCallScope, tool: str, record_ids: tuple[str, ...], result_seen: str) -> LookupEntry:
    return LookupEntry(
        tool=tool,
        record_ids=record_ids,
        passage_ids=(),
        result_seen=result_seen,
        message_id=scope.message_id,
        turn_id=scope.ids.turn_id,
    )


def tool_error_for(outcome: Refused | SlotTaken | OutOfArea) -> ToolError:
    if isinstance(outcome, OutOfArea):
        if outcome.reason == "not_served":
            return ToolError(
                code=ToolErrorCode.OUTSIDE_SERVICE_AREA,
                message="That place is outside Meridian's service area, so no visit can be booked there.",
                retryable=False,
            )
        return ToolError(
            code=ToolErrorCode.OUTSIDE_SERVICE_AREA,
            message="That place was not recognised. Ask for the city or a 5-digit ZIP.",
            retryable=True,
        )
    if isinstance(outcome, SlotTaken):
        if outcome.alternatives:
            listed = "; ".join(
                f"slot {s.slot_id}: {s.date.isoformat()} {s.window}, {s.technician}"
                for s in outcome.alternatives
            )
            message = "That window was just taken. Offer these fresh windows instead (not held): " + listed
        else:
            message = "That window was just taken and no other window is open."
        return ToolError(code=ToolErrorCode.SLOT_TAKEN, message=message, retryable=True)
    code = ToolErrorCode(outcome.code)
    if outcome.code == "fee_bearing":
        hours = outcome.hours_before if outcome.hours_before is not None else 0.0
        return ToolError(
            code=code,
            message=(
                f"This visit is {hours:.1f} hours before its window, inside 24 hours, so the late-change fee "
                "applies. Do not move or cancel it: use request_visit_change."
            ),
            retryable=False,
        )
    messages = {
        "not_shown": (
            "That window was not shown in this conversation. Search with find_windows and offer the windows it "
            "returns.",
            True,
        ),
        "outside_service_area": (
            "That window is outside the customer's service zone. Offer windows from find_windows.",
            False,
        ),
        "wrong_service_type": (
            "That window is for a different service than the visit being moved. Offer windows of the same service.",
            False,
        ),
        "booking_cap": ("No more bookings can be made in this conversation.", False),
        "not_owned": ("That visit is not on the verified customer's account.", False),
    }
    text, retry = messages[outcome.code]
    return ToolError(code=code, message=text, retryable=retry)


def _refusal(scope: ToolCallScope, tool: str, code: ToolErrorCode, error: ToolError) -> ToolResult:
    return ToolResult(
        ok=False,
        for_model=error,
        captured=SchedulingCapture(refused=code),
        lookup=_entry(scope, tool, (), f"refused:{code.value}"),
        lookup_written=False,
    )


def _outcome_result(scope: ToolCallScope, tool: str, outcome: Refused | SlotTaken) -> ToolResult:
    if isinstance(outcome, SlotTaken):
        ids = tuple(f"slot:{s.slot_id}" for s in outcome.alternatives)
        return ToolResult(
            ok=False,
            for_model=tool_error_for(outcome),
            captured=SchedulingCapture(windows=outcome.alternatives, refused=ToolErrorCode.SLOT_TAKEN),
            lookup=_entry(
                scope,
                tool,
                ids,
                f"slot_taken:slot:{outcome.slot_id} alternatives:{','.join(i.removeprefix('slot:') for i in ids)}",
            ),
            lookup_written=False,
        )
    return _refusal(scope, tool, ToolErrorCode(outcome.code), tool_error_for(outcome))


def scheduling_tools(scheduling: SchedulingService) -> tuple[ToolDef, ...]:
    def _find(args: LLMFacing, scope: ToolCallScope) -> ToolResult:
        if not isinstance(args, FindWindowsArgs):
            raise TypeError("find_windows expects FindWindowsArgs")
        tier: MembershipTier = "none"
        if scope.customer_id is not None:
            terms = scheduling.customer_terms(scope.customer_id)
            if terms is None:
                return _refusal(
                    scope,
                    FIND_WINDOWS_NAME,
                    ToolErrorCode.NOT_VERIFIED,
                    ToolError(
                        code=ToolErrorCode.NOT_VERIFIED,
                        message="The verified customer's record was not found; ask them to confirm their details again.",
                        retryable=False,
                    ),
                )
            hint, tier = terms.location, terms.tier
        else:
            hint = (args.zone_hint or "").strip()
            if not hint:
                return _refusal(
                    scope,
                    FIND_WINDOWS_NAME,
                    ToolErrorCode.BAD_ARGUMENTS,
                    ToolError(
                        code=ToolErrorCode.BAD_ARGUMENTS,
                        message="Before the customer is verified, a city or 5-digit ZIP is needed to search windows.",
                        retryable=True,
                    ),
                )
        query = WindowQuery(
            zone_hint=hint,
            service_type=args.service_type,
            member_tier=tier,
            wanted_text=args.wanted_text,
            earliest=args.earliest,
            latest=args.latest,
            window=args.window,
        )
        found = scheduling.find_windows(query, scope.now, shown_turn=scope.ids.turn_id)
        if isinstance(found, OutOfArea):
            return ToolResult(
                ok=False,
                for_model=tool_error_for(found),
                captured=SchedulingCapture(refused=ToolErrorCode.OUTSIDE_SERVICE_AREA),
                lookup=_entry(scope, FIND_WINDOWS_NAME, (), f"out_of_area:{found.reason}"),
                lookup_written=False,
            )
        windows: list[JsonValue] = [
            {
                "slot_id": w.slot_id,
                "date": w.date.isoformat(),
                "window": w.window,
                "technician": w.technician,
                "service_type": w.service_type,
                "member_reserved": w.member_reserved,
            }
            for w in found.windows
        ]
        for_model: JsonValue = {
            "zone": found.zone,
            "exact_fit": found.exact_fit,
            "held": False,
            "windows": windows,
            "fee_line": fee_note(args.service_type, tier).line,
        }
        ids = ",".join(str(w.slot_id) for w in found.windows)
        return ToolResult(
            ok=True,
            for_model=for_model,
            captured=SchedulingCapture(windows=found.windows),
            lookup=_entry(
                scope,
                FIND_WINDOWS_NAME,
                tuple(f"slot:{w.slot_id}" for w in found.windows),
                f"windows zone:{found.zone} exact_fit:{str(found.exact_fit).lower()} slots:{ids}",
            ),
            lookup_written=False,
        )

    def _key(scope: ToolCallScope, kind: ActionKind, record_id: int) -> ActionKey:
        return ActionKey(
            thread_id=scope.ids.thread_id, turn_id=scope.ids.turn_id, kind=kind, record_id=str(record_id)
        )

    def _book(args: LLMFacing, scope: ToolCallScope) -> ToolResult:
        if not isinstance(args, BookVisitArgs):
            raise TypeError("book_visit expects BookVisitArgs")
        ok_entry = _entry(scope, BOOK_VISIT_NAME, (f"slot:{args.slot_id}",), f"booked slot:{args.slot_id}")
        outcome = scheduling.book(
            _key(scope, ActionKind.BOOKED, args.slot_id), scope, args.slot_id, args.issue, ok_entry
        )
        if isinstance(outcome, (Refused, SlotTaken)):
            return _outcome_result(scope, BOOK_VISIT_NAME, outcome)
        r = outcome
        return ToolResult(
            ok=True,
            for_model={
                "booked": True,
                "appointment_id": int(r.action.records["appointment"]),
                "date": r.confirmation.date.isoformat(),
                "window": r.confirmation.window,
                "technician": r.confirmation.technician,
                "fee_line": r.confirmation.fee_note.line,
            },
            captured=SchedulingCapture(write=r),
            lookup=ok_entry,
            lookup_written=True,
        )

    def _move(args: LLMFacing, scope: ToolCallScope) -> ToolResult:
        if not isinstance(args, MoveVisitArgs):
            raise TypeError("move_visit expects MoveVisitArgs")
        ok_entry = _entry(
            scope,
            MOVE_VISIT_NAME,
            (f"appointment:{args.appointment_id}", f"slot:{args.new_slot_id}"),
            f"moved appointment:{args.appointment_id} to slot:{args.new_slot_id}",
        )
        outcome = scheduling.move(
            _key(scope, ActionKind.MOVED, args.appointment_id),
            scope,
            args.appointment_id,
            args.new_slot_id,
            ok_entry,
        )
        if isinstance(outcome, (Refused, SlotTaken)):
            return _outcome_result(scope, MOVE_VISIT_NAME, outcome)
        r = outcome
        return ToolResult(
            ok=True,
            for_model={
                "moved": True,
                "appointment_id": int(r.action.records["appointment"]),
                "date": r.confirmation.date.isoformat(),
                "window": r.confirmation.window,
                "technician": r.confirmation.technician,
                "fee_line": r.confirmation.fee_note.line,
            },
            captured=SchedulingCapture(write=r),
            lookup=ok_entry,
            lookup_written=True,
        )

    def _cancel(args: LLMFacing, scope: ToolCallScope) -> ToolResult:
        if not isinstance(args, CancelVisitArgs):
            raise TypeError("cancel_visit expects CancelVisitArgs")
        ok_entry = _entry(
            scope,
            CANCEL_VISIT_NAME,
            (f"appointment:{args.appointment_id}",),
            f"cancelled appointment:{args.appointment_id}",
        )
        outcome = scheduling.cancel(
            _key(scope, ActionKind.CANCELLED, args.appointment_id), scope, args.appointment_id, ok_entry
        )
        if isinstance(outcome, Refused):
            return _outcome_result(scope, CANCEL_VISIT_NAME, outcome)
        r = outcome
        return ToolResult(
            ok=True,
            for_model={
                "cancelled": True,
                "appointment_id": int(r.action.records["appointment"]),
                "date": r.confirmation.date.isoformat(),
                "window": r.confirmation.window,
                "technician": r.confirmation.technician,
            },
            captured=SchedulingCapture(write=r),
            lookup=ok_entry,
            lookup_written=True,
        )

    def _change(args: LLMFacing, scope: ToolCallScope) -> ToolResult:
        if not isinstance(args, RequestVisitChangeArgs):
            raise TypeError("request_visit_change expects RequestVisitChangeArgs")
        if scope.customer_id is not None:
            views = scheduling.slice_inputs(scope.customer_id).appointments
            v = next((x for x in views if x.appointment_id == args.appointment_id), None)
            if v is not None and not fee_bearing(hours_before(scope.now, v.date, v.window)):
                return _refusal(
                    scope,
                    REQUEST_VISIT_CHANGE_NAME,
                    ToolErrorCode.NOT_ALLOWED,
                    ToolError(
                        code=ToolErrorCode.NOT_ALLOWED,
                        message=(
                            "This visit is more than 24 hours away, so no staff request is needed: use move_visit "
                            "or cancel_visit."
                        ),
                        retryable=False,
                    ),
                )
        ok_entry = _entry(
            scope,
            REQUEST_VISIT_CHANGE_NAME,
            (f"appointment:{args.appointment_id}",),
            f"change_request_sent appointment:{args.appointment_id} change:{args.change}",
        )
        outcome = scheduling.request_change(
            _key(scope, ActionKind.CHANGE_REQUEST_SENT, args.appointment_id),
            scope,
            args.appointment_id,
            args.change,
            args.wanted_text,
            ok_entry,
        )
        if isinstance(outcome, Refused):
            return _outcome_result(scope, REQUEST_VISIT_CHANGE_NAME, outcome)
        d = outcome
        return ToolResult(
            ok=True,
            for_model={
                "change_request_recorded": True,
                "appointment_id": d.appointment_id,
                "change": d.change,
                "hours_before": round(d.hours_before, 1),
                "windows_shown": list(d.windows_shown),
                "appointment_unchanged": True,
            },
            captured=SchedulingCapture(change_request=d),
            lookup=ok_entry,
            lookup_written=True,
        )

    return (
        ToolDef(
            name=FIND_WINDOWS_NAME,
            description=_FIND_DESCRIPTION,
            args_model=FindWindowsArgs,
            kind=ToolKind.SLOT_SEARCH,
            effect="read",
            requires_verified=False,
            executor=_find,
        ),
        ToolDef(
            name=BOOK_VISIT_NAME,
            description=_BOOK_DESCRIPTION,
            args_model=BookVisitArgs,
            kind=ToolKind.BOOK,
            effect="write",
            requires_verified=True,
            executor=_book,
        ),
        ToolDef(
            name=MOVE_VISIT_NAME,
            description=_MOVE_DESCRIPTION,
            args_model=MoveVisitArgs,
            kind=ToolKind.MOVE,
            effect="write",
            requires_verified=True,
            executor=_move,
        ),
        ToolDef(
            name=CANCEL_VISIT_NAME,
            description=_CANCEL_DESCRIPTION,
            args_model=CancelVisitArgs,
            kind=ToolKind.CANCEL,
            effect="write",
            requires_verified=True,
            executor=_cancel,
        ),
        ToolDef(
            name=REQUEST_VISIT_CHANGE_NAME,
            description=_CHANGE_DESCRIPTION,
            args_model=RequestVisitChangeArgs,
            kind=ToolKind.CHANGE_REQUEST,
            effect="write",
            requires_verified=True,
            executor=_change,
        ),
    )
