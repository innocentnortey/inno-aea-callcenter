"""AEA-48 route tests: CON-18 getOwnerMetrics, CON-19 getMonitoring, CON-20 getLatestEval (AC-1 to AC-10, AC-13)."""

from __future__ import annotations

import copy
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from meridian.domain.staff import DemoRole
from meridian.web.deps import get_metrics_reads, get_rate_limiter
from meridian.web.schemas.reads import MEASURE_UNITS
from tests.api.reads_support import (
    EXAMPLE_NAMES,
    OPERATIONS,
    RETRY_AFTER_MS,
    FakeMetricsReads,
    RefusingLimiter,
    example,
    example_names,
    gate_held_for,
    get_read,
    reads_app,
    reads_log,
    signed_in,
)
from tests.api.web_shell_support import (
    FakeHeartbeat,
    FakeSessionStore,
    app_log_text,
    assert_matches,
    captured_log,
    cookie_header,
    error_body,
    full_app,
    log_records,
    make_client,
    make_settings,
    rand_word,
    reset_gate_of,
)
from tests.fakes.clock import CHICAGO

OWNER, MONITORING, EVAL = "getOwnerMetrics", "getMonitoring", "getLatestEval"


def test_example_pair_no_run_too_few_turns_and_role_not_allowed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """worked pair (ticket): NO_RUN, TOO_FEW_TURNS and the representative's 403, with no owner read."""
    h = reads_app(monkeypatch, make_settings(tmp_path))
    h.reads.returns[EVAL] = example(EVAL, "NO_RUN")
    h.reads.returns[MONITORING] = example(MONITORING, "TOO_FEW_TURNS")
    headers = signed_in(h, DemoRole.REPRESENTATIVE)
    with make_client(h.app) as client:
        r = get_read(client, EVAL, headers)
        assert r.status_code == 200
        assert_matches(r, EVAL)
        body = r.json()
        assert body == example(EVAL, "NO_RUN")
        assert body["splits"] == {"dev": None, "held_out": None}
        assert body["headline"] is None
        assert body["dev_label"] == "Dev (we read and fixed these, so it overstates)"
        r = get_read(client, MONITORING, headers)
        assert r.status_code == 200
        assert_matches(r, MONITORING)
        body = r.json()
        tiles = {t["label"]: t for t in body["health"]}
        for label in ("Latency p50", "Latency p95"):
            assert tiles[label]["value"] is None
            assert tiles[label]["null_reason"] == "Not enough turns yet (fewer than 20)"
        assert body["spend"] == {
            "today_cents": 612,
            "cap_cents": 3000,
            "day": "America/Chicago midnight to midnight",
            "resets_at": "2026-10-17T00:00:00-05:00",
        }
        r = get_read(client, OWNER, headers)
        details = error_body(r, 403, "ROLE_NOT_ALLOWED")["error"]["details"]
        assert details == {"role": "representative", "needs": ["owner", "supervisor"], "reason": "wrong_role"}
        assert_matches(r, OWNER)
        print("403 details:", details)
    assert h.reads.calls == [EVAL, MONITORING]


def _all_examples_validate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, op: str, role: DemoRole) -> None:
    assert example_names(op) == EXAMPLE_NAMES[op]
    h = reads_app(monkeypatch, make_settings(tmp_path))
    headers = signed_in(h, role)
    with make_client(h.app) as client:
        for name in EXAMPLE_NAMES[op]:
            h.reads.returns[op] = example(op, name)
            r = get_read(client, op, headers)
            assert r.status_code == 200, (name, r.text)
            assert_matches(r, op)
            assert r.json() == example(op, name), name
    print(f"{op}: {len(EXAMPLE_NAMES[op])} bodies validated")


def test_getOwnerMetrics_matches_openapi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-1): both CON-18 examples come back valid and equal to the reader's mapping."""
    _all_examples_validate(monkeypatch, tmp_path, OWNER, DemoRole.OWNER)


def test_getMonitoring_matches_openapi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-1): the six CON-19 examples validate for a customer (any signed-in role)."""
    _all_examples_validate(monkeypatch, tmp_path, MONITORING, DemoRole.CUSTOMER)


def test_getLatestEval_matches_openapi(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-1): the four CON-20 examples validate for a customer (any signed-in role)."""
    _all_examples_validate(monkeypatch, tmp_path, EVAL, DemoRole.CUSTOMER)


