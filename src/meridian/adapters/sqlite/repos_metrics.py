"""Read-only facts for the CON-18…CON-20 reads (AEA-53; stage7/cases.md section 9). Plain queries over stored rows.

MetricsReader counts and divides these facts. Nothing here decides an outcome, applies a rule or writes a row.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import datetime
from typing import Literal

from meridian.adapters.sqlite.db import parse_wall
from meridian.domain.common import MeridianModel

ConversationTag = Literal["live", "eval", "load", "seed"]
_TAGS: frozenset[str] = frozenset({"live", "eval", "load", "seed"})


class ConversationFact(MeridianModel):
    thread_id: str
    run_tag: ConversationTag
    outcome: Literal["ai_resolved", "handed_off", "safety_reply", "abandoned", "open"]
    topics: tuple[str, ...]  # distinct non-null turns.plan_topic of this thread, sorted
    flag_count: int  # flags rows whose case_ref names a case on this thread


class TurnFact(MeridianModel):
    status: Literal["running", "completed", "failed"]
    outcome: str | None
    degrade_reason: str | None
    server_ms: int | None
    trace_export: Literal["off", "sent", "failed"] | None


class CaseFact(MeridianModel):
    case_ref: str
    thread_id: str
    thread_run_tag: ConversationTag
    reason: str
    safety_kind: str | None
    lifecycle: str
    seed: bool


class PromiseFact(MeridianModel):
    promise_id: int
    case_ref: str
    status: Literal["open", "kept", "missed", "changed"]
    due_at: datetime | None


def _marks(run_tags: Sequence[str]) -> str:
    if not run_tags or any(tag not in _TAGS for tag in run_tags):
        raise ValueError("run_tags must be a non-empty subset of live, eval, load, seed")
    return ",".join("?" for _ in run_tags)


class MetricsRepo:
    """= tx.ops.metrics. Every query is a SELECT; the connection is the unit of work's."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def conversations(self, run_tags: Sequence[ConversationTag]) -> tuple[ConversationFact, ...]:
        marks = _marks(run_tags)
        rows = self._conn.execute(
            f"SELECT thread_id, run_tag, outcome FROM conversations WHERE run_tag IN ({marks}) "  # noqa: S608 - placeholders only
            "ORDER BY started_at, thread_id",
            tuple(run_tags),
        ).fetchall()
        topics: dict[str, list[str]] = {}
        for thread_id, topic in self._conn.execute(
            "SELECT DISTINCT thread_id, plan_topic FROM turns WHERE plan_topic IS NOT NULL "
            "ORDER BY thread_id, plan_topic"
        ):
            topics.setdefault(str(thread_id), []).append(str(topic))
        flags = {
            str(thread_id): int(n)
            for thread_id, n in self._conn.execute(
                "SELECT k.thread_id, COUNT(f.id) FROM flags f JOIN cases k ON k.case_ref = f.case_ref "
                "GROUP BY k.thread_id"
            )
        }
        return tuple(
            ConversationFact.model_validate(
                {
                    "thread_id": r[0],
                    "run_tag": r[1],
                    "outcome": r[2],
                    "topics": tuple(topics.get(str(r[0]), ())),
                    "flag_count": flags.get(str(r[0]), 0),
                }
            )
            for r in rows
        )

    def live_turns(self) -> tuple[TurnFact, ...]:
        rows = self._conn.execute(
            "SELECT t.status, t.outcome, t.degrade_reason, t.server_ms, t.trace_export FROM turns t "
            "JOIN conversations c ON c.thread_id = t.thread_id "
            "WHERE t.run_tag = 'live' AND c.run_tag = 'live' ORDER BY t.rowid"
        ).fetchall()
        return tuple(
            TurnFact.model_validate(
                {
                    "status": r[0],
                    "outcome": r[1],
                    "degrade_reason": r[2],
                    "server_ms": r[3],
                    "trace_export": r[4],
                }
            )
            for r in rows
        )

    def cases(self, run_tags: Sequence[ConversationTag]) -> tuple[CaseFact, ...]:
        marks = _marks(run_tags)
        rows = self._conn.execute(
            "SELECT k.case_ref, k.thread_id, c.run_tag, k.reason, k.safety_kind, k.lifecycle, k.seed FROM cases k "  # noqa: S608 - placeholders only
            f"JOIN conversations c ON c.thread_id = k.thread_id WHERE c.run_tag IN ({marks}) "
            "ORDER BY k.case_ref",
            tuple(run_tags),
        ).fetchall()
        return tuple(
            CaseFact.model_validate(
                {
                    "case_ref": r[0],
                    "thread_id": r[1],
                    "thread_run_tag": r[2],
                    "reason": r[3],
                    "safety_kind": r[4],
                    "lifecycle": r[5],
                    "seed": bool(r[6]),
                }
            )
            for r in rows
        )

    def promises(self, run_tags: Sequence[ConversationTag]) -> tuple[PromiseFact, ...]:
        marks = _marks(run_tags)
        rows = self._conn.execute(
            "SELECT p.id, p.case_ref, p.status, p.due_at FROM promises p "  # noqa: S608 - placeholders only
            "JOIN cases k ON k.case_ref = p.case_ref JOIN conversations c ON c.thread_id = k.thread_id "
            f"WHERE c.run_tag IN ({marks}) "
            "ORDER BY p.due_at IS NULL, p.due_at, p.case_ref, p.id",
            tuple(run_tags),
        ).fetchall()
        return tuple(
            PromiseFact.model_validate(
                {
                    "promise_id": r[0],
                    "case_ref": r[1],
                    "status": r[2],
                    "due_at": parse_wall(r[3]) if r[3] is not None else None,
                }
            )
            for r in rows
        )
