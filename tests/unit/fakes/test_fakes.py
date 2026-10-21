"""AEA-11: the DO-4 port fakes honour their ports (AC-1 to AC-12, S-1 to S-9)."""

from __future__ import annotations

import ast
import inspect
import json
import logging
import subprocess
import sys
import typing
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from pydantic import JsonValue

from meridian.domain.common import CallRecord, LLMFacing, ProviderCall, ProviderFailureKind, Role
from meridian.domain.records import Passage
from meridian.domain.turn import SpanHandle, TurnIds
from meridian.ports.models import (
    Attempt,
    ChoiceAnswer,
    ChoiceField,
    ChoiceModel,
    ChoiceRequest,
    ProviderMessages,
    StructuredModel,
    StructuredRequest,
    ToolCall,
    ToolCallingModel,
    ToolStep,
    ToolStepRequest,
    ToolTranscript,
)
from meridian.ports.runtime import Clock, IndexInfo, RetrievalIndex, TraceSink
from tests.fakes import (
    CHICAGO,
    WORKED_PAIRS_NOW,
    FakeAnthropicChoiceModel,
    FakeChoiceModel,
    FakeIndex,
    FakeStructuredModel,
    FakeToolModel,
    FixedClock,
    InMemoryTraceSink,
    RecordedModelCall,
    RecordedNode,
    ScriptedFailure,
    ScriptExhaustedError,
    provider_call,
)

REPO = Path(__file__).resolve().parents[3]
_RAW: JsonValue = {"role": "assistant"}


class _Out(LLMFacing):
    answer: str


class _Other(LLMFacing):
    note: str


def _ids() -> TurnIds:
    return TurnIds.model_validate(
        {
            "thread_id": str(uuid.uuid4()),
            "turn_id": str(uuid.uuid4()),
            "request_id": str(uuid.uuid4()),
            "run_tag": "live",
            "run_id": None,
            "agent_version": "test",
        }
    )


def _passage(n: int, score: float, text: str = "Synthetic passage") -> Passage:
    return Passage.model_validate(
        {
            "passage_id": f"policies/fake_policy.md#{n}",
            "file": "policies/fake_policy.md",
            "section": f"Section {n}",
            "version_label": "undated",
            "version_date": None,
            "text": text,
            "score": score,
        }
    )


def _choice_req(system: str = "Pick the intent.") -> ChoiceRequest:
    return ChoiceRequest(
        system=system,
        state={},
        fields=(
            ChoiceField(
                name="intent",
                instructions="Which intent?",
                options={"book": "Book a visit", "other": "Anything else"},
            ),
        ),
    )


def _struct_req(user: str = "U") -> StructuredRequest[_Out]:
    return StructuredRequest[_Out](
        system_prefix="P", system_dynamic="D", user=user, output_model=_Out, max_tokens=200, effort=None
    )


def _tool_req(messages: ProviderMessages, dynamic: str = "D") -> ToolStepRequest:
    return ToolStepRequest(
        system_prefix="P", system_dynamic=dynamic, messages=messages, tools=(), max_tokens=500, effort=None
    )


def _step() -> ToolStep:
    return ToolStep(
        text="",
        tool_calls=(ToolCall(id="call_1", name="kb_search", args={"query": "fees"}),),
        raw=_RAW,
        stop_reason="tool_use",
    )


def _answer_ok() -> ChoiceAnswer:
    return ChoiceAnswer(choices={"intent": "book"}, probabilities=None)


def _item(m: ProviderMessages, i: int) -> dict[str, JsonValue]:
    item = m.items[i]
    assert isinstance(item, dict)
    return item


