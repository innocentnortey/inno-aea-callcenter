"""AEA-40 test support, hooks: count, guard and break the unit of work (frozen with the AEA-40 tests).

Split out of `chat_storage.py` to keep every test-support file under 500 lines; no helper changed.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any


# -- hooks: count, guard and break the unit of work -------------------------------------------------------------
class _RepoProxy:
    def __init__(self, repo: Any, name: str, hooks: dict[str, Callable[..., Any]]) -> None:
        self._repo = repo
        self._name = name
        self._hooks = hooks

    def __getattr__(self, attr: str) -> Any:
        target = getattr(self._repo, attr)
        hook = self._hooks.get(f"{self._name}.{attr}")
        if hook is None or not callable(target):
            return target

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            return hook(target, *args, **kwargs)

        return wrapped


class _CoreProxy:
    def __init__(self, core: Any, hooks: dict[str, Callable[..., Any]]) -> None:
        self._core = core
        self._hooks = hooks

    def __getattr__(self, name: str) -> Any:
        target = getattr(self._core, name)
        if any(key.startswith(name + ".") for key in self._hooks):
            return _RepoProxy(target, name, self._hooks)
        hook = self._hooks.get(name)
        if hook is not None and callable(target):

            def wrapped(*args: Any, **kwargs: Any) -> Any:
                return hook(target, *args, **kwargs)

            return wrapped
        return target


class _TxProxy:
    def __init__(self, tx: Any, hooks: dict[str, Callable[..., Any]]) -> None:
        self._tx = tx
        self.core = _CoreProxy(tx.core, hooks) if hooks else tx.core

    def __getattr__(self, name: str) -> Any:
        return getattr(self._tx, name)

    def commit(self) -> None:
        self._tx.commit()


class HookedUow:
    """A `UnitOfWorkFactory` wrapper: counts entries and the open depth, and wraps named repository methods.

    `hooks` maps `"repo.method"` (or `"settled_for"`) to `hook(real_method, *args, **kwargs)`.
    `forbidden_while` is an optional callable; when it returns True at entry the entry is recorded in
    `entered_while_forbidden` and an AssertionError is raised (a unit of work opened while it must not be).
    """

    def __init__(self, real: Any, hooks: dict[str, Callable[..., Any]] | None = None) -> None:
        self._real = real
        self._hooks = hooks or {}
        self.depth = 0
        self.entries = 0
        self.forbidden_while: Callable[[], bool] | None = None
        self.entered_while_forbidden = 0
        self._lock = threading.Lock()

    @contextmanager
    def __call__(self, *, write: bool = False, exclusive: bool = False) -> Iterator[Any]:
        if self.forbidden_while is not None and self.forbidden_while():
            self.entered_while_forbidden += 1
            raise AssertionError("a unit of work was entered while it must not be open")
        with self._lock:
            self.entries += 1
            self.depth += 1
        try:
            with self._real(write=write, exclusive=exclusive) as tx:
                yield _TxProxy(tx, self._hooks)
        finally:
            with self._lock:
                self.depth -= 1


def fail_after(message: str = "injected fault") -> Callable[..., Any]:
    """A hook that runs the real method and then raises, so only a rollback can undo what it wrote."""

    def hook(real: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        real(*args, **kwargs)
        raise RuntimeError(message)

    return hook


def fail_first_call(message: str = "injected fault") -> Callable[..., Any]:
    """A hook that raises on its first call (without running the real method) and passes later calls through."""
    state = {"calls": 0}

    def hook(real: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        state["calls"] += 1
        if state["calls"] == 1:
            raise RuntimeError(message)
        return real(*args, **kwargs)

    return hook
