"""Live takeover (CON-14): a claiming representative joins, writes in, hands back or closes a live chat
(stage7/staff.md section 5; STF-11, STF-14, R-W-16). Each action is one write transaction and a refusal writes nothing.
Live actions never touch a case's lifecycle, version, owner or promise."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Literal
from zoneinfo import ZoneInfo

from pydantic import JsonValue

from meridian.adapters.sqlite.rows import (
    CaseEventRow,
    ConversationRow,
    StreamEvent,
    case_stream,
    thread_stream,
)
from meridian.domain.common import CaseRef, MeridianModel, ThreadId
from meridian.domain.staff import STAFF_PERSONAS, StaffActor
from meridian.domain.state import Controller
from meridian.policy.texts import TextId, render
from meridian.ports.runtime import Clock, UnitOfWork, UnitOfWorkFactory

LiveAction = Literal["join", "send", "hand_back", "close"]
LiveStateName = Literal["not_live", "queued", "joined", "handed_back", "closed"]
WIRE_ZONE: Final = ZoneInfo("America/Chicago")  # details times only (claimed_at)
EVENT_SPEAKER: Final[Mapping[str, JsonValue]] = {"kind": "event", "display_name": None}
_END_STATE: Final[Mapping[str, str]] = {"hand_back": "handed_back", "close": "closed"}
CASE_EVENT_KIND: Final[Mapping[str, str]] = {
    "join": "live_join",
    "send": "live_send",
    "hand_back": "live_hand_back",
    "close": "live_close",
}


class StoredChatLine(MeridianModel):
    """Serialises to the OpenAPI ChatLine (speaker kind "representative")."""

    message_id: str
    speaker_name: str
    at: datetime
    text: str


class LiveView(MeridianModel):
    """Serialises to the OpenAPI LiveActionResponse."""

    controller_kind: Literal["ai", "human"]
    controller_name: str | None
    state: LiveStateName
    since: datetime | None
    message: StoredChatLine | None = None


class LiveRefused(MeridianModel):
    code: Literal["CASE_NOT_FOUND", "NOT_CLAIMED_BY_YOU", "CASE_ALREADY_CLAIMED", "NOT_LIVE"]
    details: dict[str, str | None]


@dataclass(frozen=True)
class _Checked:
    """What a passing check hands to the write step."""

    case_ref: CaseRef
    thread_id: ThreadId
    conversation: ConversationRow


def _wire(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(WIRE_ZONE).isoformat()


def _view(conv: ConversationRow) -> LiveView:
    return LiveView(
        controller_kind=conv.controller.kind,
        controller_name=conv.controller.representative_name if conv.controller.kind == "human" else None,
        state=conv.live_state,
        since=conv.live_since,
    )


def _refused(
    code: Literal["CASE_NOT_FOUND", "NOT_CLAIMED_BY_YOU", "CASE_ALREADY_CLAIMED", "NOT_LIVE"],
    **details: str | None,
) -> LiveRefused:
    return LiveRefused(code=code, details=dict(details))


class LiveChatService:
    def __init__(self, uow: UnitOfWorkFactory, demo_clock: Clock, redact_store: Callable[[str], str]) -> None:
        self._uow = uow
        self._clock = demo_clock
        self._redact_store = redact_store

    def join(self, case_ref: CaseRef, actor: StaffActor) -> LiveView | LiveRefused:
        return self._run("join", case_ref, actor, None)

    def send(self, case_ref: CaseRef, text: str, actor: StaffActor) -> LiveView | LiveRefused:
        return self._run("send", case_ref, actor, text)

    def hand_back(self, case_ref: CaseRef, actor: StaffActor) -> LiveView | LiveRefused:
        return self._run("hand_back", case_ref, actor, None)

    def close(self, case_ref: CaseRef, actor: StaffActor) -> LiveView | LiveRefused:
        return self._run("close", case_ref, actor, None)

    def _run(
        self, action: LiveAction, case_ref: CaseRef, actor: StaffActor, text: str | None
    ) -> LiveView | LiveRefused:
        with self._uow(write=True) as tx:  # BEGIN IMMEDIATE: two staff acting at once are serialised
            checked = self._check(tx, action, case_ref, actor)
            if isinstance(checked, (LiveRefused, LiveView)):
                return checked  # no commit: the block exit rolls back; a refusal or repeat writes nothing
            now = self._clock.now()  # the only clock read
            view = self._write(tx, action, checked, actor, text, now)
            tx.commit()
            return view

    def _check(
        self, tx: UnitOfWork, action: LiveAction, case_ref: CaseRef, actor: StaffActor
    ) -> LiveRefused | LiveView | _Checked:
        owner = tx.core.cases_ro.owner(case_ref)
        if owner is None:
            return _refused("CASE_NOT_FOUND", reference=str(case_ref))
        if action == "join":
            if owner.owner_role is None:
                return _refused("NOT_CLAIMED_BY_YOU", owner=None)
            if not actor.owns(owner.owner_role):
                return _refused(
                    "CASE_ALREADY_CLAIMED",
                    claimed_by=STAFF_PERSONAS[owner.owner_role].name,
                    claimed_at=_wire(owner.owner_since),
                )
        elif not actor.owns(owner.owner_role):
            return _refused(
                "NOT_CLAIMED_BY_YOU",
                owner=None if owner.owner_role is None else STAFF_PERSONAS[owner.owner_role].name,
            )
        conv = tx.core.conversations.lookup(str(owner.thread_id))
        if not isinstance(conv, ConversationRow):  # row 5, defensive (MC-25)
            return _refused("NOT_LIVE", reason="demo_reset")
        state = conv.live_state
        if action == "join":
            if state == "joined":
                return _view(conv)
            if state != "queued":
                return _refused("NOT_LIVE", reason="not_waiting")
        elif state != "joined":
            if _END_STATE.get(action) == state:
                return _view(conv)
            return _refused("NOT_LIVE", reason="chat_closed" if state == "closed" else "not_joined")
        return _Checked(case_ref, owner.thread_id, conv)

    def _write(
        self,
        tx: UnitOfWork,
        action: LiveAction,
        c: _Checked,
        actor: StaffActor,
        text: str | None,
        now: datetime,
    ) -> LiveView:
        name = actor.name
        thread = thread_stream(c.thread_id)
        case = case_stream(c.case_ref)
        detail: dict[str, JsonValue] = {"action": action}
        events = tx.core.events
        rep_speaker: dict[str, JsonValue] = {"kind": "representative", "display_name": name}
        if action == "join":
            tx.core.conversations.set_controller(
                c.thread_id,
                Controller(kind="human", representative_name=name, case_ref=c.case_ref),
                live_state="joined",
                live_since=now,
            )
            joined_line = render(TextId.REP_JOINED, rep_name=name)
            events.append(
                thread,
                StreamEvent(
                    type="representative_joined",
                    payload={"speaker": rep_speaker, "display_name": name, "line": joined_line},
                    at=now,
                ),
            )
            events.append(
                thread,
                StreamEvent(
                    type="ai_paused",
                    payload={"speaker": dict(EVENT_SPEAKER), "line": render(TextId.AI_PAUSED, rep_name=name)},
                    at=now,
                ),
            )
            events.append(
                case,
                StreamEvent(
                    type="controller_changed",
                    payload={"controller": {"kind": "human", "display_name": name}, "line": joined_line},
                    at=now,
                ),
            )
            view = LiveView(controller_kind="human", controller_name=name, state="joined", since=now)
        elif action == "send":
            if text is None:
                raise ValueError("send needs text")
            stored = self._redact_store(text)
            mid = tx.core.messages.append(c.thread_id, "representative", stored, now)
            events.append(
                thread,
                StreamEvent(
                    type="staff_message",
                    payload={"speaker": rep_speaker, "message_id": str(mid), "text": stored},
                    at=now,
                ),
            )
            detail["message_id"] = str(mid)
            view = LiveView(
                controller_kind="human",
                controller_name=c.conversation.controller.representative_name or name,
                state="joined",
                since=c.conversation.live_since,
                message=StoredChatLine(message_id=str(mid), speaker_name=name, at=now, text=stored),
            )
        elif action == "hand_back":
            tx.core.conversations.set_controller(
                c.thread_id, Controller(kind="ai"), live_state="handed_back", live_since=now
            )
            line = render(TextId.AI_RESUMED, rep_name=name)
            events.append(
                thread,
                StreamEvent(
                    type="ai_resumed", payload={"speaker": dict(EVENT_SPEAKER), "line": line}, at=now
                ),
            )
            events.append(
                case,
                StreamEvent(
                    type="controller_changed",
                    payload={"controller": {"kind": "ai", "display_name": None}, "line": line},
                    at=now,
                ),
            )
            view = LiveView(controller_kind="ai", controller_name=None, state="handed_back", since=now)
        else:
            tx.core.conversations.set_controller(
                c.thread_id, Controller(kind="ai"), live_state="closed", live_since=now
            )
            events.append(
                thread,
                StreamEvent(
                    type="chat_closed",
                    payload={
                        "speaker": dict(EVENT_SPEAKER),
                        "line": render(TextId.CHAT_CLOSED, rep_name=name),
                        "composer_disabled": True,
                    },
                    at=now,
                ),
            )
            events.append(
                case, StreamEvent(type="chat_closed", payload={"reason": "closed_by_staff"}, at=now)
            )
            view = LiveView(controller_kind="ai", controller_name=None, state="closed", since=now)
        tx.cases.case_events.append(
            CaseEventRow.model_validate(
                {
                    "case_ref": c.case_ref,
                    "kind": CASE_EVENT_KIND[action],
                    "actor_role": actor.role.value,
                    "detail": detail,
                    "at": now,
                }
            )
        )
        return view
