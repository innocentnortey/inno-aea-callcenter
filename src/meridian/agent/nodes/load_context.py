"""load_context: the first node of every turn (graph-nodes §9.2; DO-3 §5.3–§5.4).

Rebuilds the DB-authority keys from the working copy in one read-only unit of work: settled, controller, identity,
the chat window (Limits.context) and the timeouts counter. Writes nothing, calls no model, service or trace sink;
its span comes from timed_node (graph-core §4). Owner: AEA-34.
"""

from __future__ import annotations

from langgraph.runtime import Runtime

from meridian.agent.context import GraphDeps
from meridian.domain.state import ChatLine, Controller, ConversationState, LoadContextUpdate
from meridian.domain.turn import TurnContext

__all__ = ["load_context"]

_ELLIPSIS = "…"


def load_context(
    state: ConversationState, runtime: Runtime[TurnContext], *, deps: GraphDeps
) -> LoadContextUpdate:
    ctx = runtime.context
    thread_id = ctx.ids.thread_id
    if state.thread_id != thread_id:
        raise ValueError("state and turn context disagree on the thread")

    lim = deps.limits.context
    with deps.uow(write=False) as tx:
        settled = tx.core.settled_for(thread_id, ctx.now)
        row = tx.core.conversations.lookup(thread_id)
        identity = tx.core.reads.identity_state(thread_id)
        lines = [
            ChatLine(
                speaker=m.role, text=_cut_line(m.text, lim.window_line_chars), turn_id=m.turn_id, at=m.at
            )
            for m in tx.core.messages.recent(thread_id, turns=lim.window_turns)
        ]
        timeouts = tx.core.turns.timeouts_for(thread_id)
    stored = getattr(row, "controller", None)
    controller = stored if isinstance(stored, Controller) else Controller(kind="ai")
    window = _fit_total(lines, lim.window_total_chars)
    counters = state.counters.model_copy(update={"timeouts": timeouts})
    return {
        "settled": settled,
        "controller": controller,
        "identity": identity,
        "chat_window": window,
        "counters": counters,
    }


def _cut_line(text: str, limit: int) -> str:
    """One stored line cut to `limit` characters, the last being "…" (PD-1)."""
    if limit < 1:
        raise ValueError("window_line_chars must be at least 1")
    if len(text) <= limit:
        return text
    return text[: limit - 1] + _ELLIPSIS


def _fit_total(lines: list[ChatLine], limit: int) -> list[ChatLine]:
    """Drop the oldest lines until the window's characters fit `limit` (graph-core §7; PD-6)."""
    size = sum(len(line.text) for line in lines)
    start = 0
    while start < len(lines) and size > limit:
        size -= len(lines[start].text)
        start += 1
    return lines[start:]