def test_reads_pass_through(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-2): one reader call per request; the body equals the mapping field for field."""
    owner = example(OWNER, "SEEDED")
    owner["in_scope_correct_resolution"]["label"] = rand_word(12, "zqlabel")
    owner["promises_kept_on_time"]["id"] = "M-13"
    owner["promises_kept_on_time"]["case_refs"] = ["MHC-C-0005", rand_word(8, "zqref")]
    owner["handoffs"]["null_reason"] = rand_word(10, "zqwhy")
    owner["outcomes"][0]["kind"] = "estimate"
    monitoring = example(MONITORING, "FIRING")
    monitoring["health"][3]["id"] = "M-23"
    monitoring["health"][4]["id"] = "M-23"
    monitoring["alerts"][2]["state"] = "firing"
    monitoring["alerts"][2]["fired_at"] = "2026-10-16T14:10:00-05:00"
    monitoring["trace_export"] = rand_word(10, "zqsent")
    ev = example(EVAL, "STALE_RUN")
    held = ev["splits"]["held_out"]["measures"][0]
    held["min"], held["max"], held["target"] = 0.55, 0.7, "Target " + rand_word(6)
    ev["splits"]["dev"]["measures"][1]["label"] = rand_word(10, "zqeval")
    h = reads_app(monkeypatch, make_settings(tmp_path))
    headers = signed_in(h, DemoRole.OWNER)
    with make_client(h.app) as client:
        for op, mapping in ((OWNER, owner), (MONITORING, monitoring), (EVAL, ev)):
            h.reads.returns[op] = mapping
            h.reads.calls.clear()
            r = get_read(client, op, headers)
            assert r.status_code == 200, r.text
            assert r.json() == mapping
            assert h.reads.calls == [op]
            print(op, h.reads.calls)


def test_time_fields_passed_through(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-3): wall as_of and demo_now stay distinct; CON-18 as_of is the reader's demo value."""
    wall = datetime(2026, 10, 21, 20, 4, tzinfo=UTC)
    demo = datetime(2026, 10, 19, 7, 0, tzinfo=CHICAGO)
    monitoring = example(MONITORING, "DEFAULT")
    monitoring["as_of"], monitoring["demo_now"] = wall, demo
    owner = example(OWNER, "SEEDED")
    owner["as_of"] = demo
    h = reads_app(monkeypatch, make_settings(tmp_path))
    h.reads.returns[MONITORING], h.reads.returns[OWNER] = monitoring, owner
    headers = signed_in(h, DemoRole.OWNER)
    with make_client(h.app) as client:
        r = get_read(client, MONITORING, headers)
        assert_matches(r, MONITORING)
        b = r.json()
        assert datetime.fromisoformat(b["as_of"]) == wall
        assert datetime.fromisoformat(b["demo_now"]) == demo
        assert b["as_of"] != b["demo_now"]
        assert b["demo_now"] == "2026-10-19T07:00:00-05:00"
        r2 = get_read(client, OWNER, headers)
        assert_matches(r2, OWNER)
        assert r2.json()["as_of"] == "2026-10-19T07:00:00-05:00"
        print(b["as_of"], b["demo_now"], r2.json()["as_of"])


def test_unknown_keys_dropped_and_named_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """negative (AC-4): undocumented keys never reach a client; one warning names keys, never values."""
    caplog.set_level(logging.DEBUG)
    values = {
        "trace_url": "https://langfuse.invalid/" + rand_word(10, "zqtrace"),
        "customer_name": rand_word(10, "zqname"),
        "code": rand_word(10, "zqcode"),
    }
    h = reads_app(monkeypatch, make_settings(tmp_path))
    for op in OPERATIONS:
        mapping = h.reads.returns[op]
        assert isinstance(mapping, dict)
        mapping.update(values)
    monitoring = h.reads.returns[MONITORING]
    assert isinstance(monitoring, dict)
    monitoring["health"][0]["customer_name"] = values["customer_name"]
    headers = signed_in(h, DemoRole.OWNER)
    with make_client(h.app) as client, captured_log() as stream:
        for op in OPERATIONS:
            caplog.clear()
            r = get_read(client, op, headers)
            assert r.status_code == 200
            assert_matches(r, op)
            assert set(values) & set(r.json()) == set()
            assert all(v not in r.text for v in values.values())
            warnings = reads_log(caplog, logging.WARNING)
            assert len(warnings) == 1
            message = warnings[0].getMessage()
            assert all(key in message for key in ("code", "customer_name", "trace_url"))
            if op == MONITORING:
                assert "health[].customer_name" in message
            assert all(v not in message for v in values.values())
            print(message)
    everything = [stream.getvalue(), app_log_text(caplog), *(repr(rec.__dict__) for rec in caplog.records)]
    assert all(v not in text for v in values.values() for text in everything)


