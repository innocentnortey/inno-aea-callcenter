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


def _aea02_scan(path: Path) -> list[tuple[str, bool, int]]:
    """Every import in a file as (module, inside TYPE_CHECKING, relative level)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    guarded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and ast.unparse(node.test) == "TYPE_CHECKING":
            guarded.update(id(inner) for stmt in node.body for inner in ast.walk(stmt))
    found: list[tuple[str, bool, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((alias.name, id(node) in guarded, 0) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.append((node.module or "", id(node) in guarded, node.level))
    return found


def test_domain_ports_config_imports() -> None:
    """AEA-02 AC-18: dependency direction for domain/*, ports/* and config.py (static scan)."""
    forbidden = {"anthropic", "httpx", "fastembed", "langfuse", "langgraph", "sqlite3"}
    third_party = {"pydantic", "pydantic_core"}
    stdlib = set(sys.stdlib_module_names) | {"__future__"}
    areas: list[tuple[str, list[Path]]] = [
        ("domain", sorted(p for p in (SRC / "domain").glob("*.py") if p.name != "__init__.py")),
        ("ports", sorted(p for p in (SRC / "ports").glob("*.py") if p.name != "__init__.py")),
        ("config", [SRC / "config.py"]),
    ]
    assert [len(files) for _, files in areas] == [12, 2, 1]
    for area, files in areas:
        for path in files:
            for module, type_checking, level in _aea02_scan(path):
                print(f"{area}/{path.name}: {'TYPE_CHECKING ' if type_checking else ''}{module}")
                assert level == 0, f"relative import in {path.name}"
                top = module.split(".")[0]
                assert top not in forbidden, f"{path.name} imports {module}"
                if top != "meridian":
                    assert top in stdlib or top in third_party, f"{path.name} imports {module}"
                    continue
                if module.startswith("meridian.domain"):
                    continue
                if area == "ports" and type_checking and module.startswith("meridian.adapters.sqlite.repos_"):
                    continue
                if area == "config" and (
                    module.startswith("meridian.ports") or module == "meridian.privacy.redact"
                ):
                    continue
                raise AssertionError(f"{path.name} ({area}) must not import {module}")


# --- AEA-05: gates/rules.py ---


def _aea05_imported_modules(tree: ast.Module) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative import in gates/rules.py"
            names.append(node.module or "")
    return sorted(names)


def test_rules_imports() -> None:
    """AEA-05 AC-11: gates/rules.py imports only the standard library and meridian.domain; no own types; no I/O."""
    tree = ast.parse((SRC / "gates" / "rules.py").read_text(encoding="utf-8"))
    seen = _aea05_imported_modules(tree)
    print("gates/rules.py imports:", seen)
    outside = [
        name
        for name in seen
        if not (
            name.split(".")[0] in sys.stdlib_module_names
            or name == "__future__"
            or name == "meridian.domain"
            or name.startswith("meridian.domain.")
        )
    ]
    assert not outside, outside
    defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    assert not defined & {"RuleMatches", "SafetyKind", "HandoffReason"}
    io_builtins = {"open", "print", "input", "exec", "eval", "compile", "__import__", "breakpoint"}
    called = {n.func.id for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert not called & io_builtins, called & io_builtins

    import meridian.gates.rules as rules_mod
    from meridian.domain.turn import RuleMatches, SafetyKind

    assert vars(rules_mod)["RuleMatches"] is RuleMatches
    assert vars(rules_mod)["SafetyKind"] is SafetyKind
