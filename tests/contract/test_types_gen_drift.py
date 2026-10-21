"""AEA-59 generated-types freshness check (level `mock-tested (static)`).

Runs `apps/web`'s own pinned `openapi-typescript` binary on the OpenAPI into a pytest temp directory and compares the
bytes with the committed `apps/web/src/api/types.gen.ts`. Reads `apps/web`, never writes it, never runs `npm` or `npx`
(their scripts write inside `apps/web`). A backend worktree has no `node_modules`, and none may be installed there, so
the binary is looked up in the primary checkout, read only.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Final

import pytest

from tests.api.openapi_check import load_contract
from tests.contract.openapi_variants import index_mismatches

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
WEB_ROOT: Final = REPO_ROOT / "apps" / "web"
SPEC: Final = REPO_ROOT / "docs" / "ux" / "03-structure" / "ui-contracts.openapi.yaml"
TYPES: Final = WEB_ROOT / "src" / "api" / "types.gen.ts"
BINARY_REL: Final = Path("node_modules/.bin/openapi-typescript")
PACKAGE_REL: Final = Path("node_modules/openapi-typescript/package.json")
GEN_TYPES_SCRIPT: Final = (
    "openapi-typescript ../../docs/ux/03-structure/ui-contracts.openapi.yaml -o src/api/types.gen.ts"
)


def primary_checkout(repo_root: Path) -> Path:
    """`repo_root` itself, or (for a linked worktree, whose `.git` is a file) the checkout that owns it. File reads only."""
    git = repo_root / ".git"
    if not git.is_file():
        return repo_root
    line = next(ln for ln in git.read_text("utf-8").splitlines() if ln.startswith("gitdir:"))
    gitdir = Path(line.split(":", 1)[1].strip())
    if not gitdir.is_absolute():
        gitdir = repo_root / gitdir
    return gitdir.resolve().parents[2]  # <main>/.git/worktrees/<name> -> <main>


def generator_root(repo_root: Path) -> Path:
    local = repo_root / "apps" / "web"
    return local if (local / BINARY_REL).exists() else primary_checkout(repo_root) / "apps" / "web"


def pinned_version(package_json: Path) -> str:
    value = json.loads(package_json.read_text("utf-8")).get("devDependencies", {}).get("openapi-typescript")
    if not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise AssertionError(f"openapi-typescript is not exactly pinned in {package_json}: {value!r}")
    return value


def check_pinned_binary(gen_root: Path, pin: str) -> Path:
    binary, package = gen_root / BINARY_REL, gen_root / PACKAGE_REL
    if not binary.exists() or not package.exists():
        raise AssertionError(
            f"openapi-typescript binary missing at {binary} (apps/web/package.json pins {pin}); "
            "this check never installs: run `npm ci` in apps/web in the UX session"
        )
    version = json.loads(package.read_text("utf-8")).get("version")
    if version != pin:
        raise AssertionError(
            f"openapi-typescript at {binary} is {version}, but apps/web/package.json pins {pin}"
        )
    return binary


def check_gen_types_script(package_json: Path) -> None:
    if json.loads(package_json.read_text("utf-8")).get("scripts", {}).get("gen:types") != GEN_TYPES_SCRIPT:
        raise AssertionError(
            "apps/web gen:types arguments changed; update test_types_gen_drift.py (UX-session deliverable R-W-10)"
        )


def generate_types(binary: Path, spec: Path, out_dir: Path) -> Path:
    out = out_dir / "types.gen.ts"
    done = subprocess.run(
        [str(binary), str(spec), "-o", str(out)],
        cwd=out_dir,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if done.returncode != 0:
        raise AssertionError(f"openapi-typescript exited {done.returncode}")
    return out


def assert_types_current(binary: Path, pin: str, spec: Path, committed: Path, out_dir: Path) -> None:
    fresh = generate_types(binary, spec, out_dir)
    if fresh.read_bytes() != committed.read_bytes():
        raise AssertionError(
            "stale generated file apps/web/src/api/types.gen.ts: it differs from a fresh "
            f"openapi-typescript {pin} run on {spec.name} (OpenAPI {load_contract().version}); "
            "regenerate in the UX session with `npm run gen:types` in apps/web. This check never writes apps/web."
        )


def snapshot(root: Path) -> dict[str, tuple[int, str]]:
    found: dict[str, tuple[int, str]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if "node_modules" in relative.parts or path.is_symlink() or not path.is_file():
            continue
        data = path.read_bytes()
        found[relative.as_posix()] = (len(data), hashlib.sha256(data).hexdigest())
    return found


def _binary_and_pin() -> tuple[Path, str]:
    package = WEB_ROOT / "package.json"
    check_gen_types_script(package)
    pin = pinned_version(package)
    return check_pinned_binary(generator_root(REPO_ROOT), pin), pin


def test_types_gen_is_current(tmp_path: Path) -> None:
    binary, pin = _binary_and_pin()
    assert_types_current(binary, pin, SPEC, TYPES, tmp_path)
    print(f"openapi-typescript {pin} at {binary}: byte-equal")


def test_types_gen_detects_drift(tmp_path: Path) -> None:
    binary, pin = _binary_and_pin()
    text = SPEC.read_text("utf-8")
    assert "max_message_chars" in text
    drifted = tmp_path / "spec.yaml"
    drifted.write_text(text.replace("max_message_chars", "max_message_chars_renamed"), "utf-8")
    out = tmp_path / "out"
    out.mkdir()
    with pytest.raises(AssertionError, match="stale generated file"):
        assert_types_current(binary, pin, drifted, TYPES, out)


def test_refuses_missing_or_unpinned_binary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[Any] = []

    def refuse(argv: Any, *args: Any, **kwargs: Any) -> Any:
        calls.append(argv)
        raise AssertionError("no process may start")

    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", refuse)
    empty = tmp_path / "a"
    empty.mkdir()
    with pytest.raises(AssertionError, match="binary missing at") as missing:
        check_pinned_binary(empty, "7.13.0")
    assert str(empty / BINARY_REL) in str(missing.value) and "7.13.0" in str(missing.value)
    old = tmp_path / "b"
    (old / BINARY_REL).parent.mkdir(parents=True)
    (old / BINARY_REL).write_text("", "utf-8")
    (old / PACKAGE_REL).parent.mkdir(parents=True)
    (old / PACKAGE_REL).write_text(json.dumps({"version": "7.12.0"}), "utf-8")
    with pytest.raises(AssertionError, match=r"is 7\.12\.0, but apps/web/package\.json pins 7\.13\.0"):
        check_pinned_binary(old, "7.13.0")
    loose = tmp_path / "c"
    loose.mkdir()
    (loose / "package.json").write_text(
        json.dumps({"devDependencies": {"openapi-typescript": "^7.13.0"}}), "utf-8"
    )
    with pytest.raises(AssertionError, match="not exactly pinned"):
        pinned_version(loose / "package.json")
    assert calls == []


def test_apps_web_untouched(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    roots = {WEB_ROOT, generator_root(REPO_ROOT)}
    before = {root: snapshot(root) for root in roots}
    tmp_before = (WEB_ROOT / ".tmp").exists()
    calls: list[list[str]] = []
    real_run = subprocess.run

    def recorder(argv: Any, *args: Any, **kwargs: Any) -> Any:
        calls.append([str(a) for a in argv])
        return real_run(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", recorder)
    binary, pin = _binary_and_pin()
    assert_types_current(binary, pin, SPEC, TYPES, tmp_path)
    assert index_mismatches() == []
    for root in roots:
        assert snapshot(root) == before[root], f"{root} changed"
    assert (WEB_ROOT / ".tmp").exists() == tmp_before
    assert calls, "the generator never ran"
    for argv in calls:
        assert argv[0] == str(binary)
        assert all(Path(a).name not in ("npm", "npx") for a in argv)
    print(
        f"apps/web files compared: {sum(len(s) for s in before.values())}; processes: {len(calls)} (openapi-typescript only)"
    )
