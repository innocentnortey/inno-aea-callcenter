"""Runtime ports: retrieval, clock, trace sink and unit of work (AEA-02; DO-4 section 13, models.md 4).

`RetrievalResult` (defined in `domain.records`), `ExportStatus` and `SpanHandle` (defined in `domain.turn`) are
re-exported here (plan 4.0). The unit of work's attributes are typed against the repository shells under
TYPE_CHECKING only: this module imports no adapter at run time.
"""

from __future__ import annotations

import datetime as dt
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Literal, Protocol

from meridian.domain.common import CallRecord, MeridianModel
from meridian.domain.records import Passage as Passage
from meridian.domain.records import RetrievalResult as RetrievalResult
from meridian.domain.turn import ExportStatus as ExportStatus
from meridian.domain.turn import SpanHandle as SpanHandle
from meridian.domain.turn import TurnIds as TurnIds

if TYPE_CHECKING:
    from meridian.adapters.sqlite.repos_booking import BookingRepos
    from meridian.adapters.sqlite.repos_cases import CaseRepos
    from meridian.adapters.sqlite.repos_core import CoreRepos
    from meridian.adapters.sqlite.repos_identity import IdentityRepos
    from meridian.adapters.sqlite.repos_ops import OpsRepos
    from meridian.adapters.sqlite.repos_spend import SpendRepo
    from meridian.adapters.sqlite.repos_staff import StaffRepos


class IndexInfo(MeridianModel):
    embedding_model: Literal["BAAI/bge-small-en-v1.5"]
    dimension: int
    chunks: int
    manifest_hash: str
    files: int


class RetrievalIndex(Protocol):
    def search(self, query: str, *, k: int, min_score: float) -> RetrievalResult: ...

    def info(self) -> IndexInfo: ...


class Clock(Protocol):
    def now(self) -> dt.datetime: ...


class TraceSink(Protocol):
    def turn(self, ids: TurnIds) -> AbstractContextManager[SpanHandle]: ...

    def model_call(
        self, parent: SpanHandle, record: CallRecord, masked_input: str, masked_output: str
    ) -> None: ...

    def node(self, parent: SpanHandle, name: str, elapsed_ms: int, status: str) -> None: ...

    def export_status(self, turn: SpanHandle) -> ExportStatus: ...


class UnitOfWork(Protocol):
    core: CoreRepos
    spend: SpendRepo
    identity: IdentityRepos
    booking: BookingRepos
    cases: CaseRepos
    staff: StaffRepos
    ops: OpsRepos

    def commit(self) -> None: ...


class UnitOfWorkFactory(Protocol):
    def __call__(
        self, *, write: bool = False, exclusive: bool = False
    ) -> AbstractContextManager[UnitOfWork]: ...
