# Plan — [AEA-49] web: serve the built `apps/web/dist`

**Status:** planned (READY). No product decision is open: WEB-1 is answered **A** (Innocent, D-4 in
`docs/plans/stage7-signoff.md`: "ill take all your recommendations"), UX-4 is signed (`PROJECT-CHECKLIST.md` line 88,
"Innocent ✓ 2026-10-21"), AEA-23 is merged on `main` (`1e6889a`), AEA-01's `register_frontend` stub exists, and
AEA-02's `Settings.web_dist_dir` / `require_frontend` exist. Nothing to wait for.
**Issue:** https://labs.gauntletai.com/innocentnortey/inno-aea-callcenter/-/issues/49 (spec copy:
`docs/plans/tickets/AEA-49.md`) · **Base revision:** `a581a71` (main after the AEA-42 merge) · **Planner:**
claude-opus-5-5, 2026-10-21 (first version; no earlier plan existed) · **Implementer:** `fanout-implementer` on Sonnet.
**Lane:** `lane::build-loop` · **Risk:** `risk::security` per **WEB-36** (decided, `docs/plans/7b-decisions/web.md`
line 93: "AEA-49: `risk::security` (it decides what an unsigned visitor can fetch: network exposure)"). The slice-plan
row lacks the label; the ticket asks the orchestrator to add it. Consequence (rule `build-loop-test-scope`):
`test-writer-agent` freezes the failing tests in §7 **before** the implementer starts, and `security-privacy-agent`
reads this ticket's diff at the wave-2 merge. If the orchestrator records "not security" instead, the implementer
writes the §7 tests together with the code. §5 step 0 tells the implementer how to tell which case applies.
Wave 2.

---

## 1. Goal and sources

Quoted from the issue's *What to build* (`docs/plans/tickets/AEA-49.md`):

> `web/frontend.py` with `register_frontend(container: Container, app: FastAPI) -> None` and its own
> `register_frontend()` hunk in `web/container.py` (stage7/web.md §12; WEB-29). The FastAPI app serves UX-4's
> production build of the React app (`apps/web/dist` …) from the same origin as the API, so the deployed URL is one
> interactive web app.

What that means in practice, one example (the ticket's example pair, web.md's opening example):

- Input: an unsigned browser opens `/staff/queue`.
- Process: AEA-23's gate finds no `mhc_session`, sees a page `GET`, and answers `303` to
  `/login?return_to=%2Fstaff%2Fqueue&reason=none`. `/login` is a public path (registered here), so the gate lets it
  through and **this ticket's SPA fallback route** answers the build's `index.html`. The page then loads
  `/assets/index-….js` and `/fonts/…` without a session (public prefixes registered here; WEB-1 A). After sign-in the
  deep link `/staff/cases/MHC-C-0007` answers `index.html` (React draws SCR-6), while `/api/staff/cases/MHC-C-0007`
  still reaches the API (JSON), because the fallback never matches `/api/*` or `/healthz`.
- Output: one origin serving both the UI and the API, nothing outside `dist/` ever served.

Governing sources (all read for this plan):

| Source | Location | What it obliges here |
|---|---|---|
| Ticket | `docs/plans/tickets/AEA-49.md` AC-1…AC-12 | Everything below |
| Contract (wins over DO-4) | `docs/design/contracts/stage7/web.md` §12 (frontend serving), §6 (gate, `PublicPaths`), §10 (`request` record) | Mount, fallback, traversal/dotfile 404, missing-build rule, public paths, record fields |
| Settings | `docs/design/contracts/stage7/graph-core.md` §12 lines 538–539; `src/meridian/config.py` | `web_dist_dir: Path = Path("apps/web/dist")` (`MERIDIAN_WEB_DIST_DIR`), `require_frontend: bool = False` (`MERIDIAN_REQUIRE_FRONTEND`) |
| Decisions | `docs/plans/7b-decisions/web.md` WEB-1 (A, via D-4), WEB-28, WEB-29, WEB-30, WEB-31, WEB-32, WEB-36 | Public list = `/login`, `/assets/`, `/fonts/`; 303 is AEA-23's; file is `web/frontend.py`; missing-build behaviour; WF-19; security label |
| Amendment | `docs/plans/ux-join/backend-amendments.md` AEA-49-1 (= AC-10); AEA-49-2 **not applied** (A chosen) | Cache headers; missing asset 404 |
| Audit | `docs/plans/ux-join/audit-shell-reads-build.md` C2 (favicon), C4 (cache) | C4 in AC-10; C2 is the UX session's (see §8) |
| Observability | `docs/design/observability-contract.md` line 94 (WF-19), line 273 (CAP-11) | `request` record with route template, never raw path/query/cookie |
| Code design | `docs/design/code-design.md` §2.3 (pages use the pool, < 1 s), §3 line 303/316, §8 line 668 | Module home; AC-12 doc rows |
| Rules | `.claude/rules/integrated-journeys.md` §4 (record), `build-loop-test-scope.md` (AEA addition), `context-maintenance.md` | Journey record, affected tests and journeys, context rows |
| Evaluation / metrics | DO-5 / DO-7 | **n/a** (ticket: WF-19 decides no outcome; no M-n counts page loads) |

## 2. Boundary

**Owned files (the only files the implementer may create or edit):**

