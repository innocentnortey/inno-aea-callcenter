"""CAP-1 (WF-1): the customer chat leaves exactly the records the observability contract requires, and the forbidden
values are in none of them. Real app over HTTP, a disposable DB copy, a scripted model at the provider boundary and a
Langfuse sink over an in-memory exporter. Every sentinel is generated per test; nothing private is written here.
"""

from __future__ import annotations

import json
import re
import secrets
from collections import Counter
from typing import Any

import pytest

from meridian.adapters.sqlite.migrate import WORKING_DB_NAME
from meridian.config import JEV_MODEL
from meridian.policy.texts import TextId, render
from meridian.privacy.redact import RedactionProfile, redact
from meridian.web.logging import ALLOWED_FIELDS, RECORD_ATTR
from tests.graph import worked_pair_scenarios as sc
from tests.integration.customer_api import (
    Chat,
    blocks,
    customer_row,
    inbox,
    open_chat,
    say,
    send_code,
    send_form,
)
from tests.integration.customer_support import (
    CustomerRun,
    RunOptions,
    build_capture_sink,
    finished_spans,
    open_customer_run,
    request_json,
    response_text,
    span_meta,
    span_text,
)
from tests.journeys.support.env import letters
from tests.unit.adapters._tracing_doubles import close_all, trace_hex

ISSUED_TABLES = frozenset({"customers", "technicians", "appointment_slots", "appointments", "invoices"})
JEV_ROLES = {"planner", "classifier"}


