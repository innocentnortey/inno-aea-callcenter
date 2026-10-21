"""Session-wide browser facts and the browser values for AEA-57's evidence record (AEA-58 AC-14)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from tests.journeys.support.env import REPO_ROOT
from tests.journeys.support.record import ISSUED_REL, RecordData, build_record_data
from tests.journeys.support.steps import JOURNEY_NODEID, StepCollector

if TYPE_CHECKING:
    from tests.journeys.browser.build import ProductionBuild

SHOTS_SUFFIX: Final = ""  # screenshots folder = record path without ".md"


def _counts(counter: Counter[str], owners: dict[str, str] | None = None) -> str:
    if not counter:
        return "none"
    parts = []
    for op in sorted(counter):
        owner = f" ({owners[op]})" if owners and op in owners else ""
        parts.append(f"{op}={counter[op]}{owner}")
    return ", ".join(parts)


@dataclass
class BrowserSession:
    build: ProductionBuild | None = None
    channel: str | None = None
    chrome_version: str | None = None
    devices: set[str] = field(default_factory=set)
    screenshots: list[Path] = field(default_factory=list)
    validated: Counter[str] = field(default_factory=Counter)
    unrouted: Counter[str] = field(default_factory=Counter)
    unrouted_owners: dict[str, str] = field(default_factory=dict)
    unbound: Counter[str] = field(default_factory=Counter)
    unbound_owners: dict[str, str] = field(default_factory=dict)
    sse_checked: Counter[str] = field(default_factory=Counter)
    unfinished: int = 0
    failures: int = 0

    def summary_line(self) -> str:
        return (
            f"browser API responses validated: {sum(self.validated.values())} ({_counts(self.validated)}); "
            f"SSE checked: {_counts(self.sse_checked)}; "
            f"unrouted (blocked): {_counts(self.unrouted, self.unrouted_owners)}; "
            f"unbound 500 (blocked): {_counts(self.unbound, self.unbound_owners)}; "
            f"unfinished: {self.unfinished}; failures: {self.failures}"
        )


BROWSER_KEY = pytest.StashKey[BrowserSession]()


def browser_record_values(
    base: RecordData, session: BrowserSession, *, collector: StepCollector, root: Path
) -> dict[str, str]:
    values = dict(base.values)
    journeys = (
        ", ".join(sorted({s.journey for s in collector.steps if JOURNEY_NODEID.match(s.nodeid)})) or "none"
    )
    note = collector.notes[0] if collector.notes else None
    models = ", ".join(f"{r}={m}" for r, m in sorted(note.models.items())) if note else "none"
    build = session.build
    dist = str(build.dist_dir) if build else "none"
    index_hash = build.index_sha256 if build else "n/a"
    check = build.check_line if build else "n/a"
    last = collector.notes[-1] if collector.notes else None
    devices = ", ".join(sorted(session.devices)) or "none"
    values["Claim"] = (
        f"{base.scope}: journeys {journeys} in system Chrome against the production build served by the real app "
        "(browser level), through the normal SCR-12 login, with the scripted model; per-step results under Result"
    )
    values["Environment"] = (
        f"{last.host if last else '127.0.0.1'}, ephemeral port per test; server: uvicorn.Server in a background thread "
        "over create_app(Settings.from_env(<journey environ> + MERIDIAN_WEB_DIST_DIR=<dist>, "
        "MERIDIAN_REQUIRE_FRONTEND=true), overrides=ContainerOverrides(choice, structured, tools)); "
        f"DB copy: {ISSUED_REL} (sha256 {note.issued_sha256 if note else 'n/a'}) copied by the app's first boot into a "
        f'temp MERIDIAN_DATA_DIR; frontend build: {dist} (index.html sha256 {index_hash}; check:dist: "{check}"); '
        "model adapter: ScriptedModel (tests/journeys/support/scripted_model.py); "
        f"model ids: {models}; browser: Google Chrome channel {session.channel} version {session.chrome_version}; "
        f"devices: {devices} (1280x800, 390x844), locale en-US, timezone America/Chicago, reduced motion"
    )
    folder = f"docs/testing/journeys/ (<date>-{base.scope}/)"
    if session.screenshots:
        folder = str(session.screenshots[0].parent)
        try:
            folder = str(session.screenshots[0].parent.relative_to(root))
        except ValueError:
            pass
    values["Evidence location"] = (
        f"{base.values['Evidence location']}; screenshots: {folder} ({len(session.screenshots)} files); "
        f"{session.summary_line()}"
    )
    values["Remaining limitations"] = (
        "J-2 to J-10 and J-8's staff-role steps are not in the browser yet (AEA-62; per-wave walkthroughs); SSE "
        "frames are not body-checked (status and content type only; frames are AEA-41's and AEA-59's); scripted "
        "model only (live models: AEA-61); redaction is not re-checked here (CAP-10, CAP-11); the Prism/UX-5 sweep "
        "is not this evidence (AEA-55); held-out data is never read"
    )
    return values


def sample_record_values(session: BrowserSession, collector: StepCollector) -> dict[str, str]:
    """The values a record would hold right now (AC-9 scans them for secrets)."""
    base = build_record_data(scope="AEA-58", collector=collector, root=REPO_ROOT, command="j1")
    return browser_record_values(base, session, collector=collector, root=REPO_ROOT)
