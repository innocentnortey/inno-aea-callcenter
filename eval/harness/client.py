"""The async HTTP client for the eight OpenAPI operations, with the eval headers. The only place that talks HTTP."""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Any, Final, Literal
from urllib.parse import quote

import httpx

EVAL_KEY_HEADER: Final = "X-Meridian-Eval-Key"
RUN_ID_HEADER: Final = "X-Meridian-Run-Id"
RUN_TAG_HEADER: Final = "X-Meridian-Run-Tag"  # "eval" | "load"


class HarnessHttpError(Exception):
    """An operation answered an unexpected status. The message never holds a body."""

    def __init__(self, op: str, status: int) -> None:
        super().__init__(f"{op} answered {status}")
        self.op = op
        self.status = status


@dataclass(frozen=True)
class TurnCall:
    turn_id: str
    http_status: int
    body: dict[str, Any] | None
    sent_at: datetime
    first_byte_ms: int
    total_ms: int
    timed_out: bool
    transport_error: bool


@dataclass(frozen=True)
class HandoffCall:
    turn_id: str
    http_status: int
    body: dict[str, Any] | None


class AgentClient:
    def __init__(
        self,
        base_url: str,
        *,
        transport: httpx.AsyncBaseTransport | None,
        eval_key: str,
        run_id: str,
        run_tag: Literal["eval", "load"],
        wall_clock: Callable[[], datetime],
        timeout_s: float = 65.0,
    ) -> None:
        self._wall_clock = wall_clock
        self._http = httpx.AsyncClient(
            base_url=base_url,
            transport=transport,
            timeout=httpx.Timeout(timeout_s),
            headers={EVAL_KEY_HEADER: eval_key, RUN_ID_HEADER: run_id, RUN_TAG_HEADER: run_tag},
            follow_redirects=False,
            trust_env=False,
        )

    async def __aenter__(self) -> AgentClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _get(self, op: str, path: str) -> Any:
        response = await self._http.get(path)
        if response.status_code != 200:
            raise HarnessHttpError(op, response.status_code)
        return response.json()

    async def login(self, username: str, password: str) -> None:
        response = await self._http.post("/api/login", json={"username": username, "password": password})
        if response.status_code != 200:
            raise HarnessHttpError("login", response.status_code)

    async def latest_eval(self) -> dict[str, Any]:
        body: dict[str, Any] = await self._get("getLatestEval", "/api/eval/latest")
        return body

    async def monitoring(self) -> dict[str, Any]:
        body: dict[str, Any] = await self._get("getMonitoring", "/api/monitoring")
        return body

    async def demo_clock(self) -> datetime:
        body = await self._get("getDemoClock", "/api/demo/clock")
        return datetime.fromisoformat(str(body["now"]))

    async def start_chat(self) -> str:
        response = await self._http.post("/api/chat/sessions")
        if response.status_code != 201:
            raise HarnessHttpError("startChatSession", response.status_code)
        return str(response.json()["thread_id"])

    async def _post_timed(self, path: str, payload: Mapping[str, Any], turn_id: str) -> TurnCall:
        sent_at = self._wall_clock()
        start = time.perf_counter()
        first_byte = 0
        try:
            async with self._http.stream("POST", path, json=payload) as response:
                first_byte = int((time.perf_counter() - start) * 1000)
                raw = await response.aread()
                total = int((time.perf_counter() - start) * 1000)
                status = response.status_code
        except httpx.TimeoutException:
            total = int((time.perf_counter() - start) * 1000)
            return TurnCall(turn_id, 0, None, sent_at, min(first_byte, total), total, True, False)
        except httpx.TransportError:
            total = int((time.perf_counter() - start) * 1000)
            return TurnCall(turn_id, 0, None, sent_at, min(first_byte, total), total, False, True)
        body: dict[str, Any] | None = None
        if status == 200:
            try:
                body = json.loads(raw)
            except ValueError:
                return TurnCall(turn_id, status, None, sent_at, first_byte, total, False, True)
        return TurnCall(turn_id, status, body, sent_at, first_byte, total, False, False)

    async def submit_turn(self, thread_id: str, payload: Mapping[str, Any]) -> TurnCall:
        turn_id = str(uuid.uuid4())
        path = f"/api/chat/sessions/{quote(thread_id, safe='')}/turns"
        return await self._post_timed(path, {"turn_id": turn_id, "payload": dict(payload)}, turn_id)

    async def request_person(self, thread_id: str) -> HandoffCall:
        turn_id = str(uuid.uuid4())
        path = f"/api/chat/sessions/{quote(thread_id, safe='')}/handoff"
        call = await self._post_timed(path, {"turn_id": turn_id}, turn_id)
        return HandoffCall(turn_id, call.http_status, call.body)

    async def inbox(self) -> list[dict[str, Any]]:
        body = await self._get("listDemoInbox", "/api/demo/inbox")
        messages: list[dict[str, Any]] = body["messages"]
        return messages
