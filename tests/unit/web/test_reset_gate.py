"""AEA-23 AC-21: the reset gate and what the middleware does while it is held (web section 7).

Failure modes guarded: invariant (eight operations answer 503 at once; the others wait and then see the post-reset
state; /healthz, login and the reset route never wait), boundary (a second reset while one runs).
"""

from __future__ import annotations

import ast
import threading
import time
from pathlib import Path

import anyio
import pytest

from meridian.services.reset_gate import ResetAlreadyRunning, ResetGate
from meridian.web.middleware import RESET_503_OPERATIONS
from tests.api.openapi_check import load_contract
from tests.api.web_shell_support import (
    FakeSessionStore,
    add_probe_route,
    assert_matches,
    cookie_header,
    error_body,
    login,
    make_client,
    make_settings,
    new_thread_id,
    reset_gate_of,
    web_app,
)

REPO = Path(__file__).resolve().parents[3]


def test_reset_gate_hold_and_wait_clear() -> None:
    """invariant (AC-21): held() reflects hold(); a second hold raises; wait_clear returns when the hold ends."""
    gate = ResetGate()
    assert gate.held() is False
    with gate.hold():
        assert gate.held() is True
        with pytest.raises(ResetAlreadyRunning), gate.hold():
            pass
        assert gate.held() is True, "a refused second hold must not release the first"
    assert gate.held() is False
    with pytest.raises(RuntimeError, match="boom"), gate.hold():
        raise RuntimeError("boom")
    assert gate.held() is False, "the gate is released when the reset fails"

    assert anyio.run(gate.wait_clear, 0.5) is True  # free: no wait

    with gate.hold():
        began = time.monotonic()
        assert anyio.run(gate.wait_clear, 0.3) is False
        assert time.monotonic() - began >= 0.25

    holder_started = threading.Event()

    def hold_briefly() -> None:
        with gate.hold():
            holder_started.set()
            time.sleep(0.3)

    thread = threading.Thread(target=hold_briefly)
    thread.start()
    assert holder_started.wait(2)
    assert anyio.run(gate.wait_clear, 3.0) is True
    thread.join()


def test_reset_gate_service_imports_no_web() -> None:
    """invariant (web section 7): services/reset_gate.py can be taken by ResetService without importing web/."""
    tree = ast.parse((REPO / "src" / "meridian" / "services" / "reset_gate.py").read_text("utf-8"))
    imported = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)] + [
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    ]
    assert not [name for name in imported if name.startswith("meridian.web")], imported


def test_reset_gate_503_wait_and_double_hold(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """refusal + invariant (AC-21): eight 503s at once; other operations wait for the reset; login/healthz never wait."""
    store = FakeSessionStore()
    settings = make_settings(tmp_path)
    app = web_app(monkeypatch, settings, store=store)
    state = {"value": "before-reset"}

    def read_thread() -> dict[str, str]:
        return {"value": state["value"]}

    contract = load_contract()
    refused = sorted(RESET_503_OPERATIONS)
    assert len(refused) == 8
    for operation in refused:
        add_probe_route(app, operation)
    add_probe_route(app, "getChatThread", endpoint=read_thread)
    add_probe_route(app, "resetDemo")
    token = store.issue()
    headers = cookie_header(token)
    thread = new_thread_id()

    with make_client(app) as client:
        gate = reset_gate_of(app)

        # Eight operations: 503 RESET_IN_PROGRESS, retry_after_ms 5000, at once.
        release = threading.Event()
        held = threading.Event()

        def hold_until_released() -> None:
            with gate.hold():
                held.set()
                release.wait(10)

        holder = threading.Thread(target=hold_until_released)
        holder.start()
        try:
            assert held.wait(2)
            with pytest.raises(ResetAlreadyRunning), gate.hold():
                pass
            for operation in refused:
                spec = contract.operations[operation]
                path = spec.path_template.replace("{thread_id}", thread)
                began = time.monotonic()
                response = client.request(spec.method.upper(), path, headers=headers)
                elapsed = time.monotonic() - began
                body = error_body(response, 503, "RESET_IN_PROGRESS")
                assert body["error"]["details"] == {"retry_after_ms": 5000}, operation
                assert_matches(response, operation)
                assert elapsed < 1.0, f"{operation} waited {elapsed:.2f} s"
            print(f"eight operations answered 503 at once: {refused}")

            # Never waiting: /healthz, login and the reset route itself.
            for label, call in (
                ("healthz", lambda: client.get("/healthz")),
                ("login", lambda: login(client, settings)),
                ("resetDemo", lambda: client.post("/api/demo/reset", headers=headers)),
            ):
                began = time.monotonic()
                response = call()
                assert time.monotonic() - began < 1.0, f"{label} waited on the reset gate"
                assert response.status_code != 503, label
        finally:
            release.set()
            holder.join(5)

        # Any other operation waits for the reset and then answers from the post-reset state.
        started: dict[str, float] = {}

        def reset_for_a_second() -> None:
            with gate.hold():
                started["at"] = time.monotonic()
                time.sleep(1.0)
                state["value"] = "after-reset"

        resetter = threading.Thread(target=reset_for_a_second)
        resetter.start()
        try:
            deadline = time.monotonic() + 2
            while "at" not in started and time.monotonic() < deadline:
                time.sleep(0.01)
            assert "at" in started
            waited = client.get(f"/api/chat/sessions/{thread}", headers=headers)
            answered_after = time.monotonic() - started["at"]
        finally:
            resetter.join(5)
        print(f"getChatThread answered {answered_after:.2f} s after the reset began")
        assert waited.status_code == 200
        assert waited.json() == {"value": "after-reset"}
        assert answered_after >= 0.9
    assert gate.held() is False
