"""One ApiProblem, one renderer (web.md section 1).

Routes and dependencies raise ``ApiProblem`` for every HTTP 4xx/5xx. ``render_api_problem`` is the only place in
``web/`` that builds an ``ApiError`` body; the 422 handler builds an ``ApiProblem`` too, so there is exactly one
renderer. A rejected value never reaches a body or a log.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from meridian.domain.common import ApiErrorCode

REQUEST_ID_HEADER = "X-Request-ID"
_LOCATION_PREFIXES = ("body", "query", "path", "header", "cookie")


class ApiProblem(Exception):
    def __init__(
        self,
        status: int,
        code: ApiErrorCode,
        *,
        field: str | None = None,
        constraint: str | None = None,
        details: dict[str, object] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(f"{status} {code}")
        self.status = status
        self.code = code
        self.field = field
        self.constraint = constraint
        self.details = details
        self.headers: dict[str, str] = dict(headers or {})


def render_api_problem(problem: ApiProblem, request_id: str) -> JSONResponse:
    """THE renderer: ApiError {error: {code, field, constraint, details}, request_id}."""
    return JSONResponse(
        {
            "error": {
                "code": problem.code.value,
                "field": problem.field,
                "constraint": problem.constraint,
                "details": dict(problem.details) if problem.details is not None else None,
            },
            "request_id": request_id,
        },
        status_code=problem.status,
        headers={**problem.headers, REQUEST_ID_HEADER: request_id},
    )


def _request_id_of(request: Request) -> str:
    return str(getattr(request.state, "request_id", None) or uuid.uuid4())


async def handle_api_problem(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, ApiProblem):
        raise TypeError("handle_api_problem is registered for ApiProblem only")
    if exc.status >= 500:
        request.state.error_kind = exc.code.value
    return render_api_problem(exc, _request_id_of(request))


async def handle_validation_error(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, RequestValidationError):
        raise TypeError("handle_validation_error is registered for RequestValidationError only")
    first = exc.errors()[0]  # read only loc, type and msg: never input or ctx
    loc = tuple(first["loc"])
    rest = loc[1:] if loc and loc[0] in _LOCATION_PREFIXES else loc
    if first["type"] == "json_invalid" or not rest or isinstance(rest[0], int):
        field = str(loc[0]) if loc else "body"
    else:
        field = ".".join(str(part) for part in rest)
    problem = ApiProblem(
        400,
        ApiErrorCode.VALIDATION_ERROR,
        field=field,
        constraint=str(first["msg"]),
        details=None,
    )
    return await handle_api_problem(request, problem)


def render_unhandled_error(request_id: str) -> JSONResponse:
    """500 with the request id only: the signed ApiError enum has no generic code (plan decision D-P1)."""
    return JSONResponse({"request_id": request_id}, status_code=500, headers={REQUEST_ID_HEADER: request_id})
