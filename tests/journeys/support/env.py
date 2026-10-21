"""Per-run environment and the issued-file guard (AEA-57; cases.md section 1.4, integrated-journeys rule section 2)."""

from __future__ import annotations

import secrets
import shutil
import string
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from meridian.adapters.sqlite.migrate import WORKING_DB_NAME
from meridian.config import Settings
from tests.fixtures.sqlite import ISSUED_DB
from tests.journeys.support.db import sha256_file

REPO_ROOT = Path(__file__).resolve().parents[3]
PLACEHOLDER_ANTHROPIC_KEY = "journey-placeholder-anthropic-not-a-key"
PLACEHOLDER_OPENROUTER_KEY = "journey-placeholder-openrouter-not-a-key"


def letters(n: int) -> str:
    return "".join(secrets.choice(string.ascii_lowercase) for _ in range(n))


def journey_environ(root: Path) -> dict[str, str]:
    """The environment the deployed app would get, for one run. Holds the per-run demo pair and secret: never print it."""
    return {
        "ANTHROPIC_API_KEY": PLACEHOLDER_ANTHROPIC_KEY,
        "OPENROUTER_API_KEY": PLACEHOLDER_OPENROUTER_KEY,
        "MERIDIAN_DEMO_USERNAME": "journeyuser" + letters(8),
        "MERIDIAN_DEMO_PASSWORD": "journeypass" + letters(20),
        "MERIDIAN_SESSION_SECRET": letters(48),
        "MERIDIAN_COOKIE_SECURE": "false",
        "MERIDIAN_REQUIRE_FRONTEND": "false",
        "MERIDIAN_WEB_DIST_DIR": str(root / "no-dist"),
        "MERIDIAN_DATA_DIR": str(root / "data"),
        "MERIDIAN_INDEX_DIR": str(root / "index"),
    }  # eval key, the four Langfuse names, proxy-header trust and agent version are deliberately absent


@dataclass(frozen=True)
class JourneyEnv:
    root: Path
    data_dir: Path
    web_dist_dir: Path
    index_dir: Path
    settings: Settings
    issued_sha256_before: str

    @property
    def db_path(self) -> Path:
        return self.data_dir / WORKING_DB_NAME

    def secret_values(self) -> tuple[str, str]:
        """(demo password, session secret)."""
        return (
            self.settings.demo_password.get_secret_value(),
            self.settings.session_secret.get_secret_value(),
        )


@contextmanager
def journey_environment() -> Iterator[JourneyEnv]:
    root = Path(tempfile.mkdtemp(prefix="meridian-journey-"))
    try:
        data_dir, web_dist_dir, index_dir = root / "data", root / "no-dist", root / "index"
        for folder in (data_dir, web_dist_dir, index_dir):
            folder.mkdir()
        settings = Settings.from_env(journey_environ(root))
        if Path(settings.issued_db_path).resolve() != ISSUED_DB.resolve():
            raise RuntimeError(
                "journey harness: run pytest from the repository root (Settings.issued_db_path resolves elsewhere)"
            )
        before = sha256_file(ISSUED_DB)
        yield JourneyEnv(root, data_dir, web_dist_dir, index_dir, settings, before)
        if sha256_file(ISSUED_DB) != before:
            raise AssertionError("the issued scheduling DB changed during the journey run")
    finally:
        shutil.rmtree(root, ignore_errors=True)
