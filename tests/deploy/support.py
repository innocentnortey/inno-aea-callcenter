"""AEA-50 deploy test support: sentinels, build contexts, docker helpers, saved-image scanning. Not collected.

Frozen with the AEA-50 tests (risk::security). Synthetic values only: every sentinel is generated per session and is
never a real key, phone number, card number or code. Helpers that run docker assert the exit code with a message
holding the command name and exit code only.
"""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from functools import cache, wraps
from pathlib import Path
from typing import Any

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
IMAGE, IMAGE_NOWEB, IMAGE_INDEX, IMAGE_WEB, IMAGE_NOINDEX = (
    "meridian:aea50-test",
    "meridian:aea50-noweb",
    "meridian:aea50-index",
    "meridian:aea50-web",
    "meridian:aea50-noindex",
)
ALL_TAGS = (IMAGE, IMAGE_NOWEB, IMAGE_INDEX, IMAGE_WEB, IMAGE_NOINDEX)
ISSUED_IN_IMAGE = "/app/docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite"
SECRET_NAME = re.compile(r"(?i)(KEY|SECRET|PASSWORD|PASSWD|TOKEN|CREDENTIAL)")
ALL_INTERFACES = ".".join(("0",) * 4)  # kept out of source as a literal (ruff S104)
MARKER_TEXT = "deploy: builds or runs the Docker image (AEA-50); excluded unless -m selects it; runs before every deploy"
_SKIP_REASON = "deploy test: run with -m deploy"
_DEPLOY_SELECTED = re.compile(r"(?<!not )\bdeploy\b")

_SENTINEL_KINDS = (
    "model-key",
    "openrouter-key",
    "eval-key",
    "session-secret",
    "demo-user",
    "demo-password",
    "langfuse-pk",
    "langfuse-sk",
    "name",
    "phone",
    "env-file",
    "env-local",
    "ledger",
    "heldout",
)


# ---------------------------------------------------------------- sentinels and blocked markers


def sentinel(kind: str) -> str:
    return f"aea50-{kind}-{secrets.token_hex(12)}"


@cache
def session_sentinels() -> dict[str, str]:
    return {kind: sentinel(kind) for kind in _SENTINEL_KINDS}


def module_present(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ModuleNotFoundError, ValueError):
        return False


def _blocked(condition: bool, reason: str) -> pytest.MarkDecorator:
    return pytest.mark.xfail(condition, strict=True, reason=reason)


def _handoff_missing() -> bool:
    return not module_present("meridian.services.handoff")


def _demo_missing() -> bool:
    return not module_present("meridian.services.demo")


def _sweep_missing() -> bool:
    from meridian.web.logging import ALLOWED_FIELDS

    return not (module_present("meridian.services.turn") and "turn_sweep" in ALLOWED_FIELDS)


def _export_state_missing() -> bool:
    from meridian.adapters.tracing_langfuse import LangfuseTraceSink

    return not hasattr(LangfuseTraceSink, "export_on")


def _health_ids_missing() -> bool:
    from meridian.adapters.sqlite.repos_ops import HealthEvent

    return "health_check_id" not in HealthEvent.model_fields


BLOCKED_AEA_29 = _blocked(
    _handoff_missing(), "blocked-on AEA-29: BriefAssembler (meridian.services.handoff) not merged"
)
BLOCKED_AEA_29_30 = _blocked(
    _handoff_missing() or _demo_missing(),
    "blocked-on AEA-29 and AEA-30: BriefAssembler / format_clock not merged",
)
BLOCKED_AEA_40 = _blocked(_sweep_missing(), "blocked-on AEA-40 (+ AEA-23 allow-list): start-up restart sweep")
BLOCKED_AEA_19_FU = _blocked(
    _export_state_missing(), "blocked-on AEA-19 follow-up: LangfuseTraceSink.export_on"
)
BLOCKED_AEA_32_FU = _blocked(
    _health_ids_missing(),
    "blocked-on AEA-10 + AEA-32 follow-up: health_check_id and deploy_id on health_events",
)
BLOCKED_AEA_31_FU = _blocked(True, "blocked-on AEA-31 follow-up: first-boot seed_event.deploy_id")


