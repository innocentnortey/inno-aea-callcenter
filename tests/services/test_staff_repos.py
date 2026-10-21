"""AEA-44 AC-14: repos_staff.py bodies over AEA-10's tables, reached as the unit of work's ``staff`` repos.

Failure mode guarded: invariant (round trip, ordering, AUTOINCREMENT kept across a reset so an old flag link never
resolves to another flag). Temp SQLite copy; synthetic values only.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest

from meridian.adapters.sqlite.repos_staff import FlagRow, StaffRepos, StaffSessionRow
from meridian.domain.staff import DemoRole, LoginSessionId, StaffRole, actor_for
from meridian.services.staff import FlagRejected
from tests.api.staff_session_support import make_flags, run_reset, seed_case
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import TempStore, temp_sqlite

T0 = datetime(2026, 10, 21, 19, 0, tzinfo=UTC)


@pytest.fixture
def db() -> Iterator[TempStore]:
    with temp_sqlite() as store:
        yield store


def _flag(case: object, at: datetime) -> FlagRow:
    return FlagRow.model_validate(
        {
            "case_ref": case,
            "target": "answer",
            "message_id": None,
            "note": None,
            "reason": None,
            "flagged_by_role": StaffRole.REPRESENTATIVE,
            "flagged_at": at,
            "status": "new",
            "reviewed_by_role": None,
            "reviewed_note": None,
            "reviewed_at": None,
        }
    )


def test_repos_staff_bodies(db: TempStore) -> None:
    case, _message = seed_case(db.uow, 9)
    session = StaffSessionRow(
        token_hash="h" * 64,
        session_id=LoginSessionId("11111111-1111-4111-8111-111111111111"),
        role=DemoRole.CUSTOMER,
        role_reset_pending=True,
        signed_in_demo=T0 - timedelta(days=5),
        created_real=T0,
        expires_real=T0 + timedelta(hours=12),
    )
    with db.uow(write=True) as tx:
        assert isinstance(tx.staff, StaffRepos)
        tx.staff.sessions.insert(session)
        assert tx.staff.sessions.by_token_hash(session.token_hash) == session
        assert tx.staff.sessions.by_session_id(session.session_id) == session
        assert tx.staff.sessions.by_token_hash("missing") is None
        assert tx.staff.sessions.set_role(LoginSessionId("no-such-session"), DemoRole.OWNER) is False
        assert tx.staff.sessions.set_role(session.session_id, DemoRole.SUPERVISOR) is True
        changed = tx.staff.sessions.by_session_id(session.session_id)
        assert changed is not None and changed.role == DemoRole.SUPERVISOR and not changed.role_reset_pending
        tx.staff.sessions.delete(session.token_hash)
        tx.staff.sessions.delete(session.token_hash)
        assert tx.staff.sessions.by_token_hash(session.token_hash) is None

        ids = [tx.staff.flags.insert(_flag(case, T0 + timedelta(minutes=m))) for m in (0, 5, 5)]
        assert ids == sorted(ids) and len(set(ids)) == 3
        got = tx.staff.flags.get(ids[0])
        assert got is not None and got.id == ids[0] and got.case_ref == case and got.flagged_at == T0
        assert tx.staff.flags.get(999_999) is None
        assert tx.staff.flags.review(ids[0], StaffRole.SUPERVISOR, "first", T0) is True
        assert tx.staff.flags.review(ids[0], StaffRole.OWNER, None, T0) is True
        again = tx.staff.flags.get(ids[0])
        assert again is not None and again.status == "reviewed" and again.reviewed_by_role == StaffRole.OWNER
        assert again.reviewed_note is None
        assert tx.staff.flags.review(999_999, StaffRole.OWNER, None, T0) is False
        assert [f.id for f in tx.staff.flags.list_ordered()] == [ids[2], ids[1], ids[0]]
        tx.commit()

    run_reset(db.uow)
    with db.uow() as tx:
        assert tx.staff.flags.get(ids[2]) is None
    with db.uow(write=True) as tx:
        next_id = tx.staff.flags.insert(_flag(case, T0))
        tx.commit()
    assert next_id > max(ids)
    result = make_flags(db.uow, FixedClock()).review(
        f"flg-{ids[2]}",
        None,
        actor_for(StaffRole.SUPERVISOR),
    )
    assert isinstance(result, FlagRejected) and result.code == "FLAG_NOT_FOUND"
