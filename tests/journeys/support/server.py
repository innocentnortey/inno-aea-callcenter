"""The journey wall clock, the uvicorn launcher and the loopback-only socket guard (AEA-57; web.md section 15)."""

from __future__ import annotations

import errno
import ipaddress
import socket
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import uvicorn

if TYPE_CHECKING:
    from fastapi import FastAPI

    from meridian.config import Settings
    from meridian.web.app import ContainerOverrides
    from meridian.web.container import Container

FORBIDDEN_PORTS: frozenset[int] = frozenset({4019, 5184})  # the UX track's Prism and Vite ports


class StepClock:
    """The journey wall clock (D-13; web.md section 15): real UTC time plus an offset the test moves forward."""

    def __init__(self) -> None:
        self._offset_s = 0.0
        self._lock = threading.Lock()

    def __call__(self) -> datetime:
        with self._lock:
            offset = self._offset_s
        return datetime.now(UTC) + timedelta(seconds=offset)

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("the journey clock only moves forward")
        with self._lock:
            self._offset_s += seconds

    @property
    def offset_s(self) -> float:
        with self._lock:
            return self._offset_s


@dataclass
class RunningServer:
    app: FastAPI
    container: Container
    host: str
    port: int
    thread: threading.Thread
    close_count: int = 0

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def note_closed(self) -> None:
        self.close_count += 1


@contextmanager
def launch_server(
    settings: Settings, *, overrides: ContainerOverrides | None, startup_timeout_s: float = 30.0
) -> Iterator[RunningServer]:
    from meridian.web.app import create_app

    app = create_app(settings, overrides=overrides)
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=0,
        lifespan="on",
        log_config=None,
        access_log=False,
        http="h11",
        loop="asyncio",
        ws="none",
        timeout_graceful_shutdown=5,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="journey-uvicorn", daemon=True)
    thread.start()

    def stop() -> None:
        server.should_exit = True
        thread.join(timeout=15)
        if thread.is_alive():
            server.force_exit = True
            thread.join(timeout=5)

    deadline = time.monotonic() + startup_timeout_s
    while not server.started:
        if not thread.is_alive():
            raise RuntimeError(
                "journey server stopped during start-up (the app lifespan failed; see the captured log)"
            )
        if time.monotonic() > deadline:
            stop()
            raise RuntimeError(f"journey server did not start within {startup_timeout_s}s")
        time.sleep(0.02)
    container = getattr(app.state, "container", None)
    if container is None:
        stop()
        raise RuntimeError("journey server started without a container")
    port = int(server.servers[0].sockets[0].getsockname()[1])
    if port in FORBIDDEN_PORTS or port <= 0:
        stop()
        raise RuntimeError(f"journey server bound a forbidden port: {port}")
    running = RunningServer(app, container, "127.0.0.1", port, thread)
    container.on_close(running.note_closed)
    try:
        yield running
    finally:
        stop()


class SocketGuard:
    def __init__(self) -> None:
        self.blocked: list[tuple[str, int]] = []
        self._lock = threading.Lock()

    def check(self, address: object) -> None:
        if not isinstance(address, tuple) or not address:
            return  # AF_UNIX path
        host = str(address[0])
        if host == "localhost":
            return
        try:
            if ipaddress.ip_address(host.split("%")[0]).is_loopback:
                return
        except ValueError:
            pass  # a hostname counts as non-loopback
        with self._lock:
            self.blocked.append((host, int(address[1]) if len(address) > 1 else 0))
        raise OSError(errno.EACCES, "journey socket guard: non-loopback connection refused")


@contextmanager
def socket_guard() -> Iterator[SocketGuard]:
    guard = SocketGuard()
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def guarded_connect(self: socket.socket, address: Any) -> None:
        guard.check(address)
        original_connect(self, address)

    def guarded_connect_ex(self: socket.socket, address: Any) -> int:
        guard.check(address)
        return original_connect_ex(self, address)

    socket.socket.connect = guarded_connect  # type: ignore[method-assign, assignment]
    socket.socket.connect_ex = guarded_connect_ex  # type: ignore[method-assign, assignment]
    try:
        yield guard
    finally:
        socket.socket.connect = original_connect  # type: ignore[method-assign]
        socket.socket.connect_ex = original_connect_ex  # type: ignore[method-assign]
