"""CON-11…13, CON-15…17: the staff case routes (stage7/staff.md section 6). AEA-45. Thin: role, request, one
demo-clock reading, one service call, rejection → documented status, serialise. Reads no server clock, logs nothing,
never opens a case, adds no reset check."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from datetime import datetime
from types import MappingProxyType
from typing import Final, Literal, Protocol

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from meridian.domain.common import ApiErrorCode, CaseRef
from meridian.domain.staff import LoginSession, StaffActor, StaffRole
from meridian.domain.views import ActivityIn, CaseAction, CaseActionRejected
from meridian.services.staff import FlagIn, FlagRejected
from meridian.web.deps import (
    StaffAccess,
    get_case_service,
    get_demo_service,
    get_flag_service,
    get_login_session,
    get_staff_access,
    require_staff,
)
from meridian.web.errors import ApiProblem
from meridian.web.schemas.staff_cases import (
    REFERENCE_CONSTRAINT,
    ActivityRequest,
    ActivityResponse,
    CaseActionRequest,
    CaseActionResponse,
    CaseDetailOut,
    CaseSummaryOut,
    FlagOut,
    FlagRequest,
    FlagReviewRequest,
    FlagsResponse,
    OversightResponse,
    QueueResponse,
    result_line,
)

QUEUE_PATH = "/api/staff/queue"
CASE_PATH = "/api/staff/cases/{reference}"
ACTIONS_PATH = CASE_PATH + "/actions"
ACTIVITIES_PATH = CASE_PATH + "/activities"
FLAGS_PATH = "/api/staff/flags"
FLAG_PATH = FLAGS_PATH + "/{flag_id}"
OVERSIGHT_PATH = "/api/staff/oversight"


class _ClockReading(Protocol):
    @property
    def now(self) -> datetime: ...


class _DemoClock(Protocol):
    def clock_view(self) -> _ClockReading: ...


class _Cases(Protocol):
    def queue(self, role: StaffRole, now: datetime) -> object: ...
    def detail(self, case_ref: CaseRef, role: StaffRole, now: datetime) -> object: ...
    def oversight(self, now: datetime) -> object: ...
    def apply(
        self, case_ref: CaseRef, action: CaseAction, actor: StaffActor, expected_version: int, now: datetime
    ) -> object: ...
    def record_activity(
        self, case_ref: CaseRef, activity: ActivityIn, actor: StaffActor, now: datetime
    ) -> object: ...


class _Flags(Protocol):
    def flag(self, flag: FlagIn, actor: StaffActor) -> object: ...
    def review(self, flag_id: str, note: str | None, actor: StaffActor) -> object: ...
    def list_flags(self) -> Sequence[object]: ...


_R, _S, _O = StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR, StaffRole.OWNER
_QUEUE_ROLES = require_staff(_R, _S)
_CASE_ROLES = require_staff(_R, _S, _O)
_ACTION_ROLES = require_staff(_R, _S)
_ACTIVITY_ROLES = require_staff(_R)
_CREATE_FLAG_ROLES = require_staff(_R, _S)
_LIST_FLAG_ROLES = require_staff(_R, _S, _O)
_REVIEW_FLAG_ROLES = require_staff(_S)
_OVERSIGHT_ROLES = require_staff(_S)
_SUPERVISOR_ONLY = require_staff(_S)  # STF-3 second check
SUPERVISOR_ONLY_ACTIONS: Final = frozenset({"assign", "change_priority"})
REJECTION_STATUS: Final[Mapping[ApiErrorCode, int]] = MappingProxyType(
    {
        ApiErrorCode.CASE_NOT_FOUND: 404,
        ApiErrorCode.FLAG_NOT_FOUND: 404,
        ApiErrorCode.VERSION_CONFLICT: 409,
        ApiErrorCode.CASE_ALREADY_CLAIMED: 409,
        ApiErrorCode.NOT_ALLOWED_IN_STATE: 409,
        ApiErrorCode.REASON_REQUIRED: 422,
        ApiErrorCode.WAKE_UP_REQUIRED: 422,
        ApiErrorCode.OUTCOME_REQUIRED: 422,
        ApiErrorCode.VALIDATION_ERROR: 400,
        ApiErrorCode.ROLE_NOT_ALLOWED: 403,
    }
)


def _problem(rejection: CaseActionRejected | FlagRejected) -> ApiProblem:
    """Copy the service's refusal onto its documented status; never invent a field, constraint or detail."""
    code = ApiErrorCode(str(rejection.code))
    status = REJECTION_STATUS.get(code)
    if status is None:
        raise RuntimeError(f"unmapped rejection code {code.value}")
    return ApiProblem(
        status,
        code,
        field=rejection.field,
        constraint=rejection.constraint,
        details=None if rejection.details is None else dict(rejection.details),
    )