def _assert_structural(proto: type, impl: object) -> None:
    names: set[str] = set()
    for klass in proto.__mro__:
        if klass in (object, typing.Protocol, typing.Generic):
            continue
        names.update(n for n in vars(klass) if not n.startswith("_"))
        names.update(n for n in inspect.get_annotations(klass) if not n.startswith("_"))
    for name in names:
        assert hasattr(impl, name), f"{type(impl).__name__} lacks {name}"
        proto_member = getattr(proto, name, None)
        if inspect.isfunction(proto_member):
            want = [(p.name, p.kind) for p in inspect.signature(proto_member).parameters.values()]
            got = [(p.name, p.kind) for p in inspect.signature(getattr(type(impl), name)).parameters.values()]
            assert got == want, name


def test_fakes_satisfy_protocols() -> None:
    c1: ChoiceModel = FakeChoiceModel([])
    c2: ChoiceModel = FakeAnthropicChoiceModel([])
    s: StructuredModel = FakeStructuredModel([])
    t: ToolCallingModel = FakeToolModel([])
    tt: ToolTranscript = FakeToolModel([])
    ck: Clock = FixedClock()
    ix: RetrievalIndex = FakeIndex()
    ts: TraceSink = InMemoryTraceSink()
    for proto, impl in (
        (ChoiceModel, c1),
        (ChoiceModel, c2),
        (StructuredModel, s),
        (ToolCallingModel, t),
        (ToolTranscript, tt),
        (Clock, ck),
        (RetrievalIndex, ix),
        (TraceSink, ts),
    ):
        _assert_structural(proto, impl)
    assert c1.provider == "openrouter_jev"
    assert c2.provider == "anthropic"
    assert s.provider == t.provider == "anthropic"


def test_scripted_attempts_in_order_with_provider_call() -> None:
    answer = _answer_ok()
    fake = FakeChoiceModel(
        [
            answer,
            ScriptedFailure(ProviderFailureKind.TIMEOUT),
            ScriptedFailure(ProviderFailureKind.BODY_ERROR, http_status=503),
        ]
    )
    a1, a2, a3 = (fake.choose(_choice_req(), timeout_s=3.0) for _ in range(3))
    assert a1.value is answer
    assert a1.failure is None
    assert type(a1.record) is ProviderCall
    assert a1.record.status == "ok"
    assert a1.record.provider == "openrouter_jev"
    assert a1.record.model == "typesafe/jev-1.13"
    for att, kind in ((a2, ProviderFailureKind.TIMEOUT), (a3, ProviderFailureKind.BODY_ERROR)):
        assert att.value is None
        assert att.failure is not None
        assert att.failure.kind is kind
        assert att.failure.provider == "openrouter_jev"
        assert att.record.failure == att.failure
        assert att.record.status == "error"
        assert type(att.record) is ProviderCall
        assert not isinstance(att.record, CallRecord)
        assert not hasattr(att.record, "role")
        assert not hasattr(att.record, "attempt")

    sfake = FakeStructuredModel([_Out(answer="a"), ScriptedFailure(ProviderFailureKind.OVERLOADED)])
    s1 = sfake.structured(_struct_req(), timeout_s=3.0)
    s2 = sfake.structured(_struct_req(), timeout_s=3.0)
    assert s1.value is not None
    assert s1.record.provider == "anthropic"
    assert type(s1.record) is ProviderCall
    assert s2.failure is not None
    assert s2.failure.kind is ProviderFailureKind.OVERLOADED
    assert s2.record.status == "error"
    assert type(s2.record) is ProviderCall

    tfake = FakeToolModel([_step(), ScriptedFailure(ProviderFailureKind.RATE_LIMITED, retry_after_s=2.0)])
    req = _tool_req(tfake.start("u"))
    t1 = tfake.tool_step(req, timeout_s=3.0)
    t2 = tfake.tool_step(req, timeout_s=3.0)
    assert t1.value is not None
    assert type(t1.record) is ProviderCall
    assert t1.record.stop_reason == "tool_use"
    assert t2.failure is not None
    assert t2.failure.kind is ProviderFailureKind.RATE_LIMITED
    assert t2.failure.retry_after_s == 2.0
    assert t2.record.status == "error"


