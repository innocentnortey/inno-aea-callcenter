"""Need and operation owners, preflight, blocked handling, step results and the journey file convention (AEA-57)."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, NoReturn

import pytest

if TYPE_CHECKING:
    from fastapi import FastAPI

    from meridian.web.container import Container

NEED_OWNERS: Mapping[str, str] = MappingProxyType(
    {
        "login_sessions": "AEA-44",
        "staff_access": "AEA-44",
        "flag_service": "AEA-44",
        "session_service": "AEA-40",
        "turn_service": "AEA-40",
        "demo_service": "AEA-30",
        "demo_clock": "AEA-30",
        "reply_composer": "AEA-51",
        "run_graph": "AEA-51",
        "person_requests": "AEA-42",
        "handoff_service": "AEA-29",
        "case_service": "AEA-29",
        "identity_service": "AEA-27",
        "reset_service": "AEA-31",
        "live_chat": "AEA-46",
        "metrics_reads": "AEA-53",
        "ledger": "AEA-26",
        "trace": "AEA-19",
        "heartbeat": "AEA-32",
        "uow_factory": "AEA-10",
        "checkpointer": "AEA-10",
        "restore_working_copy": "AEA-10",
        "reset_gate": "AEA-23",
        "rate_limiter": "AEA-23",
        "stream_poll_limiter": "AEA-23",
        "wall_clock": "AEA-23",
    }
)
OPERATION_OWNERS: Mapping[str, str] = MappingProxyType(
    {
        "login": "AEA-23",
        "logout": "AEA-23",
        "getSession": "AEA-44",
        "listDemoRoles": "AEA-44",
        "switchRole": "AEA-44",
        "startChatSession": "AEA-40",
        "getChatThread": "AEA-40",
        "submitTurn": "AEA-40",
        "streamChatEvents": "AEA-41",
        "requestPerson": "AEA-42",
        "saveFollowUp": "AEA-42",
        "listDemoInbox": "AEA-43",
        "getStaffing": "AEA-43",
        "setStaffing": "AEA-43",
        "getDemoClock": "AEA-43",
        "resetDemo": "AEA-43",
        "advanceDemoClock": "AEA-47",
        "getQueue": "AEA-45",
        "getCase": "AEA-45",
        "applyCaseAction": "AEA-45",
        "recordContactActivity": "AEA-45",
        "createFlag": "AEA-45",
        "listFlags": "AEA-45",
        "reviewFlag": "AEA-45",
        "getOversight": "AEA-45",
        "liveChatAction": "AEA-46",
        "streamCaseEvents": "AEA-46",
        "getOwnerMetrics": "AEA-48",
        "getMonitoring": "AEA-48",
        "getLatestEval": "AEA-48",
    }
)


@dataclass(frozen=True)
class Missing:
    what: str
    owner: str


@dataclass(frozen=True)
class StepResult:
    journey: str
    step: str
    nodeid: str
    status: Literal["pass", "fail", "blocked"]
    detail: str
    blocked_on: tuple[str, ...]
    seconds: float


@dataclass(frozen=True)
class TestOutcome:
    __test__ = False  # not a pytest class

    nodeid: str
    outcome: str  # "passed" | "failed" | "skipped"
    duration_s: float


@dataclass(frozen=True)
class RunNote:
    host: str
    port: int
    agent_version: str
    models: Mapping[str, str]
    issued_sha256: str
    spend_rows: int
    spend_total_usd: float
    outbound_blocked: int


@dataclass
class StepCollector:
    steps: list[StepResult] = field(default_factory=list)
    tests: list[TestOutcome] = field(default_factory=list)
    notes: list[RunNote] = field(default_factory=list)

    def add_step(self, result: StepResult) -> None:
        self.steps.append(result)

    def add_test(self, outcome: TestOutcome) -> None:
        self.tests.append(outcome)

    def add_note(self, note: RunNote) -> None:
        self.notes.append(note)


JOURNEY_NODEID = re.compile(r"^tests/journeys/(j(?:[1-9]|10)|browser)/")


def missing_needs(
    container: Container, app: FastAPI, needs: Sequence[str], operations: Sequence[str]
) -> tuple[Missing, ...]:
    """A step runs only when every service and route it touches is bound; an unknown name is a harness bug."""
    from fastapi.routing import iter_route_contexts

    from meridian.web.container import ContainerError, Key

    found: list[Missing] = []
    for name in needs:
        if name not in NEED_OWNERS:
            raise KeyError(f"unknown need {name!r}: add it to NEED_OWNERS (a follow-up on AEA-57)")
        try:
            container.get(Key[object](name))
        except ContainerError as exc:
            if str(exc) != f"not provided: {name}":
                raise
            found.append(Missing(f"{name} not bound", NEED_OWNERS[name]))
    routed = {getattr(ctx, "operation_id", None) for ctx in iter_route_contexts(app.router.routes)}
    for op in operations:
        if op not in OPERATION_OWNERS:
            raise KeyError(f"unknown operation {op!r}: add it to OPERATION_OWNERS (a follow-up on AEA-57)")
        if op not in routed:
            found.append(Missing(f"operation {op} not routed", OPERATION_OWNERS[op]))
    return tuple(found)


def owners_of(missing: Sequence[Missing]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(m.owner for m in missing))


def blocked_message(missing: Sequence[Missing]) -> str:
    return f"blocked-on {', '.join(owners_of(missing))}: {'; '.join(m.what for m in missing)}"


def stop_blocked(missing: Sequence[Missing], *, strict: bool) -> NoReturn:
    message = blocked_message(missing)
    if strict:
        pytest.fail(message + " [--journeys-strict]", pytrace=False)
    pytest.skip(message)


def convention_violations(root: Path) -> list[str]:
    """Journey files are tests/journeys/j<N>/test_aea_<NN>.py with N in 1..10."""
    found: list[str] = []
    base = root / "tests" / "journeys"
    for folder in sorted(base.iterdir()) if base.is_dir() else []:
        if not folder.is_dir() or not folder.name.startswith("j") or folder.name == "__pycache__":
            continue
        if not re.fullmatch(r"j([1-9]|10)", folder.name):
            found.append(f"{folder.name}: not j1…j10")
        for file in sorted(folder.glob("*.py")):
            if file.name != "__init__.py" and not re.fullmatch(r"test_aea_\d{2}\.py", file.name):
                found.append(f"{folder.name}/{file.name}: not test_aea_<NN>.py")
    return sorted(found)
