"""Agent version stamp (AEA-50, DAT-22): `<12 hex of the commit>+<8 hex of models and prompts>`.

Prints one line and nothing else on success. Never prints a setting value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, Final, cast

from meridian.config import Settings, default_model_settings

ROOT: Final = Path(__file__).resolve().parents[1]  # repo root locally; /app in the image
BUILD_SHA_FILE: Final = ROOT / "BUILD_SHA"
PROMPT_GLOBS: Final = ("src/meridian/agent/prompts/*.py", "src/meridian/policy/texts.py")
# The commit each host sets on a Git-built deploy. Railway's comes first (the frozen AEA-50 precedence); Render
# (RENDER_GIT_COMMIT, set at build and run time) hosts the app since 2026-10-21. Only one is ever set.
HOST_SHA_VARIABLES: Final = ("RAILWAY_GIT_COMMIT_SHA", "RENDER_GIT_COMMIT")


def prompt_files(root: Path = ROOT) -> tuple[Path, ...]:
    """Every prompt and policy-text source file, sorted."""
    found: set[Path] = set()
    for pattern in PROMPT_GLOBS:
        found.update(root.glob(pattern))
    return tuple(sorted(found))


def resolve_git_sha(environ: Mapping[str, str], build_sha_file: Path = BUILD_SHA_FILE) -> str:
    """The host's commit SHA (Railway's, else Render's), else the BUILD_SHA file (a `-dirty` suffix is kept),
    else `unknown`."""
    for name in HOST_SHA_VARIABLES:
        value = environ.get(name, "").strip()
        if value:
            return value
    if build_sha_file.is_file():
        text = build_sha_file.read_text(encoding="utf-8").strip()
        if text:
            return text
    return "unknown"


def _key(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def compute_agent_version(git_sha: str, model_config: Mapping[str, Any], prompt_files: Iterable[Path]) -> str:
    """Pure: same inputs give the same value; any byte change in a prompt or the map changes the suffix only."""
    prompts = {_key(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in prompt_files}
    payload = {"models": dict(model_config), "prompts": dict(sorted(prompts.items()))}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{git_sha[:12]}+{digest[:8]}"


def model_config() -> Mapping[str, Any]:
    """The deployed role to model map. `models` has no env name, so the default is the deployed map."""
    # model_construct skips the required-secret fields: this script never needs or reads a key value.
    settings = cast(Any, Settings).model_construct(models=default_model_settings())
    return cast(Mapping[str, Any], settings.role_model_map())


def build_sha_from_git(repo: Path = ROOT) -> str:
    """HEAD of `repo`; `-dirty` when a tracked file differs (untracked files never count)."""
    git = shutil.which("git")
    if git is None:
        raise FileNotFoundError("git")
    head = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [git, "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    status = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [git, "-C", str(repo), "status", "--porcelain", "--untracked-files=no"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return f"{head}-dirty" if status else head


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scripts.agent_version")
    parser.add_argument(
        "--write-build-sha", nargs="?", const=str(BUILD_SHA_FILE), default=None, metavar="PATH"
    )
    try:
        args = parser.parse_args(argv)
        if args.write_build_sha is not None:
            sha = build_sha_from_git()
            Path(args.write_build_sha).write_text(sha + "\n", encoding="utf-8")
            sys.stdout.write(f"build_sha={sha}\n")
            return 0
        version = compute_agent_version(resolve_git_sha(os.environ), model_config(), prompt_files())
    except Exception as exc:
        sys.stderr.write(f"agent_version_error={type(exc).__name__}\n")
        return 1
    sys.stdout.write(version + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
