"""Base model, validated ID types, stable error codes and the types the other domain modules build on (AEA-02).

DO-4 section 0 and section 11, with the Stage 7 addenda. Pure: standard library and pydantic only. Several types
are defined here and re-exported from their ticket home (plan section 4.0) so the modules form no import cycle.
"""

from __future__ import annotations

import datetime as dt
from enum import StrEnum
from typing import Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler, ValidationError
from pydantic_core import core_schema


class MeridianModel(BaseModel):
    """Base for every typed hand-off (DO-4 section 0). Errors never carry the input."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, hide_input_in_errors=True, str_strip_whitespace=True
    )


class LLMFacing(MeridianModel):
    """Schemas a model fills; extra="forbid" makes an invented field a loud failure.

    Pipeline-assigned fields (ids, times, turn_id) never appear here.
    """


class _PatternId(str):
    """A str subclass validated by one regex (DO-4 section 0). Error code: string_pattern_mismatch."""

    PATTERN: ClassVar[str] = ""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(pattern=cls.PATTERN, strict=True),
            serialization=core_schema.to_string_ser_schema(),
        )


_UUID4_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"


class ThreadId(_PatternId):
    """Minted by SessionService.open (CON-1)."""

    PATTERN = _UUID4_PATTERN


class TurnId(_PatternId):
    """Minted by the browser per CON-2 send."""

    PATTERN = _UUID4_PATTERN


class RequestId(_PatternId):
    """Minted by middleware."""

    PATTERN = _UUID4_PATTERN


class CustomerId(_PatternId):
    PATTERN = r"^MHC-[0-9]{5}$"


class InvoiceId(_PatternId):
    PATTERN = r"^INV-[0-9]{6}$"


class CaseRef(_PatternId):
    PATTERN = r"^MHC-C-[0-9]{4}$"


class PassageId(_PatternId):
    """`<file path>#<chunk n>`."""

    PATTERN = r"^[^#\s]+#[0-9]+$"


EventId = Annotated[int, Field(ge=0)]  # monotonically increasing per stream; 0 = none yet


class SafeError(MeridianModel):
    """One validation problem as a caller may serialise it: field, stable code, constraint; never the input."""

    field: str  # dotted loc, e.g. "values.customer_id"; "" for a model-level rule
    code: str  # pydantic error type or our PydanticCustomError type
    constraint: str  # pydantic's message for that type (it never interpolates the input)

    @classmethod
    def from_validation_error(cls, exc: ValidationError) -> tuple[SafeError, ...]:
        return tuple(
            cls(field=".".join(str(part) for part in err["loc"]), code=err["type"], constraint=err["msg"])
            for err in exc.errors(include_url=False, include_context=False, include_input=False)
        )


class ApiErrorCode(StrEnum):
    """OpenAPI Notice.code (6) + ErrorBlock.code (7) + ApiError.error.code (22): 35 members."""

    # composed notices (HTTP 200, NoticeBlock + Notice)
    TURN_TIMEOUT = "TURN_TIMEOUT"
    BUSY = "BUSY"
    SPEND_CAP_REACHED = "SPEND_CAP_REACHED"
    RATE_LIMITED = "RATE_LIMITED"
    BOOKING_CAP = "BOOKING_CAP"
    AI_PAUSED = "AI_PAUSED"
    # composed errors (HTTP 200, ErrorBlock)
    SLOT_TAKEN = "SLOT_TAKEN"
    OUT_OF_AREA = "OUT_OF_AREA"
    CODE_WRONG = "CODE_WRONG"
    CODE_EXPIRED = "CODE_EXPIRED"
    CODE_LOCKED = "CODE_LOCKED"
    CODE_CAP_REACHED = "CODE_CAP_REACHED"
    NOT_VERIFIED = "NOT_VERIFIED"
    # HTTP errors (ApiError {code, field, constraint, details})
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGIN_RATE_LIMITED = "LOGIN_RATE_LIMITED"
    REQUEST_RATE_LIMITED = "REQUEST_RATE_LIMITED"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_ENDED = "SESSION_ENDED"
    TURN_IN_PROGRESS = "TURN_IN_PROGRESS"
    RESET_IN_PROGRESS = "RESET_IN_PROGRESS"
    RESET_FAILED = "RESET_FAILED"
    HANDOFF_FAILED = "HANDOFF_FAILED"
    ROLE_NOT_ALLOWED = "ROLE_NOT_ALLOWED"
    CASE_NOT_FOUND = "CASE_NOT_FOUND"
    FLAG_NOT_FOUND = "FLAG_NOT_FOUND"
    CASE_ALREADY_CLAIMED = "CASE_ALREADY_CLAIMED"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    NOT_ALLOWED_IN_STATE = "NOT_ALLOWED_IN_STATE"
    REASON_REQUIRED = "REASON_REQUIRED"
    WAKE_UP_REQUIRED = "WAKE_UP_REQUIRED"
    OUTCOME_REQUIRED = "OUTCOME_REQUIRED"
    NOT_LIVE = "NOT_LIVE"
    NOT_CLAIMED_BY_YOU = "NOT_CLAIMED_BY_YOU"
    # NOT present: STAFF_AUTH_REQUIRED (web.md section 1, WEB-9)


class ToolErrorCode(StrEnum):
    """graph-tools section 1, 13 values."""

    NOT_ALLOWED = "not_allowed"
    BAD_ARGUMENTS = "bad_arguments"
    UNKNOWN_TOOL = "unknown_tool"
    NOT_VERIFIED = "not_verified"
    NOT_SHOWN = "not_shown"
    FEE_BEARING = "fee_bearing"
    OUTSIDE_SERVICE_AREA = "outside_service_area"
    SLOT_TAKEN = "slot_taken"
    BOOKING_CAP = "booking_cap"
    IDENTICAL_CALL = "identical_call"
    TOOL_FAILED = "tool_failed"
    WRONG_SERVICE_TYPE = "wrong_service_type"
    NOT_OWNED = "not_owned"


class ToolKind(StrEnum):
    """graph-tools section 1, 7 values (home: domain/tools.py, re-exported there)."""

    KB_SEARCH = "kb_search"
    ACCOUNT_READ = "account_read"
    SLOT_SEARCH = "slot_search"
    BOOK = "book"
    MOVE = "move"
    CANCEL = "cancel"
    CHANGE_REQUEST = "change_request"


class ProviderFailureKind(StrEnum):
    """DO-4 section 11, 14 values."""

    TIMEOUT = "timeout"
    CONNECTION = "connection"
    RATE_LIMITED = "rate_limited"
    OVERLOADED = "overloaded"
    SERVER = "server"
    PROVIDER_SPEND_CAP = "provider_spend_cap"
    OUR_SPEND_LIMIT = "our_spend_limit"
    BAD_REQUEST = "bad_request"
    AUTH = "auth"
    NOT_FOUND = "not_found"
    BODY_ERROR = "body_error"
    REFUSAL = "refusal"
    MAX_TOKENS = "max_tokens"
    INVALID_OUTPUT = "invalid_output"


ProviderName = Literal["anthropic", "openrouter_jev"]  # models.md section 1 (home: ports/models.py)


class ProviderFailure(MeridianModel):
    """DO-4 section 11."""

    kind: ProviderFailureKind
    provider: ProviderName
    http_status: int | None
    retry_after_s: float | None
    retryable: bool
    provider_request_id: str | None


class HaltReason(StrEnum):
    """DO-4 section 11, 8 values."""

    DEADLINE = "deadline"
    BRAKE_TASKS = "brake_tasks"
    BRAKE_TOOL_ROUNDS = "brake_tool_rounds"
    BRAKE_SONNET_CALLS = "brake_sonnet_calls"
    BRAKE_IDENTICAL_CALL = "brake_identical_call"
    RECURSION_LIMIT = "recursion_limit"
    SPEND_CAP = "spend_cap"
    PROVIDER_SPEND_CAP = "provider_spend_cap"


class Halt(MeridianModel):
    reason: HaltReason
    node: str
    elapsed_ms: int


class Role(StrEnum):
    """DO-4 section 12 (home: ports/models.py)."""

    PLANNER = "planner"
    CLASSIFIER = "classifier"
    PLANNER_FALLBACK = "planner_fallback"
    SPECIALIST = "specialist"
    RESPONDER = "responder"
    BRIEF = "brief"


class ProviderCall(MeridianModel):
    """models.md section 1 (home: ports/models.py)."""

    provider: ProviderName
    model: str
    latency_ms: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cache_read_tokens: int = Field(ge=0)
    cache_write_tokens: int = Field(ge=0)
    thinking_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    cost_source: Literal["reported", "price_table"]
    status: Literal["ok", "error"]
    failure: ProviderFailure | None
    provider_request_id: str | None
    stop_reason: str | None


class CallRecord(ProviderCall):
    """models.md section 1 (home: ports/models.py)."""

    role: Role
    attempt: int = Field(ge=1, le=2)

    @classmethod
    def from_provider(cls, call: ProviderCall, *, role: Role, attempt: int) -> CallRecord:
        return cls.model_validate({**call.model_dump(), "role": role, "attempt": attempt})


class HandoffReason(StrEnum):
    """DO-4 section 7 (15) + CAS-16 option A (D-14) = 16 (home: handoff.py)."""

    SAFETY = "safety"
    DANGER = "danger"
    BURNING_UNCLEAR = "burning_unclear"
    CUSTOMER_REQUESTED_PERSON = "customer_requested_person"
    REFUND = "refund"
    BILLING_DISPUTE = "billing_dispute"
    COMPLAINT_OR_MANAGER = "complaint_or_manager"
    LEGAL_OR_CHARGEBACK = "legal_or_chargeback"
    COMMERCIAL = "commercial"
    LATE_TECHNICIAN = "late_technician"
    FEE_BEARING_CHANGE = "fee_bearing_change"
    MEMBERSHIP_CANCEL = "membership_cancel"
    UNSUPPORTED_ACTION = "unsupported_action"
    IDENTITY_UNVERIFIED = "identity_unverified"
    AI_FAILURE = "ai_failure"
    BURNING_RULED_OUT = "burning_ruled_out"


class Priority(StrEnum):
    """Home: handoff.py."""

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


Presence = Literal["nobody_online", "simulated_on_shift"]  # cases.md A-1 (home: handoff.py)
# = OpenAPI CaseSummary.lifecycle enum (home: handoff.py)
CaseState = Literal[
    "live_queued", "unassigned", "claimed", "in_progress", "waiting", "resolved", "closed_unresolved"
]


class Promise(MeridianModel):
    """DO-4 section 7; fields only, NO text validator (graph-core section 10, GRC-2). Home: handoff.py."""

    policy_row: str
    text: str
    due_at: dt.datetime | None
    due_label: str | None
    extra_lines: tuple[str, ...] = ()
    live_queued: bool = False


class FollowUp(MeridianModel):
    """= OpenAPI FollowUpView (cases.md section 5). Home: handoff.py."""

    channel: Literal["email", "phone"]
    destination_label: str
    on_record: bool
    window: Literal["morning", "afternoon", "any"]
    saved_line: str


class SafetyKind(StrEnum):
    """DO-4 section 3 (home: turn.py, R-G-1)."""

    GAS = "gas"
    CO = "co"
    SPARKS_SMOKE_FLAMES = "sparks_smoke_flames"
    BURNING_WITH_BREAKER = "burning_with_breaker"


class ToolCallRecord(MeridianModel):
    """graph-tools section 1 (home: tools.py)."""

    tool_call_id: str
    name: str = Field(max_length=64)  # as the model sent it; dispatch truncates an unknown name to 64 chars
    kind: ToolKind | None
    outcome: Literal["ok", "refused", "failed"]
    error: ToolErrorCode | None
    record_ids: tuple[str, ...]
    passage_ids: tuple[PassageId, ...]
    lookup_id: int | None
    elapsed_ms: int


class FailureCounters(MeridianModel):
    """DO-4 section 1 (home: state.py); writers: graph-core section 8."""

    failed_answers: int = 0
    tool_failures: int = 0
    identity_failures: int = 0
    corrections: int = 0
    timeouts: int = 0
    bookings: int = 0
