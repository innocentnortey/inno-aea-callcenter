"""AEA-59 runner support: one bounded read of an ASGI response on the TestClient's loop.

Used for every drive of an event-stream operation (FIX-W1), so a stream that should have answered an error fails
instead of hanging the suite.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Final

import anyio
import httpx
from fastapi import FastAPI

from tests.api.openapi_check import SseFrame
from tests.contract.openapi_variants import sse_frames

STREAM_READ_TIMEOUT_S: Final = 5.0


@dataclass(frozen=True)
class SseRead:
    status: int | None
    content_type: str
    frames: tuple[SseFrame, ...]
    error: BaseException | None
    headers: Mapping[str, str] = field(default_factory=dict)
    body: bytes = b""


def as_response(read: SseRead) -> httpx.Response:
    """The read as an httpx.Response for assert_response_matches (status, every header, the raw body)."""
    assert read.status is not None, "no response start was read"
    return httpx.Response(read.status, headers=list(read.headers.items()), content=read.body)


async def read_asgi_stream(
    app: FastAPI, path: str, headers: dict[str, str], frames: int, timeout_s: float
) -> SseRead:
    raw_headers = [(b"host", b"testserver")] + [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    scope: dict[str, Any] = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": b"",
        "headers": raw_headers,
        "client": ("198.51.100.7", 50000),
        "server": ("testserver", 80),
        "state": {},
    }
    send_side, receive_side = anyio.create_memory_object_stream[bytes](max_buffer_size=10_000)
    disconnect = anyio.Event()
    done = anyio.Event()
    state: dict[str, Any] = {
        "status": None,
        "content_type": "",
        "error": None,
        "requested": False,
        "headers": {},
    }
    raw = bytearray()

    async def receive() -> dict[str, Any]:
        if not state["requested"]:
            state["requested"] = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await disconnect.wait()
        return {"type": "http.disconnect"}

    async def send_message(message: dict[str, Any]) -> None:
        if message["type"] == "http.response.start":
            state["status"] = int(message["status"])
            sent = {k.decode().lower(): v.decode() for k, v in message["headers"]}
            state["content_type"] = sent.get("content-type", "")
            state["headers"] = sent
        elif message["type"] == "http.response.body":
            chunk = message.get("body", b"")
            if chunk:
                raw.extend(chunk)
                send_side.send_nowait(chunk)
            if not message.get("more_body", False):
                send_side.close()

    async def run_app() -> None:
        try:
            await app(scope, receive, send_message)  # type: ignore[arg-type]
        except BaseException as exc:
            state["error"] = exc
        finally:
            send_side.close()
            done.set()

    buffer = ""
    async with anyio.create_task_group() as tg:
        tg.start_soon(run_app)
        with anyio.move_on_after(timeout_s):
            async for chunk in receive_side:
                buffer += chunk.decode()
                complete = buffer.rsplit("\n\n", 1)[0] + "\n\n" if "\n\n" in buffer else ""
                if len(sse_frames(complete)) >= frames:
                    break
        disconnect.set()
        with anyio.move_on_after(timeout_s):
            await done.wait()
        tg.cancel_scope.cancel()
    complete = buffer.rsplit("\n\n", 1)[0] + "\n\n" if "\n\n" in buffer else ""
    return SseRead(
        state["status"],
        state["content_type"],
        tuple(sse_frames(complete)),
        state["error"],
        dict(state["headers"]),
        bytes(raw),
    )
