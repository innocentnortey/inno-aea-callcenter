"""The affected-journeys command (AEA-01 AC-9; build-loop-test-scope AEA addition).

    uv run python -m tests.journeys.affected [--base REF] [--files PATH ...] [--root DIR] [--list-only] [-- PYTEST_ARGS ...]

Selects the journeys whose path imports a changed module, or that an always-input changed, and runs
``pytest -m journey`` on them. It reads files, never imports ``meridian``, so it works when a change breaks imports.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from collections import deque
from collections.abc import Mapping, Sequence
from pathlib import Path

ALWAYS_EXACT: tuple[str, ...] = (
    "pyproject.toml",
    "uv.lock",
    "tests/conftest.py",
    "docs/ux/03-structure/ui-contracts.openapi.yaml",
)
ALWAYS_PREFIXES: tuple[str, ...] = ("apps/web/", "docs/data/issued/", "data/", "tests/journeys/")

_JOURNEY_DIR = re.compile(r"^j\d+$")


def journey_files(root: Path) -> list[str]:
    """Journey tests: tests/journeys/j<N>/test_*.py and tests/journeys/browser/**/test_*.py, sorted."""
    base = root / "tests" / "journeys"
    found: list[str] = []
    if not base.is_dir():
        return found
    for child in base.iterdir():
        if child.is_dir() and _JOURNEY_DIR.match(child.name):
            found.extend(p.relative_to(root).as_posix() for p in child.glob("test_*.py"))
    browser = base / "browser"
    if browser.is_dir():
        found.extend(p.relative_to(root).as_posix() for p in browser.rglob("test_*.py"))
    return sorted(set(found))


def _git(args: list[str], root: Path) -> list[str]:
    done = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
    return [line for line in done.stdout.splitlines() if line]


def changed_files(base: str, root: Path) -> list[str]:
    """Commits since ``base``, uncommitted edits and untracked files, sorted and de-duplicated."""
    lines: set[str] = set()
    lines.update(_git(["diff", "--name-only", "--no-renames", f"{base}...HEAD"], root))
    lines.update(_git(["diff", "--name-only", "--no-renames", "HEAD"], root))
    lines.update(_git(["ls-files", "--others", "--exclude-standard"], root))
    return sorted(lines)


def module_name_for(rel_path: str) -> str | None:
    if not rel_path.endswith(".py"):
        return None
    parts = rel_path[: -len(".py")].split("/")
    if parts[0] == "src" and len(parts) > 1 and parts[1] == "meridian":
        parts = parts[1:]
    elif parts[0] not in ("tests", "eval"):
        return None
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else None


def module_index(root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for top in ("src/meridian", "tests", "eval"):
        base = root / top
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            name = module_name_for(path.relative_to(root).as_posix())
            if name is not None:
                index[name] = path
    return index


def _longest_prefix(candidate: str, index: Mapping[str, Path]) -> str | None:
    parts = candidate.split(".")
    while parts:
        name = ".".join(parts)
        if name in index:
            return name
        parts.pop()
    return None


def imported_modules(path: Path, module: str, index: Mapping[str, Path]) -> set[str] | None:
    """Modules in ``index`` that the file imports (anywhere in it); None if it does not parse."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return None
    candidates: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            candidates.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level > 0:
                pkg = module.split(".") if path.name == "__init__.py" else module.split(".")[:-1]
                pkg = pkg[: len(pkg) - (node.level - 1)] if node.level > 1 else pkg
                base = ".".join([*pkg, node.module] if node.module else pkg)
            if base:
                candidates.add(base)
            for alias in node.names:
                if alias.name != "*":
                    candidates.add(f"{base}.{alias.name}" if base else alias.name)
    found: set[str] = set()
    for cand in candidates:
        hit = _longest_prefix(cand, index)
        if hit is not None:
            found.add(hit)
    return found


def closure(module: str, index: Mapping[str, Path]) -> tuple[set[str], bool]:
    reached: set[str] = set()
    uncertain = False
    queue: deque[str] = deque([module])
    while queue:
        current = queue.popleft()
        if current in reached:
            continue
        reached.add(current)
        parts = current.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[:i])
            if parent in index:
                queue.append(parent)
        path = index.get(current)
        if path is None:
            continue
        imports = imported_modules(path, current, index)
        if imports is None:
            uncertain = True
            continue
        queue.extend(imports - reached)
    return reached, uncertain


def select_journeys(changed: Sequence[str], root: Path) -> list[str]:
    journeys = journey_files(root)
    if not journeys:
        return []
    selected: set[str] = set()
    touched: set[str] = set()
    everything = False
    for p in changed:
        if p in journeys:
            selected.add(p)
        elif p in ALWAYS_EXACT or p.startswith(ALWAYS_PREFIXES):
            everything = True
        elif p.endswith(".py") and module_name_for(p) is not None:
            name = module_name_for(p)
            assert name is not None
            touched.add(name)
            if not (root / p).exists():
                touched.add(name.rpartition(".")[0])
        elif p.startswith("src/meridian/") and not p.endswith(".py"):
            directory = (root / p).parent
            while directory != root and not (directory / "__init__.py").exists():
                directory = directory.parent
            name = (
                module_name_for((directory / "__init__.py").relative_to(root).as_posix())
                if directory != root
                else None
            )
            if name:
                touched.add(name)
    if everything:
        return journeys
    touched.discard("")
    if touched:
        index = module_index(root)
        for j in journeys:
            jmod = module_name_for(j)
            if jmod is None:
                continue
            reached, uncertain = closure(jmod, index)
            if uncertain or reached & touched:
                selected.add(j)
    return sorted(selected)


def main(argv: Sequence[str] | None = None) -> int:
    args_in = list(sys.argv[1:] if argv is None else argv)
    pytest_args: list[str] = []
    if "--" in args_in:
        cut = args_in.index("--")
        pytest_args = args_in[cut + 1 :]
        args_in = args_in[:cut]
    parser = argparse.ArgumentParser(prog="python -m tests.journeys.affected")
    parser.add_argument("--base", default="main")
    parser.add_argument("--files", nargs="*", default=None)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--list-only", action="store_true")
    ns = parser.parse_args(args_in)
    root = Path(ns.root)

    if ns.files is not None:
        changed = sorted(ns.files)
        label = "given"
    else:
        try:
            changed = changed_files(ns.base, root)
        except subprocess.CalledProcessError as exc:
            first = (exc.stderr or "").strip().splitlines()[:1]
            print(f"affected: git failed: {first[0] if first else exc}", file=sys.stderr)
            return 2
        label = f"base {ns.base}"
    selected = select_journeys(changed, root)
    print(f"changed files: {len(changed)} ({label})")
    print(f"{len(selected)} {'journey' if len(selected) == 1 else 'journeys'} affected")
    for s in selected:
        print(f"  {s}")
    if not selected or ns.list_only:
        return 0
    cmd = [sys.executable, "-m", "pytest", "-m", "journey", *selected, *pytest_args]
    print("running: " + " ".join(cmd))
    return subprocess.call(cmd, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