def _case_ref(reference: str, *, malformed_status: Literal[400, 404]) -> CaseRef:
    if re.fullmatch(CaseRef.PATTERN, reference) is None:
        if malformed_status == 404:
            raise ApiProblem(404, ApiErrorCode.CASE_NOT_FOUND)
        raise ApiProblem(
            400, ApiErrorCode.VALIDATION_ERROR, field="reference", constraint=REFERENCE_CONSTRAINT
        )
    return CaseRef(reference)


def _json(model: BaseModel, status: int = 200) -> JSONResponse:
    return JSONResponse(model.model_dump(mode="json"), status_code=status)


# Parameter order is load-bearing: the role dependency comes first, so a refused role answers 403 before any
# provider resolves (an unbound provider can never turn a 403 into a 500) and no service method runs.
def get_queue(
    actor: StaffActor = Depends(_QUEUE_ROLES),  # noqa: B008
    cases: _Cases = Depends(get_case_service),  # noqa: B008
    demo: _DemoClock = Depends(get_demo_service),  # noqa: B008
) -> JSONResponse:
    now = demo.clock_view().now
    return _json(QueueResponse.model_validate(cases.queue(actor.role, now)))


def get_oversight(
    actor: StaffActor = Depends(_OVERSIGHT_ROLES),  # noqa: B008
    cases: _Cases = Depends(get_case_service),  # noqa: B008
    demo: _DemoClock = Depends(get_demo_service),  # noqa: B008
) -> JSONResponse:
    now = demo.clock_view().now
    return _json(OversightResponse.model_validate(cases.oversight(now)))


def get_case(
    reference: str,
    actor: StaffActor = Depends(_CASE_ROLES),  # noqa: B008
    cases: _Cases = Depends(get_case_service),  # noqa: B008
    demo: _DemoClock = Depends(get_demo_service),  # noqa: B008
) -> JSONResponse:
    case_ref = _case_ref(reference, malformed_status=404)
    now = demo.clock_view().now
    try:
        detail = cases.detail(case_ref, actor.role, now)
    except LookupError as exc:
        if getattr(exc, "case_ref", None) != str(case_ref):
            raise  # any other LookupError (a KeyError bug) stays a 500
        raise ApiProblem(404, ApiErrorCode.CASE_NOT_FOUND, details={"reference": str(case_ref)}) from None
    return _json(CaseDetailOut.model_validate(detail))


def apply_case_action(
    reference: str,
    body: CaseActionRequest,
    actor: StaffActor = Depends(_ACTION_ROLES),  # noqa: B008
    session: LoginSession = Depends(get_login_session),  # noqa: B008
    access: StaffAccess = Depends(get_staff_access),  # noqa: B008
    cases: _Cases = Depends(get_case_service),  # noqa: B008
    demo: _DemoClock = Depends(get_demo_service),  # noqa: B008
) -> JSONResponse:
    case_ref = _case_ref(reference, malformed_status=400)
    if body.action in SUPERVISOR_ONLY_ACTIONS:
        _SUPERVISOR_ONLY(session=session, access=access)
    now = demo.clock_view().now
    action = CaseAction.model_validate(body.model_dump())
    result = cases.apply(case_ref, action, actor, body.expected_version, now)
    if isinstance(result, CaseActionRejected):
        raise _problem(result)
    summary = CaseSummaryOut.model_validate(result)
    return _json(CaseActionResponse(case=summary, result_line=result_line(body.action, summary, actor)))


