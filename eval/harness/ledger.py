"""Judge spend ledger and the app-cap preflight (AC-13)."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final
from zoneinfo import ZoneInfo

CHICAGO: Final = ZoneInfo("America/Chicago")
# [A] SP-1 option B maximum per conversation; replaced by E-1's measured mean at Stage 9.
DEFAULT_JUDGE_CAP_USD: Final = 5.0
RUN_COST_PER_CONVERSATION_USD: Final = 0.039


def _utc_now() -> datetime:
    return datetime.now(UTC)


class JudgeSpendCapReached(Exception):
    """The judge's own daily cap would be passed; the call is not made."""


class SpendPreflightRefused(Exception):
    """The run could pass the app's daily spend cap."""


class HarnessLedger:
    def __init__(
        self, cap_usd: float = DEFAULT_JUDGE_CAP_USD, *, path: Path, now: Callable[[], datetime] = _utc_now
    ) -> None:
        self._cap = cap_usd
        self._path = path
        self._now = now

    @property
    def cap_usd(self) -> float:
        return self._cap

    def _day_file(self) -> Path:
        return self._path / f"{self._now().astimezone(CHICAGO).date().isoformat()}.jsonl"

    def spent_today(self) -> float:
        day_file = self._day_file()
        if not day_file.is_file():
            return 0.0
        total = 0.0
        for line in day_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                total += float(json.loads(line)["cost_usd"])
        return total

    def charge(self, cost_usd: float) -> None:
        if cost_usd < 0:
            raise ValueError("cost must not be negative")
        if self.spent_today() + cost_usd > self._cap + 1e-9:
            raise JudgeSpendCapReached("judge spend cap for today would be passed")
        self._path.mkdir(parents=True, exist_ok=True)
        entry = {"at": self._now().astimezone(UTC).isoformat(), "cost_usd": cost_usd}
        with self._day_file().open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")


def preflight_spend(monitoring: dict[str, Any], *, run_estimate_usd: float, judge_cap_usd: float) -> None:
    spend = monitoring.get("spend")
    if not isinstance(spend, dict) or "today_cents" not in spend or "cap_cents" not in spend:
        raise SpendPreflightRefused("monitoring has no spend block")
    today = float(spend["today_cents"]) / 100
    cap = float(spend["cap_cents"]) / 100
    if today + run_estimate_usd + judge_cap_usd > cap + 1e-9:
        raise SpendPreflightRefused(
            f"today {today:.2f} + estimate {run_estimate_usd:.2f} + judge cap {judge_cap_usd:.2f} > cap {cap:.2f}"
        )
