"""AEA-20 ModelGateway: frozen tests (written first, from the acceptance criteria and the plan's named tests).

Each test names the failure mode it guards: invariant, boundary, regression, failure/refusal, capture, negative.
Doubles live in _gateway_doubles.py. No paid call, no network, no secret.
"""

from __future__ import annotations

import ast
import inspect
import logging
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest

import meridian.agent.gateway as gateway_module
from meridian.agent.gateway import CallLedger, ModelGateway, ModelOutcome
from meridian.domain.common import HaltReason, ProviderFailure, ProviderFailureKind
from meridian.domain.turn import TurnBudget, TurnContext
from meridian.policy.limits import Limits
from meridian.ports.models import Role, StructuredRequest
from meridian.privacy.redact import RedactionProfile, redact

from ._gateway_doubles import (
    FakeAdmission,
    FakeClock,
    JevChoice,
    RecordingLedger,
    Reply,
    SonnetStructured,
    SonnetTools,
    budget,
    build_gateway,
    call_role,
    card_like,
    choice_request,
    context,
    default_doubles,
    email_seed,
    failure,
    gateway_kwargs,
    key_sentinel,
    six_digit_code,
    spec,
    street_seed,
    structured_request,
    tool_request,
    wp2_line,
    wp2_phone,
)

