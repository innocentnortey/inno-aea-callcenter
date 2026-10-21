"""FU-saveFollowUp-text: `CaseService.set_followup` saves an email follow-up to a general destination.

Labels: invariant, negative, regression. Level: mock-tested (real CaseService over a temp SQLite copy of the issued DB;
no server, no model). Phone numbers and emails are read from the issued data at run time; none is written in this file.
"""

from __future__ import annotations

import re
from typing import Any

import jsonschema
import pytest

from meridian.domain.handoff import HandoffReason
from tests.api.openapi_check import load_document
from tests.services._case_fixtures import (
    NOW,
    OMAR,
    code_of,
    contact_of,
    ctx,
    followup_choice,
    is_rejected,
    j,
    jtext,
    new_thread,
    request,
    services,
    set_identity,
    store,
)

FOLLOW_UP_VIEW: dict[str, Any] = dict(load_document()["components"]["schemas"]["FollowUpView"])
SEND_CLAIM = re.compile(r"(?<!not )\bsent\b|sent you|emailed you|called you", re.IGNORECASE)


def _open_case(s: Any, handoff: Any, *, verified: bool) -> tuple[Any, Any]:
    with s.uow(write=True) as tx:
        thread, _ = new_thread(tx, customer_text="Please get back to me.")
        if verified:
            set_identity(tx, thread, "verified", OMAR)
        tx.commit()
    req = (
        request(thread, HandoffReason.REFUND, verified_customer=OMAR)
        if verified
        else request(thread, HandoffReason.REFUND)
    )
    return thread, handoff.open(req, ctx(thread, req.turn_id)).case


def test_wp7_email_general_saved() -> None:
    with store() as s:
        cases, handoff, _, _ = services(s.uow)
        thread, case = _open_case(s, handoff, verified=False)
        saved = cases.set_followup(thread, followup_choice("email", "general", "any"), NOW)
        assert not is_rejected(saved)
        assert j(saved) == {
            "channel": "email",
            "destination_label": "a general contact",
            "on_record": False,
            "window": "any",
            "saved_line": "Follow-up saved: email, any time.",
        }
        jsonschema.validate(j(saved), FOLLOW_UP_VIEW)
        with s.uow() as tx:
            stored = tx.cases.followups.get(case.case_ref)
            events = [
                e for e in tx.cases.case_events.list_for_case(case.case_ref) if e.kind == "followup_saved"
            ]
        assert stored is not None
        assert (
            stored.channel,
            stored.destination,
            stored.on_record,
            stored.window,
            stored.destination_label,
            stored.saved_line,
        ) == ("email", "general", False, "any", "a general contact", "Follow-up saved: email, any time.")
        assert len(events) == 1
        assert dict(events[0].detail) == {"channel": "email", "on_record": False, "window": "any"}


@pytest.mark.parametrize(
    ("window", "word"), [("morning", "mornings"), ("afternoon", "afternoons"), ("any", "any time")]
)
def test_email_general_window_words(window: str, word: str) -> None:
    with store() as s:
        cases, handoff, _, _ = services(s.uow)
        thread, _ = _open_case(s, handoff, verified=False)
        saved = cases.set_followup(thread, followup_choice("email", "general", window), NOW)
        assert not is_rejected(saved)
        assert saved.saved_line == f"Follow-up saved: email, {word}."
        assert saved.window == window


def test_email_general_verified_customer_reads_no_contact() -> None:
    with store() as s:
        cases, handoff, _, _ = services(s.uow)
        thread, case = _open_case(s, handoff, verified=True)
        saved = cases.set_followup(thread, followup_choice("email", "general", "morning"), NOW)
        assert not is_rejected(saved)
        assert saved.saved_line == "Follow-up saved: email, mornings."
        assert saved.on_record is False
        assert saved.destination_label == "a general contact"
        with s.uow() as tx:
            phone, digits, email = contact_of(tx)
            stored = tx.cases.followups.get(case.case_ref)
        assert stored is not None
        for blob in (jtext(saved), stored.model_dump_json()):
            assert phone not in blob and digits not in blob and email not in blob
        assert not SEND_CLAIM.search(saved.saved_line)


def test_email_general_no_open_case_refused() -> None:
    with store() as s:
        cases, _, _, _ = services(s.uow)
        with s.uow(write=True) as tx:
            lone, _ = new_thread(tx, customer_text="Hello.")
            tx.commit()
        refused = cases.set_followup(lone, followup_choice("email", "general", "any"), NOW)
        assert is_rejected(refused) and code_of(refused) == "NOT_ALLOWED_IN_STATE"
        assert j(refused)["details"] == {"state": "no_open_case"}


def test_other_combinations_unchanged() -> None:
    """Phone on record is byte-identical; email on record and phone general still raise.

    Whoever adds those two texts replaces the `pytest.raises` blocks.
    """
    phone_line = "Follow-up saved: phone call, the number ending in 02, mornings."
    with store() as s:
        cases, handoff, _, _ = services(s.uow)
        thread, case = _open_case(s, handoff, verified=True)
        phone = cases.set_followup(thread, followup_choice("phone", "on_record", "morning"), NOW)
        assert phone.saved_line == phone_line
        assert phone.destination_label == "the number ending in 02"
        for channel, destination in (("email", "on_record"), ("phone", "general")):
            with pytest.raises(NotImplementedError, match="blocked-on"):
                cases.set_followup(thread, followup_choice(channel, destination, "any"), NOW)
        with s.uow() as tx:
            stored = tx.cases.followups.get(case.case_ref)
        assert stored is not None
        assert stored.channel == "phone"
        assert stored.saved_line == phone_line
