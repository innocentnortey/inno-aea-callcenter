"""AEA-27 plan-added frozen edge tests (PA-1 to PA-5): rebind, locked threads, resend, email-only, bad construction.

Failure modes guarded: boundary (re-locate, locked thread, email-only contact, out-of-domain construction), invariant
(a resend supersedes the earlier code). Temp SQLite copies only; no phone, code or email literal.
"""

from __future__ import annotations

import re
from datetime import timedelta
from typing import Any

import pytest
from pydantic import SecretStr

from meridian.domain.identity import CodeCapReached, CodeWrong, Located, NotVerified, Verified
from meridian.policy.limits import IdentityLimits
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.identity_support import (
    NOW,
    OMAR,
    count,
    insert_email_only,
    latest_digits,
    locate_and_send,
    locator,
    make_service,
    new_secret,
    non_issued_text,
    omar_by_id,
    raw_rows,
    turn_ids,
    wrong,
)
from tests.unit.adapters.sqlite.helpers import new_thread


@pytest.fixture
def store() -> Any:
    with temp_sqlite() as s:
        yield s


def _state(store: TempStore, thread: Any) -> Any:
    with store.uow() as tx:
        return tx.core.reads.identity_state(thread)


def test_relocate_no_match_unbinds_customer(store: TempStore) -> None:
    """[boundary] A later no-match locate on the same thread drops the earlier customer and blocks sending."""
    svc = make_service(store)
    thread = new_thread()
    assert isinstance(svc.locate(thread, omar_by_id(), NOW), Located)
    assert svc.locate(thread, locator(customer_id="MHC-99999"), NOW) == NotVerified()
    state = _state(store, thread)
    assert state.status == "not_verified" and state.customer_id is None
    assert svc.send_code(thread, "sess", NOW) == NotVerified()
    assert count(store, "identity_codes") == 0


def test_locked_thread_stays_locked(store: TempStore) -> None:
    """[refusal] After three wrong tries a re-locate or a resend cannot reopen the thread."""
    svc = make_service(store)
    thread, session = new_thread(), "sess"
    locate_and_send(svc, thread, session, NOW)
    d = latest_digits(svc, session, NOW)
    for _ in range(3):
        svc.verify(turn_ids(thread), SecretStr(wrong(d)), NOW)
    before = count(store, "identity_codes")
    assert svc.locate(thread, omar_by_id(), NOW) == NotVerified()
    assert _state(store, thread).status == "locked"
    assert svc.send_code(thread, session, NOW) == CodeCapReached()
    assert count(store, "identity_codes") == before


def test_resend_supersedes_previous_code(store: TempStore) -> None:
    """[invariant] The newest code is the only live one; the older message reads expired with no digits."""
    svc = make_service(store)
    thread, session = new_thread(), "sess"
    locate_and_send(svc, thread, session, NOW)
    d1 = latest_digits(svc, session, NOW)
    svc.send_code(thread, session, NOW + timedelta(seconds=1))
    at = NOW + timedelta(seconds=2)
    d2 = latest_digits(svc, session, at)
    msgs = svc.inbox(session, at)
    assert [m.status for m in msgs] == ["active", "expired"]
    assert msgs[0].code is not None and msgs[1].code is None
    if d1 != d2:
        assert svc.verify(turn_ids(thread), SecretStr(d1), at) == CodeWrong(tries_left=2)
    assert isinstance(svc.verify(turn_ids(thread), SecretStr(d2), at), Verified)


def test_email_only_contact_hint(store: TempStore) -> None:
    """[boundary] A customer with only an email gets an email hint and the address is stored nowhere new."""
    email = insert_email_only(store)
    svc = make_service(store)
    thread = new_thread()
    assert svc.locate(thread, locator(customer_id="MHC-99993"), NOW) == Located(
        masked_hint="the email at s···@…"
    )
    svc.send_code(thread, "sess", NOW)
    assert raw_rows(store, "SELECT to_masked FROM demo_inbox") == [("s···@…",)]
    assert email not in non_issued_text(store)


@pytest.mark.parametrize(
    "limits",
    [
        IdentityLimits(tries=4),
        IdentityLimits(tries=0),
        IdentityLimits(max_sends=0),
        IdentityLimits(max_sends=4),
        IdentityLimits(code_ttl_s=0),
    ],
)
def test_constructor_rejects_out_of_domain_limits(store: TempStore, limits: IdentityLimits) -> None:
    """[boundary] Limits outside the domain bounds refuse at construction, with a digit-free message."""
    with pytest.raises(ValueError) as exc:
        make_service(store, limits=limits)
    assert not re.search(r"\d", str(exc.value))


def test_constructor_rejects_empty_secret(store: TempStore) -> None:
    """[boundary] An empty session secret refuses at construction."""
    with pytest.raises(ValueError) as exc:
        make_service(store, secret=SecretStr(""))
    assert not re.search(r"\d", str(exc.value))
    assert new_secret().get_secret_value() not in str(exc.value)
    assert OMAR not in str(exc.value)