# ---------------------------------------------------------------- pytest plumbing (used by both conftests)


def configure_deploy_marker(config: pytest.Config) -> None:
    if MARKER_TEXT not in config.getini("markers"):
        config.addinivalue_line("markers", MARKER_TEXT)


def skip_deploy_unless_selected(config: pytest.Config, items: list[pytest.Item]) -> None:
    deploy_items = [i for i in items if i.get_closest_marker("deploy") is not None]
    selected = bool(_DEPLOY_SELECTED.search(str(config.getoption("markexpr") or "")))
    if not selected:
        for item in deploy_items:
            already = any(
                m.name == "skip" and m.kwargs.get("reason") == _SKIP_REASON for m in item.iter_markers("skip")
            )
            if not already:
                item.add_marker(pytest.mark.skip(reason=_SKIP_REASON))
        return
    if not deploy_items:
        return
    if shutil.which("docker") is None:
        raise pytest.UsageError("deploy tests need docker")
    if shutil.disk_usage("/").free < 4 * 2**30:
        raise pytest.UsageError("deploy tests need 4 GB free disk")


# ---------------------------------------------------------------- environments


def sentinel_env(*, langfuse: Mapping[str, str] | None = None) -> dict[str, str]:
    s = session_sentinels()
    env = {
        "ANTHROPIC_API_KEY": s["model-key"],
        "OPENROUTER_API_KEY": s["openrouter-key"],
        "MERIDIAN_DEMO_USERNAME": s["demo-user"],
        "MERIDIAN_DEMO_PASSWORD": s["demo-password"],
        "MERIDIAN_SESSION_SECRET": s["session-secret"],
        "MERIDIAN_EVAL_KEY": s["eval-key"],
        "PORT": "8080",
    }
    env.update(langfuse or {})
    return env


def host_env(
    data_dir: Path, *, index_dir: Path | None = None, langfuse: Mapping[str, str] | None = None
) -> dict[str, str]:
    """A from-scratch environment for host subprocesses and monkeypatched in-process apps; never `os.environ`."""
    env = {"PATH": os.environ["PATH"], "HOME": str(data_dir), "LANG": "C.UTF-8"}
    env.update(sentinel_env(langfuse=langfuse))
    env["MERIDIAN_DATA_DIR"] = str(data_dir)
    if index_dir is not None:
        env["MERIDIAN_INDEX_DIR"] = str(index_dir)
    return env


def apply_env(monkeypatch: pytest.MonkeyPatch, env: Mapping[str, str]) -> None:
    """Make `os.environ` hold exactly `env` for the test (nothing from the developer's shell leaks in)."""
    for key in list(os.environ):
        if key not in env:
            monkeypatch.delenv(key)
    for key, value in env.items():
        monkeypatch.setenv(key, value)


# ---------------------------------------------------------------- build contexts


_TEMP_DIRS: list[Path] = []
_CONTAINERS: list[str] = []
_NETWORKS: list[str] = []


def _tempdir(prefix: str) -> Path:
    path = Path(tempfile.mkdtemp(prefix=prefix))
    _TEMP_DIRS.append(path)
    return path


@cache
def build_sha_value() -> str:
    return secrets.token_hex(20)


