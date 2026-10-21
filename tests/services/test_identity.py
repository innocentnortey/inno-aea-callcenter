"""AEA-27 (risk::security) frozen tests: IdentityService, the demo inbox and the WP-2 flow.

Failure modes guarded: invariant (HMAC-only storage, per-conversation proof, masked hint only), refusal/boundary (every
no-account cause looks the same, wrong/expired/locked codes, cap), negative (code, phone and secret absent from every
sink), regression (restart must not leave a live code). Temp SQLite copies only; no `.env`, no paid call.
No phone number or code is written in this file: both are read at run time.
"""

from __future__ import annotations

import ast
import importlib
import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from pydantic import SecretStr, TypeAdapter

from meridian.adapters.sqlite.repos_identity import IdentityRepos
from meridian.domain.actions import ActionKind
from meridian.domain.common import InvoiceId
from meridian.domain.identity import (
    CodeCapReached,
    CodeExpired,
    CodeLocked,
    CodeSent,
    CodeWrong,
    FormValues,
    Located,
    Locator,
    NotVerified,
    Verified,
)
from meridian.policy.limits import IdentityLimits
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.identity_support import (
    NOW,
    OMAR,
    count,
    customer_contact,
    hmac_hex,
    insert_no_contact,
    insert_omar_twin,
    latest_digits,
    locate_and_send,
    locator,
    make_service,
    new_secret,
    non_issued_text,
    raw_rows,
    scope_for_customer,
    turn_ids,
    wrong,
)
from tests.unit.adapters.sqlite.helpers import new_thread

REPO_ROOT = Path(__file__).resolve().parents[2]
_INVOICE: TypeAdapter[InvoiceId] = TypeAdapter(InvoiceId)


@pytest.fixture
def store() -> Any:
    with temp_sqlite() as s:
        yield s


def _state(store: TempStore, thread: Any) -> Any:
    with store.uow() as tx:
        return tx.core.reads.identity_state(thread)


def _account() -> Any:
    return importlib.import_module("meridian.agent.tools.account")


def test_wp2_omar_locate_code_verify_invoice(store: TempStore) -> None:
    """[invariant] WP-2 end to end at the service level: locate, code, verify, then the as-billed invoice."""
    secret = new_secret()
    svc = make_service(store, secret=secret)
    name, phone = customer_contact(store, OMAR)
    loc = Locator.from_form(FormValues(name=name, phone=SecretStr(phone)))
    assert loc is not None
    thread, session = new_thread(), "sess-" + new_secret().get_secret_value()[:8]
    assert svc.locate(thread, loc, NOW) == Located(masked_hint="the phone ending in 02")
    sent = svc.send_code(thread, session, NOW)
    assert isinstance(sent, CodeSent)
    assert sent.expires_at == NOW + timedelta(minutes=10)
    assert sent.sends_left == 2
    msgs = svc.inbox(session, NOW)
    assert len(msgs) == 1 and msgs[0].status == "active" and isinstance(msgs[0].code, SecretStr)
    digits = msgs[0].code.get_secret_value()
    ids = turn_ids(thread)
    result = svc.verify(ids, SecretStr(digits), NOW + timedelta(minutes=1))
    assert isinstance(result, Verified)
    assert result.customer_id == OMAR
    assert result.action.kind == ActionKind.VERIFIED

    account = _account()
    read_invoices = account.account_tools(store.uow)[0]
    res = read_invoices.executor(account.ReadInvoicesArgs(), scope_for_customer(OMAR))
    fm: Any = res.for_model
    assert fm["invoices"][0]["invoice_id"] == "INV-204411"
    assert [ln["amount_cents"] for ln in fm["invoices"][0]["lines"]] == [8900, 24500, 14400]
    assert [n.kind for n in res.captured.staff_notes] == [
        "billed_differs_from_schedule",
        "diagnostic_without_credit",
    ]
    assert "149" not in json.dumps(fm)