def test_missing_required_field_is_500(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """failure-refusal (AC-5): a mapping without a required field answers 500 and logs no value."""
    caplog.set_level(logging.DEBUG)
    secret_label, secret_export = rand_word(12, "zqlabel"), rand_word(12, "zqexport")
    h = reads_app(monkeypatch, make_settings(tmp_path))
    monitoring = example(MONITORING, "DEFAULT")
    monitoring["health"][0]["label"] = secret_label
    monitoring["trace_export"] = secret_export
    del monitoring["as_of"]
    owner = example(OWNER, "SEEDED")
    del owner["cases"]
    ev = example(EVAL, "BOTH_SPLITS")
    del ev["dev_label"]
    headers = signed_in(h, DemoRole.OWNER)
    with make_client(h.app) as client, captured_log() as stream:
        for op, mapping, expected in (
            (MONITORING, monitoring, "as_of missing"),
            (OWNER, owner, "cases missing"),
            (EVAL, ev, "dev_label missing"),
        ):
            h.reads.returns[op] = mapping
            caplog.clear()
            r = get_read(client, op, headers)
            assert r.status_code == 500
            assert r.json() == {"request_id": r.headers["X-Request-ID"]}
            errors = reads_log(caplog, logging.ERROR)
            assert len(errors) == 1
            assert expected in errors[0].getMessage()
            secrets = (secret_label, secret_export)
            assert all(s not in r.text for s in secrets)
            assert all(s not in app_log_text(caplog) for s in secrets)
            assert all(s not in repr(rec.__dict__) for s in secrets for rec in caplog.records)
            print(errors[0].getMessage())
        assert secret_label not in stream.getvalue()
        assert secret_export not in stream.getvalue()
    assert h.reads.calls == [MONITORING, OWNER, EVAL]


def test_headline_never_dev(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-6): a dev-only run keeps headline null; a target stays in `target`, never in `value`."""
    mapping = example(EVAL, "DEV_ONLY")
    mapping["splits"]["dev"]["measures"][0]["target"] = "Target 60 to 75 percent (ours)"
    h = reads_app(monkeypatch, make_settings(tmp_path))
    h.reads.returns[EVAL] = mapping
    with make_client(h.app) as client:
        r = get_read(client, EVAL, signed_in(h, DemoRole.CUSTOMER))
        assert r.status_code == 200
        assert_matches(r, EVAL)
        b = r.json()
    assert b["headline"] is None
    assert b["dev_label"] == mapping["dev_label"]
    assert b["splits"]["dev"] == mapping["splits"]["dev"]
    assert b["splits"]["dev"]["measures"][0]["target"] == "Target 60 to 75 percent (ours)"
    assert b["splits"]["dev"]["measures"][0]["value"] == 0.8
    assert b["splits"]["held_out"] is None


def test_reads_access(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure-refusal (AC-7, WF-6): owner metrics need owner or supervisor; the others any signed-in role; 401 without."""
    h = reads_app(monkeypatch, make_settings(tmp_path))
    with make_client(h.app) as client:
        for role in (DemoRole.OWNER, DemoRole.SUPERVISOR):
            r = get_read(client, OWNER, signed_in(h, role))
            assert r.status_code == 200
            assert_matches(r, OWNER)
        for role in (DemoRole.CUSTOMER, DemoRole.REPRESENTATIVE):
            r = get_read(client, OWNER, signed_in(h, role))
            details = error_body(r, 403, "ROLE_NOT_ALLOWED")["error"]["details"]
            assert details == {"role": role.value, "needs": ["owner", "supervisor"], "reason": "wrong_role"}
            assert_matches(r, OWNER)
            print(details)
        assert h.reads.calls.count(OWNER) == 2
        for role in DemoRole:
            headers = signed_in(h, role)
            for op in (MONITORING, EVAL):
                r = get_read(client, op, headers)
                assert r.status_code == 200
                assert_matches(r, op)
        for op in OPERATIONS:
            r = get_read(client, op)
            assert error_body(r, 401, "UNAUTHENTICATED")["error"]["details"] == {"reason": "none"}
            assert_matches(r, op)
    assert [h.reads.calls.count(op) for op in OPERATIONS] == [2, 4, 4]


def test_reads_429_and_503(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """failure-refusal (AC-8, WF-6): 429 and 503 on the two limited reads; owner metrics never limited, waits out a reset."""
    h = reads_app(monkeypatch, make_settings(tmp_path / "limited"), limiter=RefusingLimiter())
    headers = signed_in(h, DemoRole.OWNER)
    with make_client(h.app) as client:
        for op in (MONITORING, EVAL):
            r = get_read(client, op, headers)
            body = error_body(r, 429, "REQUEST_RATE_LIMITED")
            assert body["error"]["details"] == {"retry_after_ms": RETRY_AFTER_MS}
            assert_matches(r, op)
        r = get_read(client, OWNER, headers)
        assert r.status_code == 200
        assert_matches(r, OWNER)
    assert h.reads.calls == [OWNER]

    h2 = reads_app(monkeypatch, make_settings(tmp_path / "reset"))
    headers = signed_in(h2, DemoRole.OWNER)
    with make_client(h2.app) as client:
        with reset_gate_of(h2.app).hold():
            for op in (MONITORING, EVAL):
                t0 = time.monotonic()
                r = get_read(client, op, headers)
                body = error_body(r, 503, "RESET_IN_PROGRESS")
                assert body["error"]["details"] == {"retry_after_ms": 5000}
                assert_matches(r, op)
                assert time.monotonic() - t0 < 1.0
        assert h2.reads.calls == []
        h2.reads.probe = reset_gate_of(h2.app).held
        with gate_held_for(h2.app, 0.5):
            t0 = time.monotonic()
            r = get_read(client, OWNER, headers)
            elapsed = time.monotonic() - t0
        assert r.status_code == 200
        assert_matches(r, OWNER)
        assert 0.3 <= elapsed < 5.0
        print("owner metrics waited", round(elapsed, 2), "s")
    assert h2.reads.held_at_call == [False]


def test_wf6_reads_emit_request_records(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """capture (AC-9, WF-6): one request record per read, no other record kind; the reader is read once each."""
    store = FakeSessionStore()
    app = full_app(monkeypatch, make_settings(tmp_path), store=store, heartbeat=FakeHeartbeat())
    reads = FakeMetricsReads()
    app.dependency_overrides[get_metrics_reads] = lambda: reads
    headers = cookie_header(store.issue(DemoRole.OWNER))
    with make_client(app) as client, captured_log() as stream:
        responses = {op: get_read(client, op, headers) for op in OPERATIONS}
    assert all(r.status_code == 200 for r in responses.values())
    records = log_records(stream)
    assert {x["record"] for x in records} == {"request"}
    for op, r in responses.items():
        mine = [x for x in records if x["request_id"] == r.headers["X-Request-ID"]]
        assert len(mine) == 1
        rec = mine[0]
        assert rec["route"] == OPERATIONS[op]
        assert rec["status"] == 200
        assert rec["caller_role"] == "owner"
        assert rec["thread_id"] is None
        assert "error_kind" not in rec
        print(rec)
    assert reads.calls == list(OPERATIONS)


def _valid_mappings() -> dict[str, dict[str, Any]]:
    return {
        op: example(op, name)
        for op, name in ((OWNER, "SEEDED"), (MONITORING, "DEFAULT"), (EVAL, "BOTH_SPLITS"))
    }


def test_unit_vocabulary_enforced(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """failure-refusal (AC-10): unit vocabulary, share and ratio ranges, unique pairs; 500 naming field and rule only."""
    caplog.set_level(logging.DEBUG)
    assert MEASURE_UNITS == ("count", "ms", "share")
    h = reads_app(monkeypatch, make_settings(tmp_path))
    headers = signed_in(h, DemoRole.OWNER)

    def bad(op: str, mutate: Any) -> dict[str, Any]:
        mapping = _valid_mappings()[op]
        mutate(mapping)
        return mapping

    def set_in(path: list[Any], value: Any) -> Any:
        def mutate(mapping: dict[str, Any]) -> None:
            node: Any = mapping
            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = value

        return mutate

    def duplicate_health(m: dict[str, Any]) -> None:
        m["health"][1] = copy.deepcopy(m["health"][0])

    def duplicate_held_out(m: dict[str, Any]) -> None:
        measures = m["splits"]["held_out"]["measures"]
        measures[1] = copy.deepcopy(measures[0])

    cases: list[tuple[str, dict[str, Any], str, str | None]] = [
        (
            MONITORING,
            bad(MONITORING, set_in(["health", 1, "unit"], "per 100 turns")),
            "health[1].unit literal_error",
            "per 100 turns",
        ),
        (
            MONITORING,
            bad(MONITORING, set_in(["correctness", "containment_estimate", "value"], 75)),
            "correctness.containment_estimate.value share_out_of_range",
            None,
        ),
        (MONITORING, bad(MONITORING, duplicate_health), "health[1] duplicate_measure", None),
        (
            OWNER,
            bad(OWNER, set_in(["outcomes", 0, "value"], 75)),
            "outcomes[0].value share_out_of_range",
            None,
        ),
        (EVAL, bad(EVAL, set_in(["headline", "value"], 65)), "headline.value ratio_out_of_range", None),
        (EVAL, bad(EVAL, duplicate_held_out), "splits.held_out.measures[1] duplicate_measure", None),
    ]
    with make_client(h.app) as client:
        for op, mapping in _valid_mappings().items():
            h.reads.returns[op] = mapping
            r = get_read(client, op, headers)
            assert r.status_code == 200, (op, r.text)
        for op, mapping, expected, secret in cases:
            h.reads.returns[op] = mapping
            caplog.clear()
            r = get_read(client, op, headers)
            assert r.status_code == 500, expected
            errors = reads_log(caplog, logging.ERROR)
            assert len(errors) == 1
            message = errors[0].getMessage()
            assert expected in message
            if secret:
                assert secret not in message
            print(message)
        h.reads.returns[EVAL] = example(
            EVAL, "BOTH_SPLITS"
        )  # E-1 repeats in dev, held_out and headline: per-run scope
        assert get_read(client, EVAL, headers).status_code == 200


def test_wf6_request_status_values(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-13, WF-6): request.status equals the HTTP status; error_kind only on 5xx; no unlisted status."""
    store = FakeSessionStore()
    app = full_app(monkeypatch, make_settings(tmp_path), store=store, heartbeat=FakeHeartbeat())
    reads = FakeMetricsReads()
    app.dependency_overrides[get_metrics_reads] = lambda: reads
    owner = cookie_header(store.issue(DemoRole.OWNER))
    rep = cookie_header(store.issue(DemoRole.REPRESENTATIVE))
    customer = cookie_header(store.issue(DemoRole.CUSTOMER))
    sent: list[Any] = []
    with make_client(app) as client, captured_log() as stream:
        sent.append(get_read(client, OWNER, owner))
        sent.append(get_read(client, MONITORING))
        sent.append(get_read(client, OWNER, rep))
        app.dependency_overrides[get_rate_limiter] = lambda: RefusingLimiter()
        sent.append(get_read(client, MONITORING, customer))
        app.dependency_overrides.pop(get_rate_limiter)
        with reset_gate_of(app).hold():
            sent.append(get_read(client, EVAL, customer))
        broken = example(MONITORING, "DEFAULT")
        del broken["as_of"]
        reads.returns[MONITORING] = broken
        sent.append(get_read(client, MONITORING, customer))
    records = [x for x in log_records(stream) if x["record"] == "request"]
    expected_kind = {503: "RESET_IN_PROGRESS", 500: "reads_schema_violation"}
    for r in sent:
        rec = next(x for x in records if x["request_id"] == r.headers["X-Request-ID"])
        assert rec["status"] == r.status_code
        assert rec["status"] in {200, 401, 403, 429, 500, 503}
        if r.status_code in expected_kind:
            assert rec["error_kind"] == expected_kind[r.status_code]
        else:
            assert "error_kind" not in rec
        print((rec["status"], rec.get("error_kind")))
    assert [r.status_code for r in sent] == [200, 401, 403, 429, 503, 500]
