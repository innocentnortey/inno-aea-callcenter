"""The one reset gate per process (web.md section 7, WEB-13, MC-27).

``hold()`` is taken by the reset service for the length of a reset; the web middleware asks ``held()`` on the event
loop (never blocks) and ``wait_clear`` waits for a release without using a worker thread. Imports only the standard
library and anyio, never ``web/``.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager

import anyio

WAIT_POLL_S = 0.1  # [A] web section 7: an anyio.sleep(0.1) loop


class ResetAlreadyRunning(Exception):
    """A second reset tried to start while one holds the gate."""


class ResetGate:
    def __init__(self) -> None:
        self._lock = threading.Lock()

    def held(self) -> bool:
        return self._lock.locked()

    @contextmanager
    def hold(self) -> Iterator[None]:
        if not self._lock.acquire(blocking=False):
            raise ResetAlreadyRunning("a reset is already running")
        try:
            yield
        finally:
            self._lock.release()

    async def wait_clear(self, timeout_s: float) -> bool:
        deadline = time.monotonic() + timeout_s
        while self.held():
            if time.monotonic() >= deadline:
                return False
            await anyio.sleep(WAIT_POLL_S)
        return True
