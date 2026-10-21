"""AEA-50 AC-7: `compute_agent_version` is stable and sensitive (DAT-22). Pure functions, no docker, no model."""

from __future__ import annotations

import copy
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.deploy.support import ROOT

VERSION = re.compile(r"^[0-9a-f]{12}\+[0-9a-f]{8}$")
SHA_A = "a" * 40
SHA_B = "b" * 40


def _files(tmp_path: Path) -> tuple[Path, Path]:
    one, two = tmp_path / "one.py", tmp_path / "two.py"
    one.write_text('PROMPT = "alpha"\n', encoding="utf-8")
    two.write_text('PROMPT = "beta"\n', encoding="utf-8")
    return one, two


def _model_map() -> dict[str, Any]:
    from scripts.agent_version import model_config

    return copy.deepcopy(dict(model_config()))


def test_same_inputs_same_value(tmp_path: Path) -> None:
    """invariant: identical sha, model map and prompt files give one value of the form <12 hex>+<8 hex>."""
    from scripts.agent_version import compute_agent_version

    files = _files(tmp_path)
    first = compute_agent_version(SHA_A, _model_map(), files)
    second = compute_agent_version(SHA_A, _model_map(), files)
    assert first == second
    assert VERSION.match(first)
    assert first.startswith(SHA_A[:12] + "+")


def test_prompt_byte_changes_suffix_only(tmp_path: Path) -> None:
    """invariant: one changed byte in a prompt file changes the 8-hex suffix and nothing else."""
    from scripts.agent_version import compute_agent_version

    one, two = _files(tmp_path)
    before = compute_agent_version(SHA_A, _model_map(), (one, two))
    one.write_text('PROMPT = "alphb"\n', encoding="utf-8")
    after = compute_agent_version(SHA_A, _model_map(), (one, two))
    assert before.split("+")[0] == after.split("+")[0]
    assert before.split("+")[1] != after.split("+")[1]


def _bump_first_max_tokens(node: Any) -> bool:
    if isinstance(node, dict):
        if isinstance(node.get("max_tokens"), int):
            node["max_tokens"] += 1
            return True
        return any(_bump_first_max_tokens(v) for v in node.values())
    return False


def test_model_map_change_changes_suffix_only(tmp_path: Path) -> None:
    """invariant: one changed value in the role to model map changes the suffix only."""
    from scripts.agent_version import compute_agent_version

    files = _files(tmp_path)
    original = _model_map()
    changed = copy.deepcopy(original)
    assert _bump_first_max_tokens(changed), "the role map must hold at least one max_tokens"
    before = compute_agent_version(SHA_A, original, files)
    after = compute_agent_version(SHA_A, changed, files)
    assert before.split("+")[0] == after.split("+")[0]
    assert before.split("+")[1] != after.split("+")[1]


def test_git_sha_changes_prefix_only(tmp_path: Path) -> None:
    """invariant: a different commit changes the 12-char prefix and leaves the config hash alone."""
    from scripts.agent_version import compute_agent_version

    files = _files(tmp_path)
    a = compute_agent_version(SHA_A, _model_map(), files)
    b = compute_agent_version(SHA_B, _model_map(), files)
    assert a.split("+")[0] != b.split("+")[0]
    assert a.split("+")[1] == b.split("+")[1]


def test_sha_precedence(tmp_path: Path) -> None:
    """invariant: RAILWAY_GIT_COMMIT_SHA beats the BUILD_SHA file, which beats 'unknown'; blanks do not count."""
    from scripts.agent_version import resolve_git_sha

    present = tmp_path / "BUILD_SHA"
    present.write_text(SHA_B + "\n", encoding="utf-8")
    missing = tmp_path / "absent"
    assert resolve_git_sha({"RAILWAY_GIT_COMMIT_SHA": SHA_A}, present) == SHA_A
    assert resolve_git_sha({}, present) == SHA_B
    assert resolve_git_sha({}, missing) == "unknown"
    assert resolve_git_sha({"RAILWAY_GIT_COMMIT_SHA": "  "}, present) == SHA_B


def test_empty_build_sha_file_is_unknown(tmp_path: Path) -> None:
    """boundary: an empty BUILD_SHA file is treated as absent, never as an empty commit."""
    from scripts.agent_version import resolve_git_sha

    empty = tmp_path / "BUILD_SHA"
    empty.write_text("\n", encoding="utf-8")
    assert resolve_git_sha({}, empty) == "unknown"


def test_dirty_sha_kept(tmp_path: Path) -> None:
    """invariant: a '-dirty' marker survives resolution and the version prefix is the first 12 characters."""
    from scripts.agent_version import compute_agent_version, resolve_git_sha

    marker = tmp_path / "BUILD_SHA"
    marker.write_text(SHA_A + "-dirty\n", encoding="utf-8")
    resolved = resolve_git_sha({}, marker)
    assert resolved == SHA_A + "-dirty"
    version = compute_agent_version(resolved, _model_map(), _files(tmp_path))
    assert version.split("+")[0] == resolved[:12]


def test_cli_prints_one_line(capsys: pytest.CaptureFixture[str]) -> None:
    """invariant: the CLI prints exactly one version line and returns 0."""
    from scripts.agent_version import main

    assert main([]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert VERSION.match(lines[0]) or re.match(r"^unknown\+[0-9a-f]{8}$", lines[0])


def test_prompt_files_cover_both_globs() -> None:
    """invariant: the stamp covers every agent prompt module and the policy texts."""
    from scripts.agent_version import prompt_files

    found = {p.resolve().relative_to(ROOT).as_posix() for p in prompt_files()}
    assert "src/meridian/policy/texts.py" in found
    expected = {p.relative_to(ROOT).as_posix() for p in (ROOT / "src/meridian/agent/prompts").glob("*.py")}
    assert expected <= found


def test_failure_prints_class_name_only(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """negative: a failing stamp prints nothing on stdout, a class name on stderr, and exits 1 (no silent 'dev')."""
    import scripts.agent_version as module

    def boom(*_args: object, **_kwargs: object) -> str:
        raise RuntimeError("secret-looking detail must not be printed")

    monkeypatch.setattr(module, "compute_agent_version", boom)
    assert module.main([]) == 1
    out = capsys.readouterr()
    assert out.out == ""
    assert out.err.strip() == "agent_version_error=RuntimeError"


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_build_sha_from_git(tmp_path: Path) -> None:
    """invariant: HEAD is read; a tracked change adds '-dirty'; an untracked file alone does not."""
    from scripts.agent_version import build_sha_from_git

    git = shutil.which("git")
    assert git is not None

    def run(*args: str) -> str:
        return subprocess.run(
            [git, "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    run("init", "-q")
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("one\n", encoding="utf-8")
    run("add", "tracked.txt")
    run("commit", "-q", "-m", "first")
    head = run("rev-parse", "HEAD")
    assert build_sha_from_git(tmp_path) == head
    (tmp_path / "BUILD_SHA").write_text(head, encoding="utf-8")
    assert build_sha_from_git(tmp_path) == head
    tracked.write_text("two\n", encoding="utf-8")
    assert build_sha_from_git(tmp_path) == head + "-dirty"
