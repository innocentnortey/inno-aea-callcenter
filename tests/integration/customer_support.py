"""AEA-51's run launcher: AEA-57's public harness pieces plus a built KB index, per-step model scripts, an eval key and a
trace-sink override. A journey or integration test opens `open_customer_run(request, RunOptions(...))` and drives the
real app over HTTP. Only the model adapters (and, when asked, the trace sink) are substitutes, passed as
`ContainerOverrides`, the one door web.md section 15 allows.
"""

from __future__ import annotations

import atexit
import functools
import os
import shutil
import sqlite3
import tempfile
import threading
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

import pytest

from meridian.adapters.retrieval_fastembed import FastembedIndex
from meridian.config import Settings
from meridian.domain.common import ProviderFailureKind, Role
from meridian.policy.limits import Limits, TurnLimits
from meridian.ports.runtime import TraceSink
from meridian.retrieval import ingest
from meridian.retrieval.settings import EMBEDDING_MODEL
from meridian.web.app import ContainerOverrides
from tests.fakes import ScriptedFailure
from tests.fixtures.sqlite import ISSUED_DB
from tests.journeys.support.db import DbReader, sha256_file
from tests.journeys.support.env import JourneyEnv, journey_environ, letters
from tests.journeys.support.logtap import tap_logs
from tests.journeys.support.plugin import COLLECTOR_KEY
from tests.journeys.support.run import JourneyRun
from tests.journeys.support.scripted_model import (
    JourneyScript,
    ScriptedAnthropicModel,
    ScriptedCall,
    ScriptedJevModel,
    ScriptedModel,
    ScriptEntry,
    role_specs,
)
from tests.journeys.support.server import StepClock, launch_server, socket_guard
from tests.journeys.support.steps import RunNote
from tests.unit.adapters._tracing_doubles import build_sink
from tests.unit.adapters.test_retrieval_fastembed import KB_DIR, TRANSCRIPTIONS_DIR, cached_model_dir

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import ReadableSpan
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_SKIP = "bge-small-en-v1.5 is not cached locally (var/fastembed); the built-index tests need it"


@functools.cache
def built_index_dir() -> Path | None:
    """The KB index, built once per process by the ingest CLI's own entry point with an injected local embedder."""
    cache = cached_model_dir()
    if cache is None:
        return None
    import numpy as np
    from fastembed import TextEmbedding

    out = Path(tempfile.mkdtemp(prefix="meridian-aea51-index-")) / "index"
    atexit.register(shutil.rmtree, out.parent, True)
    model = TextEmbedding(EMBEDDING_MODEL, cache_dir=str(cache), local_files_only=True)

    def embed(texts: Any) -> Any:
        return np.asarray([np.asarray(v) for v in model.embed(list(texts))], dtype=np.float32)

    rc = ingest.main(
        ["--kb-dir", str(KB_DIR), "--transcriptions-dir", str(TRANSCRIPTIONS_DIR), "--out-dir", str(out)],
        embed=embed,
    )
    assert rc == 0, "the index build failed"
    assert FastembedIndex(out, model_cache_dir=cache).readiness().ok
    return out


def require_index() -> Path:
    found = built_index_dir()
    if found is None:
        pytest.skip(INDEX_SKIP)
    return found


@contextmanager
def fastembed_offline() -> Iterator[None]:
    """Process config for fastembed's query embedder (not app Settings): the cached model, no hub access."""
    cache = cached_model_dir()
    names = {"FASTEMBED_CACHE_PATH": str(cache) if cache is not None else None, "HF_HUB_OFFLINE": "1"}
    previous = {name: os.environ.get(name) for name in names}
    for name, value in names.items():
        if value is not None:
            os.environ[name] = value
    try:
        yield
    finally:
        for name, old in previous.items():
            if old is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = old


@dataclass(frozen=True)
class Stall:
    seconds: float  # the model call sleeps this long, then returns a TIMEOUT failure


StepEntry = ScriptEntry | Stall | tuple[ScriptEntry | Stall, ...]
_CURRENT = threading.local()


def _current_request() -> Any:
    return getattr(_CURRENT, "request", None)


