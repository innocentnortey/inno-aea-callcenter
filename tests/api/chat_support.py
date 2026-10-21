"""AEA-40 API test support: a chat app over a temp working copy, with every sibling doubled (frozen with the tests).

`chat_app` is `web_app` (AEA-23) plus the chat router and dependency overrides for the two services, so a test drives
the real routes, the real middleware (login gate, request ids) and real `TurnService` / `SessionService` over a temp
SQLite copy. Part A tests build it without a session service, because `SessionService` needs the `ClockView` /
`StaffingView` types of AEA-02b; Part B tests ask for it.
"""

from __future__ import annotations

import dataclasses
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from meridian.domain.common import ThreadId, TurnId
from meridian.domain.staff import LoginSession
from meridian.web.deps import get_request_context, get_session_service, get_turn_service, get_uow_factory
from meridian.web.middleware import LimitScope, LimitVerdict, RequestContext
from tests.api.web_shell_support import (
    FakeSessionStore,
    cookie_header,
    make_client,
    make_settings,
    rand_word,
    web_app,
)
from tests.fakes import InMemoryTraceSink
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services.chat_doubles import (
    FakeDemo,
    FakeSpendGuard,
    ScriptedRunGraph,
    make_session_service,
    make_turn_service,
)

REFUSED = LimitVerdict(allowed=False, scope=LimitScope.THREAD, retry_after_ms=5000)


@dataclass
class VerdictBox:
    """What `RequestContext.turn_verdict` says on the next submitTurn: None leaves the middleware's own answer."""

    verdict: LimitVerdict | None = None


@dataclass
class ChatEnv:
    store: TempStore
    app: FastAPI
    sessions: FakeSessionStore
    token: str
    session: LoginSession
    graph: Any
    turn_service: Any
    session_service: Any
    demo: FakeDemo | None
    trace: Any
    spend: FakeSpendGuard
    verdict: VerdictBox
    eval_key: str
    settings: Any
    other_token: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def demo_session(self) -> str:
        return str(self.session.session_id)

    @property
    def headers(self) -> dict[str, str]:
        return cookie_header(self.token)

    def client(self) -> TestClient:
        return make_client(self.app)

    def other_session(self) -> LoginSession:
        return self.sessions.session_of(self.other_token)


def chat_app(
    monkeypatch: pytest.MonkeyPatch,
    settings: Any,
    sessions: FakeSessionStore,
    store: TempStore,
    *,
    turn_service: Any = None,
    session_service: Any = None,
    verdict: VerdictBox | None = None,
) -> FastAPI:
    """`web_app` + the chat router + overrides. Imports the router when called (it does not exist before AEA-40)."""
    from meridian.web.routes.chat import build_router

    app = web_app(monkeypatch, settings, store=sessions)
    app.include_router(build_router())
    app.dependency_overrides[get_uow_factory] = lambda: store.uow
    if turn_service is not None:
        app.dependency_overrides[get_turn_service] = lambda: turn_service
    if session_service is not None:
        app.dependency_overrides[get_session_service] = lambda: session_service
    if verdict is not None:

        def context_with_verdict(request: Request) -> RequestContext:
            real: RequestContext = request.state.request_context
            if verdict.verdict is None:
                return real
            return dataclasses.replace(real, turn_verdict=verdict.verdict)

        app.dependency_overrides[get_request_context] = context_with_verdict
    return app


@contextmanager
def chat_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    graph: Any = None,
    with_session_service: bool = False,
    trace: Any = None,
    spend: FakeSpendGuard | None = None,
) -> Iterator[ChatEnv]:
    settings = make_settings(tmp_path, eval_key=rand_word(18, "ek"))
    sessions = FakeSessionStore()
    token = sessions.issue()
    other_token = sessions.issue()
    with temp_sqlite() as store:
        run_graph = graph if graph is not None else ScriptedRunGraph()
        sink = trace if trace is not None else InMemoryTraceSink()
        guard = spend if spend is not None else FakeSpendGuard(True)
        turn_service = make_turn_service(store, run_graph=run_graph, trace=sink, spend=guard)
        demo = FakeDemo() if with_session_service else None
        session_service = make_session_service(store, demo=demo) if with_session_service else None
        box = VerdictBox()
        app = chat_app(
            monkeypatch,
            settings,
            sessions,
            store,
            turn_service=turn_service,
            session_service=session_service,
            verdict=box,
        )
        yield ChatEnv(
            store=store,
            app=app,
            sessions=sessions,
            token=token,
            session=sessions.session_of(token),
            graph=run_graph,
            turn_service=turn_service,
            session_service=session_service,
            demo=demo,
            trace=sink,
            spend=guard,
            verdict=box,
            eval_key=settings.eval_key.get_secret_value() if settings.eval_key is not None else "",
            settings=settings,
            other_token=other_token,
        )


def post_turn(
    client: TestClient,
    token: str,
    thread_id: ThreadId | str,
    payload: dict[str, Any],
    turn_id: TurnId | str | None = None,
    *,
    extra_headers: dict[str, str] | None = None,
) -> Any:
    body = {"turn_id": str(turn_id) if turn_id is not None else str(uuid.uuid4()), "payload": payload}
    return client.post(
        f"/api/chat/sessions/{thread_id}/turns",
        json=body,
        headers={**cookie_header(token), **(extra_headers or {})},
    )


def get_thread(client: TestClient, token: str, thread_id: ThreadId | str) -> Any:
    return client.get(f"/api/chat/sessions/{thread_id}", headers=cookie_header(token))


def start_session(client: TestClient, token: str, *, extra_headers: dict[str, str] | None = None) -> Any:
    return client.post("/api/chat/sessions", headers={**cookie_header(token), **(extra_headers or {})})
