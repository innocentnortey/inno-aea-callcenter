"""AEA-50 CAP-9: WF-13..WF-17 proven at their real entry points (image build, start command, reset script, first
boot, forced health-check failure). Frozen with the AEA-50 tests (risk::security).

Default-run tests are in process or host subprocesses with fakes; every `deploy` test builds or runs the image
(`pytest -m deploy`). No model is called anywhere. Sentinel values are generated per session.
"""

from __future__ import annotations

import itertools
import json
import logging
import re
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from meridian.adapters.sqlite.db import SqliteUnitOfWorkFactory
from meridian.adapters.sqlite.migrate import KEPT_TABLES, WORKING_DB_NAME, migrate, schema_files
from tests.deploy.langfuse_stub import start_stub
from tests.deploy.support import (
    ALL_INTERFACES,
    ALLOWED_LOG_KEYS,
    BLOCKED_AEA_19_FU,
    BLOCKED_AEA_29,
    BLOCKED_AEA_29_30,
    BLOCKED_AEA_31_FU,
    BLOCKED_AEA_32_FU,
    BLOCKED_AEA_40,
    IMAGE,
    IMAGE_INDEX,
    IMAGE_NOINDEX,
    ROOT,
    Running,
    apply_env,
    assert_allow_listed,
    build_sha_value,
    build_stand_in_index,
    built_images,
    context_sentinels,
    create_network,
    db_rows,
    db_text_columns,
    host_env,
    json_lines,
    new_data_dir,
    once,
    read_from_image,
    run_in_image,
    sentinel_env,
    session_sentinels,
    snapshot_db,
    start,
    start_plain,
    wait_deploy_status,
    wait_for,
)
from tests.fixtures.sqlite import ISSUED_DB, TempStore
from tests.services.ops_support import add_conversation, add_turn, chi
from tests.services.reset_support import ISSUED_TABLES, count, demo_store, issued_rows, make_dirty_demo, rows

STATUSES = {"started", "completed", "failed", "incomplete"}
HEALTHZ = (
    "import urllib.request,sys; "
    "sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz').status == 200 else 1)"
)
LANGFUSE_KEYS = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL", "LANGFUSE_PROJECT_ID")
VERSION = re.compile(r"^[0-9a-f]{12}\+[0-9a-f]{8}$")


def _sentinel_values() -> list[str]:
    return [*session_sentinels().values()]


def _no_sentinels(text: str, *, what: str) -> None:
    leaked = [i for i, value in enumerate(_sentinel_values()) if value in text]
    assert leaked == [], f"{what}: {len(leaked)} sentinel value(s) found"


# ----------------------------------------------------------------------------------- shared image runs


@dataclass(frozen=True)
class Scenario:
    app: Running
    turn_id: str | None = None
    stub_counts: Path | None = None


def _prepare_running_turn(data_dir: Path) -> str:
    """A working copy that already holds one `running` turn, written on the host before the container starts."""
    db = data_dir / WORKING_DB_NAME
    migrate(db, issued_path=ISSUED_DB)
    store = TempStore(data_dir, db, ISSUED_DB, SqliteUnitOfWorkFactory(db))
    thread = add_conversation(store, run_tag="live", started_wall_at=chi(2026, 10, 21, 13, 0))
    turn_id = add_turn(
        store,
        thread,
        run_tag="live",
        replied_at=chi(2026, 10, 21, 13, 5),
        status="running",
        trace_export=None,
    )
    with store.uow(write=True) as tx:
        tx.connection.execute(
            "UPDATE turns SET outcome=NULL, degrade_reason=NULL, replied_at=NULL, server_ms=NULL WHERE turn_id=?",
            (turn_id,),
        )
        tx.commit()
    return turn_id


def _restarted(data_dir: Path, app: Running) -> None:
    def done() -> bool:
        rows_ = db_rows(data_dir, "SELECT status FROM deploy_records ORDER BY rowid")
        return app.restart_count() == 1 and len(rows_) >= 2 and rows_[-1][0] == "completed"

    wait_for(done, timeout=240, every=2.0, what="one restart and a completed second deploy record")


