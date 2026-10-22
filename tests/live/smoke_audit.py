"""A process-wide `sys.addaudithook` recorder of the paths the run opens (AEA-61 AC-13).

A hook cannot be removed, so one hook is installed per process. It is inactive outside `audit_opened()`, returns at once
when inactive, and never raises.
"""

from __future__ import annotations

import os
import sys
import threading
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Final

_EVENTS: Final = frozenset({"open", "os.listdir", "os.scandir", "sqlite3.connect"})


class _State:
    def __init__(self) -> None:
        self.installed = False
        self.active = False
        self.opened: list[str] = []
        self.lock = threading.Lock()


_STATE = _State()


def _hook(event: str, args: tuple[Any, ...]) -> None:
    if not _STATE.active or event not in _EVENTS:
        return
    try:
        path = args[0]
        if isinstance(path, int):
            return
        if isinstance(path, bytes):
            path = os.fsdecode(path)
        elif not isinstance(path, str):
            path = os.fspath(path)
        with _STATE.lock:
            _STATE.opened.append(os.path.abspath(path))
    except Exception:  # noqa: S110  # a hook must never raise
        pass


@contextmanager
def audit_opened() -> Iterator[list[str]]:
    if _STATE.active:
        raise RuntimeError("audit_opened is already active")
    if not _STATE.installed:
        sys.addaudithook(_hook)
        _STATE.installed = True
    _STATE.opened = []
    opened = _STATE.opened
    _STATE.active = True
    try:
        yield opened
    finally:
        _STATE.active = False


def offending_paths(
    opened: Iterable[str], *, dev_dir: Path, schema_path: Path, cases_dir: Path, heldout_key_root: Path
) -> tuple[str, ...]:
    bad: list[str] = []
    for p in opened:
        path = Path(p)
        in_cases = (
            path.is_relative_to(cases_dir) and not path.is_relative_to(dev_dir) and p != str(schema_path)
        )
        if in_cases or path.is_relative_to(heldout_key_root):
            bad.append(p)
    return tuple(bad)


def opened_counts(opened: Iterable[str], *, root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for p in opened:
        path = Path(p)
        if path.is_relative_to(root):
            key = "/".join(path.relative_to(root).parts[:3])
        else:
            key = "<outside repo>"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))
