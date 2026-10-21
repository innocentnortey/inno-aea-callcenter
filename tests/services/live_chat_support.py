"""AEA-46 test support: synthetic seed rows for a live-queued case, a snapshot of everything a live action may
write, and a stand-in for AEA-40's relayed customer message. Not a conftest; other tickets may import it read-only."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from datetime import datetime

from pydantic import JsonValue

from meridian.adapters.sqlite.rows import (
    CaseRow,
    ConversationRow,
    StreamEvent,
    case_stream,
    thread_stream,
)
from meridian.domain.common import CaseRef, HandoffReason, Priority, Promise, ThreadId
from meridian.domain.staff import CUSTOMER_SPEAKER_NAME, StaffActor, StaffRole, actor_for
from meridian.domain.state import Controller
from meridian.ports.runtime import UnitOfWorkFactory
from meridian.privacy.redact import RedactionProfile, redact
from meridian.services.live_chat import LiveChatService
from tests.fakes.clock import CHICAGO, FixedClock

WP2_REF = CaseRef("MHC-C-0007")  # WP-2, Omar Patel's case in the worked pair
SECOND_REF = CaseRef("MHC-C-0011")  # a second synthetic case (two-case sequences)
UNKNOWN_REF = CaseRef("MHC-C-0099")  # the OpenAPI CASE_NOT_FOUND example
WP2_CUSTOMER = "MHC-10002"  # issued, fictional (worked-pairs.md WP-2)
QUEUED_AT = datetime(2026, 10, 16, 14, 20, tzinfo=CHICAGO)  # case claimed and queued
JOIN_AT = datetime(
    2026, 10, 16, 14, 22, tzinfo=CHICAGO
)  # OpenAPI JOINED example time; the FixedClock for actions
STAFF_TEXT = "Hi Omar, I can look at the after-hours charge with you."
CUSTOMER_REPLY = "Thanks, that helps."
EVENT_SPEAKER: dict[str, JsonValue] = {"kind": "event", "display_name": None}
RILEY: StaffActor = actor_for(StaffRole.REPRESENTATIVE)
SUPERVISOR: StaffActor = actor_for(StaffRole.SUPERVISOR)


def store_redactor(text: str) -> str:
    """The container's binding (MC-23)."""
    return redact(text, RedactionProfile.STORE).text


def new_service(uow: UnitOfWorkFactory, at: datetime = JOIN_AT) -> LiveChatService:
    return LiveChatService(uow, FixedClock(at), store_redactor)


@dataclass(frozen=True)
class SeededCase:
    case_ref: CaseRef
    thread_id: ThreadId
    version: int


def seed_live_case(
    uow: UnitOfWorkFactory,
    *,
    case_ref: CaseRef = WP2_REF,
    owner_role: StaffRole | None = StaffRole.REPRESENTATIVE,
    live_state: str = "queued",
    lifecycle: str = "claimed",
    version: int = 1,
    session_id: str = "seed-session",
) -> SeededCase:
    tid = ThreadId(str(uuid.uuid4()))
    controller = (
        Controller(kind="human", representative_name="Riley", case_ref=case_ref)
        if live_state == "joined"
        else Controller(kind="ai")
    )
    with uow(write=True) as tx:
        tx.core.conversations.insert(
            ConversationRow.model_validate(
                {
                    "thread_id": tid,
                    "demo_session": session_id,
                    "run_tag": "live",
                    "agent_version": "test-agent-0",
                    "started_at": QUEUED_AT,
                    "live_state": live_state,
                    "live_since": None if live_state == "not_live" else QUEUED_AT,
                    "controller": controller,
                }
            )
        )
        tx.core.messages.append(tid, "assistant", "Hi, I'm Meridian's automated assistant.", QUEUED_AT)
        tx.core.messages.append(
            tid, "customer", "Can I talk to a person about the after-hours charge?", QUEUED_AT
        )
        tx.cases.cases.insert(
            CaseRow.model_validate(
                {
                    "case_ref": case_ref,
                    "thread_id": tid,
                    "customer_id": WP2_CUSTOMER,
                    "reason": HandoffReason.BILLING_DISPUTE,
                    "priority": Priority.P2,
                    "rule_id": "R-test",
                    "trigger": "customer_requested",
                    "lifecycle": lifecycle,
                    "owner_role": owner_role,
                    "owner_since": QUEUED_AT if owner_role else None,
                    "version": version,
                    "created_at": QUEUED_AT,
                    "updated_at": QUEUED_AT,
                }
            )
        )
        tx.cases.promises.insert(
            case_ref,
            Promise(
                policy_row="P-test",
                text="A representative will join this chat shortly.",
                due_at=None,
                due_label=None,
                live_queued=True,
            ),
            QUEUED_AT,
        )
        tx.commit()
    return SeededCase(case_ref, tid, version)


def snapshot(uow: UnitOfWorkFactory, seeded: SeededCase) -> dict[str, object]:
    """Everything a live action may write, as plain dumps."""
    tid, ref = seeded.thread_id, seeded.case_ref
    with uow(write=False) as tx:
        conv = tx.core.conversations.lookup(str(tid))
        case = tx.cases.cases.get(ref)
        return {
            "conversation": conv.model_dump(mode="json") if isinstance(conv, ConversationRow) else repr(conv),
            "messages": [m.model_dump(mode="json") for m in tx.core.messages.all_for_thread(tid)],
            "thread_events": [e.model_dump(mode="json") for e in tx.core.events.after(thread_stream(tid), 0)],
            "case_stream": [e.model_dump(mode="json") for e in tx.core.events.after(case_stream(ref), 0)],
            "case_events": [e.model_dump(mode="json") for e in tx.cases.case_events.list_for_case(ref)],
            "case": None if case is None else case.model_dump(mode="json"),
            "promises": [p.model_dump(mode="json") for p in tx.cases.promises.history(ref)],
        }


def invariant_holds(uow: UnitOfWorkFactory, seeded: SeededCase) -> bool:
    """controller is human exactly when live_state is joined."""
    with uow(write=False) as tx:
        conv = tx.core.conversations.lookup(str(seeded.thread_id))
    assert isinstance(conv, ConversationRow)
    return (conv.controller.kind == "human") == (conv.live_state == "joined")


def append_customer_reply(uow: UnitOfWorkFactory, seeded: SeededCase, text: str, at: datetime) -> int:
    """A stand-in for AEA-40 TurnService step 4 (web.md section 9) until it merges."""
    with uow(write=True) as tx:
        mid = tx.core.messages.append(seeded.thread_id, "customer", text, at)
        tx.core.events.append(
            case_stream(seeded.case_ref),
            StreamEvent(
                type="customer_message",
                payload={
                    "message": {
                        "message_id": str(mid),
                        "speaker": {"kind": "customer", "display_name": CUSTOMER_SPEAKER_NAME},
                        "at": at.isoformat(),
                        "text": text,
                    }
                },
                at=at,
            ),
        )
        tx.commit()
    return int(mid)


def card_like_and_code(seed: int = 46) -> tuple[str, str]:
    """A 16-digit card-like string grouped in fours and a 6-digit code, built at run time (no digit literal in tests)."""
    rng = random.Random(seed)
    digits = "".join(str(rng.randint(0, 9)) for _ in range(16))
    card = " ".join(digits[i : i + 4] for i in range(0, 16, 4))
    return card, str(rng.randint(100000, 999999))