@pytest.mark.parametrize("kind", ["name_phone", "customer_id", "invoice"])
def test_locate_each_locator_returns_masked_hint_only(store: TempStore, kind: str) -> None:
    """[invariant] Every locator kind yields only the masked hint and records status located."""
    svc = make_service(store)
    name, phone = customer_contact(store, OMAR)
    loc = {
        "name_phone": lambda: locator(name=name, phone=phone),
        "customer_id": lambda: locator(customer_id=OMAR),
        "invoice": lambda: locator(invoice_number="INV-204411"),
    }[kind]()
    thread = new_thread()
    result = svc.locate(thread, loc, NOW)
    assert result == Located(masked_hint="the phone ending in 02")
    assert set(json.loads(result.model_dump_json())) == {"kind", "masked_hint"}
    state = _state(store, thread)
    assert state.status == "located" and state.customer_id == OMAR


def test_not_verified_identical_for_every_cause(store: TempStore) -> None:
    """[boundary/refusal] No match, ambiguous match and no usable contact are indistinguishable and write nothing."""
    insert_omar_twin(store)
    insert_no_contact(store)
    name, phone = customer_contact(store, OMAR)
    assert raw_rows(store, "SELECT 1 FROM customers WHERE customer_id = 'MHC-99999'") == []
    causes = [
        locator(customer_id="MHC-99999"),
        locator(name=name, phone=phone),
        locator(customer_id="MHC-99992"),
    ]
    svc = make_service(store)
    threads = [new_thread() for _ in causes]
    results = [svc.locate(t, c, NOW) for t, c in zip(threads, causes, strict=True)]
    assert all(r == NotVerified() for r in results)
    assert {r.model_dump_json() for r in results} == {'{"kind":"not_verified"}'}
    assert count(store, "identity_codes") == 0 and count(store, "demo_inbox") == 0
    for t in threads:
        row = raw_rows(
            store,
            "SELECT status, customer_id, masked_hint, channel FROM identity_threads WHERE thread_id = ?",
            (str(t),),
        )
        assert row == [("not_verified", None, None, None)]


def test_locate_match_rules(store: TempStore) -> None:
    """[invariant] Phone matches on its last 10 digits, the name ignores case and spacing, a near miss is NotVerified."""
    svc = make_service(store)
    name, phone = customer_contact(store, OMAR)
    d = "".join(ch for ch in phone if ch.isdigit())[-10:]
    phones = [
        f"({d[:3]}) {d[3:6]}-{d[6:]}",
        f"{d[:3]} {d[3:6]} {d[6:]}",
        f"+1 {d[:3]}-{d[3:6]}-{d[6:]}",
        "1" + d,
        f"  {d}  ",
    ]
    for p in phones:
        assert svc.locate(new_thread(), locator(name=name, phone=p), NOW) == Located(
            masked_hint="the phone ending in 02"
        ), "phone variant"
    for n in (name.upper(), name.lower(), "  " + name.replace(" ", "   ") + " "):
        assert isinstance(svc.locate(new_thread(), locator(name=n, phone=phone), NOW), Located), (
            "name variant"
        )
    near = name[:-1] + ("x" if name[-1] != "x" else "y")
    assert svc.locate(new_thread(), locator(name=near, phone=phone), NOW) == NotVerified()


def test_send_code_stores_hmac_and_expiry_only(store: TempStore) -> None:
    """[invariant] Only the HMAC, boot id and times are stored; the TTL comes from IdentityLimits."""
    secret = new_secret()
    svc = make_service(store, secret=secret)
    thread, session = new_thread(), "sess-a"
    sent = locate_and_send(svc, thread, session, NOW)
    assert sent.sends_left == 2
    digits = latest_digits(svc, session, NOW)
    with store.uow() as tx:
        code = tx.identity.newest_code(thread)
    assert code is not None
    assert code.code_hmac == hmac_hex(secret, digits)
    assert code.held_by == svc.boot_id
    assert code.sent_at == NOW and code.expires_at == NOW + timedelta(seconds=600) and code.tries_left == 3
    inbox_rows = raw_rows(store, "SELECT demo_session, to_masked FROM demo_inbox")
    assert inbox_rows == [(session, "···02")]
    assert digits not in non_issued_text(store)
    cols = {r[1] for r in raw_rows(store, "PRAGMA table_info(demo_inbox)")}
    assert "code" not in cols and "body" not in cols
    short = make_service(store, secret=secret, limits=IdentityLimits(code_ttl_s=60))
    t2 = new_thread()
    locate_and_send(short, t2, "sess-b", NOW)
    with store.uow() as tx:
        c2 = tx.identity.newest_code(t2)
    assert c2 is not None and c2.expires_at == NOW + timedelta(seconds=60)


