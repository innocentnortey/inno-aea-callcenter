"""Render move (2026-10-21): `resolve_git_sha` reads Render's RENDER_GIT_COMMIT.

Not part of AEA-50's frozen set (tests/deploy/test_agent_version.py stays unchanged and keeps passing): Railway's
RAILWAY_GIT_COMMIT_SHA still wins, then Render's commit, then the BUILD_SHA file, then "unknown".
"""

from __future__ import annotations

from pathlib import Path

SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40


def test_render_commit_beats_the_build_sha_file(tmp_path: Path) -> None:
    """invariant: on Render the deployed commit is RENDER_GIT_COMMIT, never a stale BUILD_SHA or 'unknown'."""
    from scripts.agent_version import resolve_git_sha

    present = tmp_path / "BUILD_SHA"
    present.write_text(SHA_B + "\n", encoding="utf-8")
    assert resolve_git_sha({"RENDER_GIT_COMMIT": SHA_C}, present) == SHA_C
    assert resolve_git_sha({"RENDER_GIT_COMMIT": SHA_C}, tmp_path / "absent") == SHA_C


def test_railway_commit_still_comes_first(tmp_path: Path) -> None:
    """invariant: the frozen AEA-50 precedence holds; Railway's SHA wins when both are set."""
    from scripts.agent_version import resolve_git_sha

    env = {"RAILWAY_GIT_COMMIT_SHA": SHA_A, "RENDER_GIT_COMMIT": SHA_C}
    assert resolve_git_sha(env, tmp_path / "absent") == SHA_A


def test_blank_render_commit_does_not_count(tmp_path: Path) -> None:
    """boundary: a blank RENDER_GIT_COMMIT falls through to BUILD_SHA, then to 'unknown'."""
    from scripts.agent_version import resolve_git_sha

    present = tmp_path / "BUILD_SHA"
    present.write_text(SHA_B + "\n", encoding="utf-8")
    assert resolve_git_sha({"RENDER_GIT_COMMIT": "  "}, present) == SHA_B
    assert resolve_git_sha({"RENDER_GIT_COMMIT": ""}, tmp_path / "absent") == "unknown"


def test_the_version_prefix_is_the_render_commit(tmp_path: Path) -> None:
    """invariant: the agent version starts with the first 12 characters of the deployed Render commit."""
    from scripts.agent_version import compute_agent_version, resolve_git_sha

    prompt = tmp_path / "p.py"
    prompt.write_text("PROMPT = 1\n", encoding="utf-8")
    sha = resolve_git_sha({"RENDER_GIT_COMMIT": SHA_C}, tmp_path / "absent")
    version = compute_agent_version(sha, {"agent": "m"}, [prompt])
    assert version.startswith(SHA_C[:12] + "+")