class StepScript(JourneyScript):
    """Per-step entries instead of one queue (PD-8): one entry answers every call of its role in the step; a tuple is
    consumed in call order (for Role.SPECIALIST: indexed by the tool round of the run, so concurrent runs never mix).
    `by_marker` picks another table when the request's JSON contains the marker word (PD-13)."""

    def __init__(self) -> None:
        super().__init__()
        self.probe: Callable[[], None] | None = None
        self._default: Mapping[Role, StepEntry] = {}
        self._by_marker: Mapping[str, Mapping[Role, StepEntry]] = {}
        self._counters: dict[tuple[int, Role], int] = {}
        self._step_lock = threading.Lock()

    def set_step(
        self,
        default: Mapping[Role, StepEntry],
        *,
        by_marker: Mapping[str, Mapping[Role, StepEntry]] | None = None,
    ) -> None:
        with self._step_lock:
            self._default = dict(default)
            self._by_marker = dict(by_marker or {})
            self._counters = {}

    def take(self, role: Role) -> ScriptEntry | None:
        if self.probe is not None:
            self.probe()
        request = _current_request()
        text = request.model_dump_json() if request is not None else ""
        with self._step_lock:
            table: Mapping[Role, StepEntry] = next(
                (t for marker, t in self._by_marker.items() if marker in text and role in t), self._default
            )
            entry = table.get(role)
            if entry is None:
                return None
            if isinstance(entry, tuple):
                if role is Role.SPECIALIST:
                    index = int(getattr(_CURRENT, "round", 0))
                else:
                    key = (id(table), role)
                    index = self._counters.get(key, 0)
                    self._counters[key] = index + 1
                if index >= len(entry):
                    return None
                chosen: ScriptEntry | Stall = entry[index]
            else:
                chosen = entry
        if isinstance(chosen, Stall):
            time.sleep(chosen.seconds)
            return ScriptedFailure(kind=ProviderFailureKind.TIMEOUT)
        return chosen

    def calls_since(self, mark: int) -> tuple[ScriptedCall, ...]:
        return self.calls[mark:]


class StepJevModel(ScriptedJevModel):
    def choose(self, req: Any, *, timeout_s: float) -> Any:
        _CURRENT.request = req
        try:
            return super().choose(req, timeout_s=timeout_s)
        finally:
            _CURRENT.request = None


class StepAnthropicModel(ScriptedAnthropicModel):
    def choose(self, req: Any, *, timeout_s: float) -> Any:
        _CURRENT.request = req
        try:
            return super().choose(req, timeout_s=timeout_s)
        finally:
            _CURRENT.request = None

    def structured(self, req: Any, *, timeout_s: float) -> Any:
        _CURRENT.request = req
        try:
            return super().structured(req, timeout_s=timeout_s)
        finally:
            _CURRENT.request = None

    def tool_step(self, req: Any, *, timeout_s: float) -> Any:
        _CURRENT.request = req
        _CURRENT.round = (
            len(req.messages.items) - 1
        ) // 2  # start() is one item, each append with results two
        try:
            return super().tool_step(req, timeout_s=timeout_s)
        finally:
            _CURRENT.request = None
            _CURRENT.round = 0


def step_overrides(
    settings: Settings,
    script: StepScript,
    *,
    wall_clock: Callable[[], datetime] | None = None,
    trace: TraceSink | None = None,
) -> tuple[ContainerOverrides, Mapping[Role, ScriptedModel]]:
    """As AEA-57's scripted_overrides, with step-aware model objects. Each role's object carries its RoleSpec's model."""
    specs = role_specs(settings)

    def make(role: Role) -> ScriptedModel:
        provider, spec = specs[role]
        cls = StepJevModel if provider == "openrouter_jev" else StepAnthropicModel
        return cls(script, role=role, model=spec.model)

    choice = {role: make(role) for role in settings.models.choice}
    structured = {role: make(role) for role in settings.models.structured}
    tools = {role: make(role) for role in settings.models.tools}
    overrides = ContainerOverrides(
        choice=cast(Any, choice),
        structured=cast(Any, structured),
        tools=cast(Any, tools),
        trace=trace,
        wall_clock=wall_clock,
    )
    models: dict[Role, ScriptedModel] = {}
    for table in (choice, structured, tools):
        for role, model in table.items():
            models[role] = model
    return overrides, models


@dataclass(frozen=True)
class RunOptions:
    index: Literal["built", "empty"] = "built"
    eval_key: bool = False
    trace: TraceSink | None = None
    with_clock: bool = False
    deadline_s: int | None = None  # short turn deadline (PD-9); needs monkeypatch


DEFAULT_OPTIONS = RunOptions()


@dataclass
class CustomerRun(JourneyRun):
    eval_key: str | None = None  # the run's MERIDIAN_EVAL_KEY value, or None

    @property
    def steps(self) -> StepScript:
        return cast(StepScript, self.script)