def record_contact_activity(
    reference: str,
    body: ActivityRequest,
    actor: StaffActor = Depends(_ACTIVITY_ROLES),  # noqa: B008
    cases: _Cases = Depends(get_case_service),  # noqa: B008
    demo: _DemoClock = Depends(get_demo_service),  # noqa: B008
) -> JSONResponse:
    case_ref = _case_ref(reference, malformed_status=400)
    now = demo.clock_view().now
    activity = ActivityIn.model_validate(body.model_dump())
    result = cases.record_activity(case_ref, activity, actor, now)
    if isinstance(result, CaseActionRejected):
        raise _problem(result)
    return _json(ActivityResponse.model_validate(result), status=201)


def create_flag(
    body: FlagRequest,
    actor: StaffActor = Depends(_CREATE_FLAG_ROLES),  # noqa: B008
    flags: _Flags = Depends(get_flag_service),  # noqa: B008
) -> JSONResponse:
    if re.fullmatch(CaseRef.PATTERN, body.case_ref) is None:
        raise ApiProblem(
            400, ApiErrorCode.VALIDATION_ERROR, field="case_ref", constraint=REFERENCE_CONSTRAINT
        )
    flag_in = FlagIn.model_validate(
        {
            "case_ref": body.case_ref,
            "target": body.target,
            "message_id": body.message_id,
            "note": body.note,
            "reason": body.reason,
        }
    )
    result = flags.flag(flag_in, actor)
    if isinstance(result, FlagRejected):
        raise _problem(result)
    return _json(FlagOut.model_validate(result), status=201)


def list_flags(
    actor: StaffActor = Depends(_LIST_FLAG_ROLES),  # noqa: B008
    flags: _Flags = Depends(get_flag_service),  # noqa: B008
    demo: _DemoClock = Depends(get_demo_service),  # noqa: B008
) -> JSONResponse:
    now = demo.clock_view().now  # FlagsResponse.as_of is demo time (staff.md section 10)
    records = flags.list_flags()
    return _json(FlagsResponse(as_of=now, flags=[FlagOut.model_validate(r) for r in records]))


def review_flag(
    flag_id: str,
    body: FlagReviewRequest,
    actor: StaffActor = Depends(_REVIEW_FLAG_ROLES),  # noqa: B008
    flags: _Flags = Depends(get_flag_service),  # noqa: B008
) -> JSONResponse:
    result = flags.review(flag_id, body.note, actor)
    if isinstance(result, FlagRejected):
        raise _problem(result)
    return _json(FlagOut.model_validate(result))


def build_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route(QUEUE_PATH, get_queue, methods=["GET"], operation_id="getQueue", response_model=None)
    router.add_api_route(CASE_PATH, get_case, methods=["GET"], operation_id="getCase", response_model=None)
    router.add_api_route(
        ACTIONS_PATH, apply_case_action, methods=["POST"], operation_id="applyCaseAction", response_model=None
    )
    router.add_api_route(
        ACTIVITIES_PATH,
        record_contact_activity,
        methods=["POST"],
        operation_id="recordContactActivity",
        response_model=None,
        status_code=201,
    )
    router.add_api_route(
        FLAGS_PATH,
        create_flag,
        methods=["POST"],
        operation_id="createFlag",
        response_model=None,
        status_code=201,
    )
    router.add_api_route(
        FLAGS_PATH, list_flags, methods=["GET"], operation_id="listFlags", response_model=None
    )
    router.add_api_route(
        FLAG_PATH, review_flag, methods=["PATCH"], operation_id="reviewFlag", response_model=None
    )
    router.add_api_route(
        OVERSIGHT_PATH, get_oversight, methods=["GET"], operation_id="getOversight", response_model=None
    )
    return router
