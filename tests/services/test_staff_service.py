"""AEA-44 AC-4, AC-6, AC-7, AC-9, AC-11, AC-12, AC-13: StaffSessionStore and FlagService (frozen with the AEA-44 tests).

Failure modes guarded: invariant (HMAC-only storage, absolute lifetime, role-only switch, flag lifecycle, flags touch
only `flags`), refusal (blank/unknown/altered/expired tokens, role_reset, every flag refusal), negative (a rejected value
never appears in a result or a log). Temp SQLite copies only; no `.env`, no paid call. AEA-44's own modules are imported
inside the tests so the suite collects before they exist.
"""

from __future__ import annotations

import hashlib
import hmac
import inspect
import logging
import re
import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta

import pytest
from pydantic import SecretStr, ValidationError

from meridian.domain.staff import (
    DemoRole,
    LoginSession,
    RoleRefusal,
    SessionExpired,
    SessionMissing,
    StaffActor,
    StaffRole,
    actor_for,
)
from tests.api.staff_session_support import (
    LIFETIME_S,
    REPO_ROOT,
    WALL_T0,
    dir_digest,
    flag_rows,
    make_flags,
    make_store,
    run_reset,
    seed_case,
    staff_rows,
    table_counts,
)
from tests.api.web_shell_support import app_log_text, rand_word
from tests.fakes.clock import FixedClock
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.unit.adapters.sqlite.helpers import case_ref

REP_SUP = (StaffRole.REPRESENTATIVE, StaffRole.SUPERVISOR)


@pytest.fixture
def db() -> Iterator[TempStore]:
    with temp_sqlite() as store:
        yield store


def _secret() -> SecretStr:
    return SecretStr(rand_word(24, "ss"))


def _changed_columns(before: dict[str, object], after: dict[str, object]) -> set[str]:
    return {k for k in before if before[k] != after[k]}


