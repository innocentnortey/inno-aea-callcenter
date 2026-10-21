"""Network block for the harness tests: any AF_INET / AF_INET6 connect raises and is recorded.

This ticket binds no port and makes no real call, so loopback is blocked too. The attempts list is what a test reads
to prove "no network" (AC-5, AC-14, AC-15, AC-17, AC-22, AC-24).
"""

from __future__ import annotations

import socket
from typing import Any

import pytest


def install_network_block(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    attempts: list[object] = []
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex

    def _is_inet(sock: socket.socket) -> bool:
        return sock.family in (socket.AF_INET, socket.AF_INET6)

    def connect(self: socket.socket, address: Any) -> None:
        if _is_inet(self):
            attempts.append(address)
            raise AssertionError("network connect blocked in harness tests")
        real_connect(self, address)

    def connect_ex(self: socket.socket, address: Any) -> int:
        if _is_inet(self):
            attempts.append(address)
            raise AssertionError("network connect blocked in harness tests")
        return real_connect_ex(self, address)

    def create_connection(address: Any, *args: Any, **kwargs: Any) -> socket.socket:
        attempts.append(address)
        raise AssertionError("network connect blocked in harness tests")

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "create_connection", create_connection)
    return attempts


@pytest.fixture
def block_network(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    """The recorded connection attempts (always empty in a passing test)."""
    return install_network_block(monkeypatch)
