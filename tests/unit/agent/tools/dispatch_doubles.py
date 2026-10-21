"""AEA-22 test doubles (frozen with the tests). Imports domain and port types only, never
`meridian.agent.tools.dispatch`, so this module imports cleanly before the implementation exists.

Private-looking values (card-like numbers, codes, phone numbers, foreign customer ids) are built at run time by
the makers below and never written as literals. Only the issued, fictional WP-2 identifiers appear as literals.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import sqlite3
from collections.abc import Iterator
from typing import Any, cast
from zoneinfo import ZoneInfo

from pydantic import Field, JsonValue

from meridian.domain.common import (
    CustomerId,
    InvoiceId,
    LLMFacing,
    RequestId,
    ThreadId,
    TurnId,
)
from meridian.domain.tools import (
    LookupEntry,
    ToolCallScope,
    ToolDef,
    ToolError,
    ToolKind,
    ToolResult,
)
from meridian.domain.turn import TurnIds

THREAD = "3f0c2a4e-8b1d-4c2e-9a6f-1b2c3d4e5f60"
TURN = "7a1d9c3b-2e4f-4a6b-8c0d-5e6f7a8b9c0d"
REQUEST = "9b2e4d6f-1a3c-4b5d-9e7f-0a1b2c3d4e5f"
OTHER_TURN = "c4d5e6f7-0a1b-4c2d-8e3f-4a5b6c7d8e9f"
MESSAGE_ID = 41

OPEN_KINDS = frozenset({ToolKind.KB_SEARCH, ToolKind.SLOT_SEARCH})
WRITE_KINDS = frozenset({ToolKind.BOOK, ToolKind.MOVE, ToolKind.CANCEL, ToolKind.CHANGE_REQUEST})


def make_ids() -> TurnIds:
    return TurnIds(
        thread_id=ThreadId(THREAD),
        turn_id=TurnId(TURN),
        request_id=RequestId(REQUEST),
        run_tag="live",
        run_id=None,
        agent_version="dev",
    )


def make_scope(customer_id: str | None) -> ToolCallScope:
    return ToolCallScope(
        ids=make_ids(),
        customer_id=CustomerId(customer_id) if customer_id else None,
        shown_slot_ids=frozenset(),
        now=dt.datetime(2026, 10, 15, 9, 0, tzinfo=ZoneInfo("America/Chicago")),
        message_id=MESSAGE_ID,
    )


# --- run-time makers for private-looking values ---------------------------------------------------------------
def foreign_customer_id() -> str:
    return "MHC-" + str(90000 + 9999)


def full_phone() -> str:
    return "-".join(("512", "555", str(1000 + 77)))


def card_like() -> str:
    return " ".join(["4000"] * 4)


def six_digit_code() -> str:
    return str(100000 + 48291)


def private_values() -> tuple[str, str, str, str]:
    return foreign_customer_id(), full_phone(), card_like(), six_digit_code()


# --- argument models --------------------------------------------------------------------------------------------
class EmptyArgs(LLMFacing):
    pass


class KbArgs(LLMFacing):
    query: str = Field(min_length=1, max_length=300)


class InvoiceArgs(LLMFacing):
    invoice_number: InvoiceId | None = None


class TitledArgs(LLMFacing):
    title: str


class NoteArgs(LLMFacing):
    note: str


class ScopeLeakCustomerArgs(LLMFacing):
    customer_id: str


class ScopeLeakMessageArgs(LLMFacing):
    message_id: int


class InnerSlots(LLMFacing):
    shown_slot_ids: list[int]


class ScopeLeakNestedArgs(LLMFacing):
    inner: InnerSlots


# --- recording unit of work -------------------------------------------------------------------------------------
class Recorder:
    def __init__(self) -> None:
        self.events: list[str] = []


class _LookupLog:
    def __init__(self, uow: RecordingUow) -> None:
        self._uow = uow

    def append(self, entry: LookupEntry) -> int:
        self._uow.append_count += 1
        n = self._uow.append_count
        if n in self._uow.fail_on_appends:
            raise sqlite3.OperationalError("database is locked " + card_like())
        self._uow.recorder.events.append("append")
        self._uow.appended.append(entry)
        row_id = 100 + n
        self._uow.returned_ids.append(row_id)
        return row_id


class _Core:
    def __init__(self, uow: RecordingUow) -> None:
        self.lookup_log = _LookupLog(uow)


class _Tx:
    def __init__(self, uow: RecordingUow) -> None:
        self.core = _Core(uow)
        self._uow = uow

    def commit(self) -> None:
        self._uow.recorder.events.append("commit")


class RecordingUow:
    """Stands in for `UnitOfWorkFactory` (DO-4 section 13; cases.md 1.0): a callable returning a context manager."""

    def __init__(
        self, recorder: Recorder | None = None, fail_on_appends: frozenset[int] = frozenset()
    ) -> None:
        self.recorder = recorder if recorder is not None else Recorder()
        self.fail_on_appends = fail_on_appends
        self.append_count = 0
        self.depth = 0
        self.appended: list[LookupEntry] = []
        self.returned_ids: list[int] = []

    @contextlib.contextmanager
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> Iterator[_Tx]:
        self.recorder.events.append("enter:write" if write else "enter:read")
        self.depth += 1
        try:
            yield _Tx(self)
        finally:
            self.depth -= 1
            self.recorder.events.append("exit")


# --- executor doubles -------------------------------------------------------------------------------------------
class ExecutorDouble:
    """An executor the owning area would supply. Records every call.

    Its returned `lookup` entry carries `message_id=0` and a different turn id, so a test can prove dispatch stamps
    the scope's ids. When `lookup_written` is set it stands in for the scheduling service: it writes its own row
    through the same unit of work (stamped with the scope's ids, as the real service does) and commits.
    """

    def __init__(
        self,
        name: str,
        recorder: Recorder,
        uow: RecordingUow | None = None,
        *,
        for_model: ToolError | JsonValue = None,
        record_ids: tuple[str, ...] = (),
        passage_ids: tuple[Any, ...] = (),
        result_seen: str = "ok",
        lookup_written: bool = False,
        raises: BaseException | None = None,
        returns_raw: object | None = None,
        unrenderable: bool = False,
    ) -> None:
        self.name = name
        self.recorder = recorder
        self.uow = uow
        self.for_model: ToolError | JsonValue = {"ok": True} if for_model is None else for_model
        self.record_ids = record_ids
        self.passage_ids = passage_ids
        self.result_seen = result_seen
        self.lookup_written = lookup_written
        self.raises = raises
        self.returns_raw = returns_raw
        self.unrenderable = unrenderable
        self.calls: list[tuple[LLMFacing, ToolCallScope]] = []
        self.depths: list[int] = []

    def __call__(self, args: LLMFacing, scope: ToolCallScope) -> ToolResult:
        self.recorder.events.append(f"execute:{self.name}")
        self.calls.append((args, scope))
        if self.uow is not None:
            self.depths.append(self.uow.depth)
        if self.raises is not None:
            raise self.raises
        if self.returns_raw is not None:
            return self.returns_raw  # type: ignore[return-value]
        if self.lookup_written:
            entry = LookupEntry(
                tool=self.name,
                record_ids=self.record_ids,
                passage_ids=self.passage_ids,
                result_seen=self.result_seen,
                message_id=scope.message_id,
                turn_id=scope.ids.turn_id,
            )
            assert self.uow is not None, "lookup_written needs a uow"
            with self.uow(write=True) as tx:
                tx.core.lookup_log.append(entry)
                tx.commit()
        else:
            entry = LookupEntry(
                tool=self.name,
                record_ids=self.record_ids,
                passage_ids=self.passage_ids,
                result_seen=self.result_seen,
                message_id=0,
                turn_id=TurnId(OTHER_TURN),
            )
        if self.unrenderable:
            return ToolResult.model_construct(
                ok=True,
                for_model=cast(Any, {"when": object()}),
                captured=None,
                lookup=entry,
                lookup_written=self.lookup_written,
            )
        return ToolResult(
            ok=not isinstance(self.for_model, ToolError),
            for_model=self.for_model,
            captured=None,
            lookup=entry,
            lookup_written=self.lookup_written,
        )


def make_def(
    name: str,
    kind: ToolKind,
    args_model: type[LLMFacing],
    executor: ExecutorDouble,
    *,
    requires_verified: bool | None = None,
    effect: str | None = None,
) -> ToolDef:
    return ToolDef(
        name=name,
        description=f"Test tool {name}. Returns test data. Do not use for real requests.",
        args_model=args_model,
        kind=kind,
        effect="write" if (effect == "write" or (effect is None and kind in WRITE_KINDS)) else "read",
        requires_verified=(kind not in OPEN_KINDS) if requires_verified is None else requires_verified,
        executor=executor,
    )


class Boom(RuntimeError):
    """The failing executor's exception; its message holds private-looking values."""

    def __init__(self) -> None:
        super().__init__(f"failed for {card_like()} {full_phone()}")


# --- WP-2 (ticket text; amounts in integer cents) ---------------------------------------------------------------
WP2_INVOICE_FOR_MODEL: dict[str, JsonValue] = {
    "invoices": [
        {
            "invoice_id": "INV-204411",
            "issued_on": "2026-10-02",
            "due_on": "2026-11-01",
            "paid": False,
            "total_cents": 47800,
            "balance_cents": 47800,
            "lines": [
                {"description": "Diagnostic visit", "amount_cents": 8900},
                {"description": "Contactor replacement", "amount_cents": 24500},
                {"description": "After-hours dispatch", "amount_cents": 14400},
            ],
        }
    ]
}
WP2_SNAPSHOT = "INV-204411 issued 2026-10-02 due 2026-11-01 total 47800 balance 47800 unpaid"

_NO_RECURSE = frozenset({"default", "examples", "const", "enum"})


def strip_titles(node: Any) -> Any:
    """Remove schema-level `title` strings only; property and definition names are kept (plan step 2.2)."""
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for key, value in node.items():
            if key == "title" and isinstance(value, str):
                continue
            if key in ("properties", "$defs") and isinstance(value, dict):
                out[key] = {n: strip_titles(sub) for n, sub in value.items()}
            elif key in _NO_RECURSE:
                out[key] = value
            else:
                out[key] = strip_titles(value)
        return out
    if isinstance(node, list):
        return [strip_titles(v) for v in node]
    return node


def property_names(schema: Any) -> set[str]:
    """Every key of every `properties` dict at any depth."""
    names: set[str] = set()
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key == "properties" and isinstance(value, dict):
                names.update(value.keys())
            names |= property_names(value)
    elif isinstance(schema, list):
        for item in schema:
            names |= property_names(item)
    return names
