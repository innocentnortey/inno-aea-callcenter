"""Serve UX-4's built React app (apps/web/dist) from the API's origin (stage7/web.md §12; AEA-49).

Three routes, appended after every API route: /assets/{file} and /fonts/{file} answer files inside the build, and
spa_fallback answers index.html for every other GET page path (not /api, not /healthz). The route `path` attributes
are the templates the gate's `request` record carries (DO-6 WF-19), so no raw path or query is ever recorded.
Public before login (WEB-1 option A, D-4): GET /login and the /assets/ and /fonts/ prefixes. A missing build fails
start-up when Settings.require_frontend is true (deploy), else logs frontend_dist_missing once (WEB-30).
Files are only read, never written.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, cast

from fastapi import FastAPI
from starlette.datastructures import URLPath
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import BaseRoute, Match, NoMatchFound
from starlette.types import Receive, Scope, Send

from meridian.config import Settings
from meridian.web.container import Container
from meridian.web.middleware import HEALTHZ_PATH, WebShellState

FRONTEND_LOGGER: Final = "meridian.web.frontend"
DIST_MISSING_EVENT: Final = "frontend_dist_missing"
INDEX_FILE: Final = "index.html"
SPA_FALLBACK_ROUTE: Final = "spa_fallback"
ASSETS_ROUTE: Final = "/assets/{file}"
FONTS_ROUTE: Final = "/fonts/{file}"
INDEX_CACHE_CONTROL: Final = "no-cache"
ASSET_CACHE_CONTROL: Final = "public, max-age=31536000, immutable"
FONT_CACHE_CONTROL: Final = "no-cache"  # /fonts/ names are not content-hashed
NOT_FOUND_CACHE_CONTROL: Final = "no-store"
PUBLIC_PAGE_PATH: Final = "/login"
PUBLIC_PREFIXES: Final = ("/assets/", "/fonts/")
DEFAULT_CONTENT_TYPE: Final = "application/octet-stream"
CONTENT_TYPES: Mapping[str, str] = MappingProxyType(
    {
        ".js": "text/javascript",
        ".mjs": "text/javascript",
        ".css": "text/css",
        ".woff2": "font/woff2",
        ".woff": "font/woff",
        ".ttf": "font/ttf",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".ico": "image/x-icon",
        ".json": "application/json",
        ".map": "application/json",
        ".txt": "text/plain",
        ".html": "text/html",
    }
)  # explicit, so the answer never depends on the host's /etc/mime.types


class FrontendMissingError(RuntimeError):
    """Start-up refusal: require_frontend is true and Settings.web_dist_dir holds no index.html."""


def content_type_for(path: Path) -> str:
    """The explicit content type for a file's suffix."""
    return CONTENT_TYPES.get(path.suffix.lower(), DEFAULT_CONTENT_TYPE)


def is_page_path(method: str, path: str) -> bool:
    """Whether the SPA fallback may answer this request (steps P1 to P6)."""
    if method != "GET":
        return False
    if path == "/api" or path.startswith("/api/"):
        return False
    if path == HEALTHZ_PATH:
        return False
    if path in ("/assets", "/fonts") or path.startswith(PUBLIC_PREFIXES):
        return False
    if "\x00" in path or "\\" in path:
        return False
    return not any(segment.startswith(".") for segment in path.split("/") if segment)


