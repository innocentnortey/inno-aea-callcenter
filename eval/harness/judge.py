"""The judge: a Protocol, the Anthropic implementation, and calibration. Advisory until calibrated (AC-3)."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any, Final, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from eval.harness.ledger import HarnessLedger

JUDGE_MODEL: Final = "claude-sonnet-5-5"  # EVQ-2: Sonnet 5.5 until Innocent names another
PRICE_IN_PER_MTOK: Final = 2.00  # stage7/models.md section 2 ANTHROPIC_PRICES
PRICE_OUT_PER_MTOK: Final = 10.00
CALIBRATION_MIN_LABELS: Final = 20
CALIBRATION_MIN_AGREEMENT: Final = 0.8

JUDGE_SYSTEM: Final = (
    "You grade one customer-service reply against a checklist. Judge each claim on its own, only from the "
    "reply and the evidence. Answer with JSON only."
)


class JudgeVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    index: int
    passed: bool
    quote: str


class Judge(Protocol):
    @property
    def model(self) -> str: ...

    def judge(
        self, *, reply: str, evidence: Sequence[str], rubric: Sequence[str]
    ) -> tuple[JudgeVerdict, ...]: ...


class CalibrationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    judge_model: str
    labels: int = Field(ge=0)
    agreement: float = Field(ge=0, le=1)
    recorded_on: date
    labelled_by: str


def load_calibration(path: Path) -> CalibrationRecord | None:
    if not path.is_file():
        return None
    return CalibrationRecord.model_validate_json(path.read_bytes())


def is_calibrated(record: CalibrationRecord | None, *, judge_model: str) -> bool:
    return (
        record is not None
        and record.judge_model == judge_model
        and record.labels >= CALIBRATION_MIN_LABELS
        and record.agreement >= CALIBRATION_MIN_AGREEMENT
    )


class _Verdicts(BaseModel):
    model_config = ConfigDict(extra="ignore")
    verdicts: tuple[JudgeVerdict, ...]


class AnthropicJudge:
    def __init__(
        self, client: Any, *, ledger: HarnessLedger, model: str = JUDGE_MODEL, max_tokens: int = 800
    ) -> None:
        self._client = client
        self._ledger = ledger
        self._model = model
        self._max_tokens = max_tokens
        self.calls = 0
        self.spend_usd = 0.0

    @property
    def model(self) -> str:
        return self._model

    def judge(
        self, *, reply: str, evidence: Sequence[str], rubric: Sequence[str]
    ) -> tuple[JudgeVerdict, ...]:
        prompt = (
            "Evidence (statements the reply is allowed to make):\n"
            + "\n".join(f"- {e}" for e in evidence)
            + "\n\nReply:\n<<<\n"
            + reply
            + "\n>>>\n\nClaims (answer each true or false):\n"
            + "\n".join(f"{i}. {c}" for i, c in enumerate(rubric))
            + '\n\nReturn {"verdicts": [{"index": 0, "passed": true, '
            '"quote": "<the reply words that decide it, or empty>"}]}'
        )
        estimate = (
            math.ceil(len(prompt) / 3) * PRICE_IN_PER_MTOK + self._max_tokens * PRICE_OUT_PER_MTOK
        ) / 1_000_000
        self._ledger.charge(estimate)  # before the call: a refused charge means no call at all
        message = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            temperature=0,
            system=JUDGE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        self.calls += 1
        self.spend_usd += estimate
        try:
            block = next(b for b in message.content if getattr(b, "type", None) == "text")
            return _Verdicts.model_validate(json.loads(block.text)).verdicts
        except (StopIteration, ValueError, ValidationError, AttributeError, TypeError):
            return ()