def test_exhausted_script_fails_loudly() -> None:
    fake = FakeChoiceModel([_answer_ok()])
    req = _choice_req()
    assert fake.choose(req, timeout_s=3.0).failure is None
    with pytest.raises(ScriptExhaustedError) as info:
        fake.choose(req, timeout_s=3.0)
    assert "Pick the intent" not in str(info.value)
    assert "FakeChoiceModel" in str(info.value)

    def swallow() -> object:
        try:
            return fake.choose(req, timeout_s=3.0)
        except Exception:
            return None

    with pytest.raises(ScriptExhaustedError):
        swallow()
    assert issubclass(ScriptExhaustedError, BaseException)
    assert not issubclass(ScriptExhaustedError, Exception)
    with pytest.raises(ScriptExhaustedError):
        FakeStructuredModel([]).structured(_struct_req(), timeout_s=1.0)
    tf = FakeToolModel([])
    with pytest.raises(ScriptExhaustedError):
        tf.tool_step(_tool_req(tf.start("u")), timeout_s=1.0)


def test_choice_outside_options_is_invalid_output() -> None:
    fake = FakeChoiceModel(
        [
            ChoiceAnswer(choices={"intent": "cancel_everything"}, probabilities=None),
            ChoiceAnswer(choices={}, probabilities=None),
            ChoiceAnswer(choices={"intent": "book", "extra": "x"}, probabilities=None),
            _answer_ok(),
        ]
    )
    for _ in range(3):
        att = fake.choose(_choice_req(), timeout_s=3.0)
        assert att.value is None
        assert att.failure is not None
        assert att.failure.kind is ProviderFailureKind.INVALID_OUTPUT
        assert att.failure.retryable is False
        assert att.record.status == "error"
    assert fake.choose(_choice_req(), timeout_s=3.0).value is not None


def test_tool_fake_append_refuses_foreign_messages() -> None:
    step = _step()
    fake = FakeToolModel([step])
    m0 = fake.start("hello")
    assert m0.provider == "anthropic"
    assert m0.model == "claude-sonnet-5-5"
    assert len(m0.items) == 1
    m1 = fake.append(m0, step, [("call_1", '{"ok": true}')])
    assert m1.items[:1] == m0.items
    assert len(m1.items) == 3
    assert _item(m1, 1)["role"] == "assistant"
    assert _item(m1, 2)["role"] == "tool_results"
    assert len(fake.append(m1, step, []).items) == len(m1.items) + 1
    with pytest.raises(ValueError, match="another provider or model"):
        fake.append(ProviderMessages(provider="anthropic", model="claude-opus-x", items=()), step, [])
    with pytest.raises(ValueError, match="another provider or model"):
        fake.append(
            ProviderMessages(provider="openrouter_jev", model="claude-sonnet-5-5", items=()), step, []
        )
    assert len(fake.appends) == 2


def test_requests_recorded_in_order() -> None:
    reqs = [_choice_req(f"turn {n}") for n in (1, 2, 5)]
    fake = FakeChoiceModel([_answer_ok()] * 3)
    for r, t in zip(reqs, (3.0, 2.5, 1.0), strict=True):
        fake.choose(r, timeout_s=t)
    assert fake.requests == reqs
    assert all(a is b for a, b in zip(fake.requests, reqs, strict=True))
    assert fake.timeouts == [3.0, 2.5, 1.0]
    assert fake.remaining == 0

    sreqs = [_struct_req(f"u{n}") for n in (1, 2, 5)]
    sfake = FakeStructuredModel([_Out(answer="a")] * 3)
    for sr in sreqs:
        sfake.structured(sr, timeout_s=1.0)
    assert sfake.requests == sreqs

    tfake = FakeToolModel([_step()] * 3)
    msgs = tfake.start("u")
    treqs = [_tool_req(msgs, f"d{n}") for n in (1, 2, 5)]
    for tr in treqs:
        tfake.tool_step(tr, timeout_s=1.0)
    assert tfake.requests == treqs
    assert tfake.starts == ["u"]


