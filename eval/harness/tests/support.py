"""Shared helpers for the harness and capture tests: running the CLI in process, reading its outputs, a recording
judge double and an OpenAPI check. Harness imports are lazy so that a missing module fails the test that needs it."""

from __future__ import annotations

import io
import json
import re
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from eval.harness.tests.fixture_cases import OPENAPI, RunSecrets, env_for
from eval.harness.tests.stub_app import StubApp, StubCall

UUID4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def make_stub(
    run: RunSecrets,
    scripted: Callable[[StubCall], dict[str, Any] | None] | None = None,
    **kwargs: Any,
) -> StubApp:
    return StubApp(
        username=run.username, password=run.password, eval_key=run.eval_key, scripted=scripted, **kwargs
    )


class FakeJudge:
    """Records every call; fails the rubric indices in ``failing``. Never touches a network."""

    model = "fake-judge"

    def __init__(self, *, failing: Collection[int] = ()) -> None:
        self.calls: list[dict[str, Any]] = []
        self._failing = set(failing)

    def judge(self, *, reply: str, evidence: Sequence[str], rubric: Sequence[str]) -> tuple[Any, ...]:
        from eval.harness.judge import JudgeVerdict

        self.calls.append({"reply": reply, "evidence": list(evidence), "rubric": list(rubric)})
        return tuple(
            JudgeVerdict(index=i, passed=i not in self._failing, quote="stub quote")
            for i in range(len(rubric))
        )

    def rubrics(self) -> list[str]:
        return [entry for call in self.calls for entry in call["rubric"]]


@dataclass
class Outcome:
    code: int
    log_text: str
    reports_dir: Path
    stub: StubApp | None
    judge: FakeJudge | None

    def json_files(self) -> list[Path]:
        return sorted(self.reports_dir.glob("*.json")) if self.reports_dir.is_dir() else []

    def reports(self) -> list[dict[str, Any]]:
        return [json.loads(p.read_text(encoding="utf-8")) for p in self.json_files()]

    def report(self) -> dict[str, Any]:
        reports = self.reports()
        assert len(reports) == 1, f"expected one report, found {len(reports)}"
        return reports[0]

    def markdown(self) -> str:
        files = sorted(self.reports_dir.glob("*.md")) if self.reports_dir.is_dir() else []
        assert len(files) == 1
        return files[0].read_text(encoding="utf-8")

    def timings_path(self) -> Path:
        files = sorted(self.reports_dir.glob("*.client_side_turn_timings.jsonl"))
        assert len(files) == 1
        return files[0]

    def timings(self) -> list[dict[str, Any]]:
        return [json.loads(line) for line in self.timings_path().read_text(encoding="utf-8").splitlines()]

    def log_lines(self) -> list[dict[str, Any]]:
        out = []
        for line in self.log_text.splitlines():
            if line.startswith("{"):
                out.append(json.loads(line))
        return out

    def all_text(self) -> str:
        """Every output the harness wrote: the log and every file in the reports directory."""
        parts = [self.log_text]
        if self.reports_dir.is_dir():
            parts += [
                p.read_text(encoding="utf-8") for p in sorted(self.reports_dir.iterdir()) if p.is_file()
            ]
        return "\n".join(parts)


def base_argv(
    cases_dir: Path,
    reports_dir: Path,
    *,
    suite: str = "e2e",
    split: str | None = "dev",
    repeats: int = 1,
    base_url: str | None = "http://stub.example.test",
    extra: Sequence[str] = (),
) -> list[str]:
    argv = ["run", "--suite", suite]
    if split is not None:
        argv += ["--split", split]
    argv += ["--repeats", str(repeats)]
    if base_url is not None:
        argv += ["--base-url", base_url]
    argv += ["--cases-dir", str(cases_dir), "--reports-dir", str(reports_dir)]
    return [*argv, *extra]


