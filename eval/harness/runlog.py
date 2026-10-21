"""Allow-listed JSON run-log lines: ids and counts only, never free text (AC-11, P-2)."""

from __future__ import annotations

import json
import re
from typing import Final, TextIO

from eval.harness.scrub import Scrubber

ALLOWED_LOG_KEYS: Final[frozenset[str]] = frozenset(
    {
        "event",
        "run_id",
        "suite",
        "split",
        "case_id",
        "repeat",
        "conversation_index",
        "turn_index",
        "thread_id",
        "turn_id",
        "status",
        "http_status",
        "outcome",
        "notice_code",
        "elapsed_ms",
        "count",
        "cases_expected",
        "cases_scored",
        "harness_commit",
        "harness_digest",
        "experiment_id",
        "agent_version",
        "reason",
        "expected_sha256",
        "actual_sha256",
        "report_path",
        "gate",
        "findings",
        "exit_code",
        "judge_calls",
        "judge_spend_usd",
    }
)
_SAFE_VALUE: Final = re.compile(r"[\w.:+#/@-]{0,200}")


class RunLog:
    def __init__(self, stream: TextIO, scrubber: Scrubber) -> None:
        self._stream = stream
        self._scrubber = scrubber

    def emit(self, event: str, **fields: str | int | float | bool | None) -> None:
        for key in ("event", *fields):
            if key not in ALLOWED_LOG_KEYS:
                raise ValueError("log key not allowed")
        for value in (event, *fields.values()):
            if isinstance(value, str) and not _SAFE_VALUE.fullmatch(value):
                raise ValueError("log value not allowed")
        line = json.dumps({"event": event, **fields}, sort_keys=True, separators=(",", ":"))
        self._scrubber.assert_absent(line, where="run log")
        self._stream.write(line + "\n")
        self._stream.flush()

    def say(self, text: str) -> None:
        """One plain-text line (a refusal message); the same leak check applies."""
        self._scrubber.assert_absent(text, where="run log")
        self._stream.write(text + "\n")
        self._stream.flush()
