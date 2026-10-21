"""AEA-30 PA-6: the demo and scheduler services import no other adapter (DO-3 section 2.1)."""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_PREFIXES = (
    "meridian.web",
    "meridian.agent",
    "meridian.services.cases",
    "meridian.services.handoff",
    "meridian.adapters.checkpointer",
    "meridian.adapters.models",
)
FORBIDDEN_TOP = {"sqlite3", "anthropic", "httpx", "langgraph", "langfuse", "fastembed"}


def test_demo_and_scheduler_import_direction() -> None:
    root = Path(__file__).resolve().parents[3] / "src/meridian/services"
    for name in ("demo.py", "scheduler.py"):
        tree = ast.parse((root / name).read_text())
        modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.append(node.module)
        for module in modules:
            assert not module.startswith(FORBIDDEN_PREFIXES), (name, module)
            assert module.split(".")[0] not in FORBIDDEN_TOP, (name, module)


def test_view_types_come_from_domain_views() -> None:
    """The four demo views are AEA-02b's classes, re-exported, never redefined (T-1)."""
    from meridian.domain import views
    from meridian.services import demo

    for name in ("ClockView", "ClockAdvanced", "StaffingView", "StaffingChange"):
        assert getattr(demo, name) is getattr(views, name)