def test_fourth_code_refused_and_unlocated_send(store: TempStore) -> None:
    """[refusal] The cap ends in CodeCapReached and state locked; an unlocated send is NotVerified."""
    svc = make_service(store)
    thread, session = new_thread(), "sess-a"
    svc.locate(thread, locator(customer_id=OMAR), NOW)
    sent = [svc.send_code(thread, session, NOW + timedelta(seconds=i)) for i in range(3)]
    assert [s.sends_left for s in sent] == [2, 1, 0]
    assert svc.send_code(thread, session, NOW + timedelta(seconds=3)) == CodeCapReached()
    assert _state(store, thread).status == "locked"
    assert count(store, "demo_inbox") == 3 and count(store, "identity_codes") == 3
    fresh = new_thread()
    assert svc.send_code(fresh, session, NOW) == NotVerified()
    assert count(store, "demo_inbox") == 3 and count(store, "identity_codes") == 3
    assert raw_rows(store, "SELECT 1 FROM identity_threads WHERE thread_id = ?", (str(fresh),)) == []


def test_verify_writes_verified_action_same_transaction(
    store: TempStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """[invariant] actions(verified) and status verified commit together; replay is idempotent."""
    svc = make_service(store)
    thread, session = new_thread(), "sess-a"
    locate_and_send(svc, thread, session, NOW)
    digits = latest_digits(svc, session, NOW)
    ids = turn_ids(thread)

    def boom(self: Any, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("injected fault")

    monkeypatch.setattr(IdentityRepos, "mark_used", boom)
    with pytest.raises(RuntimeError):
        svc.verify(ids, SecretStr(digits), NOW + timedelta(seconds=30))
    monkeypatch.undo()
    assert count(store, "actions") == 0
    assert _state(store, thread).status == "code_sent"

    first = svc.verify(ids, SecretStr(digits), NOW + timedelta(seconds=30))
    assert isinstance(first, Verified)
    rows = raw_rows(store, "SELECT kind, records_json FROM actions WHERE thread_id = ?", (str(thread),))
    assert len(rows) == 1 and rows[0][0] == "verified" and json.loads(rows[0][1]) == {"customer": OMAR}
    assert _state(store, thread).status == "verified"
    again = svc.verify(ids, SecretStr(digits), NOW + timedelta(seconds=40))
    assert isinstance(again, Verified) and again.action == first.action
    assert count(store, "actions") == 1


def test_three_wrong_tries_lock(store: TempStore) -> None:
    """[refusal] Two wrong tries count down, the third locks, a correct code after the lock still refuses."""
    svc = make_service(store)
    thread, session = new_thread(), "sess-a"
    locate_and_send(svc, thread, session, NOW)
    d = latest_digits(svc, session, NOW)
    ids = turn_ids(thread)
    results = [svc.verify(ids, SecretStr(wrong(d)), NOW) for _ in range(3)]
    results.append(svc.verify(ids, SecretStr(d), NOW))
    assert results[0] == CodeWrong(tries_left=2)
    assert results[1] == CodeWrong(tries_left=1)
    assert results[2] == CodeLocked() and results[3] == CodeLocked()
    assert not any(isinstance(r, NotVerified) for r in results)
    assert _state(store, thread).status == "locked"


def test_expired_code_and_resend_under_cap(store: TempStore) -> None:
    """[boundary] Expiry is exclusive at expires_at; resend is offered only under the send cap."""
    svc = make_service(store)
    tx_, ty, tz = new_thread(), new_thread(), new_thread()
    locate_and_send(svc, tx_, "sx", NOW)
    assert isinstance(
        svc.verify(turn_ids(tx_), SecretStr(latest_digits(svc, "sx", NOW)), NOW + timedelta(seconds=599)),
        Verified,
    )
    locate_and_send(svc, ty, "sy", NOW)
    assert svc.verify(
        turn_ids(ty), SecretStr(latest_digits(svc, "sy", NOW)), NOW + timedelta(seconds=600)
    ) == CodeExpired(resend_offered=True, sends_left=2)
    svc.locate(tz, locator(customer_id=OMAR), NOW)
    for i in range(3):
        svc.send_code(tz, "sz", NOW + timedelta(seconds=i))
    newest = latest_digits(svc, "sz", NOW + timedelta(seconds=2))
    assert svc.verify(turn_ids(tz), SecretStr(newest), NOW + timedelta(seconds=602)) == CodeExpired(
        resend_offered=False, sends_left=0
    )


def test_restart_expires_unheld_code(store: TempStore) -> None:
    """[regression] After a restart the old code is expired and shows no digits (GRT-2)."""
    secret = new_secret()
    svc1 = make_service(store, secret=secret)
    thread, session = new_thread(), "sess-a"
    locate_and_send(svc1, thread, session, NOW)
    d = latest_digits(svc1, session, NOW)
    svc2 = make_service(store, secret=secret)
    later = NOW + timedelta(minutes=1)
    assert svc2.verify(turn_ids(thread), SecretStr(d), later) == CodeExpired(
        resend_offered=True, sends_left=2
    )
    msgs = svc2.inbox(session, later)
    assert len(msgs) == 1 and msgs[0].code is None and msgs[0].status == "expired"
    assert d not in repr(msgs)


def test_inbox_scoped_to_login_session(store: TempStore) -> None:
    """[invariant] The inbox is this session's only, newest first, with active/used/expired and held codes only."""
    svc = make_service(store)
    t1, t2, t3, t4 = (new_thread() for _ in range(4))
    locate_and_send(svc, t1, "s1", NOW)
    locate_and_send(svc, t2, "s1", NOW + timedelta(seconds=200))
    d2 = latest_digits(svc, "s1", NOW + timedelta(seconds=200))
    assert isinstance(svc.verify(turn_ids(t2), SecretStr(d2), NOW + timedelta(seconds=250)), Verified)
    locate_and_send(svc, t3, "s1", NOW + timedelta(seconds=300))
    locate_and_send(svc, t4, "s2", NOW + timedelta(seconds=310))
    at = NOW + timedelta(seconds=650)
    s1 = svc.inbox("s1", at)
    assert [int(m.id) for m in s1] == sorted((int(m.id) for m in s1), reverse=True) and len(s1) == 3
    assert [m.status for m in s1] == ["active", "used", "expired"]
    assert isinstance(s1[0].code, SecretStr) and s1[1].code is None and s1[2].code is None
    s2 = svc.inbox("s2", at)
    assert len(s2) == 1 and not ({m.id for m in s1} & {m.id for m in s2})
    assert svc.inbox("sess-nobody", at) == ()


def test_verification_is_per_conversation(store: TempStore) -> None:
    """[invariant] Verified in thread A never verifies thread B for the same customer."""
    svc = make_service(store)
    a, b = new_thread(), new_thread()
    locate_and_send(svc, a, "sa", NOW)
    assert isinstance(svc.verify(turn_ids(a), SecretStr(latest_digits(svc, "sa", NOW)), NOW), Verified)
    assert _state(store, b).status == "not_checked"
    svc.locate(b, locator(customer_id=OMAR), NOW)
    assert _state(store, b).status == "located"
    assert _state(store, a).status == "verified"


def test_code_phone_secret_absent_everywhere(store: TempStore, caplog: pytest.LogCaptureFixture) -> None:
    """[negative] Code digits, full phone and session secret appear in no table, log, result or exception."""
    caplog.set_level(logging.DEBUG)
    secret = new_secret()
    svc = make_service(store, secret=secret)
    name, phone = customer_contact(store, OMAR)
    phone_digits = "".join(ch for ch in phone if ch.isdigit())
    thread, session = new_thread(), "sess-a"
    results: list[Any] = []
    results.append(svc.locate(thread, locator(name=name, phone=phone), NOW))
    results.append(svc.send_code(thread, session, NOW))
    msgs = svc.inbox(session, NOW)
    digits = msgs[0].code.get_secret_value() if msgs[0].code else ""
    assert digits
    ids = turn_ids(thread)
    results.append(svc.verify(ids, SecretStr(wrong(digits)), NOW))
    results.append(svc.verify(ids, SecretStr(digits), NOW))
    account = _account()
    read = account.account_tools(store.uow)[0].executor(account.ReadInvoicesArgs(), scope_for_customer(OMAR))
    sinks = [r.model_dump_json() for r in results]
    sinks += [repr(m) for m in msgs] + [repr(r) for r in results]
    sinks += [non_issued_text(store), caplog.text, json.dumps(read.for_model), read.lookup.result_seen]
    sinks += [read.model_dump_json()]
    # an injected-fault exception message is a sink too
    other = make_service(store, secret=secret)
    t2 = new_thread()
    locate_and_send(other, t2, "sess-b", NOW)
    try:
        other.verify(turn_ids(t2), SecretStr("not-a-code"), NOW)
    except Exception as exc:
        sinks += [str(exc), repr(exc)]
    needles = {
        "digits": digits,
        "phone": phone,
        "phone digits": phone_digits,
        "secret": secret.get_secret_value(),
    }
    for label, needle in needles.items():
        for i, sink in enumerate(sinks):
            assert needle not in sink, f"{label} leaked in sink {i}"
    assert "SecretStr('**********')" in repr(msgs[0])
    with store.uow() as tx:
        code = tx.identity.newest_code(thread)
    assert code is not None
    assert len(code.code_hmac) == 64 and code.code_hmac == code.code_hmac.lower() and code.code_hmac != digits
    for rel in ("src/meridian/services/identity.py", "src/meridian/agent/tools/account.py"):
        tree = ast.parse((REPO_ROOT / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(a.name != "logging" for a in node.names), rel
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "print", rel
            if isinstance(node, ast.Name):
                assert node.id != "TraceSink", rel


def test_records_for_cap1_and_wf3(store: TempStore) -> None:
    """[capture] The code-sent row, the verified action and the read's lookup record carry their field sets."""
    svc = make_service(store)
    thread, session = new_thread(), "sess-a"
    locate_and_send(svc, thread, session, NOW)
    assert isinstance(
        svc.verify(turn_ids(thread), SecretStr(latest_digits(svc, session, NOW)), NOW), Verified
    )
    with store.uow() as tx:
        code = tx.identity.newest_code(thread)
        actions = tx.core.actions.for_thread(thread)
    assert code is not None and len(code.code_hmac) == 64 and code.sent_at and code.expires_at
    assert [r[1] for r in raw_rows(store, "PRAGMA table_info(identity_codes)")] == [
        "id", "thread_id", "customer_id", "code_hmac", "held_by", "sent_at", "expires_at", "tries_left",
        "used_at", "inbox_message_id",
    ]  # fmt: skip
    verified = [a for a in actions if a.kind == ActionKind.VERIFIED]
    assert len(verified) == 1 and verified[0].records["customer"] == OMAR
    account = _account()
    scope = scope_for_customer(OMAR, message_id=7)
    res = account.account_tools(store.uow)[0].executor(account.ReadInvoicesArgs(), scope)
    assert res.lookup.tool == "read_invoices"
    assert res.lookup.record_ids == ("INV-204411",)
    assert res.lookup.message_id == scope.message_id and res.lookup.turn_id == scope.ids.turn_id
    assert res.lookup_written is False


def test_inbox_not_held_is_expired(store: TempStore) -> None:
    """[invariant] A message whose digits this process no longer holds is never active (A-6, GRT-2)."""
    secret = new_secret()
    svc1 = make_service(store, secret=secret)
    thread, session = new_thread(), "sess-a"
    locate_and_send(svc1, thread, session, NOW)
    first = svc1.inbox(session, NOW)[0]
    assert first.status == "active" and first.code is not None
    value = first.code.get_secret_value()
    assert len(value) == 6 and value.isascii() and value.isdigit()
    second = make_service(store, secret=secret).inbox(session, NOW)[0]
    assert second.status == "expired" and second.code is None
