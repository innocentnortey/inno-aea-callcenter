"""AEA-46 LiveChatService: AC-1 to AC-8 and AC-21 (staff.md section 5)."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from meridian.adapters.sqlite import repos_core_aux
from meridian.adapters.sqlite.rows import StreamEvent, case_stream, thread_stream
from meridian.domain.common import CaseRef
from meridian.domain.staff import DemoRole, StaffActor, StaffRole
from meridian.ports.runtime import UnitOfWorkFactory
from meridian.services.live_chat import LiveRefused, LiveView, StoredChatLine
from tests.api.staff_live_support import app_uow, live_url, staff_live_app
from tests.api.web_shell_support import FakeSessionStore, assert_matches, cookie_header, make_client
from tests.fixtures.sqlite import temp_sqlite
from tests.services.live_chat_support import (
    JOIN_AT,
    RILEY,
    SECOND_REF,
    STAFF_TEXT,
    SUPERVISOR,
    UNKNOWN_REF,
    WP2_REF,
    SeededCase,
    card_like_and_code,
    invariant_holds,
    new_service,
    seed_live_case,
    snapshot,
)


def _types(uow: UnitOfWorkFactory, stream: Any) -> list[str]:
    with uow(write=False) as tx:
        return [e.type for e in tx.core.events.after(stream, 0)]


def test_join_writes_one_transaction() -> None:
    """AC-1, PA-2: join writes controller, live state, three events and one case event; the case rows stay put."""
    with temp_sqlite() as db:
        seeded = seed_live_case(db.uow)
        before = snapshot(db.uow, seeded)
        view = new_service(db.uow).join(WP2_REF, RILEY)
        assert view == LiveView(
            controller_kind="human", controller_name="Riley", state="joined", since=JOIN_AT, message=None
        )
        after = snapshot(db.uow, seeded)
        conv: Any = after["conversation"]
        assert conv["controller"] == {
            "kind": "human",
            "representative_name": "Riley",
            "case_ref": str(WP2_REF),
        }
        assert conv["live_state"] == "joined"
        assert datetime.fromisoformat(conv["live_since"]) == JOIN_AT
        thread: Any = after["thread_events"]
        case: Any = after["case_stream"]
        assert [e["type"] for e in thread] == ["representative_joined", "ai_paused"]
        assert [e["type"] for e in case] == ["controller_changed"]
        ids = [e["id"] for e in thread] + [e["id"] for e in case]
        assert ids == sorted(ids) and len(set(ids)) == 3
        rows: Any = after["case_events"]
        assert len(rows) == 1
        assert (rows[0]["kind"], rows[0]["actor_role"], rows[0]["detail"]) == (
            "live_join",
            "representative",
            {"action": "join"},
        )
        assert after["case"] == before["case"]
        assert after["promises"] == before["promises"]
        print("join rows:", conv["live_state"], ids, rows[0]["kind"])


@pytest.mark.parametrize(
    ("seed_kwargs", "action", "expected"),
    [
        (None, "join", LiveRefused(code="CASE_NOT_FOUND", details={"reference": "MHC-C-0099"})),
        ({"owner_role": None}, "join", LiveRefused(code="NOT_CLAIMED_BY_YOU", details={"owner": None})),
        (
            {"owner_role": StaffRole.SUPERVISOR},
            "join",
            LiveRefused(
                code="CASE_ALREADY_CLAIMED",
                details={"claimed_by": "Demo supervisor", "claimed_at": "2026-10-16T14:20:00-05:00"},
            ),
        ),
        (
            {"owner_role": StaffRole.SUPERVISOR, "live_state": "joined"},
            "send",
            LiveRefused(code="NOT_CLAIMED_BY_YOU", details={"owner": "Demo supervisor"}),
        ),
        ({"live_state": "not_live"}, "join", LiveRefused(code="NOT_LIVE", details={"reason": "not_waiting"})),
        ({}, "send", LiveRefused(code="NOT_LIVE", details={"reason": "not_joined"})),
        ({"live_state": "closed"}, "send", LiveRefused(code="NOT_LIVE", details={"reason": "chat_closed"})),
    ],
)
def test_checks_in_order_write_nothing(
    seed_kwargs: dict[str, Any] | None, action: str, expected: LiveRefused
) -> None:
    """AC-2. Check 5 (conversation row missing) is defensive and untested (MC-25)."""
    with temp_sqlite() as db:
        seeded = seed_live_case(db.uow, **seed_kwargs) if seed_kwargs is not None else None
        ref = WP2_REF if seeded is not None else UNKNOWN_REF
        if seeded is None:
            seeded = seed_live_case(db.uow, case_ref=SECOND_REF)  # an unrelated case, to snapshot something
        before = snapshot(db.uow, seeded)
        svc = new_service(db.uow)
        result = svc.join(ref, RILEY) if action == "join" else svc.send(ref, "x", RILEY)
        assert result == expected
        assert snapshot(db.uow, seeded) == before


@pytest.mark.parametrize(
    ("live_state", "action", "state", "kind"),
    [
        ("joined", "join", "joined", "human"),
        ("handed_back", "hand_back", "handed_back", "ai"),
        ("closed", "close", "closed", "ai"),
    ],
)
def test_repeats_write_nothing(live_state: str, action: str, state: str, kind: str) -> None:
    """AC-3: a repeat answers the current view and writes nothing."""
    with temp_sqlite() as db:
        seeded = seed_live_case(db.uow, live_state=live_state)
        before = snapshot(db.uow, seeded)
        view = getattr(new_service(db.uow), action)(WP2_REF, RILEY)
        assert isinstance(view, LiveView)
        assert (view.state, view.controller_kind) == (state, kind)
        assert snapshot(db.uow, seeded) == before


def test_send_same_thread() -> None:
    """AC-4: the line lands in the customer's own thread, with the demo-clock time."""
    with temp_sqlite() as db:
        seeded = seed_live_case(db.uow)
        svc = new_service(db.uow)
        svc.join(WP2_REF, RILEY)
        view = svc.send(WP2_REF, STAFF_TEXT, RILEY)
        assert isinstance(view, LiveView)
        with db.uow(write=False) as tx:
            row = tx.core.messages.all_for_thread(seeded.thread_id)[-1]
            case_events = tx.cases.case_events.list_for_case(WP2_REF)
        assert (row.thread_id, row.role, row.text, row.at) == (
            seeded.thread_id,
            "representative",
            STAFF_TEXT,
            JOIN_AT,
        )
        assert view.message == StoredChatLine(
            message_id=str(row.id), speaker_name="Riley", at=JOIN_AT, text=STAFF_TEXT
        )
        assert "staff_message" in _types(db.uow, thread_stream(seeded.thread_id))
        assert (case_events[-1].kind, case_events[-1].detail["message_id"]) == ("live_send", str(row.id))


