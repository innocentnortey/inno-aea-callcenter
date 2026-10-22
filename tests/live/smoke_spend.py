"""Spend pre-flight and the between-case stop rule (AEA-61; models.md section 6, DO-7 M-25/M-26).

Money is compared in integer micro-dollars so that 29.766 + 0.234 equals 30.0 exactly (PD-5).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Final

PER_CASE_ESTIMATE_USD: Final = 0.039  # SP-1 option B max per conversation [M] (DO-7 M-25)
RUN_ESTIMATE_USD: Final = 0.234  # 6 x 0.039 [C]
SPENT_ENV: Final = "LIVE_SMOKE_SPENT_TODAY_USD"
SPEND_STOP_KINDS: Final = frozenset({"provider_spend_cap", "our_spend_limit"})
NOT_RUN_SPEND: Final = "NOT_RUN: spend"


class SmokeRefused(RuntimeError):
    """The run will not start. The message names figures and env names only, never a value of a secret."""


def micros(usd: float) -> int:
    return round(usd * 1_000_000)


assert micros(6 * PER_CASE_ESTIMATE_USD) == micros(RUN_ESTIMATE_USD)


def preflight(environ: Mapping[str, str], *, cap_usd: float) -> float:
    raw = environ.get(SPENT_ENV, "").strip()
    if not raw:
        raise SmokeRefused(f"refused: {SPENT_ENV} is not set (the gate::paid approver states today's spend)")
    try:
        figure = float(raw)
    except ValueError:
        raise SmokeRefused(f"refused: {SPENT_ENV} is not a finite number") from None
    if not math.isfinite(figure):
        raise SmokeRefused(f"refused: {SPENT_ENV} is not a finite number")
    if figure < 0:
        raise SmokeRefused(f"refused: {SPENT_ENV}={raw} is negative")
    if micros(figure) + micros(RUN_ESTIMATE_USD) > micros(cap_usd):
        raise SmokeRefused(
            f"refused: {SPENT_ENV}={figure:.3f} + estimate {RUN_ESTIMATE_USD:.3f} = "
            f"{figure + RUN_ESTIMATE_USD:.3f} > daily cap {cap_usd:.2f}"
        )
    return figure


def should_stop(run_total_usd: float, cases_left: int, *, spent_today_usd: float, cap_usd: float) -> bool:
    return micros(run_total_usd) + micros(PER_CASE_ESTIMATE_USD) * cases_left > micros(cap_usd) - micros(
        spent_today_usd
    )
