"""AEA-02 frozen tests: model conventions, safe errors, secret fields, record types (AC-1, AC-3, AC-10, PA-1).

Frozen by the test-writer before the implementer starts; the implementer must not edit this file.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import importlib
import subprocess
import sys
from collections.abc import Callable
from typing import Any, get_args

import pydantic
import pytest
from pydantic import SecretStr, ValidationError

from meridian.domain.common import CustomerId, MeridianModel, SafeError
from meridian.domain.identity import FormValues, InboxMessage, Locator
from meridian.domain.staff import DemoRole, IssuedSession, LoginSession, LoginSessionId
from meridian.domain.turn import (
    CheckEvent,
    CodePayload,
    Intake,
    PlannerTrace,
    SignalRecord,
    TurnInput,
    TurnTrace,
)

DOMAIN_MODULES = (
    "common",
    "records",
    "actions",
    "identity",
    "specialists",
    "handoff",
    "blocks",
    "turn",
    "tools",
    "state",
    "staff",
)
PORT_MODULES = ("meridian.ports.models", "meridian.ports.runtime")
ALL_MODULES = (
    *(f"meridian.domain.{m}" for m in DOMAIN_MODULES),
    *PORT_MODULES,
    "meridian.config",
)
# Dataclasses (not pydantic models) that the walk must skip by name.
LISTED_DATACLASSES = ("TurnBudget", "TurnContext", "SpanHandle", "TokenPrice")


def _model_classes() -> list[type[pydantic.BaseModel]]:
    seen: dict[int, type[pydantic.BaseModel]] = {}
    for name in ALL_MODULES:
        module = importlib.import_module(name)
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, pydantic.BaseModel)
                and value.__module__.startswith("meridian.")
            ):
                seen[id(value)] = value
    return list(seen.values())


def test_every_model_uses_meridian_config() -> None:
    """[invariant, AC-1] Every pydantic model in domain/*, ports/* and config.py has MeridianModel's configuration."""
    classes = _model_classes()
    print(f"models checked: {len(classes)}")
    assert classes, "no models found: the modules are empty"
    bad: list[str] = []
    for cls in classes:
        config = cls.model_config
        if not (
            config.get("extra") == "forbid"
            and config.get("frozen") is True
            and config.get("hide_input_in_errors") is True
            and config.get("str_strip_whitespace") is True
        ):
            bad.append(f"{cls.__module__}.{cls.__qualname__}")
    assert not bad, f"models off the MeridianModel configuration: {bad}"

    found_dataclasses: dict[str, bool] = {}
    for name in ALL_MODULES:
        module = importlib.import_module(name)
        for dc_name in LISTED_DATACLASSES:
            candidate = vars(module).get(dc_name)
            if candidate is not None and getattr(candidate, "__module__", "").startswith("meridian."):
                found_dataclasses[dc_name] = dataclasses.is_dataclass(candidate)
    assert set(found_dataclasses) == set(LISTED_DATACLASSES), found_dataclasses
    assert all(found_dataclasses.values()), found_dataclasses


def test_rejected_value_absent_from_safe_error(make_sentinel: Callable[[str], str]) -> None:
    """[negative, AC-3] A rejected value never appears in str(exc), repr(exc) or any SafeError a caller can serialise."""

    class _Holder(MeridianModel):
        customer_id: CustomerId

    sentinel = make_sentinel("not-a-customer")
    with pytest.raises(ValidationError) as caught:
        _Holder.model_validate({"customer_id": sentinel})
    exc = caught.value
    assert sentinel not in str(exc)
    assert sentinel not in repr(exc)
    problems = SafeError.from_validation_error(exc)
    assert problems
    for problem in problems:
        assert problem.field and problem.code and problem.constraint
        assert sentinel not in problem.model_dump_json()
        assert sentinel not in repr(problem)

    # The other half of the pair: a Locator model-level rule rejects without echoing the name.
    sentinel_name = make_sentinel("sentinel-name")
    with pytest.raises(ValidationError) as caught_locator:
        Locator.model_validate({"name": sentinel_name})
    assert sentinel_name not in str(caught_locator.value)
    assert sentinel_name not in repr(caught_locator.value)
    for problem in SafeError.from_validation_error(caught_locator.value):
        assert problem.code and problem.constraint
        assert sentinel_name not in problem.model_dump_json()


def _is_secret(annotation: Any) -> bool:
    return annotation is SecretStr or SecretStr in get_args(annotation)


def test_secret_fields_absent_from_repr_and_dump(
    make_sentinel: Callable[[str], str], make_digits: Callable[[], str], make_phone: Callable[[], str]
) -> None:
    """[negative, AC-10] Private values live in SecretStr fields: absent from repr, str and JSON dump."""
    digits = make_digits()
    phone = make_phone()
    token = make_sentinel("token")
    when = dt.datetime(2026, 10, 21, 9, 0, tzinfo=dt.UTC)

    session = LoginSession(
        session_id=LoginSessionId("sess-1"),
        role=DemoRole.CUSTOMER,
        role_reset=False,
        signed_in_at=when,
        expires_at=when,
    )
    objects: dict[str, pydantic.BaseModel] = {
        "FormValues": FormValues(phone=SecretStr(phone)),
        "Intake": Intake(
            kind="code",
            text_store="[code entered]",
            code_digits=SecretStr(digits),
            form=None,
            card_number_seen=False,
            choice=None,
        ),
        "Locator": Locator(name="Test Name", phone=SecretStr(phone)),
        "IssuedSession": IssuedSession(session=session, token=SecretStr(token)),
        "InboxMessage": InboxMessage(
            id="msg-1",
            at=when,
            to_masked="***-***-**00",
            code=SecretStr(digits),
            status="active",
            expires_at=when,
        ),
        "CodePayload": CodePayload(card_id="code-x", code=SecretStr(digits)),
    }
    secrets_in = {
        "FormValues": phone,
        "Intake": digits,
        "Locator": phone,
        "IssuedSession": token,
        "InboxMessage": digits,
        "CodePayload": digits,
    }
    for name, obj in objects.items():
        secret = secrets_in[name]
        assert secret not in repr(obj), name
        assert secret not in str(obj), name
        assert secret not in obj.model_dump_json(), name

    assert _is_secret(FormValues.model_fields["phone"].annotation)
    assert _is_secret(Intake.model_fields["code_digits"].annotation)
    assert _is_secret(Locator.model_fields["phone"].annotation)
    assert _is_secret(IssuedSession.model_fields["token"].annotation)
    assert _is_secret(InboxMessage.model_fields["code"].annotation)
    assert "code_digits" not in TurnInput.model_fields
    assert "form" not in TurnInput.model_fields


_FORBIDDEN_TEXT_FIELDS = {
    "text",
    "message",
    "content",
    "body",
    "quote",
    "wanted_text",
    "phone",
    "code_digits",
}


def test_record_types_hold_codes_only() -> None:
    """[invariant, AC-10] The four record types carry codes and ids, never free text."""
    expected: dict[str, tuple[type[pydantic.BaseModel], set[str]]] = {
        "CheckEvent": (CheckEvent, {"check", "turn_id", "result", "removed", "claim_kinds", "codes"}),
        "SignalRecord": (
            SignalRecord,
            {
                "record",
                "name",
                "turn_id",
                "thread_id",
                "request_id",
                "run_tag",
                "node",
                "cause",
                "role",
                "specialist",
                "attempt",
                "recovered",
            },
        ),
        "PlannerTrace": (
            PlannerTrace,
            {
                "model",
                "fallback_used",
                "failure",
                "plan_mode",
                "plan_source",
                "intents",
                "handoff_request",
                "topic",
                "planner_failed",
            },
        ),
        "TurnTrace": (
            TurnTrace,
            {
                "gate_result",
                "path",
                "outcome",
                "degrade_reason",
                "planner",
                "danger_raised",
                "specialists_run",
            },
        ),
    }
    for name, (cls, fields) in expected.items():
        actual = set(cls.model_fields)
        print(f"{name}: {sorted(actual)}")
        assert actual == fields, name
        assert not (actual & _FORBIDDEN_TEXT_FIELDS), name


@pytest.mark.parametrize("module", [f"meridian.domain.{m}" for m in DOMAIN_MODULES] + list(PORT_MODULES))
def test_each_domain_module_imports_alone(module: str) -> None:
    """[invariant, PA-1] Every domain and port module imports on its own in a fresh interpreter (no import cycle)."""
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        check=False,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
