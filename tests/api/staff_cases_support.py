"""AEA-45 test support. Doubles of CaseService, FlagService and DemoService return the real `domain/views.py` /
`services/staff.py` types built from the OpenAPI examples. Not a conftest. Synthetic values only."""

from __future__ import annotations

import copy
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Final

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import meridian.web.app as app_module
from meridian.config import Settings
from meridian.domain.common import CaseRef
from meridian.domain.staff import DemoRole, StaffActor, StaffRole
from meridian.domain.views import (
    ActivityIn,
    ActivityResult,
    CaseAction,
    CaseActionRejected,
    CaseDetail,
    CaseSummaryView,
    ClockView,
    OversightView,
    QueueView,
)
from meridian.policy.limits import Limits
from meridian.services.staff import FlagIn, FlagRecord
from meridian.web.app import create_app
from meridian.web.container import Container, register_staff_cases, register_web
from meridian.web.deps import (
    get_case_service,
    get_demo_service,
    get_flag_service,
    get_heartbeat,
    get_login_sessions,
    get_staff_access,
)
from tests.api.openapi_check import load_contract, load_document
from tests.api.web_shell_support import FakeHeartbeat, FakeSessionStore, cookie_header, full_app
from tests.contract.openapi_variants import iter_response_examples, request_examples
from tests.fakes.clock import CHICAGO
from tests.fixtures.sqlite import ISSUED_DB

FIXED_NOW: Final = datetime(2026, 10, 19, 7, 0, tzinfo=CHICAGO)  # -05:00; the AC-12 instant
SEEDED_REF: Final = "MHC-C-0007"
PATHS: Final[dict[str, str]] = {
    "getQueue": "/api/staff/queue",
    "getCase": f"/api/staff/cases/{SEEDED_REF}",
    "applyCaseAction": f"/api/staff/cases/{SEEDED_REF}/actions",
    "recordContactActivity": f"/api/staff/cases/{SEEDED_REF}/activities",
    "createFlag": "/api/staff/flags",
    "listFlags": "/api/staff/flags",
    "reviewFlag": "/api/staff/flags/flg-3",
    "getOversight": "/api/staff/oversight",
}
METHODS: Final[dict[str, str]] = {
    "getQueue": "GET",
    "getCase": "GET",
    "applyCaseAction": "POST",
    "recordContactActivity": "POST",
    "createFlag": "POST",
    "listFlags": "GET",
    "reviewFlag": "PATCH",
    "getOversight": "GET",
}
DEFAULT_REQUESTS: Final[dict[str, tuple[str, str]]] = {
    "applyCaseAction": ("applyCaseAction", "CLAIM"),
    "recordContactActivity": ("recordContactActivity", "CALL"),
    "createFlag": ("createFlag", "ANSWER"),
    "reviewFlag": ("reviewFlag", "REVIEW"),
}


# -- OpenAPI example loaders --------------------------------------------------------------------------------------
def response_example(operation_id: str, name: str, status: str = "200") -> dict[str, Any]:
    for example in iter_response_examples():
        if (example.operation_id, example.status, example.name) == (operation_id, status, name):
            value: dict[str, Any] = copy.deepcopy(example.value)
            return value
    raise KeyError(f"{operation_id}/{status}/{name}")


def request_example(operation_id: str, name: str) -> dict[str, Any]:
    value: dict[str, Any] = request_examples(operation_id)[name]
    return value


def error_example(operation_id: str, status: str, name: str) -> dict[str, Any]:
    error: dict[str, Any] = response_example(operation_id, name, status)["error"]
    return error


def x_roles(operation_id: str) -> list[str]:
    spec = load_contract().operations[operation_id]
    node = load_document()["paths"][spec.path_template][spec.method]
    return [str(entry).split()[0] for entry in node["x-roles"]]


# -- view builders (the real types) -------------------------------------------------------------------------------
def queue_view(name: str = "SEEDED") -> QueueView:
    return QueueView.model_validate(response_example("getQueue", name))


def case_detail(name: str = "DEFAULT") -> CaseDetail:
    return CaseDetail.model_validate(response_example("getCase", name))


def oversight_view(name: str = "SEEDED") -> OversightView:
    return OversightView.model_validate(response_example("getOversight", name))


