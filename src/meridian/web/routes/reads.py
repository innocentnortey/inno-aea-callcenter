"""CON-18 to CON-20 reads: getOwnerMetrics, getMonitoring, getLatestEval (stage7/staff.md section 9). AEA-48.

Each route makes exactly one MetricsReads call (web.md section 4, MC-6), validates the mapping through
web/schemas/reads.py and returns it field for field. It computes nothing, stamps nothing and reads no clock: the reader
stamps every time field (STF-22, MC-5). Unknown keys are dropped with one warning naming them, never their values; a
mapping that breaks the schema answers 500 with one log line naming the field and rule (STF-17, AEA-48-1). Limits and
the reset gate are the middleware's (web.md sections 5 and 7); getOwnerMetrics alone needs owner or supervisor (MC-4).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Final

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from meridian.domain.staff import StaffRole
from meridian.web.deps import MetricsReads, get_metrics_reads, get_request_context, require_staff
from meridian.web.errors import render_unhandled_error
from meridian.web.middleware import RequestContext
from meridian.web.schemas.reads import (
    EvalResponse,
    MonitoringResponse,
    OwnerMetricsResponse,
    ReadModel,
    describe_errors,
    dropped_keys,
)

OWNER_METRICS_PATH: Final = "/api/staff/owner-metrics"
MONITORING_PATH: Final = "/api/monitoring"
LATEST_EVAL_PATH: Final = "/api/eval/latest"
OWNER_METRICS_OPERATION: Final = "getOwnerMetrics"
MONITORING_OPERATION: Final = "getMonitoring"
LATEST_EVAL_OPERATION: Final = "getLatestEval"
READS_LOGGER: Final = "meridian.web.reads"
SCHEMA_VIOLATION: Final = "reads_schema_violation"  # the request record's error_kind on the 500
_OWNER_OR_SUPERVISOR = require_staff(
    StaffRole.OWNER, StaffRole.SUPERVISOR
)  # x-roles order: [owner, supervisor]
_LOG = logging.getLogger(READS_LOGGER)


def _answer(
    request: Request,
    ctx: RequestContext,
    operation_id: str,
    model: type[ReadModel],
    raw: Mapping[str, object],
) -> Response:
    try:
        payload = model.model_validate(raw)
    except ValidationError as exc:
        refused = "; ".join(f"{field} {rule}" for field, rule in describe_errors(exc))
        _LOG.error("%s: reader mapping refused: %s", operation_id, refused)
        request.state.error_kind = SCHEMA_VIOLATION
        return render_unhandled_error(ctx.request_id)
    body = payload.model_dump(mode="json")
    dropped = dropped_keys(raw, body)
    if dropped:
        _LOG.warning("%s: dropped keys not in the OpenAPI: %s", operation_id, ", ".join(dropped))
    return JSONResponse(body)


def get_owner_metrics(
    request: Request,
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    reads: MetricsReads = Depends(get_metrics_reads),  # noqa: B008
) -> Response:
    return _answer(request, ctx, OWNER_METRICS_OPERATION, OwnerMetricsResponse, reads.owner_metrics())


def get_monitoring(
    request: Request,
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    reads: MetricsReads = Depends(get_metrics_reads),  # noqa: B008
) -> Response:
    return _answer(request, ctx, MONITORING_OPERATION, MonitoringResponse, reads.monitoring())


def get_latest_eval(
    request: Request,
    ctx: RequestContext = Depends(get_request_context),  # noqa: B008
    reads: MetricsReads = Depends(get_metrics_reads),  # noqa: B008
) -> Response:
    return _answer(request, ctx, LATEST_EVAL_OPERATION, EvalResponse, reads.latest_eval())


def build_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route(
        OWNER_METRICS_PATH,
        get_owner_metrics,
        methods=["GET"],
        operation_id=OWNER_METRICS_OPERATION,
        response_model=None,
        dependencies=[Depends(_OWNER_OR_SUPERVISOR)],  # route dependencies run before the endpoint's own
    )
    router.add_api_route(
        MONITORING_PATH,
        get_monitoring,
        methods=["GET"],
        operation_id=MONITORING_OPERATION,
        response_model=None,
    )
    router.add_api_route(
        LATEST_EVAL_PATH,
        get_latest_eval,
        methods=["GET"],
        operation_id=LATEST_EVAL_OPERATION,
        response_model=None,
    )
    return router
