"""WF-15 operator reset (AEA-50): restore the demo to its seeded state on a stopped service.

One stdout line per run: ids, counts and statuses only. Never prints a row, a name, a phone, a message or a setting.
"""

from __future__ import annotations

import functools
import importlib
import os
import sys
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from meridian.adapters.checkpointer import CHECKPOINTS_DB_NAME, Checkpointer
from meridian.adapters.sqlite.db import SqliteUnitOfWorkFactory
from meridian.adapters.sqlite.migrate import WORKING_DB_NAME, migrate, restore_working_copy
from meridian.config import Settings, SettingsError
from meridian.domain.common import RequestId
from meridian.services.reset import ResetDone, ResetService, seed_demo
from meridian.services.reset_gate import ResetGate
from meridian.web.logging import install_log_formatter


def _say(line: str) -> None:
    sys.stdout.write(line + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    del argv  # no options: the environment names the data directory, as for the service
    install_log_formatter()
    try:
        settings = Settings.from_env(os.environ)
    except SettingsError as exc:
        fields = ",".join(p.field for p in exc.problems)
        _say(f"reset status=refused reason=settings variables={fields}")
        return 2

    data_dir = Path(settings.data_dir)
    db_path = data_dir / WORKING_DB_NAME
    if not db_path.exists():
        _say("reset status=refused reason=no_working_copy")
        return 2
    issued_path = Path(settings.issued_db_path)
    migrate(db_path, issued_path=issued_path)  # DDL only: the copy branch cannot run, the file exists

    try:
        handoff = importlib.import_module("meridian.services.handoff")
        demo = importlib.import_module("meridian.services.demo")
    except ImportError:
        _say("reset status=refused reason=missing_module")
        return 3

    checkpointer = Checkpointer(data_dir / CHECKPOINTS_DB_NAME)
    try:
        service = ResetService(
            SqliteUnitOfWorkFactory(db_path),
            ResetGate(),
            functools.partial(restore_working_copy, issued_path=issued_path),
            checkpointer.clearing,
            functools.partial(seed_demo, assembler=handoff.BriefAssembler()),
            format_clock=demo.format_clock,
        )
        request_id = RequestId(str(uuid.uuid4()))
        result = service.reset(datetime.now(UTC), request_id=request_id, session_id=None, role=None)
    finally:
        checkpointer.close()

    if isinstance(result, ResetDone):
        _say(
            f"reset status=done request_id={request_id} "
            f"open_chats_ended={result.open_chats_ended} roles_reset={result.roles_reset}"
        )
        return 0
    _say(f"reset status=failed request_id={request_id} code={result.code}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