def test_hand_back_close_and_controller_invariant() -> None:
    """AC-5, PA-6: two cases, because close after hand_back is NOT_LIVE not_joined (spec table)."""
    with temp_sqlite() as db:
        a = seed_live_case(db.uow)
        b = seed_live_case(db.uow, case_ref=SECOND_REF)
        svc = new_service(db.uow)
        svc.join(WP2_REF, RILEY)
        assert invariant_holds(db.uow, a)
        svc.send(WP2_REF, STAFF_TEXT, RILEY)
        assert invariant_holds(db.uow, a)
        later = JOIN_AT + timedelta(minutes=1)
        view = new_service(db.uow, later).hand_back(WP2_REF, RILEY)
        assert isinstance(view, LiveView)
        assert (view.state, view.since, view.controller_kind) == ("handed_back", later, "ai")
        assert _types(db.uow, thread_stream(a.thread_id))[-1] == "ai_resumed"
        with db.uow(write=False) as tx:
            case_rows = tx.core.events.after(case_stream(WP2_REF), 0)
        assert [e.type for e in case_rows] == ["controller_changed", "controller_changed"]
        assert case_rows[1].payload["controller"] == {"kind": "ai", "display_name": None}
        assert invariant_holds(db.uow, a)

        svc.join(SECOND_REF, RILEY)
        assert invariant_holds(db.uow, b)
        end = JOIN_AT + timedelta(minutes=2)
        closed = new_service(db.uow, end).close(SECOND_REF, RILEY)
        assert isinstance(closed, LiveView)
        assert (closed.state, closed.since, closed.controller_kind) == ("closed", end, "ai")
        with db.uow(write=False) as tx:
            last_thread = tx.core.events.after(thread_stream(b.thread_id), 0)[-1]
            last_case = tx.core.events.after(case_stream(SECOND_REF), 0)[-1]
        assert (last_thread.type, last_thread.payload["composer_disabled"]) == ("chat_closed", True)
        assert (last_case.type, last_case.payload) == ("chat_closed", {"reason": "closed_by_staff"})
        assert invariant_holds(db.uow, b)