class DistDirectory:
    """One built frontend folder, resolved once. Reads only."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    @property
    def root(self) -> Path:
        return self._root

    @staticmethod
    def present(root: Path) -> bool:
        return (root / INDEX_FILE).is_file()

    def read_index(self) -> bytes:
        return (self._root / INDEX_FILE).read_bytes()

    def static_file(self, folder: str, relative: str) -> Path | None:
        """A regular file strictly inside dist/<folder>, else None (steps S1 to S6)."""
        if relative == "":
            return None
        if "\x00" in relative or "\\" in relative:
            return None
        if any(segment == "" or segment.startswith(".") for segment in relative.split("/")):
            return None
        base = (self._root / folder).resolve()
        candidate = (base / relative).resolve()
        if not candidate.is_relative_to(base) or not candidate.is_file():
            return None
        return candidate


class StaticFolderRoute(BaseRoute):
    """GET /<folder>/<relative>: a file inside dist/<folder>, or 404. Never the SPA fallback."""

    methods: frozenset[str] = frozenset({"GET"})

    def __init__(self, dist: DistDirectory, folder: str, template: str, cache_control: str) -> None:
        self._dist = dist
        self._folder = folder
        self._cache_control = cache_control
        self.path = template
        self.name = f"frontend_{folder}"
        self._prefix = f"/{folder}/"

    def matches(self, scope: Scope) -> tuple[Match, Scope]:
        if scope["type"] == "http" and scope["method"] == "GET" and scope["path"].startswith(self._prefix):
            return Match.FULL, {}
        return Match.NONE, {}

    def url_path_for(self, name: str, /, **path_params: Any) -> URLPath:
        raise NoMatchFound(name, path_params)

    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
        relative = scope["path"][len(self._prefix) :]
        found = self._dist.static_file(self._folder, relative)
        if found is None:
            not_found = JSONResponse(
                {"detail": "Not Found"},
                status_code=404,
                headers={"Cache-Control": NOT_FOUND_CACHE_CONTROL},
            )
            await not_found(scope, receive, send)
            return
        served = FileResponse(
            found,
            media_type=content_type_for(found),
            headers={"Cache-Control": self._cache_control},
        )
        await served(scope, receive, send)


class SpaFallbackRoute(BaseRoute):
    """GET <page path>: dist/index.html with Cache-Control: no-cache."""

    path: str = SPA_FALLBACK_ROUTE
    name: str = SPA_FALLBACK_ROUTE
    methods: frozenset[str] = frozenset({"GET"})

    def __init__(self, dist: DistDirectory) -> None:
        self._dist = dist

    def matches(self, scope: Scope) -> tuple[Match, Scope]:
        if scope["type"] == "http" and is_page_path(scope["method"], scope["path"]):
            return Match.FULL, {}
        return Match.NONE, {}

    def url_path_for(self, name: str, /, **path_params: Any) -> URLPath:
        raise NoMatchFound(name, path_params)

    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
        body = self._dist.read_index()  # before any response starts, so a failure becomes the gate's 500
        page = Response(
            body,
            status_code=200,
            media_type="text/html",
            headers={"Cache-Control": INDEX_CACHE_CONTROL},
        )
        await page(scope, receive, send)


def register_frontend(container: Container, app: FastAPI) -> None:
    """Register the public paths and mount the built frontend (steps R1 to R7)."""
    shell = getattr(app.state, "web_shell", None)
    if not isinstance(shell, WebShellState):
        return
    settings = cast(Settings, container.settings)
    shell.public_paths.add_exact("GET", PUBLIC_PAGE_PATH)
    for prefix in PUBLIC_PREFIXES:
        shell.public_paths.add_prefix("GET", prefix)
    dist_dir = Path(settings.web_dist_dir)
    if not DistDirectory.present(dist_dir):
        if settings.require_frontend:
            raise FrontendMissingError(
                "MERIDIAN_REQUIRE_FRONTEND is true but the built frontend is missing: "
                f"no {INDEX_FILE} in MERIDIAN_WEB_DIST_DIR={settings.web_dist_dir}"
            )
        logging.getLogger(FRONTEND_LOGGER).warning(DIST_MISSING_EVENT)
        return
    dist = DistDirectory(dist_dir)
    app.router.routes.append(StaticFolderRoute(dist, "assets", ASSETS_ROUTE, ASSET_CACHE_CONTROL))
    app.router.routes.append(StaticFolderRoute(dist, "fonts", FONTS_ROUTE, FONT_CACHE_CONTROL))
    app.router.routes.append(SpaFallbackRoute(dist))