| File | Create / modify | Content |
|---|---|---|
| `src/meridian/web/frontend.py` | create | The whole module (§4.2) |
| `src/meridian/web/container.py` | modify **only** the body and docstring of `register_frontend` (lines 624–628 on `a581a71`) | Two-line delegation (§4.3) |
| `tests/api/frontend_support.py` | create | Fixture dist, app builder, raw-ASGI helper, socket guard (§7.1). New file, unique name, so it cannot collide (same pattern as AEA-42's `tests/api/handoff_support.py`) |
| `tests/api/test_web_frontend.py` | create | AC-1, AC-2, AC-3, AC-4, AC-5, AC-10 and the example pair (§7.2) |
| `tests/capture/test_cap11_page_serving.py` | create | AC-7, AC-8, AC-11 (§7.3) |
| `tests/journeys/j1/test_aea_49.py` | create | AC-9 (§7.4) |
| `docs/testing/journeys/<YYYY-MM-DD>-AEA-49.md` | create | AC-9 evidence record (§5 step 9) |
| `.claude/reference/area-map.md` | modify row A8 (line 35) and the AEA-49 sentence in the *Screens* paragraph (line 50) only | AC-12 |
| `.claude/state/icm-progress.md` | add one *Routes verified* row; prepend to *Last reconciled* | AC-12 |
| `docs/design/code-design.md` | modify §3 lines 303 and 316 and the §8 row at line 668 only | AC-12 |

**Shared surfaces, read only (import or call; never edit):** `src/meridian/web/middleware.py` (`PublicPaths`,
`WebShellState`, `HEALTHZ_PATH`, the gate), `src/meridian/web/app.py` (`create_app`, `ContainerOverrides`),
`src/meridian/web/logging.py`, `src/meridian/web/deps.py`, `src/meridian/web/errors.py`, `src/meridian/config.py`,
`tests/api/web_shell_support.py`, `tests/api/openapi_check.py`, `tests/fakes/trace.py`, `tests/journeys/affected.py`,
`apps/web/**` (including `apps/web/dist/`), `docs/ux/**`.

**Owned by others, must not touch:** every other `register_<area>()` hunk in `web/container.py` and its module-level
imports (AEA-01's `test_container_imports_only_policy_limits` pins them); `web/app.py`, `web/middleware.py`,
`web/deps.py`, `routes/auth.py` (AEA-23); any route or schema file; the OpenAPI and `UI_CONTRACTS.md`; `apps/web/**`;
`docs/ux/**`; `tests/journeys/support/` (AEA-57); `tests/journeys/browser/` (AEA-58); `docs/plans/slice-plan.md`;
`docs/design/observability-contract.md` (see §8 item 3); the briefing, issued data, `docs/archive/`, `docs/parked/`.

## 3. Requirements table

| # | Requirement (ticket AC / source) | How it is implemented | How it is verified |
|---|---|---|---|
| AC-1 | Signed in, 12 screen paths → 200 `text/html` fixture `index.html`; `/assets/app.js`, `/fonts/f.woff2` → their bytes and content types | `SpaFallbackRoute` (template `spa_fallback`) answers `index.html` for every eligible `GET`; `StaticFolderRoute("assets")` / `("fonts")` answer files with `CONTENT_TYPES` | `tests/api/test_web_frontend.py::test_spa_fallback_and_assets` |
| AC-2 | `/api/*` and `/healthz` never shadowed; `/api/no-such-route` JSON 404, never `index.html` | `is_page_path()` returns False for `/api`, `/api/…`, `/healthz`; routes are appended **last** (the hunk runs last) | `::test_api_and_healthz_not_shadowed` |
| AC-3 | Unsigned: `/login`, `/assets/app.js`, `/fonts/f.woff2` → 200; other screens → 303 `Location: /login?return_to=<path+query>&reason=none`; expired → `reason=expired` + cookie cleared; `/api/staff/queue` → JSON 401 valid against `Unauthenticated` | `register_frontend` adds `("GET","/login")` exact and `("GET","/assets/")`, `("GET","/fonts/")` prefixes to `shell.public_paths`; the 303/401 are AEA-23's gate (unchanged) | `::test_pages_behind_login` (401 checked with `assert_matches(response, "getQueue")`) |
| AC-4 | No file outside dist; `/assets/../../pyproject.toml`, its `%2e%2e` form, `/assets/.env`, a dotfile path → 404 (303 unsigned for non-public); `return_to` not an open redirect | `DistDirectory.static_file()` (§4.2 steps S1–S6); SPA rejects dot segments; the gate's `safe_return_to` (AEA-23) | `::test_no_path_traversal_or_open_redirect` (raw ASGI paths, since the HTTP client normalises `..`) |
| AC-5 | Missing build: `require_frontend=False` → app starts, one `frontend_dist_missing` warning, `/api/*` 200, signed page path JSON 404; `True` → start-up raises naming `MERIDIAN_REQUIRE_FRONTEND` and the path | `register_frontend` steps R4–R5 (§4.2); `FrontendMissingError` | `::test_missing_dist` |
| AC-6 | Directory read, never written; diff touches nothing under `apps/web/` | Only `Path.read_bytes()` and `FileResponse` (opens `rb`); tests use a temp fixture dist | `git diff --name-only main...HEAD \| grep '^apps/web/'` empty; AC-1 test snapshots the fixture tree before/after |
| AC-7 | CAP-11: root, deep link, asset × signed in/out → one `request` record each, `request_id` = `X-Request-ID`, template `spa_fallback` / `/assets/{file}`, status, `caller_role` | Route `.path` attributes are the templates; AEA-23's middleware writes the record from the matched route's `.path` | `tests/capture/test_cap11_page_serving.py::test_page_requests_recorded` |
| AC-8 | CAP-11 forbidden: no log line or span holds `/staff/cases/MHC-C-0007`, `tab=brief`, the cookie value | `frontend.py` logs nothing per request; the only log is the start-up warning (no path in it) | `::test_no_raw_path_query_or_cookie` |
| AC-9 [journey] | J-1 over HTTP: signed-out `/` and `/staff/queue` redirect with `return_to`; `/login` + its asset files load; after login the deep link → `index.html`, `/api/chat/sessions` → JSON. Level `integrated with a scripted model` **or** record Blocked-by AEA-57 | Same code; the journey drives `create_app` with the real container | `uv run pytest -m journey tests/journeys/j1/test_aea_49.py` + `docs/testing/journeys/<date>-AEA-49.md` at level **`mock-tested`**, Blocked by AEA-57 (harness not on `main`) |
| AC-10 | `index.html` + fallback `Cache-Control: no-cache`; `/assets/` `public, max-age=31536000, immutable`; missing `/assets/` or `/fonts/` file → 404 never `index.html`, signed in and out | Constants `INDEX_CACHE_CONTROL`, `ASSET_CACHE_CONTROL`; static route answers 404 itself (never falls through) | `tests/api/test_web_frontend.py::test_cache_headers_and_missing_asset_404` |
| AC-11 | Each record's `status` = response status, no `error_kind` below 500; forced failure in the handler → 500 with non-empty `error_kind`; no non-loopback connect | `read_index()` is called before any response starts, so a raise reaches AEA-23's `except Exception` (500 + `error_kind`) | `tests/capture/test_cap11_page_serving.py::test_wf19_status_values_and_no_outbound` |
| AC-12 | Area map row, ICM row, DO-3 §3 `web/` note and §8 row name AEA-49 and `register_frontend` | §5 step 9 | `git diff --stat main...HEAD` |
| Example pair | Ticket *Example pair* (web.md opening example) — this ticket's worked pair (no WP-n applies: no agent turn) | All of the above | `tests/api/test_web_frontend.py::test_example_pair` |
| web.md §12 | "Registers its public paths (§6)" | Step R3 | AC-3 test asserts the three entries |
| WEB-30 | "one warning log `frontend_dist_missing`, nothing mounted" | Step R5 | AC-5 asserts no frontend route exists |
| DO-6 *Content and redaction* | Session cookie never in logs | No per-request logging in `frontend.py` | AC-8 |

## 4. Shared code to use

### 4.1 Signatures copied from `main` (`a581a71`)

```python
# src/meridian/web/middleware.py (AEA-23) — read only
HEALTHZ_PATH = "/healthz"
SESSION_COOKIE = "mhc_session"
UNMATCHED_ROUTE = "<unmatched>"

class PublicPaths:
    def add_exact(self, method: str, path: str) -> None: ...
    def add_prefix(self, method: str, prefix: str) -> None: ...      # matches path.startswith(prefix)
    def is_public(self, method: str, path: str) -> bool: ...
    def entries(self) -> frozenset[tuple[str, str, str]]: ...         # ("exact"|"prefix", METHOD, path)

@dataclass(frozen=True)
class WebShellState:            # app.state.web_shell, set by create_app
    settings: Settings
    wall_clock: Callable[[], datetime]
    public_paths: PublicPaths

# GateMiddleware._match(app, scope) iterates fastapi.routing.iter_route_contexts(app.router.routes) and returns
# (context.path or "<unmatched>", path_params) for the FIRST Match.FULL. context.path is getattr(route, "path").
# That value becomes the `route` field of the `request` record. Public paths skip session resolution, so their
# record's caller_role is "anonymous" even when a valid cookie was sent (AEA-23 behaviour; see §8 item 4).
```

```python
# src/meridian/web/container.py (AEA-01) — Container API used here
class Container:
    @property
    def settings(self) -> Any: ...      # the Settings object (typed Any on purpose)
```

```python
# src/meridian/config.py (AEA-02)
class Settings(MeridianModel):
    web_dist_dir: Path = Path("apps/web/dist")   # env MERIDIAN_WEB_DIST_DIR
    require_frontend: bool = False               # env MERIDIAN_REQUIRE_FRONTEND
```

```python
# starlette 1.9.0 (installed) — the route base class
class BaseRoute:
    def matches(self, scope: Scope) -> tuple[Match, Scope]: ...
    def url_path_for(self, name: str, /, **path_params: Any) -> URLPath: ...
    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None: ...
# from starlette.routing import BaseRoute, Match, NoMatchFound
# from starlette.datastructures import URLPath
# from starlette.responses import FileResponse, JSONResponse, Response
# from starlette.types import Receive, Scope, Send
```

Why a custom `BaseRoute` and not `StaticFiles` / `app.mount` / an `APIRoute` at `/{path:path}`: the middleware records
`route.path`. A `Mount` or catch-all `APIRoute` would record `/assets` or `/{full_path:path}`, not the contract's
`spa_fallback` / `/assets/{file}` (DO-6 WF-19), and a Starlette `Route` cannot have a path that does not start with
`/`. A `BaseRoute` subclass with a class attribute `path = "spa_fallback"` gives the exact template with no change to
AEA-23's middleware. **Prototyped by the planner on `a581a71`** (scratch copy, not committed) through `full_app` with the
real gate: records showed `spa_fallback`/200/customer, `/assets/{file}`/200/anonymous, `spa_fallback`/303/anonymous,
`<unmatched>`/404 for `/api/no-such-route`, and `/healthz` untouched.

Test helpers copied from `tests/api/web_shell_support.py` (import, never edit):

```python
def make_settings(tmp_path: Path, **changes: Any) -> Settings        # defaults web_dist_dir=tmp_path/"no-dist", require_frontend=False
class FakeSessionStore:  def issue(self, role: DemoRole = DemoRole.CUSTOMER, *, now: datetime | None = None) -> str
                         def expire(self, token: str) -> None
class FakeHeartbeat:     def __init__(self, fresh: bool = True, raises: Exception | None = None) -> None
def full_app(monkeypatch, settings, *, store, heartbeat, overrides: ContainerOverrides | None = None) -> FastAPI
    # create_app over the REAL build_container (every hunk), starters suppressed, store+heartbeat overridden
def make_client(app: FastAPI, *, peer: str = "198.51.100.7") -> TestClient   # follow_redirects=False, raise_server_exceptions=False; use as a context manager
def add_test_route(app: FastAPI, method: str, path: str, endpoint: Callable[..., Any]) -> None
def cookie_header(token: str) -> dict[str, str]
def set_cookie_lines(response) -> list[str]
def session_cookie_value(response) -> str | None
def login(client: TestClient, settings: Settings, **kwargs) -> Any       # POST /api/login with the demo pair
def error_body(response, status: int, code: str) -> dict[str, Any]
def assert_matches(response, operation_id: str) -> None                 # openapi_check.assert_response_matches
@contextmanager def captured_log() -> Iterator[io.StringIO]             # "meridian" tree through AllowListFormatter
def records_of(stream: io.StringIO, kind: str) -> list[dict[str, Any]]
def app_log_text(caplog: pytest.LogCaptureFixture) -> str               # only "meridian*" loggers
def effective_routes(app: FastAPI) -> list[RouteInfo]                   # RouteInfo(path, methods, operation_id, endpoint)
def rand_word(length: int = 16, prefix: str = "zq") -> str              # letters only
```

```python
# tests/fakes/trace.py (AEA-11)
class InMemoryTraceSink:
    @property
    def turns(self) -> tuple[RecordedTurn, ...]: ...
# src/meridian/web/app.py
@dataclass(frozen=True)
class ContainerOverrides: choice=None; structured=None; tools=None; trace: TraceSink | None = None; wall_clock=None
```

### 4.2 `src/meridian/web/frontend.py` — exact public surface

```python
"""Serve UX-4's built React app (apps/web/dist) from the API's origin (stage7/web.md §12; AEA-49).

Three routes, appended after every API route: /assets/{file} and /fonts/{file} answer files inside the build, and
spa_fallback answers index.html for every other GET page path (not /api, not /healthz). The route `path` attributes
are the templates the gate's `request` record carries (DO-6 WF-19), so no raw path or query is ever recorded.
Public before login (WEB-1 option A, D-4): GET /login and the /assets/ and /fonts/ prefixes. A missing build fails
start-up when Settings.require_frontend is true (deploy), else logs frontend_dist_missing once (WEB-30).
Files are only read, never written.
"""

FRONTEND_LOGGER: Final = "meridian.web.frontend"
DIST_MISSING_EVENT: Final = "frontend_dist_missing"
INDEX_FILE: Final = "index.html"
SPA_FALLBACK_ROUTE: Final = "spa_fallback"
ASSETS_ROUTE: Final = "/assets/{file}"
FONTS_ROUTE: Final = "/fonts/{file}"
INDEX_CACHE_CONTROL: Final = "no-cache"
ASSET_CACHE_CONTROL: Final = "public, max-age=31536000, immutable"
FONT_CACHE_CONTROL: Final = "no-cache"           # /fonts/ names are not content-hashed (see §8 item 5)
NOT_FOUND_CACHE_CONTROL: Final = "no-store"
PUBLIC_PAGE_PATH: Final = "/login"
PUBLIC_PREFIXES: Final = ("/assets/", "/fonts/")
DEFAULT_CONTENT_TYPE: Final = "application/octet-stream"
CONTENT_TYPES: Mapping[str, str] = MappingProxyType({
    ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
    ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf",
    ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".ico": "image/x-icon", ".json": "application/json", ".map": "application/json",
    ".txt": "text/plain", ".html": "text/html",
})   # explicit, so the answer never depends on the host's /etc/mime.types


class FrontendMissingError(RuntimeError):
    """Start-up refusal: require_frontend is true and Settings.web_dist_dir holds no index.html."""


def content_type_for(path: Path) -> str: ...      # CONTENT_TYPES.get(path.suffix.lower(), DEFAULT_CONTENT_TYPE)
def is_page_path(method: str, path: str) -> bool: ...   # the SPA fallback's eligibility test (steps P1–P6)


class DistDirectory:
    """One built frontend folder, resolved once. Reads only."""
    def __init__(self, root: Path) -> None: ...          # self._root = root.resolve()
    @property
    def root(self) -> Path: ...
    @staticmethod
    def present(root: Path) -> bool: ...                 # (root / INDEX_FILE).is_file()
    def read_index(self) -> bytes: ...                   # (self._root / INDEX_FILE).read_bytes(); called PER REQUEST
    def static_file(self, folder: str, relative: str) -> Path | None: ...   # steps S1–S6


class StaticFolderRoute(BaseRoute):
    """GET /<folder>/<relative>: a file inside dist/<folder>, or 404. Never the SPA fallback."""
    methods: frozenset[str] = frozenset({"GET"})
    def __init__(self, dist: DistDirectory, folder: str, template: str, cache_control: str) -> None: ...
        # sets self.path = template, self.name = f"frontend_{folder}", self._prefix = f"/{folder}/"
    def matches(self, scope: Scope) -> tuple[Match, Scope]: ...
        # Match.FULL iff scope["type"] == "http" and scope["method"] == "GET" and scope["path"].startswith(self._prefix)
        # else (Match.NONE, {})
    def url_path_for(self, name: str, /, **path_params: Any) -> URLPath: ...   # raise NoMatchFound(name, path_params)
    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None: ...


class SpaFallbackRoute(BaseRoute):
    """GET <page path>: dist/index.html with Cache-Control: no-cache."""
    path: str = SPA_FALLBACK_ROUTE
    name: str = SPA_FALLBACK_ROUTE
    methods: frozenset[str] = frozenset({"GET"})
    def __init__(self, dist: DistDirectory) -> None: ...
    def matches(self, scope: Scope) -> tuple[Match, Scope]: ...
        # Match.FULL iff scope["type"] == "http" and is_page_path(scope["method"], scope["path"]); else (Match.NONE, {})
    def url_path_for(self, name: str, /, **path_params: Any) -> URLPath: ...   # raise NoMatchFound(name, path_params)
    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None: ...


def register_frontend(container: Container, app: FastAPI) -> None: ...   # steps R1–R7 (web.md §12 signature)
```

Imports for `frontend.py` (module level): `from __future__ import annotations`, `logging`, `from collections.abc import
Mapping`, `from pathlib import Path`, `from types import MappingProxyType`, `from typing import Any, Final, cast`,
`from fastapi import FastAPI`, `from starlette.datastructures import URLPath`, `from starlette.responses import
FileResponse, JSONResponse, Response`, `from starlette.routing import BaseRoute, Match, NoMatchFound`,
`from starlette.types import Receive, Scope, Send`, `from meridian.config import Settings`,
`from meridian.web.container import Container`, `from meridian.web.middleware import HEALTHZ_PATH, WebShellState`.
(No cycle: `container.py` imports `frontend` only inside its hunk body.)

**`is_page_path(method, path)` — numbered, with the invariant each protects:**

- P1. `method != "GET"` → False. *(Only page loads fall back; a POST to a page path stays a JSON 404/401.)*
- P2. `path == "/api"` or `path.startswith("/api/")` → False. *(AC-2: never shadow the API.)*
- P3. `path == HEALTHZ_PATH` → False. *(AC-2.)*
- P4. `path in ("/assets", "/fonts")` or `path.startswith(PUBLIC_PREFIXES)` → False. *(AC-10: a missing asset never
  answers `index.html`, even if route order ever changed.)*
- P5. `"\x00" in path or "\\" in path` → False.
- P6. any non-empty segment of `path.split("/")` that starts with `"."` → False. *(AC-4: `.env`, `.git`, `.` and `..`
  answer 404, never `index.html`.)* Otherwise True.

**`DistDirectory.static_file(folder, relative)` — numbered:**

- S1. `relative == ""` → None.
- S2. `"\x00" in relative or "\\" in relative` → None.
- S3. any segment of `relative.split("/")` that is `""` or starts with `"."` → None. *(Rejects `..`, `.`, dotfiles and
  `//`; the request path is already percent-decoded by the server, so `%2e%2e` arrives here as `..`.)*
- S4. `base = (self._root / folder).resolve()`; `candidate = (base / relative).resolve()` (non-strict).
- S5. `not candidate.is_relative_to(base)` or `not candidate.is_file()` → None. *(Invariant: only regular files
  strictly inside `dist/<folder>` are ever returned; a symlink pointing out resolves outside and is refused.)*
- S6. return `candidate`.

**`StaticFolderRoute.handle`:** `relative = scope["path"][len(self._prefix):]`; `found = self._dist.static_file(folder,
relative)`; if `found is None`: `await JSONResponse({"detail": "Not Found"}, status_code=404, headers={"Cache-Control":
NOT_FOUND_CACHE_CONTROL})(scope, receive, send)`; else `await FileResponse(found, media_type=content_type_for(found),
headers={"Cache-Control": self._cache_control})(scope, receive, send)`. Log nothing.

**`SpaFallbackRoute.handle`:** `body = self._dist.read_index()` **first** (so a read failure raises before the
response starts, and AEA-23's middleware answers 500 with `error_kind`, AC-11); then `await Response(body,
status_code=200, media_type="text/html", headers={"Cache-Control": INDEX_CACHE_CONTROL})(scope, receive, send)`.
Starlette adds `; charset=utf-8`. Log nothing; never put the path or query in anything.

**`register_frontend(container, app)` — numbered:**

- R1. `shell = getattr(app.state, "web_shell", None)`; `if not isinstance(shell, WebShellState): return`. *(A bare
  `FastAPI()` — `tests/unit/web/test_container.py` builds one with a stand-in settings object — has no gate, so nothing
  is registered and `container.settings` is never read.)*
- R2. `settings = cast(Settings, container.settings)`.
- R3. `shell.public_paths.add_exact("GET", PUBLIC_PAGE_PATH)`; for each prefix in `PUBLIC_PREFIXES`:
  `shell.public_paths.add_prefix("GET", prefix)`. **Always**, build or no build (decision in §8 item 2).
- R4. `dist_dir = Path(settings.web_dist_dir)`; `if DistDirectory.present(dist_dir)`: go to R6.
- R5. Missing: if `settings.require_frontend`: `raise FrontendMissingError(f"MERIDIAN_REQUIRE_FRONTEND is true but the
  built frontend is missing: no {INDEX_FILE} in MERIDIAN_WEB_DIST_DIR={settings.web_dist_dir}")`. Else
  `logging.getLogger(FRONTEND_LOGGER).warning(DIST_MISSING_EVENT)` (message exactly `frontend_dist_missing`, no
  arguments) and `return` — nothing mounted.
- R6. `dist = DistDirectory(dist_dir)`.
- R7. Append, in this order: `app.router.routes.append(StaticFolderRoute(dist, "assets", ASSETS_ROUTE,
  ASSET_CACHE_CONTROL))`, `app.router.routes.append(StaticFolderRoute(dist, "fonts", FONTS_ROUTE,
  FONT_CACHE_CONTROL))`, `app.router.routes.append(SpaFallbackRoute(dist))`. Provide no container key. *(Invariant:
  these are the last routes at start-up, after every API hunk; and P2–P4 make shadowing impossible even if a later
  route is appended.)*

### 4.3 The `web/container.py` hunk — exact new body

```python
def register_frontend(container: Container, app: FastAPI, *, settings: Any, limits: Limits) -> None:
    """AEA-49 frontend: serves apps/web/dist; runs last so its SPA fallback never shadows an API route (web.md §12).

    Delegates to web/frontend.py's register_frontend(container, app): registers the public paths GET /login, /assets/
    and /fonts/ (WEB-1 option A), then mounts Settings.web_dist_dir read-only (/assets/{file}, /fonts/{file},
    spa_fallback). A missing build raises FrontendMissingError when Settings.require_frontend is true, else logs
    frontend_dist_missing once and mounts nothing (WEB-30). An app create_app did not build has no web shell, so this
    does nothing.
    """
    from meridian.web.frontend import register_frontend as mount_frontend

    mount_frontend(container, app)
```

The docstring must keep the string `AEA-49` and must **not** contain `No-op until` (AEA-01's
`test_every_register_stub_present` treats a docstring with `No-op until` as an unfilled stub). Do not touch the
module-level imports (`test_container_imports_only_policy_limits`).

## 5. Steps

0. **Which loop applies.** `git log --oneline main..HEAD`. If a commit titled like `test(web): frozen failing tests for
   AEA-49 …` exists (orchestrator applied `risk::security`): the files it added are **frozen** — do not edit them; read
   them, and if a frozen test contradicts this plan, stop and report (do not change either). Skip steps 4–7's
   *writing* and only make the frozen tests pass. Otherwise you write §7's tests yourself in steps 4–7.
   Setup: `export UV_LINK_MODE=hardlink`; `uv run python -c "import meridian.web.app"` (import check; no baseline
   suite).
1. **Create `src/meridian/web/frontend.py`** with exactly §4.2 (constants, `FrontendMissingError`, `content_type_for`,
   `is_page_path`, `DistDirectory`, `StaticFolderRoute`, `SpaFallbackRoute`, `register_frontend`). No `assert` in
   production code (ruff `S101`). Check: `uv run ruff check src/meridian/web/frontend.py && uv run mypy
   src/meridian/web/frontend.py`.
2. **Fill the hunk** in `src/meridian/web/container.py` with §4.3. Check: `uv run pytest -q
   tests/unit/web/test_container.py tests/unit/test_import_direction.py` (must stay green).
3. **Smoke the existing web tests** that build the full container (they use `make_settings`, whose default
   `web_dist_dir` is a missing folder, so they now log one warning and mount nothing): `uv run pytest -q tests/api
   tests/unit/web`. All must stay green.
4. **Create `tests/api/frontend_support.py`** (§7.1).
5. **Create `tests/api/test_web_frontend.py`** (§7.2); run it until green.
6. **Create `tests/capture/test_cap11_page_serving.py`** (§7.3); run it until green.
7. **Create `tests/journeys/j1/test_aea_49.py`** (§7.4); run `uv run pytest -q -m journey
   tests/journeys/j1/test_aea_49.py`.
8. **Fast gates and affected tests** (§7.5), cheapest first; then commit 1 with explicit paths:
   `git add src/meridian/web/frontend.py src/meridian/web/container.py tests/api/frontend_support.py
   tests/api/test_web_frontend.py tests/capture/test_cap11_page_serving.py tests/journeys/j1/test_aea_49.py`
   (omit any frozen file already committed). Message `feat(web): serve apps/web/dist with SPA fallback and public
   login assets (AEA-49)`, last line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
9. **Context rows and journey record (AC-12, AC-9)** — commit 2, naming commit 1's short sha as `<sha>`:
   - `.claude/reference/area-map.md` line 35 (row A8): in the *Owns* cell change "AEA-49 serves `apps/web/dist` with
     fallback to `index.html` (planned)" to "AEA-49 serves `apps/web/dist` with fallback to `index.html`
     (`web/frontend.py`, `register_frontend`)"; in the status cell, before "the rest planned", insert "AEA-49
     (`<sha>`): `web/frontend.py` + the `register_frontend` hunk (static mount, SPA fallback, public `/login`,
     `/assets/`, `/fonts/`) built; ". Line 50: change "AEA-49 (`web/frontend.py`, A8) serves the built
     `apps/web/dist` with a fallback to `index.html` (**planned**)" to "… (**built**, AEA-49 `<sha>`)". Touch nothing
     else in the file.
   - `.claude/state/icm-progress.md`: add one row after the last *Routes verified* row (≤ 400 characters):
     `| Routes verified against code and tests | provisional | <date>: area map A8 → web/frontend.py and the
     register_frontend hunk checked against tests/api/test_web_frontend.py, tests/capture/test_cap11_page_serving.py
     (AEA-49, <sha>; <N> pass) | Integrated level when AEA-57 and AEA-58 land |`; and prepend "AEA-49 frontend
     serving (routes row); earlier, " after "Last reconciled: <date> — ".
   - `docs/design/code-design.md` line 303: append `   built AEA-49 <sha>` to the `frontend.py` line (same style as
     line 272's `built AEA-20 2bcb8fb`); line 316: change "AEA-49 serves its dist/ with fallback to index.html
     (planned)" to "AEA-49 serves its dist/ with fallback to index.html (built: web/frontend.py, register_frontend
     hunk)"; §8 row at line 668: change "AEA-49 (A8/A12) serves `apps/web/dist` with fallback to `index.html`
     (planned)" to "AEA-49 (A8) serves `apps/web/dist` with fallback to `index.html` from `web/frontend.py` through
     its own `register_frontend()` hunk in `web/container.py` (built)".
   - `docs/testing/journeys/<YYYY-MM-DD>-AEA-49.md` (date from `date +%F`), the integrated-journeys §4 table:
     Claim (AEA-49 frontend serving AC-1…AC-12; J-1 HTTP steps at mock level), Level `mock-tested`, Tested revision
     `<sha>`, Environment (VPS, Python 3.12, `uv`, FastAPI TestClient in process, real `create_app` +
     `build_container` + AEA-23 gate, `FakeSessionStore`/`FakeHeartbeat` doubles, temp fixture dist, no server
     port, no browser, no model), Command (the §7.5 commands), Result (counts from the run), Evidence location
     (GitLab issue #49 comment; this file), Remaining limitations (real `StaffSessionStore` is AEA-44; no browser;
     real `apps/web/dist` not exercised — fixture only; `/favicon.svg` answers `index.html`/303 per web.md §12, UX
     audit C2; uvicorn must run `--no-access-log`, AEA-50), Blocked by (AEA-57 harness; AEA-58 browser J-1),
     Journeys that will exercise this code (J-1, J-AUTH; every browser journey).
   - Run `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` and fix any FAIL in your rows only.
   - `git add .claude/reference/area-map.md .claude/state/icm-progress.md docs/design/code-design.md
     docs/testing/journeys/<date>-AEA-49.md`; message `docs(AEA-49): journey record and context rows for
     web/frontend.py`, same Co-Authored-By last line.
10. **Report**: per AC, verified / not verified with the command and the printed evidence.

**Must not:** edit `middleware.py`, `app.py`, `deps.py`, `logging.py` or any route/schema; add a `Mount`, `StaticFiles`
or `app.mount`; register any public path other than the three in R3; serve any root file by name (e.g.
`/favicon.svg`) — that is a web.md §12 change; log the path, query or cookie anywhere; read `index.html` once at start
and cache it (AC-11 needs the per-request read); build `apps/web` or read `apps/web/dist` in a test; run `npm`;
bind any port (TestClient only; never 4019 or 5184); `git add -A`; force-push; read `.env`.

## 6. Data and fixtures

Synthetic only, built per test in `tmp_path` by `build_fixture_dist()` (§7.1). Distinctive values are letters only
(no digit runs that could look like a code, card or phone number). The case reference `MHC-C-0007` is the
SCREEN_SPECS demo reference used by the ticket. Source sample: the real build's shape (`apps/web/dist/index.html` has a
`<script type="module" src="/assets/index-<hash>.js">` and a stylesheet link; `dist/assets/` holds `.js`, `.css`,
`.woff`, `.woff2`; `dist/fonts/` holds `LICENSES/`), read once by the planner, never by the tests.

## 7. Tests

Commands use `uv run`; never more than `-n 2` workers. No test reads `.env`, calls a model or opens a socket.

### 7.1 `tests/api/frontend_support.py` (helpers)

```python
INDEX_MARKER = "zqfixtureindexpage"
HASHED_ASSET = "/assets/index-AbCdEf.js"
INDEX_HTML = (
    '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>' + INDEX_MARKER + "</title>"
    '<script type="module" crossorigin src="' + HASHED_ASSET + '"></script>'
    '<link rel="stylesheet" href="/assets/app.css"><link rel="preload" href="/fonts/f.woff2" as="font">'
    '</head><body><div id="root"></div></body></html>'
)
FILES: Mapping[str, bytes] = {
    "assets/app.js": b"console.log('zqappscript');\n",
    "assets/index-AbCdEf.js": b"export const zq = 'zqhashedscript';\n",
    "assets/app.css": b"body{margin:0}\n",
    "fonts/f.woff2": b"wOF2zqfixturefont",
    "assets/.env": b"ZQ_DOTFILE=zqdotfilesecret\n",
    ".env": b"ZQ_ROOT_DOTFILE=zqrootdotfile\n",
    "favicon.svg": b"<svg xmlns='http://www.w3.org/2000/svg'/>",
}
OUTSIDE_MARKER = "zqoutsidepyproject"
SCREEN_PATHS = ("/", "/demo", "/demo/inbox", "/role", "/staff/queue", "/staff/cases/MHC-C-0007",
                "/staff/oversight", "/staff/flags", "/staff/owner", "/monitoring", "/eval", "/login")

def build_fixture_dist(base: Path) -> Path:
    """Write base/"dist" (index.html + FILES) and base/"pyproject.toml" holding OUTSIDE_MARKER (the file
    /assets/../../pyproject.toml would reach). Returns the dist path."""

@dataclass
class FrontendApp:
    app: FastAPI; settings: Settings; store: FakeSessionStore; dist: Path | None

def frontend_app(monkeypatch, tmp_path: Path, *, with_dist: bool = True, require_frontend: bool = False,
                 overrides: ContainerOverrides | None = None) -> FrontendApp:
    """make_settings(tmp_path, web_dist_dir=<built dist or tmp_path/"no-dist">, require_frontend=...) then
    full_app(monkeypatch, settings, store=FakeSessionStore(), heartbeat=FakeHeartbeat(), overrides=overrides)."""

def login_redirect(path_and_query: str, reason: str = "none") -> str:
    """'/login?return_to=' + urllib.parse.quote(path_and_query, safe='') + '&reason=' + reason
    e.g. '/staff/queue' -> '/login?return_to=%2Fstaff%2Fqueue&reason=none' (same encoding as the gate)."""

@dataclass(frozen=True)
class RawResponse:
    status: int; headers: dict[str, str]; set_cookies: list[str]; body: bytes

def raw_get(client: TestClient, raw_path: str, *, token: str | None = None) -> RawResponse:
    """Call the app's ASGI callable directly through client.portal (the client must be entered), so dot segments
    reach the server un-normalised (httpx2 rewrites '/assets/../../x' to '/x' before sending; measured).
    scope: {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET", "scheme": "http",
    "path": <part before '?'>, "raw_path": <same, encoded>, "root_path": "", "query_string": <part after '?'>,
    "headers": [(b"host", b"testserver")] + [(b"cookie", b"mhc_session=<token>")] if token,
    "client": ("198.51.100.7", 50000), "server": ("testserver", 80)}; collect the sent messages; headers lower-cased."""

def install_socket_guard(monkeypatch) -> list[Any]:
    """Copy of the pattern in tests/api/test_auth.py (lines 360-378): patch socket.socket.connect and
    socket.create_connection; any address whose host is not in {"127.0.0.1", "::1", "localhost"} is appended to the
    returned list and raises AssertionError. Returns the list (empty = no outbound connect)."""
```

### 7.2 `tests/api/test_web_frontend.py`

Each test builds its own app with `frontend_app(...)`, enters `make_client(h.app)`, signs in with
`token = h.store.issue()` + `cookie_header(token)`, and prints the evidence named in the AC.

- `test_spa_fallback_and_assets` (AC-1, AC-6): snapshot `{path: (bytes, st_mtime_ns)}` of every file under the
  fixture dist; signed in, each of the 12 `SCREEN_PATHS` → 200, `content-type` starts with `text/html`, body ==
  `INDEX_HTML` bytes, `cache-control == "no-cache"`; `/assets/app.js` → 200, body == `FILES["assets/app.js"]`,
  content type `text/javascript` (split on `;`); `/fonts/f.woff2` → 200, bytes equal, content type `font/woff2`.
  After the requests the snapshot is unchanged and no file was added. Print "12 paths + 2 files".
- `test_api_and_healthz_not_shadowed` (AC-2): before entering the client `add_test_route(h.app, "GET",
  "/api/test/ping", lambda: {"pong": True})`. Signed in: `/api/test/ping` → 200 `{"pong": True}`;
  `/api/no-such-route` → 404, content type `application/json`, body `{"detail": "Not Found"}`, `INDEX_MARKER` not in
  text; `/api` → 404 JSON; `/healthz` → 200 `{"status": "ok"}`; `client.post("/staff/queue", …)` → status != 200 and
  `INDEX_MARKER` not in text. Print content type and body per path.
- `test_pages_behind_login` (AC-3): unsigned: `/login`, `/assets/app.js`, `/fonts/f.woff2` → 200; every other path in
  `SCREEN_PATHS` → 303 with `location == login_redirect(path)` and `INDEX_MARKER` not in body; a query case:
  `/staff/cases/MHC-C-0007?tab=brief` → `login_redirect("/staff/cases/MHC-C-0007?tab=brief")`. Expired:
  `t = h.store.issue(); h.store.expire(t)`; `/staff/queue` with `cookie_header(t)` → 303,
  `location == login_redirect("/staff/queue", "expired")`, one `set_cookie_lines` entry starts with `mhc_session=;`
  and contains `Max-Age=0`. `/api/staff/queue` unsigned → `error_body(r, 401, "UNAUTHENTICATED")` with
  `details == {"reason": "none"}`, then `assert_matches(r, "getQueue")`. Also assert `h.app.state.web_shell.
  public_paths.entries()` ⊇ `{("exact","GET","/login"), ("prefix","GET","/assets/"), ("prefix","GET","/fonts/")}` and
  contains no other `GET` entry except `("exact","GET","/healthz")`. Print status and Location per path.
- `test_no_path_traversal_or_open_redirect` (AC-4): through `raw_get`, signed in and signed out:
  `/assets/../../pyproject.toml`, `/assets/%2e%2e/%2e%2e/pyproject.toml` via the HTTP client (encoded dots survive
  httpx2 and are decoded by the server), `/assets/.env`, `/fonts/../index.html`, `/.env`, `/../pyproject.toml`.
  Every response: `OUTSIDE_MARKER`, `zqdotfilesecret`, `zqrootdotfile` absent from the body; status 404 when signed in;
  signed out: 404 for the `/assets/`/`/fonts/` paths (public prefixes) and 303 for `/.env` and `/../pyproject.toml`.
  Open redirect: `client.get("/login?return_to=//evil.example")` unsigned → 200, no `location` header;
  `raw_get(client, "//evil.example")` unsigned → 303 and `location` starts with `/login` and does not contain
  `evil.example`; `raw_get(client, "/\\evil.example")` unsigned → 303, same check. Every `location` seen in this test
  starts with `/` and not `//`. Print each path's status.
- `test_missing_dist` (AC-5): (a) `frontend_app(…, with_dist=False)`, `add_test_route(…, "/api/test/ping", …)`,
  `caplog.set_level(logging.WARNING, logger="meridian.web.frontend")`; enter the client: exactly one caplog record with
  `name == "meridian.web.frontend"`, `levelno == logging.WARNING`, `getMessage() == "frontend_dist_missing"`;
  `/api/test/ping` signed → 200; `/staff/queue` signed → 404, JSON `{"detail": "Not Found"}`; `/staff/queue` unsigned
  → 303 (gate still on); `/login` unsigned → 404 JSON (no redirect loop); no route in `effective_routes(h.app)` has
  path `spa_fallback`, `/assets/{file}` or `/fonts/{file}`. (b) a dist folder with `assets/app.js` but **no**
  `index.html` → same single warning, nothing mounted. (c) `frontend_app(…, with_dist=False,
  require_frontend=True)`: `with pytest.raises(FrontendMissingError) as err: with make_client(h.app): pass`;
  `"MERIDIAN_REQUIRE_FRONTEND" in str(err.value)` and `str(tmp_path / "no-dist") in str(err.value)`. Print the
  warning record, the 404 body and the error text. (Prototyped: the lifespan error propagates out of `TestClient.
  __enter__` unchanged.)
- `test_cache_headers_and_missing_asset_404` (AC-10): signed and unsigned: `/login` → `no-cache`; signed `/`,
  `/staff/queue` → `no-cache`; `/assets/app.js` and `HASHED_ASSET` → `public, max-age=31536000, immutable`;
  `/assets/missing.js` and `/fonts/missing.woff2` → 404, content type `application/json`, `INDEX_MARKER` not in body,
  in both states. Print headers per path.
- `test_example_pair` (worked pair): unsigned `/staff/queue` → 303 `/login?return_to=%2Fstaff%2Fqueue&reason=none`
  (literal string); unsigned `/login` → 200 `INDEX_HTML`; unsigned `HASHED_ASSET` and `/fonts/f.woff2` → 200; then
  `login(client, h.settings)` → 200, `token = session_cookie_value(resp)`, `client.cookies.clear()`; with
  `cookie_header(token)`: `/staff/cases/MHC-C-0007` → 200 `INDEX_HTML`; `/api/staff/cases/MHC-C-0007` → content type
  `application/json` and `INDEX_MARKER` not in body (status is 404 today, 403 once AEA-45 lands — do not assert it);
  `/api/no-such-route` → JSON 404.

### 7.3 `tests/capture/test_cap11_page_serving.py`

All three use `frontend_app(monkeypatch, tmp_path, overrides=ContainerOverrides(trace=sink))` with
`sink = InMemoryTraceSink()`, `captured_log()` entered **after** the client (so only request-time records are seen),
and `records_of(stream, "request")`.

- `test_page_requests_recorded` (AC-7): six calls in this order: signed `/`, signed
  `/staff/cases/MHC-C-0007?tab=brief`, signed `/assets/app.js`, unsigned `/`, unsigned deep link, unsigned
  `/assets/app.js`. Exactly six `request` records, zipped in order with the responses: `record["request_id"] ==
  response.headers["X-Request-ID"]`; `route` == `spa_fallback`, `spa_fallback`, `/assets/{file}`, `spa_fallback`,
  `spa_fallback`, `/assets/{file}`; `status` == 200, 200, 200, 303, 303, 200; `caller_role` == `customer`,
  `customer`, `anonymous`, `anonymous`, `anonymous`, `anonymous` (the third is `anonymous` because AEA-23's gate does
  not resolve the session on a public path; §8 item 4). Print the six records.
- `test_no_raw_path_query_or_cookie` (AC-8): run the same six calls with `caplog.set_level(logging.DEBUG)`. Build one
  haystack: the allow-list stream text + `app_log_text(caplog)` + `repr(r.__dict__)` for every caplog record whose
  name starts with `meridian` + `repr(sink.turns)`. Assert 0 hits for each of `/staff/cases/MHC-C-0007`,
  `MHC-C-0007`, `%2Fstaff%2Fcases`, `tab=brief`, and the session token. Print the hit count per value.
- `test_wf19_status_values_and_no_outbound` (AC-11): `outbound = install_socket_guard(monkeypatch)` before building
  the app. Calls: the six of AC-7, unsigned `/staff/queue` (303), `/assets/missing.js` signed and unsigned (404). For
  every `request` record: `status == response.status_code` and `"error_kind" not in record`. Then
  `monkeypatch.setattr(DistDirectory, "read_index", raising)` where `def raising(self: DistDirectory) -> bytes: raise
  OSError("zqreadfailure")`; signed `/` → 500, body `{"request_id": <X-Request-ID>}`, `zqreadfailure` not in body;
  its record has `status == 500` and a non-empty `error_kind` (expected `OSError`). Finally `outbound == []`. Print
  the (response status, record status, error_kind) triple per call and the outbound count.

### 7.4 `tests/journeys/j1/test_aea_49.py` (AC-9, the single `[journey]` criterion)

Module docstring states: "Level: `mock-tested` (real `create_app`, `build_container` and AEA-23 gate; doubles for the
login session store and heartbeat; fixture dist; TestClient, no server, no browser). Blocked by: AEA-57 (journey
harness: real server, disposable DB, scripted model), AEA-44 (real StaffSessionStore), AEA-58 (browser J-1)."
`pytestmark = pytest.mark.journey`. One test, `test_j1_login_gate_and_built_app_over_http(monkeypatch, tmp_path)`:
signed out `/` → 303 `login_redirect("/")`; `/staff/queue` → 303 `login_redirect("/staff/queue")`; `/login` → 200
`INDEX_HTML`; every `/assets/…` and `/fonts/…` URL found in `INDEX_HTML` (regex `(?:src|href)="(/(?:assets|fonts)/[^"]+)"`)
→ 200 without a cookie; `login(client, h.settings)` → 200, token via `session_cookie_value`, `client.cookies.clear()`;
with the cookie: `/staff/cases/MHC-C-0007` → 200 `INDEX_HTML`; `GET /api/chat/sessions` → content type
`application/json` and `INDEX_MARKER` not in body (404 today; 405 once AEA-40 registers the POST route). When AEA-57's
`tests/journeys/support/` lands, AEA-57/AEA-58 move this to the real server; this ticket does not wait for it.

### 7.5 Checks (run cheapest first; stop at the first red)

| Check | Command | Passing looks like |
|---|---|---|
| Lint + format | `uv run ruff check src tests && uv run ruff format --check src tests` | no findings |
| Type check | `uv run mypy` (config `files`: `src/meridian`, `tests`, `eval`) | `Success` |
| New tests (iterate) | `uv run pytest -q tests/api/test_web_frontend.py tests/capture/test_cap11_page_serving.py` | 10 passed (7 + 3) |
| Journey (AC-9) | `uv run pytest -q -m journey tests/journeys/j1/test_aea_49.py` | 1 passed |
| Affected tests (`container.py` and `create_app` users; `grep -rlE "meridian\.web\.(container\|app\|frontend)\|web_shell_support\|ops_support\|handoff_support" tests`) | `uv run pytest -q tests/api tests/capture tests/unit/web tests/services tests/adapters/test_repos_ops.py tests/unit/services/test_health.py tests/unit/test_import_direction.py tests/unit/test_skeleton.py tests/unit/test_affected_journeys.py tests/unit/test_config.py` (optionally `uv run --with pytest-xdist pytest -n 2 …`) | all pass, 0 failed |
| Affected journeys | `uv run python -m tests.journeys.affected --base main` | exit 0; lists at least `tests/journeys/j1/test_aea_49.py` |
| AC-6 | `git diff --name-only main...HEAD \| grep '^apps/web/'` and `git status --short apps/web` | both print nothing |
| AC-12 | `git diff --stat main...HEAD` | only the owned files of §2 |
| Context | `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` | no FAIL |

The full suite is **not** required (rule `build-loop-test-scope`: a hunk body in `container.py` is not a cross-cutting
fixture, setting or dependency change).

## 8. Risks and requests

1. **Collisions.** `web/container.py` — own hunk only; every wave-2 sibling edits its own function, so a textual
   merge conflict is possible only on adjacent lines (the hunk is the last function before `build_container`). The
   three context docs (`area-map.md` row A8, `icm-progress.md`, `code-design.md`) are edited by every route ticket;
   edits are row-local, expect a trivial rebase. `tests/capture/` — the slice-plan §3 collision row lists 51, 52, 53,
   24, 50; AEA-49's file name is unique (`test_cap11_page_serving.py`). **Request to the orchestrator:** add 49 to that
   row in `docs/plans/slice-plan.md` (the ticket asks for it; the slice plan is not this ticket's file).
2. **Decision made here (engineering): the three public paths are registered even when no build is mounted.** Without
   `/login` public, a no-build local server would answer an unsigned `/login` with a 303 to `/login?…`, a redirect
   loop; with it, the visitor gets an honest JSON 404. Nothing extra is exposed (no route serves those paths when no
   build exists). Reversible in one line.
3. **WF-19 template for fonts.** DO-6 names `spa_fallback` and `/assets/{file}`; this plan records `/fonts/{file}`
   for the `/fonts/` prefix the same contract requires to be served (recording fonts as `/assets/{file}` would be
   false). **Request to the integrator:** add `/fonts/{file}` to the WF-19 row in `docs/design/observability-contract.md`
   (not this ticket's file). No signed UI contract changes.
4. **`caller_role` on public paths is `anonymous` even when signed in.** AEA-23's gate skips session resolution for
   public paths, so a signed-in `/login` or asset request records `anonymous`. AC-7 is met ("anonymous when signed
   out" holds; signed-in page records carry the role). Changing it is AEA-23's gate logic, out of scope.
5. **`/fonts/` cache header is `no-cache`, not immutable.** AC-10 sets the immutable rule for `/assets/` only; the
   real build keeps hashed `.woff`/`.woff2` under `/assets/` and only `LICENSES/` under `/fonts/`, whose names are not
   content-hashed. Engineering choice, stated so the reviewer can overrule.
6. **`/favicon.svg`** sits at the build root, so per web.md §12 it answers `index.html` when signed in and 303 when
   signed out (UX audit C2, owned by the UX session; recorded for AEA-55's run). Kept as contracted.
7. **Journey level.** AEA-57's harness is not on `main`, so AC-9's record is `mock-tested` with *Blocked by* AEA-57
   (the ticket allows exactly this). AEA-58 owns the browser J-1.
8. **uvicorn access log** prints raw paths; AEA-50 must start uvicorn with `--no-access-log` (already in AEA-23's
   record). Not this ticket's file.
9. **Security review focus (for `security-privacy-agent` at the wave-2 merge):** `is_page_path`, `static_file` S1–S6,
   the public list in R3, and that no public prefix can reach anything but files inside `dist/assets` or
   `dist/fonts`.

## 9. Readiness

**READY.** Blockers met on `a581a71`: AEA-23 merged; UX-4 signed; AEA-01 stub present; AEA-02 settings present;
WEB-1 answered A (D-4). No `NEEDS-DECISION`, no `BLOCKED-ON` (AEA-57 limits only the journey's evidence level, which
the ticket allows). Gates: none paid, none live, none human.