def test_live_action_rolls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-6: an events append that raises after the controller write leaves everything as it was."""
    with temp_sqlite() as db:
        seeded = seed_live_case(db.uow)
        before = snapshot(db.uow, seeded)

        def boom(*_args: object, **_kwargs: object) -> int:
            raise RuntimeError("injected")

        monkeypatch.setattr(repos_core_aux.EventsRepo, "append", boom)
        with pytest.raises(RuntimeError, match="injected"):
            new_service(db.uow).join(WP2_REF, RILEY)
        monkeypatch.undo()
        assert snapshot(db.uow, seeded) == before


def test_staff_message_store_redacted() -> None:
    """AC-7: the stored row, the relayed event and the response all hold the STORE-redacted text."""
    card, code = card_like_and_code()
    text = f"My card is {card} and the code {code}, please"
    with temp_sqlite() as db:
        seeded = seed_live_case(db.uow)
        svc = new_service(db.uow)
        svc.join(WP2_REF, RILEY)
        view = svc.send(WP2_REF, text, RILEY)
        assert isinstance(view, LiveView) and view.message is not None
        with db.uow(write=False) as tx:
            row_text = tx.core.messages.all_for_thread(seeded.thread_id)[-1].text
            event = next(
                e
                for e in tx.core.events.after(thread_stream(seeded.thread_id), 0)
                if e.type == "staff_message"
            )
        for seen in (row_text, str(event.payload["text"]), view.message.text):
            assert "[card number removed]" in seen and "[code]" in seen
            assert card not in seen and card.replace(" ", "") not in seen and code not in seen


def test_two_sessions_share_riley(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """AC-8: claims belong to the role (STF-1): a second representative session acts on the same case."""
    store = FakeSessionStore()
    token_a = store.issue(DemoRole.REPRESENTATIVE)
    token_b = store.issue(DemoRole.REPRESENTATIVE)
    app = staff_live_app(monkeypatch, tmp_path, store=store)
    with make_client(app) as client:
        seed_live_case(app_uow(app))
        joined = client.post(live_url(str(WP2_REF)), json={"action": "join"}, headers=cookie_header(token_b))
        assert joined.status_code == 200
        assert_matches(joined, "liveChatAction")
        assert joined.json()["controller"]["display_name"] == "Riley"
        sent = client.post(
            live_url(str(WP2_REF)),
            json={"action": "send", "text": STAFF_TEXT},
            headers=cookie_header(token_a),
        )
        assert sent.status_code == 200
        print("session B joined, session A sent:", sent.json()["message"]["speaker"])


class ResolveDouble:
    """Stand-in for AEA-29 CaseService.apply (resolve only): one write unit; update_versioned(case_ref,
    expected_version, lifecycle="resolved", resolved_at=now, updated_at=now); None -> "VERSION_CONFLICT"; else append
    case_changed {"version", "lifecycle"} to the case stream, commit, return the new version."""

    def __init__(self, uow: UnitOfWorkFactory) -> None:
        self._uow = uow

    def apply(
        self, case_ref: CaseRef, action: str, actor: StaffActor, expected_version: int, now: datetime
    ) -> int | str:
        assert action == "resolve" and actor.role is StaffRole.REPRESENTATIVE
        with self._uow(write=True) as tx:
            new = tx.cases.cases.update_versioned(
                case_ref, expected_version, lifecycle="resolved", resolved_at=now, updated_at=now
            )
            if new is None:
                return "VERSION_CONFLICT"
            tx.core.events.append(
                case_stream(case_ref),
                StreamEvent(type="case_changed", payload={"version": new, "lifecycle": "resolved"}, at=now),
            )
            tx.commit()
            return int(new)


def test_live_actions_keep_case_version() -> None:
    """AC-21: live actions never change version or lifecycle and send no case_changed; a later resolve still works."""
    with temp_sqlite() as db:
        a: SeededCase = seed_live_case(db.uow, version=3)
        b: SeededCase = seed_live_case(db.uow, case_ref=SECOND_REF, version=5)
        svc = new_service(db.uow)
        svc.join(WP2_REF, RILEY)
        svc.send(WP2_REF, STAFF_TEXT, RILEY)
        svc.hand_back(WP2_REF, RILEY)
        svc.join(SECOND_REF, RILEY)
        svc.close(SECOND_REF, RILEY)
        with db.uow(write=False) as tx:
            ca, cb = tx.cases.cases.get(WP2_REF), tx.cases.cases.get(SECOND_REF)
        assert ca is not None and cb is not None
        assert (ca.version, ca.lifecycle, cb.version, cb.lifecycle) == (3, "claimed", 5, "claimed")
        types_a, types_b = _types(db.uow, case_stream(WP2_REF)), _types(db.uow, case_stream(SECOND_REF))
        print("case stream types:", types_a, types_b)
        assert types_a == ["controller_changed", "controller_changed"]
        assert types_b == ["controller_changed", "chat_closed"]
        assert a.version == 3 and b.version == 5
        double = ResolveDouble(db.uow)
        assert double.apply(WP2_REF, "resolve", RILEY, expected_version=3, now=JOIN_AT) == 4
        assert double.apply(WP2_REF, "resolve", RILEY, expected_version=3, now=JOIN_AT) == "VERSION_CONFLICT"


def test_supervisor_does_not_own_representative_case() -> None:
    """AC-2 companion: a supervisor session cannot send into a representative-owned case."""
    with temp_sqlite() as db:
        seeded = seed_live_case(db.uow, live_state="joined")
        before = snapshot(db.uow, seeded)
        result = new_service(db.uow).send(WP2_REF, "x", SUPERVISOR)
        assert result == LiveRefused(code="NOT_CLAIMED_BY_YOU", details={"owner": "Riley"})
        assert snapshot(db.uow, seeded) == before
