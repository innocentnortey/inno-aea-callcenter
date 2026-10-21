"""Production-build preflight and the Chrome launch wrapper, both failing loudly (AEA-58 AC-1, AC-12)."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from playwright.sync_api import Error as PlaywrightError

from tests.journeys.support.db import sha256_file
from tests.journeys.support.env import REPO_ROOT

if TYPE_CHECKING:
    from playwright.sync_api import Browser, Playwright

BUILD_COMMAND: Final = "npm --prefix apps/web run build && npm --prefix apps/web run check:dist"
CHECK_DIST_OK: Final = "dist is clean: no dev-layer markers"
DEFAULT_CHANNEL: Final = "chrome"


class BrowserPrerequisiteError(RuntimeError):
    """A browser journey cannot run; raised as an error, never a skip (integrated-journeys rule 6)."""


@dataclass(frozen=True)
class ProductionBuild:
    dist_dir: Path
    index_sha256: str
    check_line: str  # CHECK_DIST_OK, as printed by check-dist.mjs


def dist_dir_from_env(environ: Mapping[str, str] = os.environ) -> Path:
    """MERIDIAN_WEB_DIST_DIR, default apps/web/dist; a relative path is relative to REPO_ROOT; resolved."""
    raw = environ.get("MERIDIAN_WEB_DIST_DIR") or "apps/web/dist"
    path = Path(raw)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def check_production_build(dist_dir: Path) -> ProductionBuild:
    if not (dist_dir / "index.html").is_file():
        raise BrowserPrerequisiteError(
            f"browser journeys need the production build: no index.html in MERIDIAN_WEB_DIST_DIR={dist_dir}. "
            f"Build it first: {BUILD_COMMAND} (the server runs with MERIDIAN_REQUIRE_FRONTEND=true and refuses "
            "to start without it)"
        )
    script = dist_dir.parent / "scripts" / "check-dist.mjs"
    if dist_dir.name != "dist" or not script.is_file():
        raise BrowserPrerequisiteError(
            f"cannot run check:dist for MERIDIAN_WEB_DIST_DIR={dist_dir}: point it at an apps/web/dist folder"
        )
    try:
        done = subprocess.run(
            ["node", str(script)],
            cwd=dist_dir.parent,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except FileNotFoundError:
        raise BrowserPrerequisiteError("node is not on PATH: check:dist needs Node 24") from None
    if done.returncode != 0 or CHECK_DIST_OK not in done.stdout:
        text = (done.stderr or done.stdout)[:400]
        raise BrowserPrerequisiteError(f"check:dist failed on {dist_dir}: {text}")
    return ProductionBuild(dist_dir, sha256_file(dist_dir / "index.html"), CHECK_DIST_OK)


def launch_chrome(playwright: Playwright, launch_args: Mapping[str, object]) -> tuple[Browser, str]:
    args = dict(launch_args)
    channel = str(args.get("channel") or DEFAULT_CHANNEL)
    args["channel"] = channel
    try:
        browser = playwright.chromium.launch(**args)  # type: ignore[arg-type]
    except PlaywrightError as exc:
        first = (str(exc).strip().splitlines() or [""])[0]
        raise BrowserPrerequisiteError(
            f"system Chrome did not start for --browser-channel {channel}: {first}. "
            "Install that channel or pass --browser-channel with an installed one"
        ) from None
    return browser, channel
