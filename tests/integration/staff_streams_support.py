"""AEA-52 SSE reader: reads a stream from the real server, with an idle limit and a hard time limit."""

from __future__ import annotations

import threading
import time
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

import httpx

from tests.api.openapi_check import SseFrame


@dataclass(frozen=True)
class StreamRead:
    status: int
    frames: tuple[SseFrame, ...]
    closed_by_server: bool
    response: httpx.Response


def parse_sse(lines: Iterable[str]) -> Iterator[SseFrame]:
    """`id:`, `event:` and `data:` lines; `:` lines are heartbeats; a blank line ends a frame."""
    event: str | None = None
    ident: str | None = None
    data: list[str] = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if line == "":
            if data:
                yield SseFrame(event=event, id=ident, data="\n".join(data))
            event, ident, data = None, None, []
        elif line.startswith(":"):
            continue
        elif line.startswith("id:"):
            ident = line[3:].strip()
        elif line.startswith("event:"):
            event = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].lstrip(" "))
    # a frame without its closing blank line is not complete: dropped


def read_stream(
    base_url: str,
    cookie: str,
    path: str,
    *,
    last_event_id: str | None = None,
    idle_s: float = 3.0,
    max_s: float = 20.0,
) -> StreamRead:
    headers = {"Last-Event-ID": last_event_id} if last_event_id is not None else {}
    timeout = httpx.Timeout(connect=5.0, read=idle_s, write=5.0, pool=5.0)
    frames: list[SseFrame] = []
    closed = False
    with httpx.Client(base_url=base_url, cookies={"mhc_session": cookie}, timeout=timeout) as client:
        with client.stream("GET", path, headers=headers) as resp:
            if resp.status_code != 200:
                resp.read()
                return StreamRead(resp.status_code, (), True, resp)
            deadline = time.monotonic() + max_s
            try:
                for frame in parse_sse(resp.iter_lines()):
                    frames.append(frame)
                    if time.monotonic() > deadline:
                        break
                else:
                    closed = True
            except httpx.ReadTimeout:
                closed = False
            return StreamRead(resp.status_code, tuple(frames), closed, resp)


class BackgroundStream:
    """A stream read on a daemon thread, so a test can act while the stream is open."""

    def __init__(
        self, base_url: str, cookie: str, path: str, *, last_event_id: str | None = None, max_s: float = 30.0
    ) -> None:
        self._args = (base_url, cookie, path)
        self._last_event_id = last_event_id
        self._max_s = max_s
        self._result: StreamRead | None = None
        self._thread = threading.Thread(target=self._run, name="aea52-stream", daemon=True)

    def _run(self) -> None:
        self._result = read_stream(
            *self._args, last_event_id=self._last_event_id, idle_s=self._max_s, max_s=self._max_s
        )

    def start(self) -> None:
        self._thread.start()

    def join(self, timeout: float = 15.0) -> StreamRead:
        self._thread.join(timeout)
        if self._result is None:
            raise AssertionError("background stream did not finish in time")
        return self._result
