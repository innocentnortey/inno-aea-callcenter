"""The deployed factory (AEA-50, WF-13): `uvicorn --factory scripts.serve:create_deployed_app`.

It calls `create_app()` with no arguments (web.md section 15: nothing is overridden) and wraps its lifespan so the start
writes one `deploy_record`, checks the retrieval index, loads the committed eval reports, and marks the record
`completed` once `/healthz` answers 200. It adds no route (AC-14).
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import logging
import os
import uuid
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Final, Protocol, runtime_checkable

import httpx
from fastapi import FastAPI

from meridian.adapters.retrieval_fastembed import FastembedIndex
from meridian.adapters.sqlite.repos_ops import DeployRecord, RunStatus
from meridian.adapters.tracing_langfuse import NullTraceSink
from meridian.config import Settings
from meridian.services.health import load_eval_reports
from meridian.web import deps
from meridian.web.app import create_app
from meridian.web.container import Container, Key
from meridian.web.middleware import HEALTHZ_PATH
from scripts.agent_version import ROOT, resolve_git_sha

REPORTS_DIR: Final = ROOT / "eval" / "reports"
COMPLETE_WITHIN_S: Final = 60.0  # [A] /healthz must answer 200 within this, else status "incomplete"
POLL_EVERY_S: Final = 0.5  # [A]
TRACE_KEY: Final = Key[Any]("trace")  # AEA-19's register_tracing key


class IndexNotReady(RuntimeError):
    """The retrieval index failed its readiness check; the deploy does not go live."""


@runtime_checkable
class _ExportStateReader(Protocol):
    """AEA-19 follow-up: `LangfuseTraceSink.export_on` (plan R-2)."""

    @property
    def export_on(self) -> bool: ...


def trace_export_on(sink: object) -> bool | None:
    """Null sink: off. A sink that reports its state: that state. Otherwise unknown (NULL)."""
    if isinstance(sink, NullTraceSink):
        return False
    if isinstance(sink, _ExportStateReader):
        return bool(sink.export_on)
    return None


def config_hash(settings: Settings, index_dir: Path) -> str:
    """SHA-256 over non-secret configuration and the index manifest hash; no secret value is unwrapped."""
    try:
        record = json.loads((index_dir / "index_record.json").read_text(encoding="utf-8"))
        manifest_hash = record["manifest_hash"]
    except (OSError, ValueError, KeyError, TypeError):
        manifest_hash = None
    payload = {
        "models": dict(settings.role_model_map()),
        "cookie_secure": settings.cookie_secure,
        "trust_proxy_headers": settings.trust_proxy_headers,
        "require_frontend": settings.require_frontend,
        "langfuse_configured": settings.langfuse_complete(),
        "index_manifest_hash": manifest_hash,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def deploy_id_from(environ: Mapping[str, str]) -> str:
    return environ.get("RAILWAY_DEPLOYMENT_ID", "").strip() or str(uuid.uuid4())


class DeployStartup:
    def __init__(
        self, container: Container, settings: Settings, deploy_id: str, environ: Mapping[str, str]
    ) -> None:
        self.container = container
        self.settings = settings
        self.deploy_id = deploy_id
        self.environ = environ

    def begin(self) -> None:
        """Sync; run in a worker thread. The row exists before anything that can fail."""
        uow = self.container.get(deps.UOW_FACTORY)
        wall = self.container.get(deps.WALL_CLOCK)
        sink = self.container.get(TRACE_KEY)
        record = DeployRecord(
            deploy_id=self.deploy_id,
            at_wall=wall(),
            agent_version=self.settings.agent_version,
            git_commit=resolve_git_sha(self.environ),
            image_digest=None,
            config_hash=config_hash(self.settings, Path(self.settings.index_dir)),
            trace_export_on=trace_export_on(sink),
            status="started",
        )
        with uow(write=True) as tx:
            tx.ops.deploy.insert(record)
            tx.commit()
        try:
            readiness = FastembedIndex(Path(self.settings.index_dir)).readiness()
            if not readiness.ok:
                raise IndexNotReady("retrieval index not ready: " + ",".join(readiness.reasons))
            load_eval_reports(REPORTS_DIR, uow, wall_clock=wall, agent_version=self.settings.agent_version)
        except BaseException:
            with contextlib.suppress(Exception):
                self.set_status("failed")
            raise

    def set_status(self, status: RunStatus) -> None:
        uow = self.container.get(deps.UOW_FACTORY)
        with uow(write=True) as tx:
            tx.ops.deploy.set_status(self.deploy_id, status)
            tx.commit()

    async def complete_when_healthy(self, app: FastAPI) -> None:
        """Probe /healthz through the real middleware; no sync SQLite on the event loop."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + COMPLETE_WITHIN_S
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://deploy.local") as client:
            while loop.time() < deadline:
                try:
                    response = await client.get(HEALTHZ_PATH)
                except httpx.HTTPError:
                    response = None
                if response is not None and response.status_code == 200:
                    await asyncio.to_thread(self.set_status, "completed")
                    return
                await asyncio.sleep(POLL_EVERY_S)
        await asyncio.to_thread(self.set_status, "incomplete")


def create_deployed_app() -> FastAPI:
    """uvicorn --factory target; takes no arguments."""
    logging.captureWarnings(True)
    app = create_app()
    settings: Settings = app.state.web_shell.settings
    deploy_id = deploy_id_from(os.environ)
    app.state.deploy_id = deploy_id
    inner = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(a: FastAPI) -> AsyncIterator[None]:
        async with inner(a):  # builds the container: migrate, first-boot seed, trace check, watchdog
            startup = DeployStartup(a.state.container, settings, deploy_id, os.environ)
            await asyncio.to_thread(startup.begin)  # raises IndexNotReady: start-up fails, uvicorn exits
            task = asyncio.create_task(startup.complete_when_healthy(a), name="meridian-deploy-complete")
            try:
                yield
            finally:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task

    app.router.lifespan_context = lifespan
    return app