def test_fixed_clock() -> None:
    c = FixedClock()
    assert c.now() == datetime(2026, 10, 16, 10, 0, tzinfo=ZoneInfo("America/Chicago"))
    assert c.now() is c.now()
    tz = c.now().tzinfo
    assert isinstance(tz, ZoneInfo)
    assert tz.key == "America/Chicago"
    assert c.now().strftime("%A") == "Friday"
    d = c.advanced(timedelta(hours=1))
    assert d is not c
    assert d.now().hour == 11
    assert c.now().hour == 10
    assert WORKED_PAIRS_NOW == c.now()


def test_fixed_clock_refuses_naive_and_foreign_tz() -> None:
    bad = (
        datetime(2026, 10, 16, 10, 0),
        datetime(2026, 10, 16, 15, 0, tzinfo=UTC),
        datetime(2026, 10, 16, 10, 0, tzinfo=timezone(timedelta(hours=-5))),
        datetime(2026, 10, 16, 11, 0, tzinfo=ZoneInfo("America/New_York")),
    )
    for at in bad:
        with pytest.raises(ValueError, match="FixedClock"):
            FixedClock(at)


def test_fake_index_floor_and_info() -> None:
    ix = FakeIndex([_passage(1, 0.5), _passage(2, 0.9), _passage(3, 0.7)])
    hit = ix.search("fees", k=2, min_score=0.6)
    assert tuple(p.score for p in hit.passages) == (0.9, 0.7)
    assert hit.below_floor is False
    assert len(ix.search("fees", k=1, min_score=0.6).passages) == 1
    floor = ix.search("fees", k=2, min_score=0.95)
    assert floor.passages == ()
    assert floor.below_floor is True
    equal = ix.search("fees", k=5, min_score=0.7)
    assert tuple(p.score for p in equal.passages) == (0.9, 0.7)
    info = ix.info()
    assert info.embedding_model == "BAAI/bge-small-en-v1.5"
    assert info.dimension == 384
    assert info.files == 17
    assert info.chunks == 3
    given = IndexInfo(
        embedding_model="BAAI/bge-small-en-v1.5", dimension=3, chunks=1, manifest_hash="h", files=2
    )
    assert FakeIndex(info=given).info() is given


def test_trace_sink_handle_and_export_status() -> None:
    sink = InMemoryTraceSink()
    rec = CallRecord.from_provider(
        provider_call(provider="anthropic", model="claude-sonnet-5-5"), role=Role.RESPONDER, attempt=1
    )
    ids_a, ids_b = _ids(), _ids()
    with sink.turn(ids_a) as span_a:
        sink.model_call(span_a, rec, "in A", "out A")
        sink.node(span_a, "gates", 3, "ok")
    with sink.turn(ids_b) as span_b:
        sink.node(span_b, "plan", 5, "ok")
    assert span_a.turn_id == ids_a.turn_id
    assert span_a.trace_id == "0" * 31 + "1"
    assert span_b.trace_id == "0" * 31 + "2"
    a = sink.spans_for(span_a)
    assert a.model_calls == [RecordedModelCall(rec, "in A", "out A")]
    assert a.nodes == [RecordedNode("gates", 3, "ok")]
    assert sink.spans_for(span_b).model_calls == []
    assert sink.spans_for(span_b).nodes == [RecordedNode("plan", 5, "ok")]
    assert all(t.closed for t in sink.turns)
    assert sink.export_status(span_a) in ("off", "sent", "failed")
    assert sink.export_status(span_a) == "sent"
    assert [t.ids for t in sink.turns] == [ids_a, ids_b]
    failed = InMemoryTraceSink(status="failed")
    with failed.turn(_ids()) as span:
        pass
    assert failed.export_status(span) == "failed"


