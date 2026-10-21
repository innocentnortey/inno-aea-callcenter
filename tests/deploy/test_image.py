"""AEA-50 AC-1..AC-5, AC-17: the built image. Every test here builds or runs docker and is marked `deploy`."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from tests.deploy.support import (
    BLOCKED_AEA_29_30,
    IMAGE,
    IMAGE_NOWEB,
    IMAGE_WEB,
    ISSUED_IN_IMAGE,
    ROOT,
    SECRET_NAME,
    build,
    build_sha_value,
    built_images,
    context_sentinels,
    docker,
    image_env,
    new_data_dir,
    read_from_image,
    run_in_image,
    scan_saved_image,
    sentinel_env,
    start,
    wait_deploy_status,
)

pytestmark = pytest.mark.deploy

ISSUED_HOST = ROOT / "docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite"
SIX_ARTEFACTS = (
    "manifest.json",
    "passages.jsonl",
    "vectors.npy",
    "index_record.json",
    "ingest_run.json",
    "staff_notes.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_index_built_in_image(tmp_path: Path) -> None:
    """invariant (AC-1): the index stage ran the ingest CLI; the runtime holds the six index files and the rest."""
    images = built_images()
    assert "python -m meridian.retrieval.ingest" in images.main_log
    read_from_image(IMAGE, "/app/index", tmp_path / "index")
    for name in SIX_ARTEFACTS:
        assert (tmp_path / "index" / name).is_file(), f"/app/index/{name} is missing"
    record = json.loads((tmp_path / "index/index_record.json").read_text(encoding="utf-8"))
    assert record["embedding_model"] == "BAAI/bge-small-en-v1.5"
    assert record["files"] == 17
    assert record["chunks"] > 0
    assert re.fullmatch(r"[0-9a-f]{64}", record["manifest_hash"])
    run = json.loads((tmp_path / "index/ingest_run.json").read_text(encoding="utf-8"))
    assert run["status"] == "completed"

    listing = run_in_image(
        IMAGE, "sh", "-c", f"test -d /app/eval/reports && cat /app/BUILD_SHA && test -f {ISSUED_IN_IMAGE}"
    )
    assert listing.returncode == 0
    assert listing.stdout.strip() == build_sha_value()


def test_web_stage_conditional() -> None:
    """invariant (AC-2): dist is built when apps/web/package.json exists and absent when it does not."""
    images = built_images()
    with_web = run_in_image(
        IMAGE,
        "sh",
        "-c",
        "test -f /app/apps/web/dist/index.html && find /app /usr/local/lib -name node_modules | wc -l",
    )
    assert with_web.returncode == 0
    assert with_web.stdout.strip() == "0"
    without = run_in_image(IMAGE_NOWEB, "sh", "-c", "test ! -e /app/apps/web/dist")
    assert without.returncode == 0
    assert "frontend build skipped" in images.noweb_log


def test_web_stage_recipe() -> None:
    """invariant (AC-17): the web stage regenerates types from the copied spec and passes check:dist; the OpenAPI
    file never reaches the runtime image."""
    images = built_images()
    log = build(IMAGE_WEB, images.context, "--target", "web", "--no-cache-filter", "web")
    assert "openapi-typescript" in log
    assert "dist is clean" in log
    found = run_in_image(IMAGE, "sh", "-c", "find / -xdev -name ui-contracts.openapi.yaml | wc -l")
    assert found.stdout.strip() == "0"


def test_runs_without_network() -> None:
    """invariant (AC-3): readiness and a knowledge search work with no network; nothing is downloaded."""
    built_images()
    result = run_in_image(
        IMAGE,
        "python",
        "-m",
        "scripts.image_check",
        "--search",
        "What does the Comfort Club membership include?",
        network="none",
    )
    assert result.returncode == 0
    assert "readiness ok=true" in result.stdout
    assert "search status=ok" in result.stdout
    combined = result.stdout + result.stderr
    for forbidden in ("Downloading", "huggingface.co", "Fetching"):
        assert forbidden not in combined


def test_no_secrets_in_image() -> None:
    """negative (AC-4): sentinel .env, .env.local, run ledger and held-out key never reach any layer or the history."""
    built_images()
    needles = context_sentinels()
    assert scan_saved_image(IMAGE, needles) == []
    history = docker("history", "--no-trunc", "--format", "{{.CreatedBy}}", IMAGE).stdout
    assert not any(n in history for n in needles)
    assert [n for n in image_env(IMAGE) if SECRET_NAME.search(n)] == []


def test_first_boot_writes_only_data_dir() -> None:
    """invariant (AC-5): the working copy and checkpoints live only in the data dir; the issued file is unchanged."""
    built_images()
    before = _sha256(ISSUED_HOST)
    in_image = run_in_image(IMAGE, "sha256sum", ISSUED_IN_IMAGE)
    assert in_image.stdout.split()[0] == before

    data_dir = new_data_dir()
    app = start(data_dir=data_dir, env=sentinel_env(), name_hint="firstboot")
    wait_deploy_status(data_dir, "completed")
    after = app.exec("sha256sum", ISSUED_IN_IMAGE)
    assert after.stdout.split()[0] == before
    assert (data_dir / "meridian.sqlite").is_file()
    assert (data_dir / "checkpoints.sqlite").is_file()
    stray = app.exec("sh", "-c", "find / -xdev -name meridian.sqlite -not -path '/data/*'")
    assert stray.stdout.strip() == ""
    assert _sha256(ISSUED_HOST) == before


@BLOCKED_AEA_29_30
def test_reset_leaves_issued_file_unchanged() -> None:
    """invariant (AC-5, reset leg): after the operator reset on the stopped service the issued file is identical."""
    built_images()
    before = _sha256(ISSUED_HOST)
    data_dir = new_data_dir()
    app = start(data_dir=data_dir, env=sentinel_env(), name_hint="resetleg")
    wait_deploy_status(data_dir, "completed")
    app.stop()
    result = run_in_image(
        IMAGE,
        "sh",
        "-c",
        f"python -m scripts.reset && sha256sum {ISSUED_IN_IMAGE}",
        network="none",
        env=sentinel_env(),
        volumes={data_dir: "/data"},
    )
    assert result.returncode == 0
    assert "reset status=done" in result.stdout
    assert result.stdout.split()[-2] == before
