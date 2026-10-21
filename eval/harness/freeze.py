"""Harness digest, commit, freeze file and the tamper check (AC-5)."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from eval.harness.deps import HARNESS_ROOT, REPO_ROOT

DIGEST_EXTRA_FILES: Final = ("eval/cases/models.py",)  # the case format the scorer depends on


class NotFrozen(Exception):
    """No freeze file exists."""


class TamperDetected(Exception):
    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(f"harness digest mismatch: frozen {expected} computed {actual}")
        self.expected = expected
        self.actual = actual


@dataclass(frozen=True)
class FreezeStamp:
    harness_commit: str
    harness_digest: str


def harness_digest(root: Path = HARNESS_ROOT, *, repo_root: Path = REPO_ROOT) -> str:
    files = sorted(
        (p for p in root.rglob("*.py") if not {"tests", "__pycache__"} & set(p.relative_to(root).parts)),
        key=lambda p: p.relative_to(root).as_posix(),
    )
    digest = hashlib.sha256()
    for path in files:
        label = "harness/" + path.relative_to(root).as_posix()
        digest.update(label.encode() + b"\0" + path.read_bytes() + b"\0")
    for rel in DIGEST_EXTRA_FILES:
        extra = repo_root / rel
        if extra.is_file():
            digest.update(rel.encode() + b"\0" + extra.read_bytes() + b"\0")
    return digest.hexdigest()


def _git(git: str, repo_root: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(  # noqa: S603 (fixed argv, no shell)
            [git, "-C", str(repo_root), *args], capture_output=True, text=True, check=False, timeout=10
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def harness_commit(repo_root: Path = REPO_ROOT) -> str:
    git = shutil.which("git")
    if git is None:
        return "unknown"
    head = _git(git, repo_root, "rev-parse", "HEAD")
    if not head:
        return "unknown"
    dirty = _git(git, repo_root, "status", "--porcelain", "--", "eval/harness", "eval/cases/models.py")
    return f"{head}-dirty" if dirty else head


def write_freeze(freeze_file: Path, *, root: Path = HARNESS_ROOT, repo_root: Path = REPO_ROOT) -> FreezeStamp:
    stamp = FreezeStamp(harness_commit(repo_root), harness_digest(root, repo_root=repo_root))
    payload = {
        "harness_digest": stamp.harness_digest,
        "harness_commit": stamp.harness_commit,
        "frozen_at": datetime.now(UTC).isoformat(),
    }
    freeze_file.parent.mkdir(parents=True, exist_ok=True)
    freeze_file.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return stamp


def check_frozen(freeze_file: Path, *, root: Path = HARNESS_ROOT, repo_root: Path = REPO_ROOT) -> FreezeStamp:
    if not freeze_file.is_file():
        raise NotFrozen("the harness has not been frozen")
    expected = str(json.loads(freeze_file.read_text(encoding="utf-8"))["harness_digest"])
    actual = harness_digest(root, repo_root=repo_root)
    if expected != actual:
        raise TamperDetected(expected, actual)
    return FreezeStamp(harness_commit(repo_root), actual)