@once
def run_first_boot() -> Scenario:
    """R0: offline first boot on an empty data directory, sentinels in the environment, no Langfuse."""
    built_images()
    data_dir = new_data_dir()
    app = start(data_dir=data_dir, env=sentinel_env(), name_hint="r0")
    wait_deploy_status(data_dir, "completed", timeout=240)
    return Scenario(app)


@once
def run_first_boot_then_restart() -> Scenario:
    """R4: the same first boot, then a plain `docker restart` (WF-16: a second start writes no second seed)."""
    built_images()
    data_dir = new_data_dir()
    app = start(data_dir=data_dir, env=sentinel_env(), name_hint="r4")
    wait_deploy_status(data_dir, "completed", timeout=240)
    app.restart()
    wait_deploy_status(data_dir, "completed", count=2, timeout=240)
    return Scenario(app)


@once
def run_forced_failure() -> Scenario:
    """R1: offline, `--restart on-failure`, the first process answers /healthz 503, one `running` turn waits."""
    built_images()
    data_dir = new_data_dir()
    turn_id = _prepare_running_turn(data_dir)
    app = start(
        data_dir=data_dir,
        restart="on-failure",
        env=sentinel_env(),
        fault_once=True,
        name_hint="r1",
    )
    _restarted(data_dir, app)
    return Scenario(app, turn_id)


@once
def run_stub_restart() -> Scenario:
    """R2: wrong-project stub Langfuse on an internal network, forced failure, restart."""
    built_images()
    network = create_network(internal=True)
    stub_dir = new_data_dir()
    stub = start_plain(
        IMAGE,
        "python",
        "/srv/langfuse_stub.py",
        "--host",
        ALL_INTERFACES,
        "--port",
        "8000",
        "--project-id",
        "proj-other",
        "--counts",
        "/stub/counts.json",
        network=network,
        volumes={
            stub_dir: "/stub",
            Path(__file__).parents[1] / "deploy/langfuse_stub.py": "/srv/langfuse_stub.py:ro",
        },
        name_hint="stub",
    )
    wait_for(
        lambda: (
            stub.exec(
                "python", "-c", "import socket; socket.create_connection(('127.0.0.1', 8000), 2)"
            ).returncode
            == 0
        ),
        timeout=60,
        what="the stub Langfuse to listen",
    )
    s = session_sentinels()
    langfuse = {
        "LANGFUSE_PUBLIC_KEY": s["langfuse-pk"],
        "LANGFUSE_SECRET_KEY": s["langfuse-sk"],
        "LANGFUSE_BASE_URL": f"http://{stub.name}:8000",
        "LANGFUSE_PROJECT_ID": "proj-aea50",
    }
    data_dir = new_data_dir()
    app = start(
        data_dir=data_dir,
        network=network,
        restart="on-failure",
        env=sentinel_env(langfuse=langfuse),
        fault_once=True,
        name_hint="r2",
    )
    _restarted(data_dir, app)
    return Scenario(app, stub_counts=stub_dir / "counts.json")


@once
def run_open_turn() -> Scenario:
    """R3: no fault; a `running` turn is already in the data directory when the container starts."""
    built_images()
    data_dir = new_data_dir()
    turn_id = _prepare_running_turn(data_dir)
    app = start(data_dir=data_dir, env=sentinel_env(), name_hint="r3")
    wait_deploy_status(data_dir, "completed", timeout=240)
    return Scenario(app, turn_id)


# ----------------------------------------------------------------------------------- WF-13 (start-up record)


@pytest.mark.deploy
def test_wf13_startup_writes_deploy_record() -> None:
    """capture (AC-6): the start command writes one deploy_record with every field set; export reads off."""
    from scripts.agent_version import compute_agent_version, model_config, prompt_files

    app = run_first_boot().app
    records = db_rows(
        app.data_dir,
        "SELECT deploy_id, git_commit, agent_version, config_hash, trace_export_on, status FROM deploy_records",
    )
    assert len(records) == 1
    deploy_id, git_commit, agent_version, config_hash, trace_export_on, status = records[0]
    assert deploy_id
    assert git_commit == build_sha_value()
    assert agent_version == compute_agent_version(build_sha_value(), model_config(), prompt_files())
    assert VERSION.match(agent_version)
    assert re.fullmatch(r"[0-9a-f]{64}", config_hash or "")
    assert trace_export_on == 0
    assert status == "completed"