def summary(name: str = "CLAIMED", **changes: Any) -> CaseSummaryView:
    return CaseSummaryView.model_validate({**response_example("applyCaseAction", name)["case"], **changes})


def activity_result(name: str = "CALL_REACHED") -> ActivityResult:
    return ActivityResult.model_validate(response_example("recordContactActivity", name, "201"))


def flag_record(op: str = "createFlag", name: str = "ANSWER", status: str = "201") -> FlagRecord:
    return FlagRecord.model_validate(response_example(op, name, status))


def flag_records(name: str = "THREE") -> tuple[FlagRecord, ...]:
    return tuple(FlagRecord.model_validate(f) for f in response_example("listFlags", name)["flags"])


def case_rejected(operation_id: str, status: str, name: str) -> CaseActionRejected:
    return CaseActionRejected.model_validate(error_example(operation_id, status, name))


_KEEP_AS_DICT: Final = frozenset({"snapshot", "current", "details"})


def as_attrs(value: Any) -> Any:
    """Dicts become namespaces (lists element-wise) except the values under snapshot, current and details."""
    if isinstance(value, dict):
        return SimpleNamespace(**{k: v if k in _KEEP_AS_DICT else as_attrs(v) for k, v in value.items()})
    if isinstance(value, list):
        return [as_attrs(v) for v in value]
    return value


class CaseNotFoundStandIn(LookupError):
    """AEA-29's CaseNotFound shape: a LookupError carrying `case_ref`."""

    def __init__(self, case_ref: str) -> None:
        super().__init__(f"no case {case_ref}")
        self.case_ref = case_ref


@dataclass
class ServiceCall:
    method: str
    args: dict[str, Any]


class FakeDemoService:
    def __init__(self, now: datetime = FIXED_NOW) -> None:
        self.now = now
        self.reads = 0

    def clock_view(self) -> ClockView:
        self.reads += 1
        return ClockView(now=self.now, label="demo label", date_label="demo date label")


class FakeCaseService:
    """CaseService double: records every call by argument name and returns the programmed result. No open_case."""

    def __init__(self) -> None:
        self.queue_result: Any = queue_view()
        self.detail_result: Any = case_detail()
        self.detail_raises: BaseException | None = None
        self.oversight_result: Any = oversight_view()
        self.apply_result: Any = summary()
        self.activity_result: Any = activity_result()
        self.calls: list[ServiceCall] = []

    def queue(self, role: StaffRole, now: datetime) -> Any:
        self.calls.append(ServiceCall("queue", {"role": role, "now": now}))
        return self.queue_result

    def detail(self, case_ref: CaseRef, role: StaffRole, now: datetime) -> Any:
        self.calls.append(ServiceCall("detail", {"case_ref": case_ref, "role": role, "now": now}))
        if self.detail_raises is not None:
            raise self.detail_raises
        return self.detail_result

    def oversight(self, now: datetime) -> Any:
        self.calls.append(ServiceCall("oversight", {"now": now}))
        return self.oversight_result

    def apply(
        self, case_ref: CaseRef, action: CaseAction, actor: StaffActor, expected_version: int, now: datetime
    ) -> Any:
        self.calls.append(
            ServiceCall(
                "apply",
                {
                    "case_ref": case_ref,
                    "action": action,
                    "actor": actor,
                    "expected_version": expected_version,
                    "now": now,
                },
            )
        )
        return self.apply_result

    def record_activity(
        self, case_ref: CaseRef, activity: ActivityIn, actor: StaffActor, now: datetime
    ) -> Any:
        self.calls.append(
            ServiceCall(
                "record_activity", {"case_ref": case_ref, "activity": activity, "actor": actor, "now": now}
            )
        )
        return self.activity_result

    def calls_of(self, method: str) -> list[ServiceCall]:
        return [c for c in self.calls if c.method == method]


