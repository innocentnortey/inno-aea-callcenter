"""AEA-24 AC-12: nothing under eval/harness/ imports the app; only eval/run_retrieval.py may (AST scan)."""

from __future__ import annotations

import ast
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
EVAL = HARNESS.parent
APP_ROOTS = {"meridian", "src"}
PRODUCTION_MODULES = {
    "__main__.py",
    "cases.py",
    "cli.py",
    "client.py",
    "dbcheck.py",
    "deps.py",
    "dryrun.py",
    "freeze.py",
    "invariants.py",
    "judge.py",
    "ledger.py",
    "load.py",
    "records.py",
    "report.py",
    "retrieval.py",
    "runlog.py",
    "runner.py",
    "scoring.py",
    "scrub.py",
}


def _imported_modules(path: Path) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.append(node.module)
    return modules


def test_harness_imports_no_app_code() -> None:
    """invariant: the scan is not vacuous (every planned module exists) and finds no app import."""
    present = {p.name for p in HARNESS.glob("*.py")}
    assert PRODUCTION_MODULES <= present, f"missing harness modules: {sorted(PRODUCTION_MODULES - present)}"
    offending = [
        f"{path.relative_to(EVAL.parent)}: {module}"
        for path in sorted(HARNESS.rglob("*.py"))
        for module in _imported_modules(path)
        if module.split(".")[0] in APP_ROOTS
    ]
    assert offending == []


def test_run_retrieval_is_the_only_eval_module_that_imports_the_app() -> None:
    """invariant: eval/run_retrieval.py imports FastembedIndex and the production floor; no other eval file imports app code."""
    entry = EVAL / "run_retrieval.py"
    assert entry.is_file()
    imported = _imported_modules(entry)
    assert "meridian.adapters.retrieval_fastembed" in imported
    assert "meridian.retrieval.settings" in imported
    importers = [
        str(path.relative_to(EVAL))
        for path in sorted(EVAL.rglob("*.py"))
        if any(m.split(".")[0] in APP_ROOTS for m in _imported_modules(path))
    ]
    assert importers == ["run_retrieval.py"]