def _in_process(case: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Any]:
    from scripts.serve import create_deployed_app

    stub = start_stub("proj-aea50" if case == "right" else "proj-other", tmp_path / "counts.json")
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    try:
        index_dir = build_stand_in_index(tmp_path / "index")
        s = session_sentinels()
        langfuse = {
            "LANGFUSE_PUBLIC_KEY": s["langfuse-pk"],
            "LANGFUSE_SECRET_KEY": s["langfuse-sk"],
            "LANGFUSE_BASE_URL": stub.base_url,
            "LANGFUSE_PROJECT_ID": "proj-aea50",
        }
        if case == "missing_project_id":
            del langfuse["LANGFUSE_PROJECT_ID"]
        monkeypatch.chdir(ROOT)
        apply_env(monkeypatch, host_env(data_dir, index_dir=index_dir, langfuse=langfuse))
        with TestClient(create_deployed_app()):
            wait_for(
                lambda: db_rows(data_dir, "SELECT 1 FROM deploy_records WHERE status = 'completed'") != [],
                timeout=20,
                every=0.5,
                what="the in-process deploy record to complete",
            )
            return {
                "alerts": db_rows(
                    data_dir, "SELECT alert_type, reason_code FROM health_events WHERE kind = 'alert_fired'"
                ),
                "export": [r[0] for r in db_rows(data_dir, "SELECT trace_export_on FROM deploy_records")],
                "counts": stub.counts(),
            }
    finally:
        stub.close()
        logging.captureWarnings(False)