class FakeFlagService:
    def __init__(self) -> None:
        self.flag_result: object | None = None
        self.review_result: object = flag_record("reviewFlag", "REVIEWED", "200")
        self.list_result: tuple[FlagRecord, ...] = flag_records()
        self.calls: list[ServiceCall] = []

    def flag(self, flag: FlagIn, actor: StaffActor) -> object:
        self.calls.append(ServiceCall("flag", {"flag": flag, "actor": actor}))
        if self.flag_result is not None:
            return self.flag_result
        return flag_record().model_copy(
            update={
                "note": flag.note,
                "reason": flag.reason,
                "case_ref": flag.case_ref,
                "target": flag.target,
                "message_id": flag.message_id,
            }
        )

    def review(self, flag_id: str, note: str | None, actor: StaffActor) -> object:
        self.calls.append(ServiceCall("review", {"flag_id": flag_id, "note": note, "actor": actor}))
        return self.review_result

    def list_flags(self) -> tuple[FlagRecord, ...]:
        self.calls.append(ServiceCall("list_flags", {}))
        return self.list_result


@dataclass
class StaffCasesHarness:
    app: FastAPI
    settings: Settings
    store: FakeSessionStore
    cases: FakeCaseService = field(default_factory=FakeCaseService)
    flags: FakeFlagService = field(default_factory=FakeFlagService)
    demo: FakeDemoService = field(default_factory=FakeDemoService)


def staff_app(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    *,
    store: FakeSessionStore | None = None,
    cases: FakeCaseService | None = None,
    flags: FakeFlagService | None = None,
    demo: FakeDemoService | None = None,
) -> StaffCasesHarness:
    """create_app over a container running register_web and register_staff_cases; doubles as dependency overrides."""

    def build(app: FastAPI, settings: Any, *, overrides: Any = None) -> Container:
        limits = Limits()
        container = Container(settings=settings, limits=limits)
        register_web(container, app, settings=settings, limits=limits)
        register_staff_cases(container, app, settings=settings, limits=limits)
        container.build()
        return container

    monkeypatch.setattr(app_module, "build_container", build)
    app = create_app(settings)
    h = StaffCasesHarness(
        app=app,
        settings=settings,
        store=store if store is not None else FakeSessionStore(),
        cases=cases if cases is not None else FakeCaseService(),
        flags=flags if flags is not None else FakeFlagService(),
        demo=demo if demo is not None else FakeDemoService(),
    )
    _override(app, h)
    return h


def _override(app: FastAPI, h: StaffCasesHarness) -> None:
    app.dependency_overrides[get_login_sessions] = lambda: h.store
    app.dependency_overrides[get_staff_access] = lambda: h.store
    app.dependency_overrides[get_heartbeat] = lambda: FakeHeartbeat()
    app.dependency_overrides[get_case_service] = lambda: h.cases
    app.dependency_overrides[get_flag_service] = lambda: h.flags
    app.dependency_overrides[get_demo_service] = lambda: h.demo


def staff_full_app(
    monkeypatch: pytest.MonkeyPatch,
    settings: Settings,
    *,
    store: FakeSessionStore,
    cases: FakeCaseService,
    flags: FakeFlagService,
    demo: FakeDemoService,
) -> FastAPI:
    """The real build_container (every hunk) with the three services overridden (AC-17)."""
    app = full_app(monkeypatch, settings, store=store, heartbeat=FakeHeartbeat())
    app.dependency_overrides[get_case_service] = lambda: cases
    app.dependency_overrides[get_flag_service] = lambda: flags
    app.dependency_overrides[get_demo_service] = lambda: demo
    return app


def as_role(h: StaffCasesHarness, role: DemoRole) -> dict[str, str]:
    return cookie_header(h.store.issue(role))


def call(
    client: TestClient, op: str, headers: dict[str, str], *, path: str | None = None, body: Any = None
) -> Any:
    return client.request(METHODS[op], path or PATHS[op], headers=headers, json=body)


def default_body(op: str) -> Any:
    """The operation's default request body (CLAIM, CALL, ANSWER, REVIEW), or None."""
    pair = DEFAULT_REQUESTS.get(op)
    return None if pair is None else request_example(*pair)


def seeded_contact(customer_id: str = "MHC-10002") -> tuple[str, str]:
    """(email, service_address) of one issued customer, read-only. Never print or log the values."""
    connection = sqlite3.connect(f"file:{ISSUED_DB}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT email, service_address FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
    finally:
        connection.close()
    return str(row[0]), str(row[1])
