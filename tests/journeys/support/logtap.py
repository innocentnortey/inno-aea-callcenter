"""A root-logger handler that keeps every record, so journeys can look up workflow records and scan for secrets."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager

from meridian.web.logging import RECORD_ATTR


class LogTap(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self._records: list[logging.LogRecord] = []
        self._lock = threading.Lock()

    def emit(self, record: logging.LogRecord) -> None:
        with self._lock:
            self._records.append(record)

    def _snapshot(self) -> list[logging.LogRecord]:
        with self._lock:
            return list(self._records)

    def structured(self, kind: str) -> list[dict[str, object]]:
        found: list[dict[str, object]] = []
        for record in self._snapshot():
            payload = record.__dict__.get(RECORD_ATTR)
            if isinstance(payload, Mapping) and payload.get("record") == kind:
                found.append(dict(payload))
        return found

    def wait_for(
        self, kind: str, predicate: Callable[[Mapping[str, object]], bool], *, timeout_s: float = 2.0
    ) -> dict[str, object]:
        deadline = time.monotonic() + timeout_s
        while True:
            for payload in self.structured(kind):
                if predicate(payload):
                    return payload
            if time.monotonic() >= deadline:
                raise AssertionError(f"no {kind} record matched within {timeout_s}s")
            time.sleep(0.01)

    def all_text(self) -> str:
        formatter = logging.Formatter()
        parts = [formatter.format(r) + "\n" + repr(vars(r)) for r in self._snapshot()]
        return "\n".join(parts)


@contextmanager
def tap_logs() -> Iterator[LogTap]:
    tap = LogTap()
    root = logging.getLogger()
    root.addHandler(tap)
    try:
        yield tap
    finally:
        root.removeHandler(tap)
