"""Pure case rules and staff display values (A6): allowed actions, refusals, due state, queue order, oversight lanes,
labels, masking. No I/O and no clock read; every time is an argument.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, Literal, TypeAlias
from zoneinfo import ZoneInfo

from pydantic import JsonValue

from meridian.adapters.sqlite.repos_cases import CLOSED_LIFECYCLES
from meridian.domain.common import ApiErrorCode
from meridian.domain.handoff import HandoffReason, Priority, Promise
from meridian.domain.identity import IdentityState
from meridian.domain.staff import ROLE_ACTIONS, STAFF_PERSONAS, StaffRole
from meridian.domain.tools import LookupRow
from meridian.domain.views import (
    AllowedAction,
    CaseAction,
    CaseActionName,
    CaseActionRejected,
    DueState,
    StaffingView,
)
from meridian.policy.handoff import DUE_SOON_WINDOW, UNOWNED_AFTER, due_label
from meridian.policy.texts import TEXTS, TextId
from meridian.privacy.redact import RedactionProfile, redact

_CHICAGO: Final = ZoneInfo("America/Chicago")

LiveState: TypeAlias = Literal["not_live", "queued", "joined", "handed_back", "closed"]
LaneName: TypeAlias = Literal["p0_p1", "overdue", "due_soon", "unowned", "stuck_waiting"]

CON13_ACTIONS: Final[tuple[CaseActionName, ...]] = (
    "claim",
    "release",
    "start",
    "wait",
    "resolve",
    "close_unresolved",
    "assign",
    "change_priority",
)
"""The eight CON-13 case actions (the others are live chat, contact log and flags)."""

ACTION_ORDER: Final[tuple[AllowedAction, ...]] = (
    "claim",
    "claim_and_join",
    "join_chat",
    "send_live_message",
    "hand_back",
    "close_chat",
    "start",
    "log_call",
    "log_email",
    "wait",
    "resolve",
    "close_unresolved",
    "release",
    "assign",
    "change_priority",
    "flag",
)
"""The order in which allowed actions are listed (the signed examples' order)."""

CLOSED: Final[frozenset[str]] = frozenset(CLOSED_LIFECYCLES)
"""Lifecycles in which a case is closed."""

# Derived from the representative examples CLAIMED, WAITING and LIVE_JOINED (STF-18 marks the supervisor ones illustrative).
OWNER_LIFECYCLES: Final[Mapping[str, frozenset[str]]] = MappingProxyType(
    {
        "start": frozenset({"claimed", "waiting"}),
        "wait": frozenset({"claimed", "in_progress"}),
        "resolve": frozenset({"claimed", "in_progress"}),
        "close_unresolved": frozenset({"claimed", "in_progress"}),
        "release": frozenset({"claimed", "in_progress", "waiting"}),
        "log_call": frozenset({"claimed", "in_progress"}),
        "log_email": frozenset({"claimed", "in_progress"}),
    }
)

LANE_ORDER: Final[tuple[LaneName, ...]] = ("p0_p1", "overdue", "due_soon", "unowned", "stuck_waiting")
"""The five oversight lanes in their fixed order."""

# [Source: OpenAPI Priority.word]
PRIORITY_WORD: Final[
    Mapping[Priority, Literal["Safety", "Danger", "Time-sensitive", "Standard", "Routine"]]
] = MappingProxyType(
    {
        Priority.P0: "Safety",
        Priority.P1: "Danger",
        Priority.P2: "Time-sensitive",
        Priority.P3: "Standard",
        Priority.P4: "Routine",
    }
)

# [Source: OpenAPI examples where they exist; the rest decided in the AEA-29 plan, R-11]
REASON_LABEL: Final[Mapping[HandoffReason, str]] = MappingProxyType(
    {
        HandoffReason.SAFETY: "Safety report in chat",
        HandoffReason.DANGER: "Someone may be in danger",
        HandoffReason.BURNING_UNCLEAR: "Burning smell, risk unclear",
        HandoffReason.BURNING_RULED_OUT: "Burning smell, danger ruled out",
        HandoffReason.CUSTOMER_REQUESTED_PERSON: "Asked for a person",
        HandoffReason.REFUND: "Refund request",
        HandoffReason.BILLING_DISPUTE: "Billing dispute",
        HandoffReason.COMPLAINT_OR_MANAGER: "Complaint or manager request",
        HandoffReason.LEGAL_OR_CHARGEBACK: "Legal or chargeback request",
        HandoffReason.COMMERCIAL: "Commercial request",
        HandoffReason.LATE_TECHNICIAN: "Late technician",
        HandoffReason.FEE_BEARING_CHANGE: "Fee-bearing change request",
        HandoffReason.MEMBERSHIP_CANCEL: "Membership cancellation",
        HandoffReason.UNSUPPORTED_ACTION: "Request the assistant can't complete",
        HandoffReason.IDENTITY_UNVERIFIED: "Identity not confirmed",
        HandoffReason.AI_FAILURE: "Assistant couldn't finish",
    }
)

SAFETY_KIND_LABEL: Final[Mapping[str, str]] = MappingProxyType(
    {
        "gas": "Gas smell reported in chat",
        "co": "CO alarm reported in chat",
        "sparks_smoke_flames": "Sparks, smoke or flames reported in chat",
        "burning_with_breaker": "Burning smell with a tripped breaker reported in chat",
    }
)

LIFECYCLE_WORD: Final[Mapping[str, str]] = MappingProxyType(
    {
        "live_queued": "Live-queued",
        "unassigned": "Unassigned",
        "claimed": "Claimed",
        "in_progress": "In progress",
        "waiting": "Waiting",
        "resolved": "Resolved",
        "closed_unresolved": "Closed unresolved",
    }
)

WINDOW_WORD: Final[Mapping[str, str]] = MappingProxyType(
    {"morning": "mornings", "afternoon": "afternoons", "any": "any time"}
)


def state_allows(
    action: AllowedAction,
    *,
    lifecycle: str,
    owner_role: StaffRole | None,
    live_state: str,
    staffing: str,
    actor_role: StaffRole,
) -> bool:
    """Whether the case state allows the action for this actor: the one place that decides it."""
    mine = owner_role is not None and owner_role == actor_role
    if action == "claim":
        return lifecycle in {"live_queued", "unassigned"}
    if action == "claim_and_join":
        return lifecycle == "live_queued" and live_state == "queued" and staffing == "simulated_on_shift"
    if action == "join_chat":
        return mine and live_state == "queued"
    if action in ("send_live_message", "hand_back", "close_chat"):
        return mine and live_state == "joined"
    if action in OWNER_LIFECYCLES:
        return mine and lifecycle in OWNER_LIFECYCLES[action]
    if action in ("assign", "change_priority"):
        return lifecycle not in CLOSED
    if action == "flag":
        return True
    raise ValueError("unknown action")


def actions_for(
    *, lifecycle: str, owner_role: StaffRole | None, live_state: str, staffing: str, actor_role: StaffRole
) -> tuple[AllowedAction, ...]:
    """The allowed actions: the role's table intersected with the state's, in table order."""
    return tuple(
        a
        for a in ACTION_ORDER
        if a in ROLE_ACTIONS[actor_role]
        and state_allows(
            a,
            lifecycle=lifecycle,
            owner_role=owner_role,
            live_state=live_state,
            staffing=staffing,
            actor_role=actor_role,
        )
    )


def staff_name(actor_role: str) -> str:
    """The persona name of a staff role; "System" for the assistant and the system."""
    if actor_role in ("ai", "system"):
        return "System"
    return STAFF_PERSONAS[StaffRole(actor_role)].name


def _claimed_refusal(owner_role: StaffRole | None, owner_since: dt.datetime | None) -> CaseActionRejected:
    return CaseActionRejected(
        code=ApiErrorCode.CASE_ALREADY_CLAIMED,
        details={
            "claimed_by": staff_name(owner_role.value) if owner_role else "System",
            "claimed_at": owner_since.isoformat() if owner_since else None,
        },
    )


def con13_refusal(
    action: CaseActionName,
    *,
    lifecycle: str,
    owner_role: StaffRole | None,
    owner_since: dt.datetime | None,
    actor_role: StaffRole,
) -> CaseActionRejected | None:
    """The first CON-13 rule that refuses the action, or None when the state accepts it."""
    if action not in ROLE_ACTIONS[actor_role]:
        needs = [
            r.value for r in (StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR) if action in ROLE_ACTIONS[r]
        ]
        return CaseActionRejected(
            code=ApiErrorCode.ROLE_NOT_ALLOWED,
            details={"role": actor_role.value, "needs": list(needs), "reason": "wrong_role"},
        )
    if lifecycle in CLOSED:
        return CaseActionRejected(
            code=ApiErrorCode.NOT_ALLOWED_IN_STATE, details={"state": lifecycle, "needs": "open"}
        )
    if action == "claim":
        if lifecycle in {"claimed", "in_progress", "waiting"}:
            return _claimed_refusal(owner_role, owner_since)
        return None
    if action in {"assign", "change_priority"}:
        return None
    if owner_role is None:
        return CaseActionRejected(
            code=ApiErrorCode.NOT_ALLOWED_IN_STATE, details={"state": lifecycle, "needs": "claimed"}
        )
    if owner_role != actor_role:
        return _claimed_refusal(owner_role, owner_since)
    if lifecycle not in OWNER_LIFECYCLES[action]:
        return CaseActionRejected(
            code=ApiErrorCode.NOT_ALLOWED_IN_STATE,
            details={"state": lifecycle, "needs": " or ".join(sorted(OWNER_LIFECYCLES[action]))},
        )
    return None


def _blank(value: str | None) -> bool:
    return value is None or not value.strip()


def missing_field_refusal(action: CaseAction, now: dt.datetime) -> CaseActionRejected | None:
    """The refusal for a missing or invalid field of the action; `details` never echoes a value."""
    name = action.action
    if name in {"release", "close_unresolved", "assign", "change_priority"} and _blank(action.reason):
        return CaseActionRejected(
            code=ApiErrorCode.REASON_REQUIRED, field="reason", constraint=f"required for {name}"
        )
    if name == "wait":
        if action.wake_up_at is None:
            return CaseActionRejected(
                code=ApiErrorCode.WAKE_UP_REQUIRED, field="wake_up_at", constraint="required for wait"
            )
        if action.wake_up_at <= now:
            return CaseActionRejected(
                code=ApiErrorCode.VALIDATION_ERROR,
                field="wake_up_at",
                constraint="must be after the demo time",
            )
    if name == "resolve" and _blank(action.outcome):
        return CaseActionRejected(
            code=ApiErrorCode.OUTCOME_REQUIRED, field="outcome", constraint="required for resolve"
        )
    if name == "assign" and action.assignee is None:
        return CaseActionRejected(
            code=ApiErrorCode.VALIDATION_ERROR, field="assignee", constraint="required for assign"
        )
    if name == "change_priority" and action.priority is None:
        return CaseActionRejected(
            code=ApiErrorCode.VALIDATION_ERROR, field="priority", constraint="required for change_priority"
        )
    return None


def due_state(case_due: dt.datetime | None, now: dt.datetime) -> DueState:
    """Overdue is a state, never a negative countdown."""
    if case_due is None:
        return "no_due_time"
    if case_due < now:
        return "overdue"
    if case_due - now <= DUE_SOON_WINDOW:
        return "due_soon"
    return "on_time"


def queue_key(
    priority: Priority, state: DueState, case_due: dt.datetime | None, created_at: dt.datetime, case_ref: str
) -> tuple[int, int, int, float, float, str]:
    """Sort key: P0, then P1, then overdue, then due ascending, then created; no-due rows after dated ones."""
    tier = 0 if priority is Priority.P0 else 1 if priority is Priority.P1 else 2
    return (
        tier,
        0 if state == "overdue" else 1,
        1 if case_due is None else 0,
        0.0 if case_due is None else case_due.timestamp(),
        created_at.timestamp(),
        case_ref,
    )


def lane_for(
    priority: Priority,
    state: DueState,
    lifecycle: str,
    created_at: dt.datetime,
    wake_up_at: dt.datetime | None,
    now: dt.datetime,
) -> LaneName | None:
    """The first oversight lane the case qualifies for, or None."""
    if priority in (Priority.P0, Priority.P1):
        return "p0_p1"
    if state == "overdue":
        return "overdue"
    if state == "due_soon":
        return "due_soon"
    if lifecycle == "unassigned" and now - created_at >= UNOWNED_AFTER:
        return "unowned"
    if lifecycle == "waiting" and wake_up_at is not None and wake_up_at < now:
        return "stuck_waiting"
    return None


def reason_label(reason: HandoffReason, safety_kind: str | None = None) -> str:
    """The staff wording for a reason; never the enum value."""
    if reason is HandoffReason.SAFETY and safety_kind is not None and safety_kind in SAFETY_KIND_LABEL:
        return SAFETY_KIND_LABEL[safety_kind]
    return REASON_LABEL[reason]


def follow_up_short(channel: str | None, window: str | None) -> str | None:
    """The short follow-up label on a queue row."""
    if channel is None:
        return None
    if channel == "phone":
        return f"Phone · {WINDOW_WORD[window or 'any']}"
    if window in (None, "any"):
        return "Email"
    return f"Email · {WINDOW_WORD[window]}"


def clock_text(at: dt.datetime) -> str:
    """12-hour Chicago clock text, e.g. "2:14 pm"."""
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("at must be timezone-aware")
    local = at.astimezone(_CHICAGO)
    hour = local.hour % 12 or 12
    return f"{hour}:{local.minute:02d} {'am' if local.hour < 12 else 'pm'}"


def age_label(created_at: dt.datetime, now: dt.datetime, *, queued_at: dt.datetime | None = None) -> str:
    """How long the case has been open (or waiting, for a live-queued case)."""
    if queued_at is not None:
        return f"Waiting since {clock_text(queued_at)}"
    minutes = max(0, int((now - created_at).total_seconds() // 60))
    if minutes < 60:
        return f"Open {minutes} min"
    if minutes < 1440:
        hours, rest = divmod(minutes, 60)
        return f"Open {hours} h" if rest == 0 else f"Open {hours} h {rest} min"
    days, rest_minutes = divmod(minutes, 1440)
    hours = rest_minutes // 60
    unit = "day" if days == 1 else "days"
    return f"Open {days} {unit}" if hours == 0 else f"Open {days} {unit} {hours} h"


def case_due_label(case_due: dt.datetime | None, *, is_window_start: bool) -> str | None:
    """The due label of the case; a fee-bearing case's due is the window start and says so."""
    if case_due is None:
        return None
    label = due_label(case_due)
    return f"{label}, the window start" if is_window_start else label


_IDENTITY_LINES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "verified": "The customer entered the code sent to the phone on file. (Demo simulation. Not real ID proof.)",
        "code_sent": "A code was sent to the phone on file. The customer has not entered it yet. (Demo simulation.)",
        "not_checked": "The customer has not confirmed who they are in this chat.",
        "not_verified": "The customer could not be confirmed in this chat.",
        "locked": "Code entry is locked after too many tries. (Demo simulation.)",
    }
)


def identity_view(identity: IdentityState, *, case_customer: bool) -> tuple[str, str, str]:
    """(status, line, demo_note) for the case view; a case opened by a verified customer reads verified."""
    if identity.status == "verified" or case_customer:
        status = "verified"
    elif identity.status == "located":
        status = "code_sent" if identity.codes_sent > 0 else "not_checked"
    else:
        status = identity.status
    return status, _IDENTITY_LINES[status], "Demo simulation"


def promise_status_after_resolve(
    promise_due: dt.datetime | None, now: dt.datetime
) -> Literal["kept", "missed"]:
    """A resolved case keeps its promise when it is resolved by the due time."""
    return "kept" if promise_due is None or now <= promise_due else "missed"


def promise_status_after_activity(
    outcome: str, promise_due: dt.datetime | None, now: dt.datetime, current: str
) -> str:
    """A reached customer or a left message on time keeps the promise; otherwise it stays as it is."""
    if current not in {"open", "changed"}:
        return current
    if outcome in {"reached", "left_message"} and (promise_due is None or now <= promise_due):
        return "kept"
    return current


def fill_promise_text(promise: Promise, case_ref: str) -> str:
    """The promise words as the customer saw them: the table text with its placeholders filled."""
    if "{" not in promise.text:
        return promise.text
    return promise.text.format(due_label=promise.due_label or "", case_ref=case_ref)


def mask(text: str) -> str:
    """Removes contact values (cards, emails, phones, addresses, codes) from staff-facing text."""
    return redact(text, RedactionProfile.SONNET).text


def _cents(text: str) -> int:
    """`"$1,234.56"` -> 123456; `"-$5.00"` -> -500."""
    value = int(re.sub(r"[-$,.]", "", text))
    return -value if text.startswith("-") else value


def parse_seen(result_seen: str, record_id: str | None = None) -> dict[str, JsonValue]:
    """Reads a lookup row's `result_seen`; the first form that matches wins.

    Forms: JSON, AEA-27's invoice / membership / warranty sentences, `key=value` text, and bare text. A form nobody
    parses gives `{"seen": text}`, a key no current record has, so it never reads as a change.
    """
    s = result_seen.strip()
    if s.startswith("{"):
        try:
            loaded = json.loads(s)
        except ValueError:
            loaded = None
        if isinstance(loaded, dict):
            return loaded
    if record_id is not None and re.fullmatch(r"INV-[0-9]{6}", record_id):
        m = re.search(
            re.escape(record_id) + r" total (-?\$[0-9,]+\.[0-9]{2}) balance (-?\$[0-9,]+\.[0-9]{2})", s
        )
        if m:
            return {"amount_cents": _cents(m[1]), "balance_cents": _cents(m[2])}
    m = re.fullmatch(r"membership tier (\S+) renewal (\S+)", s)
    if m:
        return {"membership_tier": m[1], "membership_renewal_date": None if m[2] == "none" else m[2]}
    m = re.fullmatch(r"warranty install (\S+)(?: brand (.+))?", s)
    if m:
        out: dict[str, JsonValue] = {"system_install_date": None if m[1] == "none" else m[1]}
        if m[2] is not None:
            out["system_brand"] = None if m[2] == "none" else m[2]
        return out
    pairs = re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([^\s;,]+)", s)
    if pairs:
        return {k: int(v) if re.fullmatch(r"-?[0-9]+", v) else v for k, v in pairs}
    return {"seen": s}


def staffing_view(mode: str) -> StaffingView:
    """The staffing label and banner shown on the staff views."""
    if mode == "simulated_on_shift":
        return StaffingView(
            mode="simulated_on_shift",
            label="Simulated staff on shift (demo)",
            banner=TEXTS[TextId.STAFFING_BANNER],
        )
    return StaffingView(mode="nobody_online", label="Nobody online", banner=None)


RecordKind: TypeAlias = Literal["invoice", "customer", "appointment", "slot"]


def record_kind(record_id: str) -> tuple[RecordKind, str] | None:
    """What a `lookup_log.record_ids` entry names, and its bare id; None for anything else."""
    if re.fullmatch(r"INV-[0-9]{6}", record_id):
        return "invoice", record_id
    if re.fullmatch(r"MHC-[0-9]{5}", record_id):
        return "customer", record_id
    m = re.fullmatch(r"(?:appointment:)?([0-9]+)", record_id)
    if m:
        return "appointment", m[1]
    m = re.fullmatch(r"slot:([0-9]+)", record_id)
    if m:
        return "slot", m[1]
    return None


def row_title(row: LookupRow) -> str:
    """A short staff title for what a lookup row looked at; the brief and the source chips share it."""
    kind = record_kind(row.record_ids[0]) if row.record_ids else None
    if kind is not None:
        what, ident = kind
        if what == "invoice":
            return f"Invoice {ident}"
        if what == "customer":
            return (
                "Warranty record" if row.tool == "read_warranty" else "Membership record"
            )  # agent/tools/account.py
        if what == "appointment":
            return f"Appointment {ident}"
        return (
            "Open visit windows" if row.tool == "find_windows" else f"Visit window {ident}"
        )  # agent/tools/scheduling.py
    if row.passage_ids:
        return str(row.passage_ids[0]).split("#")[0]
    return row.tool