@contextmanager
def customer_environment(*, index_dir: Path | None, eval_key: str | None) -> Iterator[JourneyEnv]:
    root = Path(tempfile.mkdtemp(prefix="meridian-aea51-"))
    try:
        for name in ("data", "no-dist", "index"):
            (root / name).mkdir()
        environ = journey_environ(root)
        if index_dir is not None:
            environ["MERIDIAN_INDEX_DIR"] = str(index_dir)
        if eval_key is not None:
            environ["MERIDIAN_EVAL_KEY"] = eval_key
        settings = Settings.from_env(environ)
        before = sha256_file(ISSUED_DB)
        yield JourneyEnv(
            root=root,
            data_dir=root / "data",
            web_dist_dir=root / "no-dist",
            index_dir=Path(environ["MERIDIAN_INDEX_DIR"]),
            settings=settings,
            issued_sha256_before=before,
        )
        assert sha256_file(ISSUED_DB) == before, "the issued scheduling DB changed during the run"
    finally:
        shutil.rmtree(root, ignore_errors=True)


@contextmanager
def open_customer_run(
    request: pytest.FixtureRequest,
    options: RunOptions = DEFAULT_OPTIONS,
    *,
    monkeypatch: pytest.MonkeyPatch | None = None,
) -> Iterator[CustomerRun]:
    """AEA-57's open_journey order: socket guard, log tap, environment, server; the same evidence collection."""
    with socket_guard() as guard, tap_logs() as logs, fastembed_offline():
        index_dir = require_index() if options.index == "built" else None
        eval_key = letters(40) if options.eval_key else None
        with customer_environment(index_dir=index_dir, eval_key=eval_key) as env:
            if options.deadline_s is not None:
                assert monkeypatch is not None, "deadline_s needs the monkeypatch fixture"
                deadline = options.deadline_s
                monkeypatch.setattr(
                    "meridian.web.container.Limits", lambda: Limits(turn=TurnLimits(deadline_s=deadline))
                )
            script = StepScript()
            clock = StepClock() if options.with_clock else None
            overrides, models = step_overrides(env.settings, script, wall_clock=clock, trace=options.trace)
            collector = request.config.stash[COLLECTOR_KEY]
            with launch_server(env.settings, overrides=overrides) as server:
                run = CustomerRun(
                    env=env,
                    server=server,
                    script=script,
                    models=models,
                    clock=clock,
                    db=DbReader(env.db_path),
                    logs=logs,
                    guard=guard,
                    collector=collector,
                    strict=bool(request.config.getoption("--journeys-strict")),
                    nodeid=request.node.nodeid,
                    eval_key=eval_key,
                )
                try:
                    yield run
                finally:
                    run.close_clients()
            spend = DbReader(env.db_path).one(
                "SELECT COUNT(*) AS n, COALESCE(SUM(cost_usd), 0.0) AS total FROM spend_ledger"
            )
            collector.add_note(
                RunNote(
                    host=server.host,
                    port=server.port,
                    agent_version=env.settings.agent_version,
                    models={r.value: f"{m.provider}/{m.model}" for r, m in models.items()},
                    issued_sha256=env.issued_sha256_before,
                    spend_rows=int(spend["n"]),
                    spend_total_usd=float(spend["total"]),
                    outbound_blocked=len(guard.blocked),
                )
            )
    if guard.blocked:
        raise AssertionError(f"socket guard refused {len(guard.blocked)} non-loopback connection(s)")


def build_capture_sink(registry: list[Any]) -> tuple[TraceSink, InMemorySpanExporter]:
    sink, exporter, _stub, _alerts = build_sink(registry)
    sink.start()
    return sink, cast("InMemorySpanExporter", exporter)


def finished_spans(sink: Any, exporter: InMemorySpanExporter) -> list[ReadableSpan]:
    sink.flush()
    return sorted(exporter.get_finished_spans(), key=lambda s: s.start_time or 0)


def write_probe(db_path: Path, failures: list[str]) -> Callable[[], None]:
    """A function that fails (into `failures`) exactly when another connection holds a write transaction."""

    def probe() -> None:
        conn = sqlite3.connect(str(db_path), timeout=0, isolation_level=None)
        try:
            conn.execute("PRAGMA busy_timeout=0")
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError as exc:
            failures.append(f"{type(exc).__name__}: {exc}")
        finally:
            conn.close()

    return probe