_ALL_ROLES = list(Role)
_GATEWAY_SOURCE = Path(gateway_module.__file__ or "")
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _clocked(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    clock = FakeClock()
    monkeypatch.setattr(gateway_module, "_monotonic", clock.now)
    monkeypatch.setattr(gateway_module, "_sleep", clock.sleep)
    return clock


def _mypy_rejects_planner_as_structured_role(
    gw: ModelGateway, req: StructuredRequest[Reply], ctx: TurnContext
) -> None:
    """Static check for AC-1 (invariant): never called. `uv run mypy` passes only if it reports arg-type here."""
    gw.structured(Role.PLANNER, req, ctx)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------------------------------------------
# AC-1 [invariant] role maps decide the adapter and the spec
# ---------------------------------------------------------------------------------------------------------------


def test_role_maps_route_each_role(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-1 invariant: each role reaches its own adapter with its own RoleSpec."""
    clock = _clocked(monkeypatch)
    specs = {
        Role.PLANNER: spec(cap_s=3.0, redaction=RedactionProfile.JEV, max_tokens=101, effort=None),
        Role.CLASSIFIER: spec(cap_s=3.0, redaction=RedactionProfile.JEV, max_tokens=102, effort=None),
        Role.PLANNER_FALLBACK: spec(cap_s=8.0, redaction=RedactionProfile.SONNET, max_tokens=103),
        Role.RESPONDER: spec(cap_s=12.0, redaction=RedactionProfile.SONNET, max_tokens=104),
        Role.BRIEF: spec(cap_s=12.0, redaction=RedactionProfile.SONNET, max_tokens=105, effort="medium"),
        Role.SPECIALIST: spec(cap_s=8.0, redaction=RedactionProfile.SONNET, max_tokens=106, effort="high"),
    }
    gw, d = build_gateway(specs=specs)
    ctx = context(budget(clock, 60.0))
    adapters: dict[Role, Any] = {
        Role.PLANNER: d.planner,
        Role.CLASSIFIER: d.classifier,
        Role.PLANNER_FALLBACK: d.fallback,
        Role.RESPONDER: d.responder,
        Role.BRIEF: d.brief,
        Role.SPECIALIST: d.specialist,
    }
    for role in _ALL_ROLES:
        call_role(gw, role, ctx, wp2_line())
    for role, adapter in adapters.items():
        want = specs[role]
        assert len(adapter.requests) == 1, role
        assert adapter.timeouts == [want.cap_s], role
        req = adapter.requests[0]
        if role in (Role.RESPONDER, Role.BRIEF, Role.SPECIALIST):
            assert req.max_tokens == want.max_tokens != 9999, role
            assert req.effort == want.effort, role
        main = req.system if role in (Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK) else None
        if role in (Role.RESPONDER, Role.BRIEF):
            main = req.user
        if role is Role.SPECIALIST:
            main = req.system_dynamic
        assert main == redact(wp2_line(), want.redaction).text, role
    by_role = {rec.role: rec for rec, _ in d.ledger.records}
    assert set(by_role) == set(Role)
    for role, adapter in adapters.items():
        assert by_role[role].model == adapter.model


# ---------------------------------------------------------------------------------------------------------------
# AC-2 [failure/refusal] provider admission
# ---------------------------------------------------------------------------------------------------------------


def test_refused_provider_halts_without_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-2 failure/refusal: REFUSE halts with PROVIDER_SPEND_CAP and touches nothing (MOD-11)."""
    clock = _clocked(monkeypatch)
    ledger = RecordingLedger(admissions=[FakeAdmission.REFUSE])
    gw, d = build_gateway(ledger=ledger)
    ctx = context(budget(clock, 60.0))
    out = call_role(gw, Role.RESPONDER, ctx)
    assert out.value is None
    assert out.calls == ()
    assert out.failure is None
    assert out.halt is not None
    assert out.halt.reason == HaltReason.PROVIDER_SPEND_CAP
    assert out.halt.node == "responder"
    assert d.responder.requests == []
    assert ledger.records == []
    assert d.sink.model_calls == []
    # no brake count was taken: six further calls all reach the adapter
    for _ in range(Limits().brakes.sonnet_calls):
        assert call_role(gw, Role.RESPONDER, ctx).halt is None
    assert len(d.responder.requests) == Limits().brakes.sonnet_calls
    assert ledger.allow_turn_calls == 0
    assert ledger.models_disabled_calls == 0
    source = _GATEWAY_SOURCE.read_text()
    assert "allow_turn" not in source
    assert "models_disabled" not in source
    assert re.search(r"(?<!PROVIDER_)SPEND_CAP\b", source) is None


# ---------------------------------------------------------------------------------------------------------------
# AC-3 [invariant] deadline
# ---------------------------------------------------------------------------------------------------------------


def test_timeout_is_min_of_cap_and_remaining(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-3 invariant: timeout_s == min(cap_s, time left)."""
    clock = _clocked(monkeypatch)
    gw, d = build_gateway()
    ctx = context(budget(clock, 60.0))
    for role in (Role.PLANNER, Role.SPECIALIST, Role.RESPONDER, Role.BRIEF):
        call_role(gw, role, ctx)
    assert d.planner.timeouts == [3.0]
    assert d.specialist.timeouts == [8.0]
    assert d.responder.timeouts == [12.0]
    assert d.brief.timeouts == [12.0]
    short = context(budget(clock, 5.0))
    call_role(gw, Role.RESPONDER, short)
    call_role(gw, Role.PLANNER, short)
    assert d.responder.timeouts[-1] == 5.0
    assert d.planner.timeouts[-1] == 3.0


def test_deadline_halts_without_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-3 boundary: under 1.0 s left, every role halts with DEADLINE and makes no call."""
    clock = _clocked(monkeypatch)
    gw, d = build_gateway()
    ctx = context(budget(clock, 0.5))
    for role in _ALL_ROLES:
        out = call_role(gw, role, ctx)
        assert out.halt is not None
        assert out.halt.reason == HaltReason.DEADLINE
        assert out.halt.node == role.value
        assert out.calls == ()
        assert out.value is None
    for adapter in (d.planner, d.classifier, d.fallback, d.responder, d.brief, d.specialist):
        assert adapter.requests == []
    assert d.ledger.records == []
    assert d.sink.model_calls == []
    assert gw._sonnet_calls == {}


# ---------------------------------------------------------------------------------------------------------------
# AC-4 [failure/refusal] retry
# ---------------------------------------------------------------------------------------------------------------

_K = ProviderFailureKind


@dataclass(frozen=True)
class RetryCase:
    id: str
    admission: FakeAdmission
    script: tuple[ProviderFailure | None, ...]
    left: float
    attempts: int
    wait: str | float | None  # None: no wait; "backoff": 0.5-1.0; float: exactly that
    value_set: bool
    failure_kind: ProviderFailureKind | None
    second_timeout: float | None = None
    closes: tuple[str, ...] = ()
    unused_script: int = 0


RETRY_CASES = [
    RetryCase(
        "overloaded_then_ok",
        FakeAdmission.ALLOW,
        (failure(_K.OVERLOADED), None),
        60,
        2,
        "backoff",
        True,
        None,
    ),
    RetryCase(
        "rate_limited_60s_with_20s_left",
        FakeAdmission.ALLOW,
        (failure(_K.RATE_LIMITED, retry_after_s=60.0),),
        20,
        1,
        None,
        False,
        _K.RATE_LIMITED,
    ),
    RetryCase(
        "rate_limited_no_header_backoff",
        FakeAdmission.ALLOW,
        (failure(_K.RATE_LIMITED), None),
        20,
        2,
        "backoff",
        True,
        None,
    ),
    RetryCase(
        "backoff_does_not_fit",
        FakeAdmission.ALLOW,
        (failure(_K.RATE_LIMITED),),
        1.4,
        1,
        None,
        False,
        _K.RATE_LIMITED,
    ),
    RetryCase(
        "retry_after_fits",
        FakeAdmission.ALLOW,
        (failure(_K.RATE_LIMITED, retry_after_s=5.0), None),
        10,
        2,
        5.0,
        True,
        None,
        second_timeout=5.0,
    ),
    RetryCase(
        "non_retryable", FakeAdmission.ALLOW, (failure(_K.BAD_REQUEST),), 60, 1, None, False, _K.BAD_REQUEST
    ),
    RetryCase(
        "two_retryable_failures",
        FakeAdmission.ALLOW,
        (failure(_K.SERVER), failure(_K.SERVER), None),
        60,
        2,
        "backoff",
        False,
        _K.SERVER,
        unused_script=1,
    ),
    RetryCase(
        "probe_single_attempt",
        FakeAdmission.PROBE,
        (failure(_K.OVERLOADED), None),
        60,
        1,
        None,
        False,
        _K.OVERLOADED,
        closes=("anthropic",),
        unused_script=1,
    ),
]


@pytest.mark.parametrize("case", RETRY_CASES, ids=[c.id for c in RETRY_CASES])
def test_retry_at_most_once_and_only_if_it_fits(case: RetryCase, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-4 failure/refusal: at most 2 attempts, the second only when its wait plus 1 s fits; PROBE gets one."""
    clock = _clocked(monkeypatch)
    ledger = RecordingLedger(admissions=[case.admission])
    responder = SonnetStructured("sonnet-responder", script=list(case.script))
    gw, _ = build_gateway(ledger=ledger, responder=responder)
    b = budget(clock, float(case.left))
    ctx = context(b)
    t0 = clock.now()
    out = call_role(gw, Role.RESPONDER, ctx)
    assert len(responder.requests) == case.attempts
    assert len(out.calls) == case.attempts
    assert (out.value is not None) is case.value_set
    if case.failure_kind is None:
        assert out.failure is None
    else:
        assert out.failure is not None
        assert out.failure.kind == case.failure_kind
    assert out.halt is None
    if case.wait is None:
        assert clock.waits == []
    else:
        assert len(clock.waits) == 1
        started, w = clock.waits[0]
        assert started == t0
        if case.wait == "backoff":
            assert 0.5 <= w <= 1.0
        else:
            assert w == case.wait
        assert started + w + 1.0 <= b.deadline
    if case.second_timeout is not None:
        assert responder.timeouts[1] == case.second_timeout
    assert tuple(ledger.closes) == case.closes
    assert len(responder.script) == case.unused_script


# ---------------------------------------------------------------------------------------------------------------
# AC-5 [capture] one ledger row and one span per attempt
# ---------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("role", "script", "attempts"),
    [
        (Role.RESPONDER, [None], 1),
        (Role.RESPONDER, [failure(_K.OVERLOADED), None], 2),
        (Role.RESPONDER, [failure(_K.SERVER), failure(_K.SERVER)], 2),
    ],
    ids=["ok", "retried_ok", "two_failures"],
)
def test_every_attempt_records_ledger_and_span(
    role: Role, script: list[ProviderFailure | None], attempts: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-5 capture: exactly one ledger.record and one trace.model_call per attempt, success or failure."""
    clock = _clocked(monkeypatch)
    responder = SonnetStructured("sonnet-responder", script=list(script))
    gw, d = build_gateway(responder=responder)
    ctx = context(budget(clock, 60.0))
    out = call_role(gw, role, ctx)
    assert len(d.ledger.records) == len(d.sink.model_calls) == attempts
    for i, (rec, ids) in enumerate(d.ledger.records):
        assert rec.attempt == i + 1
        assert rec.role == role
        assert rec.model_dump(exclude={"role", "attempt"}) == responder.calls_returned[i].model_dump()
        assert ids is ctx.ids
    for parent, _, _, _ in d.sink.model_calls:
        assert parent is ctx.span
    assert out.calls == tuple(r for r, _ in d.ledger.records) == tuple(c[1] for c in d.sink.model_calls)


def test_planner_attempt_is_recorded_with_its_role(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-5 capture: a Jev call is recorded too, with the planner role and attempt 1."""
    clock = _clocked(monkeypatch)
    gw, d = build_gateway()
    ctx = context(budget(clock, 60.0))
    call_role(gw, Role.PLANNER, ctx)
    assert [(r.role, r.attempt, r.provider) for r, _ in d.ledger.records] == [
        (Role.PLANNER, 1, "openrouter_jev")
    ]
    assert len(d.sink.model_calls) == 1


# ---------------------------------------------------------------------------------------------------------------
# AC-6 [failure/refusal] circuit
# ---------------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class CircuitCase:
    id: str
    role: Role
    admission: FakeAdmission
    fail: ProviderFailure | None
    trips: int
    closes: tuple[str, ...]
    halt: bool
    provider: str


CIRCUIT_CASES = [
    CircuitCase(
        "a_provider_cap",
        Role.RESPONDER,
        FakeAdmission.ALLOW,
        failure(_K.PROVIDER_SPEND_CAP, retryable=True),
        1,
        (),
        True,
        "anthropic",
    ),
    CircuitCase(
        "b_our_limit",
        Role.RESPONDER,
        FakeAdmission.ALLOW,
        failure(_K.OUR_SPEND_LIMIT, retryable=True),
        1,
        (),
        True,
        "anthropic",
    ),
    CircuitCase(
        "c_jev_cap",
        Role.PLANNER,
        FakeAdmission.ALLOW,
        failure(_K.PROVIDER_SPEND_CAP, "openrouter_jev", retryable=True),
        1,
        (),
        True,
        "openrouter_jev",
    ),
    CircuitCase(
        "d_probe_ok", Role.RESPONDER, FakeAdmission.PROBE, None, 0, ("anthropic",), False, "anthropic"
    ),
    CircuitCase(
        "e_probe_overloaded",
        Role.RESPONDER,
        FakeAdmission.PROBE,
        failure(_K.OVERLOADED),
        0,
        ("anthropic",),
        False,
        "anthropic",
    ),
    CircuitCase(
        "f_probe_cap",
        Role.RESPONDER,
        FakeAdmission.PROBE,
        failure(_K.PROVIDER_SPEND_CAP),
        1,
        (),
        True,
        "anthropic",
    ),
]


@pytest.mark.parametrize("case", CIRCUIT_CASES, ids=[c.id for c in CIRCUIT_CASES])
def test_spend_cap_kinds_trip_and_probe_closes(case: CircuitCase, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-6 failure/refusal: cap failures trip the provider circuit with no retry; a PROBE that ends in anything else closes it."""
    clock = _clocked(monkeypatch)
    ledger = RecordingLedger(admissions=[case.admission])
    script: list[ProviderFailure | None] = [case.fail, None]
    kwargs: dict[str, Any] = (
        {"planner": JevChoice("jev-planner", script=script)}
        if case.role is Role.PLANNER
        else {"responder": SonnetStructured("sonnet-responder", script=script)}
    )
    gw, d = build_gateway(ledger=ledger, **kwargs)
    adapter = d.planner if case.role is Role.PLANNER else d.responder
    out = call_role(gw, case.role, context(budget(clock, 60.0)))
    assert len(adapter.requests) == 1
    assert len(ledger.trips) == case.trips
    assert tuple(ledger.closes) == case.closes
    assert ledger.admitted == [case.provider]
    if case.halt:
        assert out.halt is not None
        assert out.halt.reason == HaltReason.PROVIDER_SPEND_CAP
        assert case.fail is not None
        assert out.failure is not None
        assert out.failure.kind == case.fail.kind
        assert ledger.trips == [out.failure]
    else:
        assert out.halt is None
        assert (out.failure is None) is (case.fail is None)


# ---------------------------------------------------------------------------------------------------------------
# AC-7 [failure/refusal] Sonnet-call brake
# ---------------------------------------------------------------------------------------------------------------

_SONNET_CYCLE = (Role.PLANNER_FALLBACK, Role.RESPONDER, Role.BRIEF, Role.SPECIALIST)


def test_sonnet_call_brake_counts_logical_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-7 failure/refusal: the (limit+1)th logical Anthropic call halts; retries and Jev never count; bounded map."""
    clock = _clocked(monkeypatch)
    limit = Limits().brakes.sonnet_calls
    assert limit == 6

    # (i) mixed roles, then one more
    gw, d = build_gateway()
    ctx = context(budget(clock, 60.0))
    for i in range(limit):
        assert call_role(gw, _SONNET_CYCLE[i % 4], ctx).halt is None
    before = len(d.responder.requests)
    out = call_role(gw, Role.RESPONDER, ctx)
    assert out.halt is not None
    assert out.halt.reason == HaltReason.BRAKE_SONNET_CALLS
    assert out.halt.node == "responder"
    assert len(d.responder.requests) == before
    assert out.calls == ()

    # (ii) a retried call counts once
    responder = SonnetStructured("sonnet-responder", script=[failure(_K.OVERLOADED), None])
    gw, d = build_gateway(responder=responder)
    ctx = context(budget(clock, 60.0))
    for _ in range(limit):
        assert call_role(gw, Role.RESPONDER, ctx).value is not None
    assert len(responder.requests) == limit + 1
    out = call_role(gw, Role.RESPONDER, ctx)
    assert out.halt is not None
    assert out.halt.reason == HaltReason.BRAKE_SONNET_CALLS
    assert len(responder.requests) == limit + 1

    # (iii) Jev calls never count
    gw, d = build_gateway()
    ctx = context(budget(clock, 60.0))
    for _ in range(10):
        assert call_role(gw, Role.PLANNER, ctx).halt is None
    for _ in range(limit):
        assert call_role(gw, Role.RESPONDER, ctx).halt is None

    # (iv) Try again: same turn_id, new TurnBudget starts at zero
    gw, d = build_gateway()
    budget_a = budget(clock, 60.0)
    ctx_a = context(budget_a)
    for _ in range(limit):
        call_role(gw, Role.RESPONDER, ctx_a)
    assert call_role(gw, Role.RESPONDER, ctx_a).halt is not None
    clock.advance(1.0)
    ctx_b = context(budget(clock, 60.0), turn_id=ctx_a.ids.turn_id)
    assert ctx_b.ids.turn_id == ctx_a.ids.turn_id
    assert call_role(gw, Role.RESPONDER, ctx_b).halt is None

    # (v) the counter map stays bounded over 1,000 sequential turns
    gw, d = build_gateway()
    for _ in range(1000):
        turn_ctx = context(budget(clock, 60.0))
        assert call_role(gw, Role.RESPONDER, turn_ctx).halt is None
        assert len(gw._sonnet_calls) <= 2
        assert all(e.deadline >= clock.now() - 1.0 for e in gw._sonnet_calls.values())
        clock.advance(61.5)


# ---------------------------------------------------------------------------------------------------------------
# AC-8 [negative] redaction by role, nothing sensitive in spans or logs
# ---------------------------------------------------------------------------------------------------------------


def test_redaction_profile_per_role(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-8 negative: JEV hides everything; SONNET keeps name and IDs but no phone, card, code, email or street."""
    caplog.set_level(logging.DEBUG)
    clock = _clocked(monkeypatch)
    phone, card, code, mail, street = wp2_phone(), card_like(), six_digit_code(), email_seed(), street_seed()
    seeded = f"{wp2_line()}. card {card} code {code} mail {mail} at {street}"
    key = key_sentinel()
    responder = SonnetStructured(
        "sonnet-responder", next_value=Reply(text=f"call {phone} code {code} {mail}"), api_key=key
    )
    planner = JevChoice("jev-planner", api_key=key)
    specialist = SonnetTools("sonnet-specialist", api_key=key)
    gw, d = build_gateway(responder=responder, planner=planner, specialist=specialist)
    ctx = context(budget(clock, 60.0))

    jev_req = choice_request(seeded, instructions=f"Pick one for {seeded}")
    out_p = gw.choose(Role.PLANNER, jev_req, ctx)
    assert out_p.value is not None
    gw.structured(Role.RESPONDER, structured_request(seeded, system_dynamic=seeded), ctx)
    gw.tool_step(Role.SPECIALIST, tool_request(seeded), ctx)

    jev_dump = planner.requests[0].model_dump_json()
    for forbidden in ("Omar Patel", phone, "MHC-10002", "INV-204411", card, code, mail, street):
        assert forbidden not in jev_dump
    for token in ("[name]", "[phone]", "[customer id]", "[invoice id]"):
        assert token in jev_dump

    sonnet_dumps = [
        responder.requests[0].model_dump_json(exclude={"output_model"}),
        specialist.requests[0].model_dump_json(),
    ]
    for dump in sonnet_dumps:
        for forbidden in (card, code, mail, street, phone):
            assert forbidden not in dump
        for kept in ("[phone ending 02]", "Omar Patel", "MHC-10002", "INV-204411"):
            assert kept in dump

    assert len(d.sink.model_calls) == 3
    for _, _, masked_in, masked_out in d.sink.model_calls:
        for forbidden in (phone, code, card, key):
            assert forbidden not in masked_in
            assert forbidden not in masked_out
    for forbidden in (phone, code, card, key):
        assert forbidden not in caplog.text


# ---------------------------------------------------------------------------------------------------------------
# AC-9 [invariant] a failed attempt is an outcome, never an exception
# ---------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("kind", list(ProviderFailureKind), ids=lambda k: k.value)
def test_failed_attempt_returns_outcome(kind: ProviderFailureKind, monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-9 invariant: every failure kind yields a ModelOutcome with the failure set, recorded once."""
    clock = _clocked(monkeypatch)
    responder = SonnetStructured("sonnet-responder", script=[failure(kind, retryable=False)])
    gw, d = build_gateway(responder=responder)
    out = call_role(gw, Role.RESPONDER, context(budget(clock, 60.0)))
    assert isinstance(out, ModelOutcome)
    assert out.value is None
    assert out.failure is not None
    assert out.failure.kind == kind
    assert len(out.calls) == 1
    if kind in (_K.PROVIDER_SPEND_CAP, _K.OUR_SPEND_LIMIT):
        assert out.halt is not None
        assert out.halt.reason == HaltReason.PROVIDER_SPEND_CAP
    else:
        assert out.halt is None
    assert len(d.ledger.records) == 1
    assert d.ledger.records[0][0].status == "error"


# ---------------------------------------------------------------------------------------------------------------
# AC-10 [invariant] no SDK, no unit of work
# ---------------------------------------------------------------------------------------------------------------


def test_gateway_imports_no_sdk() -> None:
    """AC-10 invariant: agent/gateway.py imports no provider SDK, HTTP client or adapter, and opens no unit of work."""
    path = _REPO_ROOT / "src" / "meridian" / "agent" / "gateway.py"
    source = path.read_text()
    banned = {"anthropic", "httpx", "openai", "langfuse", "sqlite3", "fastembed"}
    offenders: list[str] = []
    for node in ast.walk(ast.parse(source)):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        for name in names:
            if name.split(".")[0] in banned or name.startswith(("meridian.adapters", "meridian.services")):
                offenders.append(name)
    assert offenders == []
    params = list(inspect.signature(ModelGateway.__init__).parameters)
    assert params == ["self", "choice", "structured", "tools", "ledger", "trace", "redact", "limits"]
    assert "UnitOfWork" not in source


# ---------------------------------------------------------------------------------------------------------------
# WP-2 worked pair
# ---------------------------------------------------------------------------------------------------------------


def test_wp2_first_turn_planner_and_responder(monkeypatch: pytest.MonkeyPatch) -> None:
    """WP-2 worked pair: planner sees placeholders, responder keeps name and IDs and shows the phone's last two."""
    clock = _clocked(monkeypatch)
    gw, d = build_gateway()
    ctx = context(budget(clock, 60.0))
    req = choice_request(wp2_line())
    req = req.model_copy(
        update={
            "state": {
                "recent_chat": [wp2_line()],
                "new_message": "I got an invoice … and I'm not sure what it's for.",
            }
        }
    )
    gw.choose(Role.PLANNER, req, ctx)
    dump = d.planner.requests[0].model_dump_json()
    for token in ("[name]", "[phone]", "[customer id]", "[invoice id]"):
        assert token in dump
    for raw in ("Omar Patel", wp2_phone(), "MHC-10002", "INV-204411"):
        assert raw not in dump
    assert d.planner.timeouts == [3.0]
    assert len(d.ledger.records) == 1
    assert len(d.sink.model_calls) == 1
    rec, _ = d.ledger.records[0]
    assert (rec.role, rec.attempt, rec.model) == (Role.PLANNER, 1, d.planner.model)
    assert d.sink.model_calls[0][0] is ctx.span

    gw.structured(Role.RESPONDER, structured_request(wp2_line()), ctx)
    user = d.responder.requests[0].user
    for kept in ("Omar Patel", "MHC-10002", "INV-204411", "[phone ending 02]"):
        assert kept in user
    assert wp2_phone() not in user


# ---------------------------------------------------------------------------------------------------------------
# P-1 [invariant] misconfigured maps are refused at construction
# ---------------------------------------------------------------------------------------------------------------


def _bad_maps() -> list[tuple[str, dict[str, Any]]]:
    d = default_doubles()
    good = gateway_kwargs(d)
    jev_spec = d.specs[Role.PLANNER]
    sonnet_spec = d.specs[Role.RESPONDER]
    cases: list[tuple[str, dict[str, Any]]] = [
        ("planner_in_structured", {"structured": {Role.PLANNER: (d.responder, sonnet_spec)}}),
        ("responder_in_choice", {"choice": {Role.RESPONDER: (d.fallback, sonnet_spec)}}),
        ("brief_in_tools", {"tools": {Role.BRIEF: (d.specialist, sonnet_spec)}}),
        ("jev_in_structured", {"structured": {Role.RESPONDER: (d.planner, jev_spec)}}),
        ("jev_in_tools", {"tools": {Role.SPECIALIST: (d.planner, jev_spec)}}),
        ("jev_with_sonnet_profile", {"choice": {**good["choice"], Role.PLANNER: (d.planner, sonnet_spec)}}),
    ]
    for profile in (RedactionProfile.LOG, RedactionProfile.STORE, RedactionProfile.TRACE):
        bad = spec(cap_s=12.0, redaction=profile)
        cases.append(
            (
                f"responder_profile_{profile.value}",
                {"structured": {**good["structured"], Role.RESPONDER: (d.responder, bad)}},
            )
        )
    return cases


@pytest.mark.parametrize(("name", "override"), _bad_maps(), ids=[n for n, _ in _bad_maps()])
def test_constructor_rejects_misconfigured_maps(name: str, override: dict[str, Any]) -> None:
    """P-1 invariant: Jev can never be asked to write a reply; only JEV/SONNET profiles may leave for a provider."""
    kwargs = {**gateway_kwargs(default_doubles()), **override}
    with pytest.raises(ValueError):
        ModelGateway(**cast(Any, kwargs))


def test_missing_role_entry_raises_on_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """P-1 boundary: a role with no entry raises ValueError when called, not at construction."""
    clock = _clocked(monkeypatch)
    d = default_doubles()
    kwargs = gateway_kwargs(d)
    kwargs["choice"] = {Role.PLANNER: kwargs["choice"][Role.PLANNER]}
    kwargs["structured"] = {}
    kwargs["tools"] = {}
    gw = ModelGateway(**cast(Any, kwargs))
    ctx = context(budget(clock, 60.0))
    assert gw.choose(Role.PLANNER, choice_request("hello"), ctx).value is not None
    with pytest.raises(ValueError):
        gw.choose(Role.CLASSIFIER, choice_request("hello"), ctx)


# ---------------------------------------------------------------------------------------------------------------
# P-2 [invariant] the brake is safe under concurrent calls
# ---------------------------------------------------------------------------------------------------------------


def test_brake_counter_is_thread_safe() -> None:
    """P-2 invariant: 8 concurrent Sonnet calls in one turn make exactly `limit` requests and halt the rest."""
    limit = Limits().brakes.sonnet_calls
    gw, d = build_gateway()
    now = time.monotonic()
    ctx = context(TurnBudget(started=now, deadline=now + 60.0))
    barrier = threading.Barrier(8)
    outcomes: list[ModelOutcome[Any]] = []
    errors: list[BaseException] = []
    lock = threading.Lock()

    def worker() -> None:
        try:
            barrier.wait(timeout=10)
            out = gw.structured(Role.RESPONDER, structured_request("hello"), ctx)
            with lock:
                outcomes.append(out)
        except BaseException as exc:
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=20)
    assert errors == []
    assert len(d.responder.requests) == limit
    halted = [o for o in outcomes if o.halt is not None and o.halt.reason == HaltReason.BRAKE_SONNET_CALLS]
    assert len(outcomes) == 8
    assert len(halted) == 8 - limit


# ---------------------------------------------------------------------------------------------------------------
# P-3 [capture] span text is the TRACE-masked rendered request
# ---------------------------------------------------------------------------------------------------------------


def test_span_text_is_trace_masked_rendered_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """P-3 capture: spans hold the rendered request after TRACE masking; provider message items never appear."""
    clock = _clocked(monkeypatch)
    gw, d = build_gateway()
    ctx = context(budget(clock, 60.0))
    gw.choose(Role.PLANNER_FALLBACK, choice_request("PLANNER-SYSTEM-MARKER " + wp2_line()), ctx)
    assert "Omar Patel" in d.fallback.requests[0].model_dump_json()
    _, _, masked_in, _ = d.sink.model_calls[0]
    for present in ("PLANNER-SYSTEM-MARKER", "This is [name]", "MHC-10002", "[phone ending 02]"):
        assert present in masked_in
    assert "Omar Patel" not in masked_in

    gw.tool_step(
        Role.SPECIALIST,
        tool_request("dynamic", items=({"role": "user", "content": "MESSAGES-ITEM-MARKER"},)),
        ctx,
    )
    _, _, tool_in, tool_out = d.sink.model_calls[1]
    assert "MESSAGES-ITEM-MARKER" not in tool_in
    assert "MESSAGES-ITEM-MARKER" not in tool_out


# ---------------------------------------------------------------------------------------------------------------
# AC-11 [journey] / AC-12 [regression/context] evidence the implementer must leave
# ---------------------------------------------------------------------------------------------------------------


def test_journey_record_states_level_and_blockers() -> None:
    """AC-11 regression/context: the journey record says mock-tested, blocked by AEA-57, naming J-1..J-5 and J-9."""
    records = sorted((_REPO_ROOT / "docs" / "testing" / "journeys").glob("*-AEA-20.md"))
    assert len(records) == 1, "docs/testing/journeys/<date>-AEA-20.md is missing"
    text = records[0].read_text()
    assert "mock-tested" in text
    assert "AEA-57" in text
    for journey in ("J-1", "J-2", "J-3", "J-4", "J-5", "J-9"):
        assert journey in text


def test_area_map_marks_gateway_built() -> None:
    """AC-12 regression/context: the area map's A2 row records agent/gateway.py as actual (AEA-20)."""
    text = (_REPO_ROOT / ".claude" / "reference" / "area-map.md").read_text()
    row = next(line for line in text.splitlines() if line.startswith("| 1 | **A2 Models** |"))
    status = (
        row.strip().strip("|").split("|")[-1]
    )  # the Status cell only (the Owns cell already names the file)
    assert "agent/gateway.py" in status
    assert "AEA-20" in status


def test_callledger_protocol_is_exported() -> None:
    """Plan R-1 invariant: the gateway types its ledger with its own four-method CallLedger Protocol (AEA-26 is wave 2)."""
    assert set(gateway_module.__all__) == {"CallLedger", "ModelGateway", "ModelOutcome"}
    for name in ("admit_call", "record", "trip_provider_cap", "close_provider_cap"):
        assert hasattr(CallLedger, name)
