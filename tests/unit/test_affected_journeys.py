"""AEA-01 AC-9: the affected-journeys selector."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tests.journeys import affected
from tests.journeys.affected import closure, main, module_index, select_journeys

J1 = "tests/journeys/j1/test_aea_57.py"
J2 = "tests/journeys/j2/test_aea_51.py"

FILES = {
    "src/meridian/__init__.py": "",
    "src/meridian/policy/__init__.py": "",
    "src/meridian/policy/limits.py": "",
    "src/meridian/gates/__init__.py": "",
    "src/meridian/gates/rules.py": "",
    "src/meridian/adapters/__init__.py": "",
    "src/meridian/adapters/sqlite/__init__.py": "",
    "src/meridian/adapters/sqlite/db.py": "",
    "src/meridian/adapters/sqlite/schema/00_core.sql": "-- schema",
    "src/meridian/web/__init__.py": "",
    "src/meridian/web/app.py": (
        "from meridian.policy.limits import Limits\n\ndef create_app():\n    from meridian.adapters.sqlite import db\n"
    ),
    "tests/__init__.py": "",
    "tests/journeys/__init__.py": "",
    "tests/journeys/support/__init__.py": "from .harness import launch\n",
    "tests/journeys/support/harness.py": "from meridian.web.app import create_app\n",
    "tests/journeys/j1/__init__.py": "",
    "tests/journeys/j1/test_aea_57.py": "from tests.journeys.support import launch\n",
    "tests/journeys/j2/__init__.py": "",
    "tests/journeys/j2/test_aea_51.py": "import json\n",
}


def _tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    return _tree(tmp_path, FILES)


def test_no_journey_yet_prints_zero_and_exits_0(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A tree with no journey files: any change selects none, prints 0 and exits 0 (whatever the real repo holds)."""
    no_journeys = {
        rel: text
        for rel, text in FILES.items()
        if not rel.startswith(("tests/journeys/j1/", "tests/journeys/j2/"))
    }
    root = _tree(tmp_path, no_journeys)
    assert affected.journey_files(root) == []
    code = main(
        ["--files", "pyproject.toml", "src/meridian/policy/limits.py", "--list-only", "--root", str(root)]
    )
    assert code == 0
    assert "0 journeys affected" in capsys.readouterr().out.splitlines()


def test_changed_module_on_the_path_selects_the_journey(tree: Path) -> None:
    assert select_journeys(["src/meridian/policy/limits.py"], tree) == [J1]


def test_module_off_every_path_selects_none(tree: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert select_journeys(["src/meridian/gates/rules.py", "docs/x.md"], tree) == []
    main(["--files", "src/meridian/gates/rules.py", "docs/x.md", "--list-only", "--root", str(tree)])
    assert "0 journeys affected" in capsys.readouterr().out


@pytest.mark.parametrize(
    "path",
    [
        "pyproject.toml",
        "uv.lock",
        "tests/conftest.py",
        "apps/web/src/main.tsx",
        "docs/ux/03-structure/ui-contracts.openapi.yaml",
        "docs/data/issued/x.db",
        "tests/journeys/support/harness.py",
    ],
)
def test_always_inputs_select_every_journey(tree: Path, path: str) -> None:
    assert select_journeys([path], tree) == [J1, J2]


def test_non_python_file_maps_to_its_package(tree: Path) -> None:
    assert select_journeys(["src/meridian/adapters/sqlite/schema/00_core.sql"], tree) == [J1]


def test_changed_journey_file_selects_itself(tree: Path) -> None:
    assert select_journeys([J2], tree) == [J2]


def test_relative_import_followed(tree: Path) -> None:
    reached, uncertain = closure("tests.journeys.j1.test_aea_57", module_index(tree))
    assert "tests.journeys.support.harness" in reached
    assert "meridian.adapters.sqlite.db" in reached
    assert not uncertain


def test_syntax_error_on_a_path_selects_conservatively(tmp_path: Path) -> None:
    files = {**FILES, J2: "import meridian.bad\n", "src/meridian/bad.py": "def ("}
    root = _tree(tmp_path, files)
    assert select_journeys(["src/meridian/gates/rules.py"], root) == [J2]


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=aea01-test", "-c", "user.email=aea01@example.invalid", *args],
        cwd=root,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def git_tmp(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-b", "main")
    (tmp_path / "a.txt").write_text("a\n")
    _git(tmp_path, "add", "a.txt")
    _git(tmp_path, "commit", "-m", "a")
    _git(tmp_path, "switch", "-c", "work")
    (tmp_path / "b.txt").write_text("b\n")
    _git(tmp_path, "add", "b.txt")
    _git(tmp_path, "commit", "-m", "b")
    (tmp_path / "a.txt").write_text("a2\n")
    (tmp_path / "c.txt").write_text("c\n")
    return tmp_path


def test_changed_files_reads_commits_edits_and_untracked(git_tmp: Path) -> None:
    assert affected.changed_files("main", git_tmp) == ["a.txt", "b.txt", "c.txt"]


def test_bad_base_returns_2(git_tmp: Path) -> None:
    assert main(["--base", "no-such-ref", "--root", str(git_tmp)]) == 2


def test_run_invokes_pytest_with_journey_marker(tree: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    recorded: list[list[str]] = []

    def fake_call(cmd: list[str], **_: object) -> int:
        recorded.append(cmd)
        return 0

    monkeypatch.setattr("tests.journeys.affected.subprocess.call", fake_call)
    code = main(["--files", "pyproject.toml", "--root", str(tree), "--", "-x"])
    assert code == 0
    assert recorded == [[sys.executable, "-m", "pytest", "-m", "journey", J1, J2, "-x"]]
