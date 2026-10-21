"""Static import-direction checks (one function per owning ticket; AEA-01, 02, 03, 04, 05)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def _aea03_imported_modules(path: Path) -> list[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text("utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add("." * node.level + (node.module or ""))
    return sorted(found)


def test_texts_imports_stdlib_only() -> None:
    path = Path(__file__).resolve().parents[2] / "src/meridian/policy/texts.py"
    seen = _aea03_imported_modules(path)
    print("policy/texts.py imports:", seen)
    relative = [name for name in seen if name.startswith(".")]
    outside = [n for n in seen if n.split(".")[0] not in sys.stdlib_module_names]
    assert not relative, f"relative imports: {relative}"
    assert not outside, f"non-stdlib imports: {outside}"