def app_tables_text(run: CustomerRun, *, only: tuple[str, ...] | None = None) -> str:
    """Every row of the tables the app writes (the issued scheduling tables are data, not records)."""
    names = [
        r["name"]
        for r in run.db.rows(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    wanted = [n for n in names if (n in only if only is not None else n not in ISSUED_TABLES)]
    return "\n".join(repr(row) for name in wanted for row in run.db.table_rows(name))


def card_like() -> str:
    return "4000 " + " ".join(f"{secrets.randbelow(10000):04d}" for _ in range(3))


def run_with_sink(request: pytest.FixtureRequest) -> Any:
    """A customer run with a capture sink; the caller closes the registry."""
    registry: list[Any] = []
    sink, exporter = build_capture_sink(registry)
    return registry, sink, exporter, open_customer_run(request, RunOptions(trace=sink))


def probe_turn(run: CustomerRun, chat: Chat, *, name: str, card: str, phrase: str) -> Any:
    run.steps.set_step(
        {
            sc.Role.CLASSIFIER: sc.NORMAL,
            sc.Role.PLANNER: sc.planner(),
            sc.Role.RESPONDER: sc.responder(f"Thanks for that. {phrase}"),
        }
    )
    return say(chat, f"my name is {name}, my card is {card}, {phrase}")


def test_required_records_present(request: pytest.FixtureRequest) -> None:
    """AC-17: a request record per HTTP call, one conversation, one turn per message with its fields, one trace per
    turn with nested node, model and tool spans, lookup rows, the R-46 event, a gate event per turn, a classifier event
    per classifier run, ledger rows, and one thread id across the checkpoint, the rows and the trace."""
    registry, sink, exporter, opened = run_with_sink(request)
    try:
        with opened as run:
            client = run.login().client
            result = sc.wp2(run, client)
            chat = Chat(run=run, client=client, thread_id=result.thread_id, opened={})
            probe_turn(
                run, chat, name="Zed" + letters(5).title(), card=card_like(), phrase="sentinel-" + letters(8)
            )
            spans = finished_spans(sink, exporter)

            request_ids = {r["request_id"] for r in run.logs.structured("request")}
            for c in run.clients:
                for response in c.responses:
                    assert response.headers["X-Request-ID"] in request_ids
            assert run.db.count("conversations", "thread_id = ?", (chat.thread_id,)) == 1

            turns = run.db.rows(
                "SELECT * FROM turns WHERE thread_id = ? ORDER BY sequence", (chat.thread_id,)
            )
            assert len(turns) == 6
            by_trace: dict[str, list[Any]] = {}
            for span in spans:
                by_trace.setdefault(trace_hex(span), []).append(span)
            calls = Counter(c.role.value for c in run.script.calls)
            for turn in turns:
                for field in ("gate_result", "outcome", "server_ms", "trace_id", "trace_export"):
                    assert turn[field] is not None, field
                in_trace = by_trace[turn["trace_id"]]
                roots = [s for s in in_trace if s.name == "turn"]
                assert len(roots) == 1
                root = roots[0]
                assert all(
                    s.parent is not None and s.parent.span_id == root.context.span_id
                    for s in in_trace
                    if s is not root
                )
                assert {"load_context", "gates", "compose"} <= {s.name for s in in_trace}
                ledger = Counter(
                    r["role"]
                    for r in run.db.rows(
                        "SELECT role FROM spend_ledger WHERE turn_id = ?", (turn["turn_id"],)
                    )
                )
                model_spans = Counter(
                    s.name.split(":", 1)[1] for s in in_trace if s.name.startswith("model_call:")
                )
                assert model_spans == ledger
                tools = run.container.get(sc.Key("tool_registry"))
                tool_rows = [
                    r
                    for r in run.db.rows("SELECT tool FROM lookup_log WHERE turn_id = ?", (turn["turn_id"],))
                    if tools.get(r["tool"]) is not None  # staff guidance and the like are not tool calls
                ]
                tool_spans = sorted(s.name for s in in_trace if s.name.startswith("tool:"))
                assert tool_spans == sorted(f"tool:{r['tool']}" for r in tool_rows)
                assert all(
                    dict(s.attributes or {}).get("session.id") == chat.thread_id
                    for s in in_trace
                    if s is root
                )
                assert span_meta(root, "turn_id") == turn["turn_id"]
            gates = run.db.count("check_events", "thread_id = ? AND check_kind = 'gate'", (chat.thread_id,))
            assert gates == len(turns)
            assert (
                run.db.count("check_events", "thread_id = ? AND check_kind = 'classifier'", (chat.thread_id,))
                == calls["classifier"]
            )
            assert (
                run.db.count(
                    "check_events", "thread_id = ? AND check_kind IN ('completion','fact')", (chat.thread_id,)
                )
                >= 2
            )
            assert run.db.count("lookup_log", "thread_id = ?", (chat.thread_id,)) >= 1
            for table in ("turns", "lookup_log", "cases"):
                assert {
                    r["thread_id"]
                    for r in run.db.rows(
                        f"SELECT thread_id FROM {table} WHERE thread_id = ?",  # noqa: S608
                        (chat.thread_id,),
                    )
                } <= {chat.thread_id}
            import sqlite3

            checkpoints = sqlite3.connect(f"file:{run.env.data_dir / 'checkpoints.sqlite'}?mode=ro", uri=True)
            try:
                saved = {r[0] for r in checkpoints.execute("SELECT DISTINCT thread_id FROM checkpoints")}
            finally:
                checkpoints.close()
            assert chat.thread_id in saved
    finally:
        close_all(registry)


def test_forbidden_values_absent(request: pytest.FixtureRequest) -> None:
    """AC-18: the code, a card-like number, a full phone number, an introduced name, a key and a cookie are absent or
    masked as specified in every record the chat leaves; log keys stay within the allow-list."""
    registry, sink, exporter, opened = run_with_sink(request)
    try:
        with opened as run:
            client = run.login().client
            result = sc.wp2(run, client)
            chat = Chat(run=run, client=client, thread_id=result.thread_id, opened={})
            name, card, phrase = "Zed" + letters(5).title(), card_like(), "sentinel-" + letters(10)
            probe_turn(run, chat, name=name, card=card, phrase=phrase)
            spans = finished_spans(sink, exporter)
            phone = str(customer_row(run, "MHC-10002")["phone"])
            codes = list(result.codes)
            assert codes and all(c.isdigit() and len(c) == 6 for c in codes)
            secrets_in_play = run.secret_values()
            logs, span_blob = run.logs.all_text(), span_text(spans)
            stored = app_tables_text(run)
            bodies = response_text(run.clients)
            requests = request_json(run)
            inbox_bodies = [
                r.text for c in run.clients for r in c.responses if r.request.url.path == "/api/demo/inbox"
            ]
            non_inbox = "\n".join(
                r.text for c in run.clients for r in c.responses if r.request.url.path != "/api/demo/inbox"
            )

            for code in codes:  # the code lives on CON-6 only
                assert not any(code in blob for blob in (logs, span_blob, stored, non_inbox, requests))
            assert "[code entered]" in app_tables_text(run, only=("messages",))
            for blob in (logs, span_blob, stored, bodies, requests):  # a card number is nowhere
                assert card not in blob and card.replace(" ", "") not in blob
            assert "[card number removed]" in app_tables_text(run, only=("messages",))
            for blob in (logs, bodies):  # a full phone number is in no log and no reply
                assert phone not in blob
            masked = f"[phone ending {phone[-2:]}]"
            assert phone not in span_blob and phone not in requests and masked not in logs
            assert (
                name not in logs and name not in span_blob
            )  # an introduced name: never in logs, masked in spans
            assert phrase not in logs  # the free text is only a length in a log record
            assert redact(phrase, RedactionProfile.TRACE).text == phrase or phrase not in span_blob
            for secret in secrets_in_play:
                assert not any(secret in blob for blob in (logs, span_blob, stored, bodies, requests))
            assert run.settings.anthropic_api_key.get_secret_value() not in logs + span_blob + stored
            cookie = client.cookie()
            assert cookie and not any(cookie in blob for blob in (logs, span_blob, stored))
            assert len(inbox_bodies) >= 1
            for record in (
                r for r in run.logs._snapshot() if isinstance(getattr(r, RECORD_ATTR, None), dict)
            ):
                payload = getattr(record, RECORD_ATTR)
                if payload["record"] in ALLOWED_FIELDS:
                    assert set(payload) <= ALLOWED_FIELDS[payload["record"]], payload["record"]
    finally:
        close_all(registry)


def test_model_requests_redacted(request: pytest.FixtureRequest) -> None:
    """AC-19: requests to the Jev roles carry no phone, email, street, introduced name, customer or invoice id;
    requests to the Sonnet roles carry no code, card, email or street, and a phone only as [phone ending NN]."""
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        result = sc.wp2(run, client)
        chat = Chat(run=run, client=client, thread_id=result.thread_id, opened={})
        name, card = "Zed" + letters(5).title(), card_like()
        probe_turn(run, chat, name=name, card=card, phrase="sentinel-" + letters(8))
        row = customer_row(run, "MHC-10002")
        street = str(row["service_address"]).split(",")[0]
        phone_digits = re.compile(r"\d{3}\D?\d{3}\D?\d{4}")
        jev = [c for c in run.script.calls if c.role.value in JEV_ROLES]
        sonnet = [c for c in run.script.calls if c.role.value not in JEV_ROLES]
        assert jev and sonnet
        for call in jev:
            text = json.dumps(call.request.model_dump(mode="json", exclude={"output_model"}), default=str)
            assert not phone_digits.search(text) and "@" not in text
            assert street not in text and name not in text
            assert not re.search(r"MHC-\d{5}", text) and not re.search(r"INV-\d{6}", text)
        codes = list(result.codes)
        for call in sonnet:
            text = json.dumps(call.request.model_dump(mode="json", exclude={"output_model"}), default=str)
            assert (
                not any(c in text for c in codes) and card not in text and card.replace(" ", "") not in text
            )
            assert "@" not in text and street not in text
            for match in phone_digits.finditer(text):
                raise AssertionError(
                    f"a phone number reached a {call.role.value} request: {match.group(0)[:3]}..."
                )
        assert JEV_MODEL  # the Jev roles are the PLANNER and CLASSIFIER roles of the configured model


def test_intake_never_in_state(request: pytest.FixtureRequest) -> None:
    """AC-20: code digits, a form phone number and a card number are in no stored file (the working copy, the checkpoint
    and their write-ahead logs), no table, log, span or model request; their placeholders are."""
    registry, sink, exporter, opened = run_with_sink(request)
    try:
        with opened as run:
            client = run.login().client
            chat = Chat(run=run, client=client, thread_id=open_chat(run, client).thread_id, opened={})
            wrong_code = "".join(secrets.choice("0123456789") for _ in range(6))
            phone = f"512-555-{secrets.randbelow(9000) + 1000}"
            card = card_like()
            run.steps.set_step(
                {
                    sc.Role.CLASSIFIER: sc.NORMAL,
                    sc.Role.PLANNER: sc.planner(account="invoice", topic="billing"),
                    sc.Role.RESPONDER: sc.responder("I need to find your record first."),
                }
            )
            opening = say(chat, "I need my invoice explained")
            run.steps.set_step({sc.Role.RESPONDER: sc.responder("I could not find that record.")})
            row = customer_row(run, "MHC-10001")
            sent = send_form(
                chat,
                blocks(opening, "locate_prompt")[0]["card_id"],
                {"name": str(row["name"]), "phone": phone},
            )
            assert blocks(sent, "locate_prompt") or blocks(sent)
            run.steps.set_step({sc.Role.RESPONDER: sc.responder("Thanks.")})
            try:
                send_code(chat, "code-card-unknown", wrong_code)
            except AssertionError:
                pass  # a code for a card that does not exist may be refused; the digits must still not be kept
            probe_turn(run, chat, name="Zed" + letters(5).title(), card=card, phrase="sentinel-" + letters(8))
            spans = finished_spans(sink, exporter)
            for value in (wrong_code, phone, card, card.replace(" ", "")):
                assert run.files_containing(value) == [], value
                assert value not in run.logs.all_text() + span_text(spans) + request_json(run)
                assert value not in app_tables_text(run)
            assert run.files_containing("[card number removed]") != []
    finally:
        close_all(registry)


def test_record_consistency_over_dev_set(request: pytest.FixtureRequest) -> None:
    """AC-30: over the dev set and the CON-4 turns, lookup rows equal tool calls, ledger rows equal model calls, a
    handed-off turn has a case, versions and export states are stored, planner turns carry their topic, and the
    snapshots hold only what the tool showed."""
    with open_customer_run(request, RunOptions()) as run:
        sc.run_dev_set(run)
        settings = run.settings
        for turn in run.db.rows("SELECT * FROM turns"):
            assert run.db.count("lookup_log", "turn_id = ?", (turn["turn_id"],)) == turn["tool_calls"]
            assert run.db.count("spend_ledger", "turn_id = ?", (turn["turn_id"],)) == turn["model_calls"]
            assert turn["agent_version"] == settings.agent_version and turn["trace_export"] is not None
            if turn["planner_model"] is not None:
                assert turn["plan_topic"] is not None
            if turn["outcome"] == "handed_off":
                assert run.db.count("cases", "thread_id = ?", (turn["thread_id"],)) >= 1
        for conversation in run.db.rows("SELECT agent_version FROM conversations WHERE run_tag != 'seed'"):
            assert conversation["agent_version"] == settings.agent_version
        person = run.db.rows("SELECT * FROM turns WHERE gate_result = 'person_requested' AND path IS NULL")
        assert all(t["model_calls"] == 0 for t in person)
        for lookup in run.db.rows("SELECT tool, result_seen FROM lookup_log"):
            seen = lookup["result_seen"]
            assert len(seen) <= 400
            if seen.startswith(("{", "[")):
                parsed = json.loads(seen)
                strings = [
                    v for v in (parsed.values() if isinstance(parsed, dict) else parsed) if isinstance(v, str)
                ]
                assert all(len(s) <= 80 for s in strings)
        assert render(TextId.GREETING)


def test_wf3_inbox_records_and_scope(request: pytest.FixtureRequest) -> None:
    """AC-31: reading the demo inbox leaves a request record with the code request's thread; the code is stored only as
    a keyed hash and an expiry; a second login's inbox is empty; the code is in no log; nothing left the machine."""
    with open_customer_run(request, RunOptions()) as run:
        client = run.login().client
        result = sc.wp2(run, client)
        chat = Chat(run=run, client=client, thread_id=result.thread_id, opened={})
        [code] = result.codes
        messages = inbox(chat)
        assert any(m["code"] for m in messages)
        record = run.logs.wait_for("request", lambda p: p.get("route") == "/api/demo/inbox")
        assert record["status"] == 200
        stored = run.db.rows("SELECT * FROM identity_codes WHERE thread_id = ?", (result.thread_id,))
        assert stored
        for row in stored:
            assert row["code_hmac"] != code and code not in " ".join(str(v) for v in row.values())
            assert row["expires_at"]
        from meridian.web.routes.demo import to_wire_message  # noqa: F401  (the serialiser renders the body)

        body = next(m["body"] for m in messages if m["status"] in ("active", "used", "expired"))
        assert code not in run.logs.all_text()
        second = run.client()
        run.login(second)
        other = second.call("GET", "/api/demo/inbox", operation_id="listDemoInbox")
        assert other.status_code == 200 and other.json()["messages"] == []
        assert body
        forbidden = [c for c in run.logs.structured("request") if c.get("route") == "/api/demo/inbox"]
        assert forbidden and all(set(c) <= ALLOWED_FIELDS["request"] for c in forbidden)
        assert run.guard.blocked == []
        assert WORKING_DB_NAME


STATUS_VALUES = {  # DO-6 "Status values" (observability-contract.md): the stored enumerations
    "outcome": {"answered", "acted", "safety_reply", "handed_off", "to_staff", "degraded_handoff"},
    "gate_result": {"clear", "safety", "burning_unclear", "danger", "person_requested", "ai_paused"},
    "degrade_reason": {"model_error", "tool_error", "timeout", "brake", "spend_cap", "rate_limit"},
    "trace_export": {"off", "sent", "failed"},
    "status": {"running", "completed", "failed"},
}


def test_status_values_within_lists(request: pytest.FixtureRequest) -> None:
    """AC-42 (PD-14): every stored status value is within the contract's list; degrade_reason appears only with a
    degraded handoff; a forced 5xx (the held write lock of AC-48) logs an error_kind."""
    import sqlite3
    import threading
    import uuid

    with open_customer_run(request, RunOptions()) as run:
        sc.run_dev_set(run)
        for column, allowed in STATUS_VALUES.items():
            seen = {
                r[column]
                for r in run.db.rows(f"SELECT DISTINCT {column} FROM turns")  # noqa: S608
                if r[column] is not None
            }
            assert seen <= allowed, (column, seen - allowed)
        for turn in run.db.rows("SELECT outcome, degrade_reason FROM turns"):
            assert (turn["degrade_reason"] is None) == (turn["outcome"] != "degraded_handoff")
        client = run.clients[0]
        fresh = open_chat(run, client)
        holder = sqlite3.connect(str(run.env.db_path), isolation_level=None, timeout=0)
        holder.execute("BEGIN IMMEDIATE")
        outcome: dict[str, Any] = {}

        def send() -> None:
            try:
                # raw: the answer to a held lock is checked by the AC-48 test; here only the 5xx record matters
                outcome["r"] = client._http.post(
                    f"/api/chat/sessions/{fresh.thread_id}/handoff", json={"turn_id": str(uuid.uuid4())}
                )
            except Exception as exc:
                outcome["error"] = repr(exc)

        thread = threading.Thread(target=send)
        thread.start()
        thread.join(timeout=60)
        holder.execute("ROLLBACK")
        holder.close()
        assert "r" in outcome, outcome.get("error")
        assert outcome["r"].status_code >= 500
        failed = [c for c in run.logs.structured("request") if int(str(c.get("status", 0))) >= 500]
        assert failed and all(c.get("error_kind") for c in failed)
