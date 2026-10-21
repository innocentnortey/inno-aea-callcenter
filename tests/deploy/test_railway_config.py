"""AEA-50 AC-4, AC-13, AC-14, AC-17: railway.json, .dockerignore, Dockerfile and the image's configuration.

Static tests run by default (no docker); the read-back of the built image is marked `deploy`.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import pytest

from tests.deploy.support import (
    IMAGE,
    ROOT,
    SECRET_NAME,
    apply_env,
    built_images,
    host_env,
    image_cmd,
    image_env,
    run_in_image,
)

RAILWAY_JSON = ROOT / "railway.json"
DOCKERFILE = ROOT / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"
OPENAPI = "docs/ux/03-structure/ui-contracts.openapi.yaml"

EXPECTED_RAILWAY: dict[str, Any] = {
    "build": {"builder": "DOCKERFILE", "dockerfilePath": "Dockerfile"},
    "deploy": {
        "healthcheckPath": "/healthz",
        "restartPolicyType": "ON_FAILURE",
        "restartPolicyMaxRetries": 10,
        "numReplicas": 1,
    },
}


def _instructions(text: str) -> list[tuple[str, str]]:
    """(stage, instruction line) pairs with backslash continuations joined; comments and blanks dropped."""
    joined = re.sub(r"\\\n", " ", text)
    stage = ""
    out: list[tuple[str, str]] = []
    for raw in joined.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"(?i)^FROM\s+\S+\s+AS\s+(\S+)", line)
        if match:
            stage = match.group(1)
        out.append((stage, line))
    return out


def _cmd_string(text: str) -> str:
    for _, line in _instructions(text):
        if line.upper().startswith("CMD "):
            parts = json.loads(line[4:])
            assert isinstance(parts, list)
            return " ".join(str(p) for p in parts)
    raise AssertionError("Dockerfile has no CMD")


def _declared_names(text: str) -> list[str]:
    names: list[str] = []
    for _, line in _instructions(text):
        head, _, rest = line.partition(" ")
        if head.upper() == "ARG":
            names.append(rest.split("=", 1)[0].strip())
        elif head.upper() == "ENV":
            names.extend(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=", rest))
    return names


def test_railway_json_values() -> None:
    """invariant (AC-13): railway.json holds exactly the data.md section 7 values and nothing else."""
    assert json.loads(RAILWAY_JSON.read_text(encoding="utf-8")) == EXPECTED_RAILWAY


def test_dockerignore_lists_required_patterns() -> None:
    """negative (AC-4 read-back): secrets, run artefacts and eval cases are excluded; the OpenAPI file is re-included."""
    lines = [ln.strip() for ln in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()]
    for required in (".env", ".env.*", "var/", ".venv/", ".git/", "**/node_modules", "eval/cases/"):
        assert required in lines, f".dockerignore must list {required}"
    assert f"!{OPENAPI}" in lines, "the web stage reads the one OpenAPI file; it must be re-included"
    assert not any(ln == OPENAPI for ln in lines), "the OpenAPI file must not be excluded"


def test_dockerfile_static_rules() -> None:
    """invariant (AC-4, AC-13, AC-17): stage order, no secret names, the start command, the web recipe, no USER."""
    text = DOCKERFILE.read_text(encoding="utf-8")
    instructions = _instructions(text)
    stages = [s for s, line in instructions if re.match(r"(?i)^FROM\s", line)]
    assert stages == ["web", "base", "index", "runtime"]

    bad = [n for n in _declared_names(text) if SECRET_NAME.search(n)]
    assert bad == [], f"ARG/ENV names that look like secrets: {bad}"

    cmd = _cmd_string(text)
    for needle in (
        "export MERIDIAN_AGENT_VERSION",
        "python -m scripts.agent_version",
        "uvicorn --factory scripts.serve:create_deployed_app",
        "--host 0.0.0.0",
        '--port "$PORT"',
        "--workers 1",
    ):
        assert needle in cmd, f"start command must contain {needle!r}"

    web_runs = " ".join(
        line for stage, line in instructions if stage == "web" and line.upper().startswith("RUN ")
    )
    for needle in ("npm ci", "npm run build", "npm run check:dist"):
        assert needle in web_runs
    for forbidden in ("--omit=dev", "NODE_ENV=production", "--mode"):
        assert forbidden not in web_runs
    web_copies = " ".join(
        line for stage, line in instructions if stage == "web" and line.upper().startswith("COPY")
    )
    assert "apps/web/" in web_copies
    assert OPENAPI in web_copies

    engines = json.loads((ROOT / "apps/web/package.json").read_text(encoding="utf-8")).get("engines", {})
    major = re.search(r"\d+", engines.get("node", "") or "")
    expected = major.group(0) if major else "24"
    assert f"ARG NODE_VERSION={expected}" in text

    heads = {line.split(" ", 1)[0].upper() for _, line in instructions}
    assert not heads & {"USER", "VOLUME", "HEALTHCHECK"}


def test_dockerfile_copies_only_dist_into_runtime() -> None:
    """invariant (AC-17): the runtime stage copies the web stage's output only, never node_modules or the OpenAPI."""
    instructions = _instructions(DOCKERFILE.read_text(encoding="utf-8"))
    from_web = [line for stage, line in instructions if stage == "runtime" and "--from=web" in line]
    assert from_web, "runtime must copy the built frontend from the web stage"
    assert all("node_modules" not in line and "openapi" not in line.lower() for line in from_web)


def test_no_timeout_below_65s(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """invariant (AC-14): no server or proxy timeout under 65 s, and the deployed factory adds no route."""
    cmd = _cmd_string(DOCKERFILE.read_text(encoding="utf-8"))
    values = [int(v) for v in re.findall(r"--timeout-[a-z-]+\s+(\d+)", cmd)]
    assert all(v >= 65 for v in values), values
    railway = json.dumps(json.loads(RAILWAY_JSON.read_text(encoding="utf-8")))
    assert "timeout" not in railway.lower()

    from meridian.web.app import create_app

    # isort: split
    from scripts.serve import create_deployed_app

    monkeypatch.chdir(ROOT)
    apply_env(monkeypatch, host_env(tmp_path / "data"))
    try:
        deployed = {getattr(r, "path", None) for r in create_deployed_app().routes}
        baseline = {getattr(r, "path", None) for r in create_app().routes}
    finally:
        logging.captureWarnings(False)
    assert deployed == baseline


@pytest.mark.deploy
def test_image_config_read_back() -> None:
    """negative + invariant (AC-13): the built image's Cmd, Env and file system match the committed Dockerfile."""
    built_images()
    dockerfile_cmd = _cmd_string(DOCKERFILE.read_text(encoding="utf-8"))
    assert " ".join(image_cmd(IMAGE)) == dockerfile_cmd

    names = list(image_env(IMAGE))
    assert [n for n in names if SECRET_NAME.search(n)] == []
    assert "PYTHONPATH" not in names
    assert "AEA50_FAULT_ONCE_FILE" not in names

    probe = run_in_image(IMAGE, "sh", "-c", "test ! -e /app/tests && ! python -c 'import aea50_fault_app'")
    assert probe.returncode == 0, "the fault module and tests/ must not exist in the image"
    assert "startCommand" not in json.dumps(json.loads(RAILWAY_JSON.read_text(encoding="utf-8")))
    assert os.environ.get("AEA50_FAULT_ONCE_FILE") is None
