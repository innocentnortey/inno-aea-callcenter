"""What the conversation has done: actions, open case and the Settled view (AEA-02; DO-4 section 1, graph-core 14).

`Settled` is built only from the stored `actions` rows plus the case row, so the responder and the "What's settled"
panel read the same object (N-27). Pure: no I/O.
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum
from typing import Literal

from meridian.domain.common import (
    CaseRef,
    CaseState,
    FollowUp,
    HandoffReason,
    MeridianModel,
    Priority,
    Promise,
    ThreadId,
    TurnId,
)
from meridian.domain.records import ServiceType, Window


class ActionKind(StrEnum):
    """DO-4 section 1, 7 values."""

    BOOKED = "booked"
    MOVED = "moved"
    CANCELLED = "cancelled"
    CHANGE_REQUEST_SENT = "change_request_sent"
    CASE_OPENED = "case_opened"
    FOLLOWUP_SAVED = "followup_saved"
    VERIFIED = "verified"


class ActionKey(MeridianModel):
    thread_id: ThreadId
    turn_id: TurnId
    kind: ActionKind
    record_id: str


class CompletedAction(MeridianModel):
    key: ActionKey
    kind: ActionKind
    records: dict[Literal["appointment", "slot", "old_slot", "case", "customer", "promise"], str]
    before: dict[str, str] | None = None
    after: dict[str, str] | None = None
    at: dt.datetime
    source: Literal["actions_table"] = "actions_table"


class OpenCase(MeridianModel):
    case_ref: CaseRef
    reason: HandoffReason
    priority: Priority
    state: CaseState
    promise: Promise
    followup: FollowUp | None
    live_queued: bool


class VisitChange(MeridianModel):
    """graph-core section 14 = OpenAPI SettledVisit.change_request."""

    change: Literal["move", "cancel"]
    wanted_text: str
    fee_line: str


class VisitView(MeridianModel):
    """graph-core section 14 = OpenAPI SettledVisit minus window_label."""

    appointment_id: int
    date: dt.date
    window: Window
    technician: str
    service_type: ServiceType
    fee_line: str
    status: Literal["booked", "moved", "original_stays"]
    change_request: VisitChange | None


class Settled(MeridianModel):
    """Everything the conversation has done. Built ONLY from actions + cases/promises rows."""

    actions: tuple[CompletedAction, ...]
    open_case: OpenCase | None
    read_at: dt.datetime

    def has(self, kind: ActionKind, record_id: str | None = None) -> bool:
        """True when a stored action of this kind (and record, when given) exists (R-46)."""
        return any(
            a.kind == kind and (record_id is None or a.key.record_id == record_id) for a in self.actions
        )

    def current_visit(self) -> VisitView | None:
        """The newest booked or moved visit with no later cancellation (graph-core section 14)."""
        # "Later" means a greater (at, position): ties in `at` keep stored order.
        ordered = sorted(enumerate(self.actions), key=lambda pair: (pair[1].at, pair[0]))
        for index, (_, action) in enumerate(reversed(ordered)):
            if (
                action.kind not in (ActionKind.BOOKED, ActionKind.MOVED)
                or "appointment" not in action.records
            ):
                continue
            appointment = action.records["appointment"]
            later = [later_action for _, later_action in ordered[len(ordered) - index :]]
            if any(
                a.kind == ActionKind.CANCELLED and a.records.get("appointment") == appointment for a in later
            ):
                continue
            requests = [
                a
                for a in later
                if a.kind == ActionKind.CHANGE_REQUEST_SENT and a.records.get("appointment") == appointment
            ]
            after = action.after or {}
            data: dict[str, object] = {
                "appointment_id": int(appointment),
                "date": after.get("date"),
                "window": after.get("window"),
                "technician": after.get("technician"),
                "service_type": after.get("service_type"),
                "fee_line": after.get("fee_line"),
            }
            if requests:
                asked = requests[-1].after or {}
                data["status"] = "original_stays"
                data["change_request"] = {
                    "change": asked.get("change"),
                    "wanted_text": asked.get("wanted_text"),
                    "fee_line": asked.get("fee_line"),
                }
            else:
                data["status"] = action.kind.value
                data["change_request"] = None
            return VisitView.model_validate(data)
        return None

    def only_turn(self, turn_id: TurnId) -> Settled:
        """The same view limited to one turn's actions (R-46's literal "this turn" reading)."""
        kept = tuple(a for a in self.actions if a.key.turn_id == turn_id)
        case = self.open_case
        if case is not None and not any(
            a.kind == ActionKind.CASE_OPENED and a.key.record_id == case.case_ref for a in kept
        ):
            case = None
        return Settled(actions=kept, open_case=case, read_at=self.read_at)