def run_cli(
    tmp_path: Path,
    argv: Sequence[str],
    *,
    stub: StubApp | None,
    run: RunSecrets,
    judge: FakeJudge | None = None,
    harness_root: Path | None = None,
    freeze: bool = True,
    env: dict[str, str] | None = None,
) -> Outcome:
    """Run ``eval.harness.cli.main`` in process against the stub, with a fresh freeze file for the given root."""
    from eval.harness.cli import main
    from eval.harness.deps import HARNESS_ROOT, HarnessDeps
    from eval.harness.freeze import write_freeze

    root = harness_root or HARNESS_ROOT
    freeze_file = tmp_path / "freeze.json"
    if freeze:
        write_freeze(freeze_file, root=root)
    log = io.StringIO()
    deps = HarnessDeps(
        transport=stub.transport if stub is not None else None,
        judge=judge,
        env=env if env is not None else env_for(run),
        harness_root=root,
        freeze_file=freeze_file,
        log_stream=log,
        ledger_dir=tmp_path / "ledger",
    )
    code = main(list(argv), deps=deps)
    reports_dir = (
        Path(argv[argv.index("--reports-dir") + 1]) if "--reports-dir" in argv else tmp_path / "reports"
    )
    return Outcome(code=code, log_text=log.getvalue(), reports_dir=reports_dir, stub=stub, judge=judge)


def reports_dir_arg(argv: Sequence[str]) -> Path:
    return Path(argv[argv.index("--reports-dir") + 1])


def measure(summary: dict[str, Any], measure_id: str) -> dict[str, Any]:
    found = [m for m in summary["measures"] if m["id"] == measure_id]
    assert len(found) == 1, (
        f"measure {measure_id} not present exactly once: {[m['id'] for m in summary['measures']]}"
    )
    entry: dict[str, Any] = found[0]
    return entry


def items_of(result: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [i for i in result["items"] if i["item"] == kind]


def validate_eval_run(summary: dict[str, Any]) -> None:
    """The summary validates as the OpenAPI ``EvalRun`` (what CON-20 reads)."""
    spec = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
    schema = {"components": spec["components"], "$ref": "#/components/schemas/EvalRun"}
    Draft202012Validator(schema).validate(summary)


def validate_report_file(report: dict[str, Any]) -> Any:
    from eval.harness.records import EvalReportFile

    return EvalReportFile.model_validate(report)


def markdown_sections(md: str) -> dict[str, str]:
    """Heading line -> its body, for the ``##`` sections."""
    sections: dict[str, str] = {}
    current: str | None = None
    for line in md.splitlines():
        if line.startswith("## "):
            current = line
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def markdown_headings(md: str) -> list[str]:
    return [line for line in md.splitlines() if line.startswith("#")]


def assert_targets_only_in_target_column(md: str, summary: dict[str, Any]) -> None:
    """A target appears only in the column headed ``Target`` of the measures (or latency) table."""
    targets = {m["target"] for m in summary["measures"] if m.get("target") and len(m["target"]) >= 3}
    sections = markdown_sections(md)
    for heading, body in sections.items():
        in_measures = heading.startswith(("## Measures", "## Latency"))
        for target in targets:
            if target not in body:
                continue
            assert in_measures, f"target {target!r} appears under {heading!r}"
            for line in body.splitlines():
                if target in line:
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]
                    assert cells[-1] == target, (
                        f"target {target!r} is not in the last (Target) cell: {line!r}"
                    )
        if in_measures and body.strip():
            header = next(line for line in body.splitlines() if line.startswith("|"))
            assert header.strip().strip("|").split("|")[-1].strip() == "Target"
    head = md.split("## ", 1)[0]
    for target in targets:
        assert target not in head


def assert_log_allow_listed(lines: Sequence[dict[str, Any]]) -> None:
    from eval.harness.runlog import ALLOWED_LOG_KEYS

    assert lines, "the run wrote no log lines"
    for line in lines:
        assert set(line) <= ALLOWED_LOG_KEYS, f"unlisted log keys: {set(line) - ALLOWED_LOG_KEYS}"


def assert_absent(text: str, values: Collection[str], *, where: str) -> None:
    for value in values:
        assert value and value not in text, f"a secret or sentinel value leaked into {where}"


def assert_all_requests_have_eval_headers(
    stub: StubApp, run: RunSecrets, run_id: str, tag: str, *, host: str = "stub.example.test"
) -> None:
    assert stub.requests
    for index, request in enumerate(stub.requests):
        assert request.headers["x-meridian-eval-key"] == run.eval_key
        assert request.headers["x-meridian-run-id"] == run_id
        assert request.headers["x-meridian-run-tag"] == tag
        assert request.url.host == host
        if index > 0:
            assert "mhc_session=" in request.headers.get("cookie", "")