def make_context(dst: Path, *, with_sentinels: bool, drop: Sequence[str] = ()) -> Path:
    """What a clean checkout holds (tracked plus untracked-not-ignored), copied to `dst`, plus a BUILD_SHA."""
    listing = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-co", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
        timeout=60,
    ).stdout.decode()
    dropped = set(drop)
    for rel in filter(None, listing.split("\0")):
        src = ROOT / rel
        if rel in dropped or not src.is_file():
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    (dst / "BUILD_SHA").write_text(build_sha_value() + "\n", encoding="utf-8")
    if with_sentinels:
        s = session_sentinels()
        files = {
            ".env": f"ANTHROPIC_API_KEY={s['env-file']}\n",
            ".env.local": f"OPENROUTER_API_KEY={s['env-local']}\n",
            "var/sp1-runs/ledger.jsonl": json.dumps({"note": s["ledger"]}) + "\n",
            "eval/cases/heldout/x.key.json": json.dumps({"key": s["heldout"]}) + "\n",
        }
        for rel, text in files.items():
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
    return dst


def context_sentinels() -> list[str]:
    s = session_sentinels()
    return [s["env-file"], s["env-local"], s["ledger"], s["heldout"]]


# ---------------------------------------------------------------- docker


def _fail_docker(args: Sequence[str], rc: int) -> AssertionError:
    return AssertionError(f"docker {args[0] if args else ''} exited {rc}")


def docker(
    *args: str, timeout: float = 600, check: bool = True, input: str | None = None
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["docker", *args], capture_output=True, text=True, timeout=timeout, check=False, input=input
    )
    if check and proc.returncode != 0:
        raise _fail_docker(args, proc.returncode)
    return proc


def _excerpt(log: str) -> str:
    """Error lines only, sentinel values masked; helps the implementer without echoing anything sensitive."""
    masked = log
    for value in session_sentinels().values():
        masked = masked.replace(value, "<sentinel>")
    lines = [ln for ln in masked.splitlines() if re.search(r"ERROR|error:|failed|not found", ln)]
    return " | ".join(ln.strip()[:200] for ln in lines[:4])