@pytest.mark.parametrize("case", ["right", "wrong", "missing_project_id"])
def test_wf13_wrong_project_keys_turn_export_off(
    case: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """capture (AC-8, MOD-6): right project id -> no alert; another id -> one wrong_project alert and 0 spans sent;
    a missing Langfuse value -> NullTraceSink, no alert and no project check."""
    result = _in_process(case, monkeypatch, tmp_path)
    counts = result["counts"]
    if case == "right":
        assert result["alerts"] == []
        assert counts["project_checks"] >= 1
    elif case == "wrong":
        assert result["alerts"] == [("trace_export_failed", "wrong_project")]
        assert counts["project_checks"] >= 1
        assert counts["spans"] == 0
    else:
        assert result["alerts"] == []
        assert counts["project_checks"] == 0
        assert counts["spans"] == 0


@BLOCKED_AEA_19_FU
@pytest.mark.parametrize(("case", "expected"), [("right", 1), ("wrong", 0), ("missing_project_id", 0)])
def test_wf13_deploy_record_reads_export_state(
    case: str, expected: int, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """capture (AC-8, plan-added): the deploy_record states export on only for the matching project."""
    assert _in_process(case, monkeypatch, tmp_path)["export"] == [expected]


@pytest.mark.deploy
def test_wf13_startup_logs_allow_listed() -> None:
    """negative (AC-18): every start-up log line is one allow-listed JSON record; no sentinel in a line or the row."""
    app = run_first_boot().app
    lines = app.logs()
    assert lines, "the container wrote no log lines"
    assert_allow_listed(json_lines(lines))
    _no_sentinels("\n".join(lines), what="start-up logs")
    record = db_rows(app.data_dir, "SELECT * FROM deploy_records")
    _no_sentinels(json.dumps(record, default=str), what="deploy_record")


@pytest.mark.deploy
def test_wf13_deploy_record_status() -> None:
    """capture (AC-19): completed once /healthz answers; a start with the index removed is failed, never completed."""
    ok = run_first_boot().app
    statuses = {r[0] for r in db_rows(ok.data_dir, "SELECT status FROM deploy_records")}
    assert statuses == {"completed"}

    built_images()
    data_dir = new_data_dir()
    broken = start(IMAGE_NOINDEX, data_dir=data_dir, env=sentinel_env(), restart="no", name_hint="noindex")
    wait_for(lambda: not broken.is_running(), timeout=120, every=2.0, what="the index-less container to exit")
    failed = db_rows(data_dir, "SELECT status FROM deploy_records")
    assert [r[0] for r in failed] == ["failed"]
    assert {r[0] for r in failed} <= STATUSES


@BLOCKED_AEA_40
@pytest.mark.deploy
def test_wf13_startup_sweeps_running_turns() -> None:
    """failure (AC-20): a turn left running is failed / degraded_handoff / timeout; one turn_sweep line, ids and
    a count only."""
    scenario = run_open_turn()
    row = db_rows(
        scenario.app.data_dir,
        "SELECT status, outcome, degrade_reason FROM turns WHERE turn_id = ?",
        (scenario.turn_id,),
    )
    assert row == [("failed", "degraded_handoff", "timeout")]
    sweeps = [r for r in json_lines(scenario.app.logs()) if r.get("record") == "turn_sweep"]
    assert len(sweeps) == 1
    assert sweeps[0]["count"] == 1
    assert set(sweeps[0]) <= ALLOWED_LOG_KEYS["turn_sweep"]


# ----------------------------------------------------------------------------------- WF-14 (ingestion)


@pytest.mark.deploy
def test_wf14_manifest_and_index_in_image(tmp_path: Path) -> None:
    """capture (AC-9, WP-1): 17 manifest rows; every non-current row holds 0 chunks, including the stale membership
    twin; no passage from archive/ or the staff-only notes; the run record agrees with the index record."""
    built_images()
    index = read_from_image(IMAGE, "/app/index", tmp_path / "index")
    manifest = json.loads((index / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) == 17
    assert all(r.get("status") and r.get("parse_method") for r in manifest)
    by_path = {r["path"]: r for r in manifest}
    stale = by_path["archive/comfort_club_overview.md"]
    assert stale["status"] == "excluded"
    assert all(r["chunks"] == 0 for r in manifest if r["status"] != "current")
    assert stale["chunks"] == 0

    passages = [
        json.loads(line)
        for line in (index / "passages.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert passages
    for p in passages:
        assert not str(p["file"]).startswith("archive/")
        assert not str(p["passage_id"]).startswith("archive/")
        assert p["file"] != "internal/agent_discretion_notes.md"
    notes = json.loads((index / "staff_notes.json").read_text(encoding="utf-8"))
    assert all(n["file"] == "internal/agent_discretion_notes.md" for n in notes)

    record = json.loads((index / "index_record.json").read_text(encoding="utf-8"))
    run = json.loads((index / "ingest_run.json").read_text(encoding="utf-8"))
    assert run["ingest_run_id"]
    assert run["manifest_hash"] == record["manifest_hash"]
    assert run["chunks"] == record["chunks"]


@pytest.mark.deploy
def test_wf14_index_clean_and_offline(tmp_path: Path) -> None:
    """negative (AC-21): no context sentinel in any index artefact; re-running ingest offline reproduces the build."""
    built_images()
    index = read_from_image(IMAGE, "/app/index", tmp_path / "index")
    artefacts = sorted(p for p in index.iterdir() if p.is_file())
    assert len(artefacts) == 6
    needles = [n.encode() for n in context_sentinels()]
    for artefact in artefacts:
        data = artefact.read_bytes()
        assert not any(n in data for n in needles), f"{artefact.name}: sentinel found"

    record = json.loads((index / "index_record.json").read_text(encoding="utf-8"))
    result = run_in_image(
        IMAGE_INDEX,
        "sh",
        "-c",
        "python -m meridian.retrieval.ingest --kb-dir /build/knowledge_base "
        "--transcriptions-dir /build/kb_transcriptions --out-dir /tmp/reindex",
        env={"HF_HUB_OFFLINE": "1"},
        network="none",
    )
    assert result.returncode == 0
    last = result.stdout.strip().splitlines()[-1]
    assert f"manifest_hash={record['manifest_hash']}" in last
    assert f"chunks={record['chunks']}" in last


# ----------------------------------------------------------------------------------- WF-15 (reset script)


@contextmanager
def _reset_run(
    *, message: str
) -> Iterator[tuple[TempStore, subprocess.CompletedProcess[str], dict[str, int]]]:
    with demo_store() as (store, cp):
        make_dirty_demo(store, cp, open_chats=1, customer_message=message)
        before = {t: count(store.db_path, t) for t in KEPT_TABLES if t in KEPT_COUNTED}
        cp.close()
        proc = subprocess.run(
            [sys.executable, "-m", "scripts.reset"],
            cwd=ROOT,
            env=host_env(store.data_dir),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        yield store, proc, before


KEPT_COUNTED = ("spend_ledger", "health_events", "deploy_records", "eval_runs", "job_runs")


def _person_message() -> str:
    s = session_sentinels()
    return f"My name is {s['name']}, call me on {s['phone']}"


@BLOCKED_AEA_29_30
def test_wf15_reset_script() -> None:
    """capture (AC-10): the operator script writes one reset_event and one seed_event, restores the issued tables,
    empties the cleared tables apart from the four seeds, and leaves the kept tables alone."""
    with _reset_run(message=_person_message()) as (store, proc, before):
        assert proc.returncode == 0
        out_lines = proc.stdout.strip().splitlines()
        assert len(out_lines) == 1
        match = re.fullmatch(
            r"reset status=done request_id=([0-9a-f-]{36}) open_chats_ended=1 roles_reset=(\d+)", out_lines[0]
        )
        assert match, "stdout must be exactly the one status line"
        request_id = match.group(1)

        reset = rows(
            store.db_path,
            "SELECT reset_id, asked_by_role, asked_by_session, request_id, restored_json, open_chats_ended, "
            "roles_reset, checkpoints_cleared FROM reset_events ORDER BY at_wall DESC, rowid DESC",
        )
        assert len(reset) == 1
        reset_id, role, session, rid, restored, ended, _roles, cleared = reset[0]
        assert (role, session, rid, ended, cleared) == (None, None, request_id, 1, 1)
        assert restored and restored != "{}"
        seeds = rows(store.db_path, "SELECT reset_id, seed_count, label FROM seed_events ORDER BY rowid DESC")
        assert seeds[0] == (reset_id, 4, "demo seed")

        for table in ISSUED_TABLES:
            assert rows(store.db_path, f"SELECT * FROM {table} ORDER BY rowid") == issued_rows(  # noqa: S608
                store.issued_path, table
            )
        assert rows(store.db_path, "SELECT COUNT(*) FROM conversations WHERE run_tag != 'seed'") == [(0,)]
        assert rows(store.db_path, "SELECT COUNT(*) FROM cases WHERE seed = 0") == [(0,)]
        for table in ("flags", "identity_codes", "demo_inbox", "identity_threads"):
            assert count(store.db_path, table) == 0
        after = {t: count(store.db_path, t) for t in before}
        assert after == before


@BLOCKED_AEA_29_30
def test_wf15_reset_holds_no_values() -> None:
    """negative (AC-22): sentinels in the script's environment and in the data appear in neither event row, stdout
    nor stderr."""
    with _reset_run(message=_person_message()) as (store, proc, _before):
        assert proc.returncode == 0
        events = rows(store.db_path, "SELECT * FROM reset_events") + rows(
            store.db_path, "SELECT * FROM seed_events"
        )
        _no_sentinels(json.dumps(events, default=str), what="event rows")
        _no_sentinels(proc.stdout, what="stdout")
        _no_sentinels(proc.stderr, what="stderr")


def _run_script(args: list[str], data_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", *args],
        cwd=ROOT,
        env=host_env(data_dir),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


@pytest.mark.parametrize(
    "script",
    ["agent_version", "image_check", pytest.param("reset", marks=BLOCKED_AEA_29_30)],
)
def test_ops_output_has_no_values(script: str, tmp_path: Path) -> None:
    """negative (AC-15): the three scripts print IDs, counts and statuses only; no sentinel in stdout or stderr."""
    if script == "reset":
        with _reset_run(message=_person_message()) as (_store, proc, _before):
            assert proc.returncode == 0
            outputs = [proc.stdout, proc.stderr]
    else:
        if script == "agent_version":
            proc = _run_script(["scripts.agent_version"], tmp_path)
        else:
            index_dir = build_stand_in_index(tmp_path / "index")
            proc = _run_script(["scripts.image_check", "--index-dir", str(index_dir)], tmp_path)
        assert proc.returncode == 0, f"{script} exited {proc.returncode}"
        outputs = [proc.stdout, proc.stderr]
    for text in outputs:
        _no_sentinels(text, what=f"{script} output")
    stderr = outputs[1]
    if stderr.strip():
        json_lines(stderr.splitlines())


# ----------------------------------------------------------------------------------- WF-16 (first boot, seed)


def _schema_tables() -> list[str]:
    names: list[str] = []
    for path in schema_files():
        names += re.findall(
            r"CREATE TABLE IF NOT EXISTS\s+([A-Za-z_][A-Za-z0-9_]*)", path.read_text(encoding="utf-8")
        )
    return names


@BLOCKED_AEA_29
@pytest.mark.deploy
def test_wf16_first_boot_seed() -> None:
    """capture (AC-11): schemas applied, four seeds (MHC-C-0005..0008, run_tag seed), one seed_event; a second start
    writes no second seed."""
    app = run_first_boot().app
    present = {r[0] for r in db_rows(app.data_dir, "SELECT name FROM sqlite_master WHERE type='table'")}
    assert set(_schema_tables()) <= present
    refs = [
        r[0] for r in db_rows(app.data_dir, "SELECT case_ref FROM cases WHERE seed = 1 ORDER BY case_ref")
    ]
    assert refs == ["MHC-C-0005", "MHC-C-0006", "MHC-C-0007", "MHC-C-0008"]
    tags = db_rows(
        app.data_dir,
        "SELECT DISTINCT c.run_tag FROM conversations c JOIN cases k ON k.thread_id = c.thread_id WHERE k.seed = 1",
    )
    assert tags == [("seed",)]
    events = db_rows(app.data_dir, "SELECT seed_count, label, reset_id FROM seed_events")
    assert events == [(4, "demo seed", None)]

    second = run_first_boot_then_restart().app
    assert db_rows(second.data_dir, "SELECT COUNT(*) FROM seed_events") == [(1,)]
    assert db_rows(second.data_dir, "SELECT COUNT(*) FROM deploy_records WHERE status = 'completed'") == [
        (2,)
    ]


@BLOCKED_AEA_31_FU
@pytest.mark.deploy
def test_wf16_seed_event_carries_deploy_id() -> None:
    """capture (AC-11, plan-added): the first-boot seed_event names the deploy that wrote it."""
    app = run_first_boot().app
    deploy = db_rows(app.data_dir, "SELECT deploy_id FROM deploy_records ORDER BY rowid LIMIT 1")
    seed = db_rows(app.data_dir, "SELECT deploy_id FROM seed_events")
    assert seed == deploy
    assert seed[0][0]


@BLOCKED_AEA_29
@pytest.mark.deploy
def test_wf16_first_boot_offline_and_clean() -> None:
    """negative (AC-23): offline first boot with sentinels completes; allow-listed logs; no sentinel in a log line,
    the seed_event or any text column of the working copy."""
    app = run_first_boot().app
    assert db_rows(app.data_dir, "SELECT COUNT(*) FROM seed_events") == [(1,)]
    lines = app.logs()
    assert_allow_listed(json_lines(lines))
    _no_sentinels("\n".join(lines), what="boot logs")
    _no_sentinels(
        json.dumps(db_rows(app.data_dir, "SELECT * FROM seed_events"), default=str), what="seed_event"
    )
    cells = db_text_columns(app.data_dir)
    leaked = [(t, c) for t, c, v in cells if any(s in v for s in _sentinel_values())]
    assert leaked == [], f"sentinel found in text columns: {sorted(set(leaked))}"


# ----------------------------------------------------------------------------------- WF-17 (health, restart)


@pytest.mark.deploy
def test_wf17_forced_failure_restarts() -> None:
    """capture (AC-12): /healthz answers 200 unsigned; forced failure -> three failed probes, a restart row and one
    container restart."""
    ok = run_first_boot().app
    assert ok.exec("python", "-c", HEALTHZ).returncode == 0

    scenario = run_forced_failure()
    assert scenario.app.restart_count() == 1
    events = db_rows(
        scenario.app.data_dir, "SELECT kind, at_wall, reason_code FROM health_events ORDER BY id"
    )
    kinds = [e[0] for e in events]
    restart_at = kinds.index("restart")
    failed = [e for e in events[:restart_at] if e[0] == "check_failed"]
    assert len(failed) >= 3
    assert events[restart_at][2].startswith("healthz_failed_")
    stamps = [datetime.fromisoformat(e[1]) for e in failed]
    assert all(b - a >= timedelta(seconds=10) for a, b in itertools.pairwise(stamps))
    newest = db_rows(scenario.app.data_dir, "SELECT status FROM deploy_records ORDER BY rowid DESC LIMIT 1")
    assert newest == [("completed",)]


@BLOCKED_AEA_32_FU
@pytest.mark.deploy
def test_wf17_health_events_carry_ids() -> None:
    """capture (AC-24): each check_failed / restart row has its own health_check_id and the writing process's
    deploy_id."""
    scenario = run_forced_failure()
    data_dir = scenario.app.data_dir
    first_deploy = db_rows(data_dir, "SELECT deploy_id FROM deploy_records ORDER BY rowid LIMIT 1")[0][0]
    events = db_rows(
        data_dir,
        "SELECT kind, health_check_id, deploy_id FROM health_events WHERE kind IN ('check_failed', 'restart') "
        "ORDER BY id",
    )
    assert events
    assert all(e[1] for e in events), "every row needs a health_check_id"
    failed_ids = [e[1] for e in events if e[0] == "check_failed"]
    assert len(failed_ids) == len(set(failed_ids)), "health_check_id must be distinct per probe"
    assert {e[2] for e in events} == {first_deploy}


@pytest.mark.deploy
def test_wf17_restart_offline_and_clean() -> None:
    """negative (AC-25): the restart path works under --network none with sentinels and leaks none of them."""
    scenario = run_forced_failure()
    assert scenario.app.restart_count() == 1
    health = db_rows(scenario.app.data_dir, "SELECT * FROM health_events")
    _no_sentinels(json.dumps(health, default=str), what="health_events")
    _no_sentinels("\n".join(scenario.app.logs()), what="container logs")


@BLOCKED_AEA_40
@pytest.mark.deploy
def test_wf17_restart_sweeps_open_turn() -> None:
    """failure (AC-26): a running turn at the forced failure is failed / degraded_handoff / timeout after restart."""
    scenario = run_forced_failure()
    row = db_rows(
        scenario.app.data_dir,
        "SELECT status, outcome, degrade_reason FROM turns WHERE turn_id = ?",
        (scenario.turn_id,),
    )
    assert row == [("failed", "degraded_handoff", "timeout")]


@pytest.mark.deploy
def test_wf17_restart_rechecks_project() -> None:
    """capture (AC-27): the restarted process re-checks the Langfuse project; export stays off, the alert state is
    firing, and the stub receives 0 spans across both processes."""
    scenario = run_stub_restart()
    assert scenario.app.restart_count() == 1
    assert scenario.stub_counts is not None
    counts = json.loads(scenario.stub_counts.read_text(encoding="utf-8"))
    assert counts["project_checks"] == 2
    assert counts["spans"] == 0

    snapshot = SqliteUnitOfWorkFactory(snapshot_db(scenario.app.data_dir))
    with snapshot() as tx:
        states = tx.ops.health.latest_alert_states()
    assert states["trace_export_failed"].state == "firing"
    alerts = db_rows(
        scenario.app.data_dir,
        "SELECT reason_code FROM health_events WHERE kind = 'alert_fired' AND alert_type = 'trace_export_failed'",
    )
    assert alerts == [("wrong_project",)]


@BLOCKED_AEA_19_FU
@pytest.mark.deploy
def test_wf17_restart_export_state_per_process() -> None:
    """capture (AC-27, plan-added): both processes' deploy records state trace export off."""
    scenario = run_stub_restart()
    exports = db_rows(scenario.app.data_dir, "SELECT trace_export_on FROM deploy_records ORDER BY rowid")
    assert exports == [(0,), (0,)]
