"""AEA-02 AC-16: minimal in-test stubs satisfy every port. The proof is the type check (`uv run mypy`) over this file."""

from __future__ import annotations

import datetime as dt
from collections.abc import Sequence
from contextlib import AbstractContextManager, nullcontext
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel

from meridian.domain.common import ProviderName
from meridian.domain.records import RetrievalResult
from meridian.ports.models import (
    Attempt,
    CallRecord,
    ChoiceAnswer,
    ChoiceModel,
    ChoiceRequest,
    ProviderMessages,
    StructuredModel,
    StructuredRequest,
    ToolCallingModel,
    ToolStep,
    ToolStepRequest,
    ToolTranscript,
)
from meridian.ports.runtime import (
    Clock,
    ExportStatus,
    IndexInfo,
    RetrievalIndex,
    SpanHandle,
    TraceSink,
    TurnIds,
    UnitOfWork,
    UnitOfWorkFactory,
)

if TYPE_CHECKING:
    from meridian.adapters.sqlite.repos_booking import BookingRepos
    from meridian.adapters.sqlite.repos_cases import CaseRepos
    from meridian.adapters.sqlite.repos_core import CoreRepos
    from meridian.adapters.sqlite.repos_identity import IdentityRepos
    from meridian.adapters.sqlite.repos_ops import OpsRepos
    from meridian.adapters.sqlite.repos_spend import SpendRepo
    from meridian.adapters.sqlite.repos_staff import StaffRepos


class _Choice:
    provider: ClassVar[ProviderName] = "openrouter_jev"

    def choose(self, req: ChoiceRequest, *, timeout_s: float) -> Attempt[ChoiceAnswer]:
        raise NotImplementedError


class _Structured:
    provider: ClassVar[ProviderName] = "anthropic"

    def structured[T: BaseModel](self, req: StructuredRequest[T], *, timeout_s: float) -> Attempt[T]:
        raise NotImplementedError


class _Tools:
    provider: ClassVar[ProviderName] = "anthropic"

    def start(self, user: str) -> ProviderMessages:
        raise NotImplementedError

    def tool_step(self, req: ToolStepRequest, *, timeout_s: float) -> Attempt[ToolStep]:
        raise NotImplementedError

    def append(
        self, messages: ProviderMessages, step: ToolStep, results: Sequence[tuple[str, str]]
    ) -> ProviderMessages:
        raise NotImplementedError


class _Transcript:
    def start(self, user: str) -> ProviderMessages:
        raise NotImplementedError

    def append(
        self, messages: ProviderMessages, step: ToolStep, results: Sequence[tuple[str, str]]
    ) -> ProviderMessages:
        raise NotImplementedError


class _Sink:
    def turn(self, ids: TurnIds) -> AbstractContextManager[SpanHandle]:
        raise NotImplementedError

    def model_call(
        self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str
    ) -> None:
        raise NotImplementedError

    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None:
        raise NotImplementedError

    def export_status(self, turn: SpanHandle) -> ExportStatus:
        return "off"


class _Index:
    def search(self, query: str, *, k: int, min_score: float) -> RetrievalResult:
        return RetrievalResult(passages=(), below_floor=True)

    def info(self) -> IndexInfo:
        raise NotImplementedError


class _Clock:
    def now(self) -> dt.datetime:
        return dt.datetime(2026, 10, 16, 10, 0, tzinfo=dt.UTC)


class _Uow:
    core: CoreRepos
    spend: SpendRepo
    identity: IdentityRepos
    booking: BookingRepos
    cases: CaseRepos
    staff: StaffRepos
    ops: OpsRepos

    def commit(self) -> None:
        return None


class _Factory:
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> AbstractContextManager[UnitOfWork]:
        return nullcontext(_Uow())


choice: ChoiceModel = _Choice()
structured: StructuredModel = _Structured()
tools: ToolCallingModel = _Tools()
transcript: ToolTranscript = _Transcript()
sink: TraceSink = _Sink()
index: RetrievalIndex = _Index()
clock: Clock = _Clock()
uow: UnitOfWork = _Uow()
factory: UnitOfWorkFactory = _Factory()


def test_stubs_satisfy_ports() -> None:
    assert all(
        obj is not None for obj in (choice, structured, tools, transcript, sink, index, clock, uow, factory)
    )
    assert _Choice.provider == "openrouter_jev"
    assert factory(write=True).__enter__() is not None
