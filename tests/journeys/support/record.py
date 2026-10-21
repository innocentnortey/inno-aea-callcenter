"""The evidence record with rule section 4's nine fields (AEA-57; integrated-journeys rule section 4)."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tests.journeys.support.steps import JOURNEY_NODEID, StepCollector

FIELDS: tuple[str, ...] = (
    "Claim",
    "Level",
    "Tested revision",
    "Environment",
    "Command",
    "Result",
    "Evidence location",
    "Remaining limitations",
    "Blocked by",
)
SCOPE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,40}$")
LEVEL = "integrated with a scripted model"
ISSUED_REL = "docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite"


@dataclass(frozen=True)
class RecordData:
    scope: str
    values: Mapping[str, str]


def _git(root: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)
    except OSError:
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def tested_revision(root: Path, agent_version: str) -> str:
    sha = _git(root, "rev-parse", "--short", "HEAD")
    if not sha:
        return f"unknown (git unavailable); agent_version {agent_version}"
    dirty = _git(root, "status", "--porcelain", "--", "src", "tests", "eval", "pyproject.toml", "uv.lock")
    if dirty:
        return f"uncommitted (HEAD {sha}); agent_version {agent_version}"
    return f"{sha}; agent_version {agent_version}"


def _step_line(journey: str, step: str, nodeid: str, status: str, detail: str) -> str:
    func = nodeid.rsplit("::", 1)[-1]
    head = f"{journey} · {step} ({func})"
    if status == "pass":
        return f"{head}: pass"
    if status == "fail":
        return f"{head}: fail: {detail}"
    return f"{head}: {detail}"


def build_record_data(*, scope: str, collector: StepCollector, root: Path, command: str) -> RecordData:
    steps = [s for s in collector.steps if JOURNEY_NODEID.match(s.nodeid)]
    tests = [t for t in collector.tests if JOURNEY_NODEID.match(t.nodeid)]
    notes = collector.notes
    journeys = sorted({s.journey for s in steps})
    passed = any(s.status == "pass" for s in steps)
    note = notes[0] if notes else None
    last = notes[-1] if notes else None
    models = ", ".join(f"{r}={m}" for r, m in sorted(note.models.items())) if note else "none"
    result_lines = [_step_line(s.journey, s.step, s.nodeid, s.status, s.detail) for s in steps]
    for journey in journeys:
        ids = {s.nodeid for s in steps if s.journey == journey}
        mine = [t for t in tests if t.nodeid in ids]
        result_lines.append(
            f"{journey} wall time: {sum(t.duration_s for t in mine):.1f} s across {len(mine)} tests"
        )
    owners = sorted({o for s in steps if s.status == "blocked" for o in s.blocked_on})
    values = {
        "Claim": (
            f"{scope}: journeys {', '.join(journeys) or 'none'} through the real app over HTTP (API level) "
            "with the scripted model; per-step results under Result"
        ),
        "Level": LEVEL + " for the steps marked pass"
        if passed
        else "none reached: every step was blocked or failed",
        "Tested revision": tested_revision(root, note.agent_version if note else "dev"),
        "Environment": (
            f"{last.host if last else '127.0.0.1'} (ephemeral port per test, last {last.port if last else 'n/a'}); "
            "server: uvicorn.Server in a background thread over create_app(Settings.from_env(<journey environ>), "
            "overrides=ContainerOverrides(choice, structured, tools, wall_clock)); "
            f"DB copy: {ISSUED_REL} (sha256 {note.issued_sha256 if note else 'n/a'}) copied by the app's first boot "
            "into a temp MERIDIAN_DATA_DIR; frontend build: none (API level); model adapter: ScriptedModel "
            f"(tests/journeys/support/scripted_model.py); model ids: {models}"
        ),
        "Command": command,
        "Result": "\n".join(result_lines) if result_lines else "no journey steps ran",
        "Evidence location": (
            f"this file; pytest output of the command; spend_ledger rows written: {sum(n.spend_rows for n in notes)}, "
            f"total cost_usd {sum(n.spend_total_usd for n in notes):.2f}; "
            f"non-loopback connections refused: {sum(n.outbound_blocked for n in notes)}"
        ),
        "Remaining limitations": (
            "API level only (browser journeys: AEA-58); scripted model only (live models: AEA-61); "
            "J-1 only (other journeys land with their tickets); redaction is not re-checked here (CAP tests); "
            "held-out data is never read"
        ),
        "Blocked by": ", ".join(owners) if owners else "none",
    }
    return RecordData(scope=scope, values=values)


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def render_record(data: RecordData) -> str:
    lines = [f"# Journey record: {data.scope} (journey harness run)", "", "| Field | Value |", "|---|---|"]
    lines.extend(f"| {name} | {_cell(data.values[name])} |" for name in FIELDS)
    return "\n".join(lines) + "\n"


def record_path(root: Path, scope: str, day: date) -> Path:
    return root / "docs" / "testing" / "journeys" / f"{day.isoformat()}-{scope}.md"


def maybe_write_record(
    scope: str | None, *, root: Path, collector: StepCollector, command: str, day: date
) -> Path | None:
    if scope is None:
        return None
    if not SCOPE_PATTERN.match(scope):
        raise ValueError(f"bad journey record scope: {scope!r}")
    data = build_record_data(scope=scope, collector=collector, root=root, command=command)
    path = record_path(root, scope, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_record(data), encoding="utf-8")
    return path