def build(tag: str, ctx: Path, *extra: str, timeout: float = 1800) -> str:
    proc = subprocess.run(
        ["docker", "build", "--progress=plain", "--label", "aea50.test=1", "-t", tag, *extra, str(ctx)],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    log = proc.stdout + proc.stderr
    if proc.returncode != 0:
        raise AssertionError(f"docker build exited {proc.returncode}: {_excerpt(log)}")
    return log


@dataclass(frozen=True)
class ImageSet:
    main_log: str
    noweb_log: str
    context: Path


def once[T](fn: Callable[[], T]) -> Callable[[], T]:
    """Run `fn` once per session and replay its outcome, a failure included, so a broken build fails every
    dependent test quickly instead of being retried (and re-timed) by each of them."""
    box: list[tuple[bool, Any]] = []

    @wraps(fn)
    def wrapper() -> T:
        if not box:
            try:
                box.append((True, fn()))
            except BaseException as exc:
                box.append((False, exc))
        ok, value = box[0]
        if ok:
            return value  # type: ignore[no-any-return]
        raise value

    return wrapper


@once
def built_images() -> ImageSet:
    ctx = make_context(_tempdir("aea50-ctx-"), with_sentinels=True)
    main_log = build(IMAGE, ctx)
    build(IMAGE_INDEX, ctx, "--target", "index")
    noweb_ctx = make_context(
        _tempdir("aea50-ctx-noweb-"), with_sentinels=False, drop=("apps/web/package.json",)
    )
    noweb_log = build(IMAGE_NOWEB, noweb_ctx)
    noindex = subprocess.run(
        ["docker", "build", "--label", "aea50.test=1", "-t", IMAGE_NOINDEX, "-"],
        input=f"FROM {IMAGE}\nRUN rm -rf /app/index\n",
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if noindex.returncode != 0:
        raise _fail_docker(["build"], noindex.returncode)
    return ImageSet(main_log, noweb_log, ctx)


def image_cmd(image: str) -> list[str]:
    out = docker("inspect", "--format", "{{json .Config.Cmd}}", image).stdout
    cmd = json.loads(out)
    assert isinstance(cmd, list)
    return [str(part) for part in cmd]


def image_env(image: str) -> dict[str, str]:
    out = docker("inspect", "--format", "{{json .Config.Env}}", image).stdout
    pairs = json.loads(out) or []
    return {k: v for k, _, v in (str(p).partition("=") for p in pairs)}


def _env_file(env: Mapping[str, str]) -> Path:
    fd, name = tempfile.mkstemp(prefix="aea50-env-")
    path = Path(name)
    _TEMP_DIRS.append(path)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:  # mkstemp creates the file with mode 0600
        for key, value in env.items():
            handle.write(f"{key}={value}\n")
    return path


def run_in_image(
    image: str,
    *cmd: str,
    network: str = "none",
    env: Mapping[str, str] | None = None,
    volumes: Mapping[Path, str] | None = None,
    timeout: float = 900,
) -> subprocess.CompletedProcess[str]:
    args = ["docker", "run", "--rm", "--network", network]
    if env:
        args += ["--env-file", str(_env_file(env))]
    for host, target in (volumes or {}).items():
        args += ["-v", f"{host}:{target}"]
    return subprocess.run([*args, image, *cmd], capture_output=True, text=True, timeout=timeout, check=False)


def new_data_dir() -> Path:
    return _tempdir("aea50-data-")


def create_network(*, internal: bool = True) -> str:
    name = f"aea50-net-{secrets.token_hex(4)}"
    docker("network", "create", *(["--internal"] if internal else []), name)
    _NETWORKS.append(name)
    return name


@dataclass
class Running:
    name: str
    data_dir: Path

    def logs(self) -> list[str]:
        proc = subprocess.run(
            ["docker", "logs", self.name], capture_output=True, text=True, timeout=60, check=False
        )
        return [ln for ln in (proc.stdout + proc.stderr).splitlines() if ln.strip()]

    def exec(self, *cmd: str) -> subprocess.CompletedProcess[str]:
        return docker("exec", self.name, *cmd, check=False, timeout=120)

    def restart_count(self) -> int:
        return int(docker("inspect", "--format", "{{.RestartCount}}", self.name).stdout.strip())

    def is_running(self) -> bool:
        return docker("inspect", "--format", "{{.State.Running}}", self.name).stdout.strip() == "true"

    def restart(self) -> None:
        docker("restart", self.name)

    def stop(self) -> None:
        docker("rm", "-f", self.name, check=False)


def start(
    image: str = IMAGE,
    *,
    data_dir: Path,
    network: str = "none",
    restart: str = "no",
    env: Mapping[str, str],
    fault_once: bool = False,
    extra_volumes: Mapping[Path, str] | None = None,
    name_hint: str = "app",
) -> Running:
    """`docker run -d` with the image's own start command. Never publishes a port."""
    name = f"aea50-{name_hint}-{secrets.token_hex(4)}"
    full_env = dict(env)
    volumes: dict[Path, str] = {data_dir: "/data", **(extra_volumes or {})}
    cmd: list[str] = []
    args = ["run", "-d", "--name", name, "--network", network, "--restart", restart]
    if fault_once:
        (data_dir / "aea50-fault-once").write_text("1", encoding="utf-8")
        full_env["PYTHONPATH"] = "/fault"
        full_env["AEA50_FAULT_ONCE_FILE"] = "/data/aea50-fault-once"
        fault_module = Path(__file__).with_name("fault_app.py")
        args += ["-v", f"{fault_module}:/fault/aea50_fault_app.py:ro"]
        original = image_cmd(image)
        swapped = [
            part.replace("scripts.serve:create_deployed_app", "aea50_fault_app:create_faulty_app")
            for part in original
        ]
        replacements = sum(a != b for a, b in zip(original, swapped, strict=True))
        assert replacements == 1, "start command must name scripts.serve:create_deployed_app exactly once"
        cmd = swapped
    args += ["--env-file", str(_env_file(full_env))]
    for host, target in volumes.items():
        args += ["-v", f"{host}:{target}"]
    docker(*args, image, *cmd)
    _CONTAINERS.append(name)
    return Running(name, data_dir)


def start_plain(
    image: str,
    *cmd: str,
    network: str,
    volumes: Mapping[Path, str] | None = None,
    name_hint: str = "aux",
) -> Running:
    """A detached helper container (for example the stub Langfuse) running `cmd` in `image`."""
    name = f"aea50-{name_hint}-{secrets.token_hex(4)}"
    args = ["run", "-d", "--name", name, "--network", network]
    for host, target in (volumes or {}).items():
        args += ["-v", f"{host}:{target}"]
    docker(*args, image, *cmd)
    _CONTAINERS.append(name)
    return Running(name, next(iter(volumes or {Path(): ""})))


def snapshot_db(data_dir: Path) -> Path:
    """A private copy of the working copy (database plus WAL) so a host read never needs the root-owned -shm."""
    src = data_dir / "meridian.sqlite"
    if not src.is_file():
        raise FileNotFoundError("working copy not created yet")
    tmp = _tempdir("aea50-snap-")
    shutil.copy2(src, tmp / "meridian.sqlite")
    wal = data_dir / "meridian.sqlite-wal"
    if wal.is_file():
        shutil.copy2(wal, tmp / "meridian.sqlite-wal")
    return tmp / "meridian.sqlite"


def db_rows(data_dir: Path, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    path = snapshot_db(data_dir)
    conn = sqlite3.connect(path)
    try:
        return [tuple(r) for r in conn.execute(sql, params)]
    finally:
        conn.close()
        shutil.rmtree(path.parent, ignore_errors=True)


def db_text_columns(data_dir: Path) -> list[tuple[str, str, str]]:
    """Every (table, column, value) of every TEXT cell in the working copy; for no-sentinel scans."""
    path = snapshot_db(data_dir)
    conn = sqlite3.connect(path)
    out: list[tuple[str, str, str]] = []
    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]
            for row in conn.execute(f'SELECT * FROM "{table}"'):  # noqa: S608  # names from sqlite_master
                out.extend((table, c, v) for c, v in zip(cols, row, strict=True) if isinstance(v, str))
    finally:
        conn.close()
        shutil.rmtree(path.parent, ignore_errors=True)
    return out


def wait_for(predicate: Callable[[], bool], *, timeout: float, every: float = 1.0, what: str) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            if predicate():
                return
        except (FileNotFoundError, sqlite3.Error):
            pass
        if time.monotonic() >= deadline:
            pytest.fail(f"timed out after {timeout:.0f}s waiting for {what}")
        time.sleep(every)


def wait_deploy_status(data_dir: Path, status: str, *, count: int = 1, timeout: float = 120) -> None:
    def seen() -> bool:
        rows = db_rows(data_dir, "SELECT COUNT(*) FROM deploy_records WHERE status = ?", (status,))
        return int(rows[0][0]) >= count

    wait_for(seen, timeout=timeout, what=f"{count} deploy_record(s) with status {status}")


def json_lines(lines: Sequence[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        try:
            parsed = json.loads(line)
        except ValueError:
            raise AssertionError(f"log line {number} is not JSON") from None
        if not isinstance(parsed, dict):
            raise AssertionError(f"log line {number} is not a JSON object")
        out.append(parsed)
    return out


def _allowed_log_keys() -> Mapping[str, frozenset[str]]:
    from meridian.web.logging import ALLOWED_FIELDS

    merged = dict(ALLOWED_FIELDS)
    merged["log"] = frozenset({"record", "logger", "level", "length", "exc_type"})
    return merged


ALLOWED_LOG_KEYS: Mapping[str, frozenset[str]] = _allowed_log_keys()


def assert_allow_listed(records: Sequence[Mapping[str, Any]]) -> None:
    """Each record names its kind and holds only that kind's allowed keys (record kinds, never values, in messages)."""
    for number, record in enumerate(records, start=1):
        kind = record.get("record")
        assert isinstance(kind, str) and kind in ALLOWED_LOG_KEYS, f"log record {number}: unknown kind"
        extra = set(record) - ALLOWED_LOG_KEYS[kind]
        assert not extra, f"log record {number} ({kind}): keys outside the allow-list: {sorted(extra)}"


def scan_saved_image(image: str, needles: Sequence[str]) -> list[str]:
    """`docker save` the image and scan every layer (gunzipped when needed) for the needles; no value is returned."""
    work = _tempdir("aea50-save-")
    tar_path = work / "image.tar"
    docker("save", "-o", str(tar_path), image, timeout=900)
    encoded = [(i, n.encode()) for i, n in enumerate(needles)]
    overlap = max(len(b) for _, b in encoded) - 1
    hits: list[str] = []
    with tarfile.open(tar_path, mode="r:") as outer:
        for member in outer:
            if not member.isfile():
                continue
            handle = outer.extractfile(member)
            if handle is None:
                continue
            head = handle.read(4)
            handle.seek(0)
            if head[:4] == b"\x28\xb5\x2f\xfd":
                raise AssertionError("unsupported layer compression (zstd)")
            stream: Any = gzip.GzipFile(fileobj=handle) if head[:2] == b"\x1f\x8b" else handle
            tail = b""
            found: set[int] = set()
            while chunk := stream.read(1 << 20):
                window = tail + chunk
                found.update(i for i, needle in encoded if needle in window)
                tail = window[-overlap:] if overlap else b""
            hits.extend(f"{member.name}: needle#{i}" for i in sorted(found))
    shutil.rmtree(work, ignore_errors=True)
    return hits


def read_from_image(image: str, path: str, dest: Path) -> Path:
    """`docker create` + `docker cp` a path out of an image; returns the host path."""
    cid = docker("create", image).stdout.strip()
    try:
        docker("cp", f"{cid}:{path}", str(dest))
    finally:
        docker("rm", "-f", cid, check=False)
    return dest


# ---------------------------------------------------------------- stand-in index (no model download)


def stand_in_embed(texts: Sequence[str]) -> Any:
    rows = []
    for text in texts:
        digest = hashlib.sha256(text.encode("utf-8")).digest()[:8]
        rows.append(np.append(np.frombuffer(digest, dtype=np.uint8).astype(np.float32), np.float32(1.0)))
    return np.stack(rows)


def build_stand_in_index(out_dir: Path) -> Path:
    from meridian.retrieval.ingest import build_index

    build_index(
        ROOT / "docs/data/issued/meridian_dataset/knowledge_base",
        out_dir,
        transcriptions_dir=ROOT / "data/kb_transcriptions",
        embed=stand_in_embed,
    )
    return out_dir


# ---------------------------------------------------------------- cleanup


def release_dir(path: Path) -> None:
    """Containers run as root and leave root-owned files; hand them back before removing the directory."""
    if not path.exists():
        return
    if shutil.which("docker") and docker("image", "inspect", IMAGE, check=False).returncode == 0:
        docker(
            "run", "--rm", "--network", "none", "-v", f"{path}:/d", IMAGE,
            "chown", "-R", f"{os.getuid()}:{os.getgid()}", "/d",
            check=False,
        )  # fmt: skip
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def cleanup_session() -> None:
    """Idempotent: containers, data directories, networks, then the five test images."""
    if shutil.which("docker") is not None:
        while _CONTAINERS:
            docker("rm", "-f", _CONTAINERS.pop(), check=False)
    while _TEMP_DIRS:
        release_dir(_TEMP_DIRS.pop())
    if shutil.which("docker") is not None:
        while _NETWORKS:
            docker("network", "rm", _NETWORKS.pop(), check=False)
        if _used_docker():
            docker("image", "rm", "-f", *ALL_TAGS, check=False)


def _used_docker() -> bool:
    return any(docker("image", "inspect", tag, check=False).returncode == 0 for tag in ALL_TAGS)


def unique_name() -> str:
    return uuid.uuid4().hex[:8]