# -- AC-6 ---------------------------------------------------------------------------------------------------------
def test_session_lookup(db: TempStore) -> None:
    """refusal (AC-6): token shape, HMAC-only storage, blank/unknown/altered/other-secret/expired lookups, end idempotent."""
    secret = _secret()
    store = make_store(db.uow, secret=secret)
    issued = store.start(WALL_T0)
    token = issued.token.get_secret_value()
    assert re.fullmatch(r"[A-Za-z0-9_-]{43}", token), "token_urlsafe(32) shape"

    rows = staff_rows(db.uow)
    assert len(rows) == 1
    row = rows[0]
    expected_hash = hmac.new(
        secret.get_secret_value().encode("utf-8"), token.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    assert row["token_hash"] == expected_hash
    assert all(token not in str(value) for value in row.values()), "the token is in a column"
    assert row["role"] == "customer"
    assert row["role_reset_pending"] == 0
    assert uuid.UUID(str(row["session_id"])).version == 4
    assert issued.session.role is DemoRole.CUSTOMER and issued.session.role_reset is False

    flipped = token[:-1] + ("A" if token[-1] != "A" else "B")
    for label, candidate in (("blank", ""), ("unknown", rand_word(43)), ("altered", flipped)):
        result = store.resolve(SecretStr(candidate), WALL_T0)
        assert isinstance(result, SessionMissing), label

    found = store.resolve(issued.token, WALL_T0)
    assert isinstance(found, LoginSession)
    assert found.session_id == issued.session.session_id

    other_secret = make_store(db.uow, secret=_secret())
    assert isinstance(other_secret.resolve(issued.token, WALL_T0), SessionMissing)

    assert isinstance(store.resolve(issued.token, issued.session.expires_at), SessionExpired)
    assert staff_rows(db.uow) == [], "an expired session row must be deleted"

    again = store.start(WALL_T0)
    store.end(again.token)
    store.end(again.token)
    store.end(SecretStr(""))
    assert staff_rows(db.uow) == []
    print(
        "session lookup: token 43 chars, hash=hmac-sha256, blank/unknown/altered -> missing, expired -> deleted"
    )


# -- AC-7 ---------------------------------------------------------------------------------------------------------
def test_lifetime_absolute_wall_clock(db: TempStore) -> None:
    """invariant (AC-7): 43,200 s absolute on the wall clock, no sliding write, a demo-clock advance expires nobody."""
    from meridian.services.staff import StaffSessionStore

    parameter = inspect.signature(StaffSessionStore.__init__).parameters["lifetime_s"]
    assert parameter.default is inspect.Parameter.empty, "lifetime_s must have no default"

    secret = _secret()
    store = make_store(db.uow, secret=secret)
    issued = store.start(WALL_T0)
    assert issued.session.expires_at == WALL_T0 + timedelta(seconds=LIFETIME_S)
    before = staff_rows(db.uow)
    for offset in (1, 60, 3_600, LIFETIME_S - 1):
        result = store.resolve(issued.token, WALL_T0 + timedelta(seconds=offset))
        assert isinstance(result, LoginSession), f"+{offset}s"
        assert staff_rows(db.uow) == before, f"+{offset}s wrote to the table"

    later_demo = make_store(db.uow, secret=secret, demo=FixedClock().advanced(timedelta(days=3)))
    still = later_demo.resolve(issued.token, WALL_T0 + timedelta(seconds=100))
    assert isinstance(still, LoginSession)
    assert still.signed_in_at == issued.session.signed_in_at
    assert still.signed_in_at == FixedClock().now()

    gone = later_demo.resolve(issued.token, WALL_T0 + timedelta(seconds=LIFETIME_S))
    assert isinstance(gone, SessionExpired)
    assert staff_rows(db.uow) == []


# -- AC-9 ---------------------------------------------------------------------------------------------------------
def test_reset_sends_roles_to_customer(db: TempStore) -> None:
    """failure/refusal (AC-9): a reset sends staff roles to customer with role_reset; only switch_role clears it."""
    store = make_store(db.uow, secret=_secret())
    a = store.start(WALL_T0)
    b = store.start(WALL_T0)
    store.switch_role(a.session.session_id, DemoRole.REPRESENTATIVE)

    assert run_reset(db.uow) == 1, "only the representative session counts as reset"

    for _tab in ("tab 1", "tab 2"):
        session = store.resolve(a.token, WALL_T0)
        assert isinstance(session, LoginSession)
        assert session.role is DemoRole.CUSTOMER and session.role_reset is True
        refusal = store.actor_for(session, REP_SUP)
        assert refusal == RoleRefusal(role=DemoRole.CUSTOMER, needs=REP_SUP, reason="role_reset")
        assert store.session_info(session).display_name == "Customer (demo)"

    other = store.resolve(b.token, WALL_T0)
    assert isinstance(other, LoginSession) and other.role_reset is False
    other_refusal = store.actor_for(other, REP_SUP)
    assert isinstance(other_refusal, RoleRefusal) and other_refusal.reason == "wrong_role"

    switched = store.switch_role(a.session.session_id, DemoRole.REPRESENTATIVE)
    assert switched.role_reset is False
    assert store.actor_for(switched, REP_SUP) == StaffActor(
        role=StaffRole.REPRESENTATIVE, name="Riley", signature="Riley (demo)"
    )
    rows = {r["session_id"]: r for r in staff_rows(db.uow)}
    assert rows[str(a.session.session_id)]["role_reset_pending"] == 0
    after = store.resolve(a.token, WALL_T0)
    assert isinstance(after, LoginSession) and after.role is DemoRole.REPRESENTATIVE and not after.role_reset


# -- AC-4 ---------------------------------------------------------------------------------------------------------
def test_switch_changes_only_role(db: TempStore) -> None:
    """invariant (AC-4): a switch changes role (and clears the marker) and nothing else; unknown id raises SessionGone."""
    from meridian.services.staff import SessionGone

    store = make_store(db.uow, secret=_secret())
    issued = store.start(WALL_T0)
    session_id = issued.session.session_id

    before = staff_rows(db.uow)[0]
    changed = store.switch_role(session_id, DemoRole.SUPERVISOR)
    after = staff_rows(db.uow)[0]
    assert _changed_columns(before, after) == {"role"}
    assert changed.session_id == issued.session.session_id
    assert changed.signed_in_at == issued.session.signed_in_at
    assert changed.expires_at == issued.session.expires_at
    assert changed.role is DemoRole.SUPERVISOR

    assert run_reset(db.uow) == 1
    marked = staff_rows(db.uow)[0]
    assert marked["role"] == "customer" and marked["role_reset_pending"] == 1
    store.switch_role(session_id, DemoRole.CUSTOMER)
    cleared = staff_rows(db.uow)[0]
    assert _changed_columns(marked, cleared) == {"role_reset_pending"}
    assert cleared["role_reset_pending"] == 0

    store.switch_role(session_id, DemoRole.CUSTOMER)
    assert staff_rows(db.uow)[0] == cleared, "switching to the current role must write nothing else"

    snapshot = staff_rows(db.uow)
    with pytest.raises(SessionGone):
        store.switch_role(type(session_id)(str(uuid.uuid4())), DemoRole.OWNER)
    assert staff_rows(db.uow) == snapshot


# -- AC-11 --------------------------------------------------------------------------------------------------------
def test_flag_lifecycle(db: TempStore) -> None:
    """invariant (AC-11): flag stores the actor role and demo time, review overwrites, list is at desc then id desc."""
    from meridian.services.staff import FlagIn, FlagRecord

    ref_a, msg_a = seed_case(db.uow, 9)
    ref_b, _msg_b = seed_case(db.uow, 10)
    rep = actor_for(StaffRole.REPRESENTATIVE)
    sup = actor_for(StaffRole.SUPERVISOR)
    t0 = FixedClock()
    t1 = t0.advanced(timedelta(hours=1))
    t2 = t0.advanced(timedelta(hours=2))

    first = make_flags(db.uow, t0).flag(
        FlagIn(
            case_ref=ref_a,
            target="answer",
            message_id=str(msg_a),
            note="synthetic note",
            reason="synthetic reason",
        ),
        rep,
    )
    assert isinstance(first, FlagRecord)
    rows = flag_rows(db.uow)
    assert len(rows) == 1
    row = rows[0]
    assert first.flag_id == f"flg-{row['id']}"
    assert first.flagged_by == "Riley (demo)"
    assert first.status == "new" and first.reviewed_by is None and first.reviewed_note is None
    assert first.at == t0.now()
    assert (first.case_ref, first.target, first.message_id) == (ref_a, "answer", str(msg_a))
    assert (first.note, first.reason) == ("synthetic note", "synthetic reason")
    assert (
        row["case_ref"] == str(ref_a) and row["target"] == "answer" and str(row["message_id"]) == str(msg_a)
    )
    assert row["note"] == "synthetic note" and row["reason"] == "synthetic reason"
    assert row["flagged_by_role"] == "representative" and row["status"] == "new"
    assert datetime.fromisoformat(str(row["flagged_at"])) == t0.now()
    assert row["reviewed_by_role"] is None and row["reviewed_note"] is None and row["reviewed_at"] is None

    second = make_flags(db.uow, t1).flag(
        FlagIn(case_ref=ref_b, target="brief", message_id=None, note=None, reason=None), sup
    )
    third = make_flags(db.uow, t1).flag(
        FlagIn(case_ref=ref_b, target="escalation", message_id=None, note=None, reason=None), rep
    )
    assert isinstance(second, FlagRecord) and isinstance(third, FlagRecord)
    assert second.flagged_by == "Demo supervisor"

    service = make_flags(db.uow, t2)
    listed = service.list_flags()
    assert [r.flag_id for r in listed] == [third.flag_id, second.flag_id, first.flag_id]

    reviewed = service.review(first.flag_id, "reviewed ok", sup)
    assert isinstance(reviewed, FlagRecord)
    assert reviewed.status == "reviewed" and reviewed.reviewed_by == "Demo supervisor"
    assert reviewed.reviewed_note == "reviewed ok"
    assert reviewed.flagged_by == "Riley (demo)" and reviewed.at == t0.now()
    stored = flag_rows(db.uow)[0]
    assert stored["status"] == "reviewed" and stored["reviewed_by_role"] == "supervisor"
    assert stored["reviewed_note"] == "reviewed ok"
    assert datetime.fromisoformat(str(stored["reviewed_at"])) == t2.now()

    again = service.review(first.flag_id, "second look", rep)
    assert isinstance(again, FlagRecord)
    assert again.reviewed_by == "Riley (demo)" and again.reviewed_note == "second look"
    assert flag_rows(db.uow)[0]["reviewed_by_role"] == "representative"
    assert [r.flag_id for r in service.list_flags()] == [third.flag_id, second.flag_id, first.flag_id]
    print("flag lifecycle:", [r.flag_id for r in service.list_flags()])


# -- AC-12 --------------------------------------------------------------------------------------------------------
def test_flag_refusals(db: TempStore, caplog: pytest.LogCaptureFixture) -> None:
    """failure/refusal (AC-12): each refusal names its code, writes no row, and never echoes the rejected value."""
    from meridian.services.staff import FlagIn, FlagRecord, FlagRejected

    caplog.set_level(logging.DEBUG)
    ref_a, msg_a = seed_case(db.uow, 9)
    _ref_b, msg_b = seed_case(db.uow, 10)
    rep = actor_for(StaffRole.REPRESENTATIVE)
    service = make_flags(db.uow, FixedClock())
    too_long = rand_word(2001)
    seen: list[object] = []

    def refused(result: object) -> FlagRejected:
        assert isinstance(result, FlagRejected), result
        seen.append(result)
        assert too_long not in repr(result) and too_long not in result.model_dump_json()
        return result

    with pytest.raises(ValidationError) as excinfo:
        FlagIn(case_ref=ref_a, target="answer", message_id=None, note=too_long, reason=None)
    assert too_long not in str(excinfo.value)

    bypass_note = FlagIn.model_construct(
        case_ref=ref_a, target="answer", message_id=None, note=too_long, reason=None
    )
    result = refused(service.flag(bypass_note, rep))
    assert result.code == "VALIDATION_ERROR" and result.field == "note" and result.constraint
    bypass_reason = FlagIn.model_construct(
        case_ref=ref_a, target="answer", message_id=None, note=None, reason=too_long
    )
    assert refused(service.flag(bypass_reason, rep)).field == "reason"

    wrong_message = refused(
        service.flag(
            FlagIn(case_ref=ref_a, target="answer", message_id=str(msg_b), note=None, reason=None), rep
        )
    )
    assert wrong_message.code == "VALIDATION_ERROR" and wrong_message.field == "message_id"
    assert wrong_message.constraint == "not a message of this case"
    not_a_number = refused(
        service.flag(FlagIn(case_ref=ref_a, target="answer", message_id="abc", note=None, reason=None), rep)
    )
    assert not_a_number.field == "message_id" and not_a_number.constraint == "not a message of this case"

    unknown_case = refused(
        service.flag(
            FlagIn(case_ref=case_ref(999), target="brief", message_id=None, note=None, reason=None), rep
        )
    )
    assert unknown_case.code == "CASE_NOT_FOUND" and unknown_case.details == {"reference": "MHC-C-0999"}
    assert flag_rows(db.uow) == [], "a refusal wrote a row"

    good = service.flag(
        FlagIn(case_ref=ref_a, target="answer", message_id=str(msg_a), note="   ", reason="  "), rep
    )
    assert isinstance(good, FlagRecord)
    assert good.note is None and good.reason is None
    stored = flag_rows(db.uow)
    assert len(stored) == 1 and stored[0]["note"] is None and stored[0]["reason"] is None, (
        "blank must store NULL"
    )

    long_review = refused(service.review(good.flag_id, too_long, rep))
    assert long_review.code == "VALIDATION_ERROR" and long_review.field == "note"
    malformed = refused(service.review("not-a-flag", None, rep))
    assert malformed.code == "FLAG_NOT_FOUND" and malformed.details is None
    unknown_flag = refused(service.review("flg-999999", None, rep))
    assert unknown_flag.code == "FLAG_NOT_FOUND" and unknown_flag.details == {"flag_id": "flg-999999"}

    assert len(flag_rows(db.uow)) == 1, "refusals changed the flag count"
    assert flag_rows(db.uow)[0]["status"] == "new", "a refused review changed the flag"
    assert too_long not in app_log_text(caplog), "a rejected value reached a log record"
    print(f"flag refusals: {len(seen)} FlagRejected, 0 rows written, value absent from results and logs")


# -- AC-13 --------------------------------------------------------------------------------------------------------
def test_flags_touch_only_flags_table(db: TempStore) -> None:
    """negative (AC-13, R-37): flags change nothing automatically; only the flags table moves."""
    from meridian.services.staff import FlagIn, FlagRecord

    ref_a, msg_a = seed_case(db.uow, 9)
    watched = {
        "knowledge_base": REPO_ROOT / "docs/data/issued/meridian_dataset/knowledge_base",
        "eval_cases": REPO_ROOT / "eval/cases",
        "prompts": REPO_ROOT / "src/meridian/agent/prompts",
    }
    digests_before = {name: dir_digest(path) for name, path in watched.items()}
    skip = frozenset({"flags", "sqlite_sequence"})
    counts_before = table_counts(db.uow, skip=skip)

    service = make_flags(db.uow, FixedClock())
    rep = actor_for(StaffRole.REPRESENTATIVE)
    one = service.flag(
        FlagIn(case_ref=ref_a, target="answer", message_id=str(msg_a), note="n", reason="r"), rep
    )
    two = service.flag(FlagIn(case_ref=ref_a, target="brief", message_id=None, note=None, reason=None), rep)
    assert isinstance(one, FlagRecord) and isinstance(two, FlagRecord)
    assert isinstance(service.review(one.flag_id, "reviewed", rep), FlagRecord)

    assert len(flag_rows(db.uow)) == 2
    assert table_counts(db.uow, skip=skip) == counts_before
    assert {name: dir_digest(path) for name, path in watched.items()} == digests_before
