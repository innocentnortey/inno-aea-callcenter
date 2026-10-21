"""AEA-01 AC-5 and AC-7: import direction of limits.py and the composition root."""

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