def test_fakes_import_no_vendor_sdk() -> None:
    code = (
        "import json, sys\n"
        f"sys.path.insert(0, {str(REPO / 'src')!r})\n"
        f"sys.path.insert(0, {str(REPO)!r})\n"
        "import tests.fakes as f\n"
        "f.FakeChoiceModel([]); f.FakeAnthropicChoiceModel([]); f.FakeStructuredModel([]); f.FakeToolModel([])\n"
        "f.FixedClock(); f.FakeIndex(); f.InMemoryTraceSink()\n"
        "print(json.dumps(sorted(m for m in ('anthropic', 'httpx', 'langfuse', 'fastembed') if m in sys.modules)))\n"
    )
    done = subprocess.run(
        [sys.executable, "-I", "-c", code], cwd=REPO, capture_output=True, text=True, check=False, timeout=120
    )
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout.strip().splitlines()[-1]) == []


def test_fakes_leak_nothing_and_sink_does_not_mask(
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    caplog.set_level(logging.DEBUG)
    monkeypatch.chdir(tmp_path)
    s = "zq" + uuid.uuid4().hex[:12]
    FakeChoiceModel([_answer_ok()]).choose(_choice_req(f"S {s}"), timeout_s=1.0)
    FakeStructuredModel([_Out(answer=s)]).structured(_struct_req(f"U {s}"), timeout_s=1.0)
    tf = FakeToolModel([_step()])
    msgs = tf.start(s)
    tf.tool_step(_tool_req(msgs, s), timeout_s=1.0)
    tf.append(msgs, _step(), [("call_1", s)])
    FakeIndex([_passage(1, 0.9, text=s)]).search(s, k=3, min_score=0.0)
    clock = FixedClock()
    clock.now()
    clock.advanced(timedelta(hours=1))
    sink = InMemoryTraceSink()
    rec = CallRecord.from_provider(
        provider_call(provider="anthropic", model="claude-sonnet-5-5"), role=Role.RESPONDER, attempt=1
    )
    with sink.turn(_ids()) as span:
        sink.model_call(span, rec, f"in {s}", f"out {s}")
        sink.node(span, "n", 1, "ok")
    out, err = capsys.readouterr()
    assert s not in out
    assert s not in err
    assert s not in caplog.text
    assert all(s not in r.getMessage() for r in caplog.records)
    assert list(tmp_path.iterdir()) == []
    call = sink.spans_for(span).model_calls[0]
    assert call.masked_input == f"in {s}"
    assert call.masked_output == f"out {s}"
    forbidden_attrs = {"write_text", "write_bytes", "mkdir", "touch", "unlink"}
    for path in (REPO / "tests/fakes").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(a.name != "logging" for a in node.names), path
            if isinstance(node, ast.ImportFrom):
                assert node.module != "logging", path
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in {"print", "open"}, path
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in forbidden_attrs, path


def test_structured_fake_validates_output_model() -> None:
    kept = _Out(answer="kept")
    fake = FakeStructuredModel([{"answer": "from dict"}, {"wrong": 1}, _Other(note="n"), kept])
    a1 = fake.structured(_struct_req(), timeout_s=1.0)
    assert isinstance(a1.value, _Out)
    assert a1.value.answer == "from dict"
    for _ in range(2):
        bad = fake.structured(_struct_req(), timeout_s=1.0)
        assert bad.value is None
        assert bad.failure is not None
        assert bad.failure.kind is ProviderFailureKind.INVALID_OUTPUT
    a4 = fake.structured(_struct_req(), timeout_s=1.0)
    assert a4.value is kept
    assert a4.model_dump()["value"] == {"answer": "kept"}


@pytest.mark.parametrize(
    ("kind", "status", "expected"),
    [
        (ProviderFailureKind.TIMEOUT, None, True),
        (ProviderFailureKind.CONNECTION, None, True),
        (ProviderFailureKind.RATE_LIMITED, None, True),
        (ProviderFailureKind.OVERLOADED, 529, True),
        (ProviderFailureKind.SERVER, 500, True),
        (ProviderFailureKind.BODY_ERROR, 503, True),
        (ProviderFailureKind.BODY_ERROR, 400, False),
        (ProviderFailureKind.BODY_ERROR, None, False),
        (ProviderFailureKind.BAD_REQUEST, 400, False),
        (ProviderFailureKind.PROVIDER_SPEND_CAP, 402, False),
        (ProviderFailureKind.REFUSAL, None, False),
        (ProviderFailureKind.MAX_TOKENS, None, False),
    ],
    ids=lambda v: str(v),
)
def test_scripted_failure_retryable_defaults(
    kind: ProviderFailureKind, status: int | None, expected: bool
) -> None:
    att = FakeChoiceModel([ScriptedFailure(kind, http_status=status)]).choose(_choice_req(), timeout_s=1.0)
    assert att.failure is not None
    assert att.failure.retryable is expected
    if kind is ProviderFailureKind.REFUSAL:
        assert att.record.stop_reason == "refusal"
    if kind is ProviderFailureKind.MAX_TOKENS:
        assert att.record.stop_reason == "max_tokens"


def test_scripted_failure_retryable_override() -> None:
    fake = FakeChoiceModel([ScriptedFailure(ProviderFailureKind.TIMEOUT, retryable=False)])
    att = fake.choose(_choice_req(), timeout_s=1.0)
    assert att.failure is not None
    assert att.failure.retryable is False


def test_prebuilt_attempts_checked_at_construction() -> None:
    answer = _answer_ok()
    good = Attempt[ChoiceAnswer](
        value=answer,
        record=provider_call(
            provider="openrouter_jev",
            model="typesafe/jev-1.13",
            input_tokens=120,
            cost_usd=0.000005,
            cost_source="reported",
        ),
        failure=None,
    )
    assert FakeChoiceModel([good]).choose(_choice_req(), timeout_s=1.0) is good
    as_record = CallRecord.from_provider(
        provider_call(provider="openrouter_jev", model="typesafe/jev-1.13"), role=Role.PLANNER, attempt=1
    )
    with pytest.raises(ValueError, match="CallRecord"):
        FakeChoiceModel([Attempt[ChoiceAnswer](value=answer, record=as_record, failure=None)])
    anth = Attempt[ChoiceAnswer](
        value=answer, record=provider_call(provider="anthropic", model="claude-sonnet-5-5"), failure=None
    )
    with pytest.raises(ValueError, match="another provider"):
        FakeChoiceModel([anth])
    other_model = Attempt[ChoiceAnswer](
        value=answer, record=provider_call(provider="openrouter_jev", model="other"), failure=None
    )
    with pytest.raises(ValueError, match="another provider"):
        FakeChoiceModel([other_model])
    assert FakeAnthropicChoiceModel([anth]).choose(_choice_req(), timeout_s=1.0) is anth
    with pytest.raises(TypeError):
        FakeChoiceModel(["not an entry"])  # type: ignore[list-item]


def test_fixed_clock_advances_by_elapsed_time() -> None:
    start = FixedClock(datetime(2026, 11, 1, 0, 30, tzinfo=CHICAGO))
    later = start.advanced(timedelta(hours=2)).now()
    assert later.astimezone(UTC) == datetime(2026, 11, 1, 7, 30, tzinfo=UTC)
    assert later.utcoffset() == timedelta(hours=-6)
    tz = later.tzinfo
    assert isinstance(tz, ZoneInfo)
    assert tz.key == "America/Chicago"
    assert FixedClock().advanced(timedelta(days=3)).now() == datetime(2026, 10, 19, 10, 0, tzinfo=CHICAGO)


def test_fake_index_by_query_and_records_searches() -> None:
    ix = FakeIndex([_passage(1, 0.9)], by_query={"gas": [_passage(7, 0.8)]})
    assert ix.search("gas", k=3, min_score=0.5).passages[0].passage_id == "policies/fake_policy.md#7"
    assert ix.search("other", k=3, min_score=0.5).passages[0].passage_id == "policies/fake_policy.md#1"
    assert ix.searches == [("gas", 3, 0.5), ("other", 3, 0.5)]
    assert ix.info().chunks == 2


def test_trace_sink_refuses_foreign_handle_and_closes_on_error() -> None:
    sink = InMemoryTraceSink()
    ids = _ids()
    other = InMemoryTraceSink()
    with other.turn(ids) as foreign:
        pass
    bare = SpanHandle(turn_id=ids.turn_id, trace_id=None)
    rec = CallRecord.from_provider(
        provider_call(provider="anthropic", model="claude-sonnet-5-5"), role=Role.RESPONDER, attempt=1
    )
    for handle in (foreign, bare):
        with pytest.raises(ValueError, match="not opened"):
            sink.model_call(handle, rec, "i", "o")
        with pytest.raises(ValueError, match="not opened"):
            sink.node(handle, "n", 1, "ok")
        with pytest.raises(ValueError, match="not opened"):
            sink.export_status(handle)
        with pytest.raises(ValueError, match="not opened"):
            sink.spans_for(handle)
    holder: list[SpanHandle] = []
    with pytest.raises(RuntimeError, match="boom"), sink.turn(ids) as span:
        holder.append(span)
        raise RuntimeError("boom")
    assert sink.spans_for(holder[0]).closed is True
    assert sink.export_status(holder[0]) == "sent"


def test_fakes_read_no_wall_clock() -> None:
    for path in (REPO / "tests/fakes").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            owner = node.func.value
            if isinstance(owner, ast.Name):
                assert not (
                    owner.id in {"datetime", "date"} and node.func.attr in {"now", "utcnow", "today"}
                ), path
                assert not (owner.id == "time" and node.func.attr in {"time", "time_ns"}), path


def test_model_fake_is_thread_safe() -> None:
    fake = FakeChoiceModel([_answer_ok()] * 200)
    req = _choice_req()

    def work() -> list[Attempt[ChoiceAnswer]]:
        return [fake.choose(req, timeout_s=1.0) for _ in range(25)]

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = [a for batch in pool.map(lambda _: work(), range(8)) for a in batch]
    assert len(results) == 200
    assert all(a.failure is None for a in results)
    assert len(fake.requests) == 200
    assert fake.remaining == 0
    with pytest.raises(ScriptExhaustedError):
        fake.choose(req, timeout_s=1.0)


def test_provider_classvars_and_default_models() -> None:
    assert FakeChoiceModel.provider == "openrouter_jev"
    assert FakeAnthropicChoiceModel.provider == "anthropic"
    assert FakeStructuredModel.provider == FakeToolModel.provider == "anthropic"
    assert "provider" not in vars(FakeChoiceModel([]))
    assert FakeChoiceModel([]).model == "typesafe/jev-1.13"
    assert FakeAnthropicChoiceModel([]).model == "claude-sonnet-5-5"
    assert FakeStructuredModel([]).model == "claude-sonnet-5-5"
    assert FakeToolModel([]).model == "claude-sonnet-5-5"
    assert FakeToolModel([], model="claude-x").model == "claude-x"
    assert issubclass(FakeAnthropicChoiceModel, FakeChoiceModel)
    fake = FakeAnthropicChoiceModel([_answer_ok(), ScriptedFailure(ProviderFailureKind.TIMEOUT)])
    ok = fake.choose(_choice_req(), timeout_s=1.0)
    assert ok.record.provider == "anthropic"
    assert ok.record.model == "claude-sonnet-5-5"
    bad = fake.choose(_choice_req(), timeout_s=1.0)
    assert bad.failure is not None
    assert bad.failure.provider == "anthropic"
