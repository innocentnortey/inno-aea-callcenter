"""Demo-fix item 1: the retrieval warm thread starts after build, repeats, and stops when the container closes."""

from __future__ import annotations

import threading
import time
from typing import Any, cast

from meridian.adapters.retrieval_fastembed import FastembedIndex
from meridian.policy.limits import Limits
from meridian.web.container import Container, _start_retrieval_warmer


class _Ready:
    ok = True


class _Index:
    def __init__(self, ok: bool = True) -> None:
        self.ok = ok
        self.calls = 0

    def readiness(self) -> Any:
        r = _Ready()
        r.ok = self.ok
        return r

    def warm(self) -> bool:
        self.calls += 1
        return True


def _container() -> Container:
    return Container(settings=object(), limits=Limits())


def _wait(predicate: Any) -> None:
    deadline = time.monotonic() + 3.0
    while not predicate() and time.monotonic() < deadline:
        time.sleep(0.01)


def test_warmer_warms_repeatedly_and_stops_on_close() -> None:
    c, index = _container(), _Index()
    _start_retrieval_warmer(c, cast(FastembedIndex, index), interval_s=0.01)
    _wait(lambda: index.calls >= 2)
    assert index.calls >= 2
    c.close()
    assert not any(t.name == "retrieval-warmer" and t.is_alive() for t in threading.enumerate())


def test_warmer_skipped_when_index_not_ready() -> None:
    c, index = _container(), _Index(ok=False)
    _start_retrieval_warmer(c, cast(FastembedIndex, index))
    time.sleep(0.05)
    assert index.calls == 0
    c.close()
