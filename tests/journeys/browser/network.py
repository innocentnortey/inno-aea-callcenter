"""Record every browser request and /api/* exchange; resolve operationIds; validate responses (AEA-58 AC-7, AC-8, PA-4)."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Final
from urllib.parse import parse_qs, urlsplit

import httpx
from playwright.sync_api import Error as PlaywrightError

from tests.api.openapi_check import Contract, assert_response_matches
from tests.journeys.support.steps import missing_needs, owners_of

if TYPE_CHECKING:
    from fastapi import FastAPI
    from playwright.sync_api import BrowserContext, Page, Request, Response

    from meridian.web.container import Container

DEV_PARAMS: Final = frozenset({"signedin", "role", "scenario", "staffing", "ex", "delay"})

# PA-4: service needs per mounted chat operation. A 500 from one of these while a listed need is unbound is blocked
# work, not a contract failure. Names are AEA-57 NEED_OWNERS keys, equal to tests/journeys/j1/test_aea_57.py
# CHAT_NEEDS / TURN_NEEDS (a self-check pins the equality). Never add other operations.
_CHAT: Final = ("login_sessions", "session_service", "demo_service", "demo_clock", "reply_composer")
UNBOUND_500_NEEDS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "startChatSession": _CHAT,
        "getChatThread": _CHAT,
        "submitTurn": (*_CHAT, "turn_service", "run_graph"),
    }
)


@dataclass
class SeenRequest:
    index: int
    method: str
    url: str
    resource_type: str
    is_navigation: bool


@dataclass
class ApiExchange:
    index: int  # SeenRequest.index of the request
    method: str
    url: str
    path: str
    operation_id: str | None
    status: int
    headers: list[tuple[str, str]]
    request_body: bytes | None
    body: bytes | None = None  # filled on requestfinished; stays None for SSE
    is_sse: bool = False
    failed: str | None = None  # requestfailed text

    def header(self, name: str) -> str | None:
        for key, value in self.headers:
            if key.lower() == name.lower():
                return value
        return None


@dataclass
class ValidationSummary:
    validated: Counter[str] = field(default_factory=Counter)
    unrouted: Counter[str] = field(default_factory=Counter)
    unrouted_owners: dict[str, str] = field(default_factory=dict)
    unbound: Counter[str] = field(default_factory=Counter)
    unbound_owners: dict[str, str] = field(default_factory=dict)
    sse_checked: Counter[str] = field(default_factory=Counter)
    unfinished: int = 0
    failures: list[str] = field(default_factory=list)


_RESOLVERS: dict[int, list[tuple[str, re.Pattern[str], int, str]]] = {}


def _resolver(contract: Contract) -> list[tuple[str, re.Pattern[str], int, str]]:
    key = id(contract)
    if key not in _RESOLVERS:
        built = []
        for spec in contract.operations.values():
            pattern = re.sub(r"\\\{[^}]*\\\}", "[^/]+", re.escape(spec.path_template))
            built.append(
                (
                    spec.method.upper(),
                    re.compile("^" + pattern + "$"),
                    spec.path_template.count("{"),
                    spec.operation_id,
                )
            )
        _RESOLVERS[key] = built
    return _RESOLVERS[key]


def operation_for(method: str, path: str, contract: Contract) -> str | None:
    hits = [(n, op) for m, rx, n, op in _resolver(contract) if m == method and rx.match(path)]
    if not hits:
        return None
    return min(hits, key=lambda h: h[0])[1]


def to_httpx(exchange: ApiExchange) -> httpx.Response:
    return httpx.Response(status_code=exchange.status, headers=exchange.headers, content=exchange.body or b"")


def validate_exchanges(
    exchanges: Sequence[ApiExchange], *, container: Container, app: FastAPI, contract: Contract
) -> ValidationSummary:
    out = ValidationSummary()
    for ex in exchanges:
        label = f"{ex.method} {ex.path}"
        op = ex.operation_id
        if op is None:
            out.failures.append(f"{label}: no operationId in the OpenAPI matches")
            continue
        routing = missing_needs(container, app, (), (op,))
        if routing:
            out.unrouted[op] += 1
            out.unrouted_owners[op] = ", ".join(owners_of(routing))
            continue
        if ex.status == 500 and op in UNBOUND_500_NEEDS:
            missing = missing_needs(container, app, UNBOUND_500_NEEDS[op], ())
            if missing:
                out.unbound[op] += 1
                out.unbound_owners[op] = ", ".join(owners_of(missing))
                continue
        spec = contract.operations[op]
        if ex.is_sse:
            ctype = ex.header("content-type") or ""
            if str(ex.status) not in spec.responses:
                out.failures.append(f"{op} {ex.status}: undocumented status on an event stream")
            elif ex.status == 200 and not ctype.startswith("text/event-stream"):
                out.failures.append(f"{op} 200: content type {ctype!r} is not text/event-stream")
            else:
                out.sse_checked[op] += 1
            continue
        if ex.body is None and ex.failed is None:
            out.unfinished += 1
            continue
        if ex.failed:
            out.failures.append(f"{op} {ex.status}: request failed: {ex.failed}")
            continue
        try:
            assert_response_matches(to_httpx(ex), op)
        except AssertionError as exc:
            first = (str(exc).splitlines() or [""])[0][:300]
            out.failures.append(f"{op}: {first}")
        else:
            out.validated[op] += 1
    return out


def teardown_failures(summary: ValidationSummary, *, strict: bool) -> list[str]:
    found = list(summary.failures)
    if strict:
        for op in sorted(summary.unrouted):
            found.append(f"{op}: unrouted, blocked-on {summary.unrouted_owners[op]} [--journeys-strict]")
        for op in sorted(summary.unbound):
            found.append(
                f"{op}: 500 while a service is unbound, blocked-on {summary.unbound_owners[op]} [--journeys-strict]"
            )
    return found


def _path_query(url: str) -> str:
    parts = urlsplit(url)
    return parts.path + (f"?{parts.query}" if parts.query else "")


class NetworkLog:
    def __init__(self, contract: Contract) -> None:
        self.contract = contract
        self.requests: list[SeenRequest] = []
        self.exchanges: list[ApiExchange] = []
        self._index: dict[Request, int] = {}
        self._by_index: dict[int, ApiExchange] = {}

    def attach(self, context: BrowserContext) -> None:
        context.on("request", self._on_request)
        context.on("response", self._on_response)
        context.on("requestfinished", self._on_finished)
        context.on("requestfailed", self._on_failed)

    def _on_request(self, req: Request) -> None:
        seen = SeenRequest(
            len(self.requests), req.method, req.url, req.resource_type, req.is_navigation_request()
        )
        self.requests.append(seen)
        self._index[req] = seen.index

    def _on_response(self, resp: Response) -> None:
        req = resp.request
        index = self._index.get(req)
        path = urlsplit(resp.url).path
        if index is None or not path.startswith("/api/"):
            return
        ctype = resp.headers.get("content-type", "")
        ex = ApiExchange(
            index=index,
            method=req.method,
            url=resp.url,
            path=path,
            operation_id=operation_for(req.method, path, self.contract),
            status=resp.status,
            headers=[(h["name"], h["value"]) for h in resp.headers_array()],
            request_body=req.post_data_buffer,
            is_sse=ctype.startswith("text/event-stream"),
        )
        self.exchanges.append(ex)
        self._by_index[index] = ex
        if not ex.is_sse:
            try:  # a handler runs in its own greenlet, so it may wait for the body
                ex.body = resp.body()
            except PlaywrightError:
                pass  # the page navigated away first: requestfinished or the close-time count decides

    def _on_finished(self, req: Request) -> None:
        ex = self._by_index.get(self._index.get(req, -1))
        if ex is None or ex.is_sse:
            return
        try:
            response = req.response()
            ex.body = response.body() if response is not None else b""
        except PlaywrightError as exc:
            ex.failed = (str(exc).splitlines() or ["failed"])[0]

    def _on_failed(self, req: Request) -> None:
        ex = self._by_index.get(self._index.get(req, -1))
        if ex is not None:
            ex.failed = req.failure or "failed"

    def mark(self) -> int:
        return len(self.requests)

    def operations(self, since: int = 0) -> list[str]:
        return [e.operation_id for e in self.exchanges if e.index >= since and e.operation_id]

    def wait_for(
        self,
        page: Page,
        operation_id: str,
        *,
        since: int = 0,
        timeout_ms: int = 15_000,
        finished: bool = True,
    ) -> ApiExchange:
        waited = 0
        while True:
            for ex in self.exchanges:
                if ex.operation_id == operation_id and ex.index >= since:
                    if not finished or ex.body is not None or ex.is_sse or ex.failed:
                        return ex
            if waited >= timeout_ms:
                raise AssertionError(
                    f"no {operation_id} response within {timeout_ms} ms (seen: {self.operations(since)})"
                )
            page.wait_for_timeout(50)
            waited += 50

    def origins(self) -> set[str]:
        found: set[str] = set()
        for seen in self.requests:
            parts = urlsplit(seen.url)
            if parts.scheme in ("http", "https"):
                found.add(f"{parts.scheme}://{parts.netloc}")
        return found

    def dev_param_hits(self, *, allowed_urls: Collection[str] = ()) -> list[str]:
        hits: list[str] = []
        for seen in self.requests:
            parts = urlsplit(seen.url)
            if parts.scheme not in ("http", "https"):
                continue
            target = _path_query(seen.url)
            if target in allowed_urls:
                continue
            if DEV_PARAMS & set(parse_qs(parts.query, keep_blank_values=True)):
                hits.append(target)
        return hits
