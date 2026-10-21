"""A local stub Langfuse for AEA-50 (stdlib only, so a bare image can run it as a script).

GET /api/public/projects answers one project; POST to an ingestion or OTLP path counts as a span; anything else is
404 and counted as `other`. Counts: {"project_checks", "spans", "other"}.
"""

from __future__ import annotations

import argparse
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


class _State:
    def __init__(self, project_id: str, counts_path: Path | None) -> None:
        self.project_id = project_id
        self.counts_path = counts_path
        self.counts = {"project_checks": 0, "spans": 0, "other": 0}
        self.lock = threading.Lock()

    def bump(self, key: str) -> None:
        with self.lock:
            self.counts[key] += 1
            if self.counts_path is not None:
                tmp = self.counts_path.with_name(self.counts_path.name + ".tmp")
                tmp.write_text(json.dumps(self.counts), encoding="utf-8")
                os.replace(tmp, self.counts_path)


class _Handler(BaseHTTPRequestHandler):
    server: Any

    def _reply(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        state: _State = self.server.state
        if self.path.split("?")[0] == "/api/public/projects":
            state.bump("project_checks")
            self._reply(200, {"data": [{"id": state.project_id, "name": "stub"}]})
        else:
            state.bump("other")
            self._reply(404, {})

    def do_POST(self) -> None:
        state: _State = self.server.state
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        if "/otel/" in self.path or "/ingestion" in self.path:
            state.bump("spans")
            self._reply(200, {})
        else:
            state.bump("other")
            self._reply(404, {})

    def log_message(self, format: str, *args: Any) -> None:  # silence the default stderr access log
        return


def _make_server(host: str, port: int, project_id: str, counts_path: Path | None) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), _Handler)
    server.state = _State(project_id, counts_path)  # type: ignore[attr-defined]
    return server


class StubHandle:
    def __init__(self, server: ThreadingHTTPServer, thread: threading.Thread) -> None:
        self._server = server
        self._thread = thread

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def counts(self) -> dict[str, int]:
        state: _State = self._server.state  # type: ignore[attr-defined]
        with state.lock:
            return dict(state.counts)

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def start_stub(project_id: str, counts: Path) -> StubHandle:
    server = _make_server("127.0.0.1", 0, project_id, counts)
    thread = threading.Thread(target=server.serve_forever, name="langfuse-stub", daemon=True)
    thread.start()
    return StubHandle(server, thread)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--counts", type=Path, required=True)
    args = parser.parse_args()
    server = _make_server(args.host, args.port, args.project_id, args.counts)
    server.serve_forever()


if __name__ == "__main__":
    main()
