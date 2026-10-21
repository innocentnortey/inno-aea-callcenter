"""Static import-direction checks (one function per owning ticket; AEA-01, 02, 03, 04, 05)."""

from __future__ import annotations

import ast
import dataclasses
import sys
from pathlib import Path

import meridian.policy.limits as limits_mod

SRC = Path(__file__).resolve().parents[2] / "src" / "meridian"


def _imports(nodes: list[ast.stmt] | ast.AST) -> list[str]:
    found: list[str] = []
    walker = ast.walk(nodes) if isinstance(nodes, ast.AST) else (n for s in nodes for n in ast.walk(s))
    for node in walker:
        if isinstance(node, ast.Import):
            found.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return found


def test_limits_imports_stdlib_only() -> None:
    tree = ast.parse((SRC / "policy" / "limits.py").read_text(encoding="utf-8"))
    seen = _imports(tree)
    print("limits.py imports:", seen)
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    assert seen
    assert all(name.split(".")[0] in stdlib for name in seen), seen

    limits = limits_mod.Limits()
    for part in dataclasses.fields(limits):
        assert "role" not in part.name.lower()
        for f in dataclasses.fields(getattr(limits, part.name)):
            assert f.name != "cap_s"
            assert not f.name.endswith("_cap_s")
            assert "role" not in f.name.lower()
    for name in dir(limits_mod):
        assert "role" not in name.lower()


def test_container_imports_only_policy_limits() -> None:
    tree = ast.parse((SRC / "web" / "container.py").read_text(encoding="utf-8"))
    module_level: list[str] = []
    type_checking: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.If) and ast.unparse(node.test) == "TYPE_CHECKING":
            type_checking.extend(_imports(node.body))
        elif isinstance(node, ast.Import | ast.ImportFrom):
            module_level.extend(_imports([node]))
    print("module level:", module_level, "TYPE_CHECKING:", type_checking)
    assert {m for m in module_level if m.split(".")[0] == "meridian"} == {"meridian.policy.limits"}
    assert set(type_checking) == {"fastapi"}


def test_redact_imports_stdlib_only() -> None:
    """AEA-04 AC-10: privacy/redact.py imports only these stdlib modules and calls no I/O builtin."""
    path = Path(__file__).resolve().parents[2] / "src" / "meridian" / "privacy" / "redact.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative import in privacy/redact.py"
            found.add(node.module or "")
    print("privacy/redact.py imports:", sorted(found))
    allowed = {"__future__", "collections.abc", "dataclasses", "enum", "re", "types", "typing"}
    assert found <= allowed, sorted(found - allowed)
    assert all(name.split(".")[0] in sys.stdlib_module_names for name in found)
    io_builtins = {"open", "print", "input", "exec", "eval", "compile", "__import__", "breakpoint"}
    called = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert not called & io_builtins, sorted(called & io_builtins)


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
