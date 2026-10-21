"""AEA-29 Step 9: the register_cases hunk binds the three objects, tolerates unbound siblings, resolves staff guidance."""

from __future__ import annotations

import hashlib
import json
import types
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI

from meridian.domain.handoff import Brief, HandoffReason
from meridian.policy.handoff import STAFF_GUIDANCE_FOR
from meridian.policy.limits import Limits
from meridian.services.cases import CaseService
from meridian.services.handoff import BriefAssembler, CaseWriteFailed, HandoffService
from meridian.web.container import Container, ContainerError, Key, register_cases
from meridian.web.deps import CASE_SERVICE, HANDOFF_SERVICE
from meridian.web.middleware import PublicPaths, WebShellState
from tests.api.web_shell_support import make_settings
from tests.fixtures.sqlite import TempStore, temp_sqlite
from tests.services._case_fixtures import NOW, ctx, new_thread, ref, request, rows_for_thread


def _wall() -> datetime:
    return datetime(2026, 10, 21, tzinfo=UTC)


def _app(tmp_path: Path) -> FastAPI:
    app = FastAPI()
    app.state.web_shell = WebShellState(
        settings=make_settings(tmp_path), wall_clock=_wall, public_paths=PublicPaths()
    )
    return app


def _index(directory: Path, *, skip_refund: bool = False) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    passages: list[dict[str, str]] = []
    for reason, prefixes in STAFF_GUIDANCE_FOR.items():
        for prefix in prefixes:
            if skip_refund and reason is HandoffReason.REFUND:
                continue
            text = prefix + " (synthetic test passage)."
            passages.append(
                {
                    "passage_id": f"internal/agent_discretion_notes.md#{len(passages)}",
                    "file": "internal/agent_discretion_notes.md",
                    "section": "Agents may NOT",
                    "version_label": "undated",
                    "text": text,
                    "text_sha256": hashlib.sha256(text.strip().encode()).hexdigest(),
                }
            )
    (directory / "staff_notes.json").write_text(json.dumps(passages), encoding="utf-8")
    return directory


class _Demo:
    def presence(self, tx: Any = None) -> str:
        return "nobody_online"


def _container(
    tmp_path: Path, db: TempStore, *, index_dir: Path | None, demo: bool = False
) -> tuple[Container, FastAPI]:
    settings = types.SimpleNamespace(index_dir=index_dir)
    c = Container(settings=settings, limits=Limits())
    c.provide(Key[Any]("uow_factory"), lambda _c: db.uow)
    if demo:
        c.provide(Key[Any]("demo_service"), lambda _c: _Demo())
        c.provide(Key[Any]("demo_clock"), lambda _c: types.SimpleNamespace(now=lambda: NOW))
    app = _app(tmp_path)
    register_cases(c, app, settings=settings, limits=c.limits)
    return c, app


def test_register_binds_services(tmp_path: Path) -> None:
    with temp_sqlite() as db:
        c, _ = _container(tmp_path, db, index_dir=None)
        c.build()
        assert isinstance(c.get(CASE_SERVICE), CaseService)
        assert isinstance(c.get(HANDOFF_SERVICE), HandoffService)
        assert isinstance(c.get(Key[Any]("brief_assembler")), BriefAssembler)
    doc = register_cases.__doc__ or ""
    assert "AEA-29" in doc and "No-op until" not in doc


def test_unbound_siblings_name_the_key(tmp_path: Path) -> None:
    with temp_sqlite() as db:
        c, _ = _container(tmp_path, db, index_dir=None)
        c.build()
        with db.uow(write=True) as tx:
            thread, _ = new_thread(tx, customer_text="I want a person.")
            tx.commit()
        req = request(thread, HandoffReason.CUSTOMER_REQUESTED_PERSON)
        with pytest.raises(CaseWriteFailed) as err:
            c.get(HANDOFF_SERVICE).open(req, ctx(thread, req.turn_id))
        assert isinstance(err.value.__cause__, RuntimeError)
        assert str(err.value.__cause__) == "not bound: demo_service"
        with pytest.raises(RuntimeError, match="not bound: demo_clock"):
            c.get(CASE_SERVICE).attach_brief(ref(9), cast(Brief, types.SimpleNamespace(case_ref=ref(9))))


def test_staff_guidance_resolved_from_index(tmp_path: Path) -> None:
    with temp_sqlite() as db:
        c, _ = _container(tmp_path, db, index_dir=_index(tmp_path / "idx"), demo=True)
        c.build()
        with db.uow(write=True) as tx:
            thread, _ = new_thread(tx, customer_text="I want a full refund.")
            tx.commit()
        req = request(thread, HandoffReason.REFUND)
        c.get(HANDOFF_SERVICE).open(req, ctx(thread, req.turn_id))
        with db.uow() as tx:
            assert rows_for_thread(tx, thread)["lookup_log"] == 1
            (row,) = tx.core.lookup_log.for_thread(thread)
        expected = STAFF_GUIDANCE_FOR[HandoffReason.REFUND][0] + " (synthetic test passage)."
        assert row.tool == "staff_guidance"
        assert row.result_seen == hashlib.sha256(expected.strip().encode()).hexdigest()


def test_unknown_prefix_fails_build(tmp_path: Path) -> None:
    with temp_sqlite() as db:
        c, _ = _container(tmp_path, db, index_dir=_index(tmp_path / "idx", skip_refund=True))
        with pytest.raises(ValueError, match="refund"):
            c.build()


def test_missing_index_gives_no_guidance(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with temp_sqlite() as db:
        c, _ = _container(tmp_path, db, index_dir=empty, demo=True)
        c.build()
        with db.uow(write=True) as tx:
            thread, _ = new_thread(tx, customer_text="I want a full refund.")
            tx.commit()
        req = request(thread, HandoffReason.REFUND)
        c.get(HANDOFF_SERVICE).open(req, ctx(thread, req.turn_id))
        with db.uow() as tx:
            assert rows_for_thread(tx, thread)["lookup_log"] == 0
            assert rows_for_thread(tx, thread)["cases"] == 1


def test_register_ignores_app_without_web_shell(tmp_path: Path) -> None:
    c = Container(settings=types.SimpleNamespace(index_dir=None), limits=Limits())
    register_cases(c, FastAPI(), settings=c.settings, limits=c.limits)
    c.build()
    with pytest.raises(ContainerError, match="not provided"):
        c.get(CASE_SERVICE)
