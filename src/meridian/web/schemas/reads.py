"""Wire shapes for CON-18 to CON-20 (OpenAPI OwnerMetricsResponse, MonitoringResponse, EvalResponse). AEA-48.

The routes validate each MetricsReads mapping through these models (stage7/staff.md section 9, STF-17). Field names and
shapes are copied from the OpenAPI. Unknown keys are ignored here and named by the route (dropped_keys); a missing
required field or a broken rule raises ValidationError, which the route answers with 500. Three rules are stricter than
the OpenAPI (AEA-48-1): `unit` is count, ms or share; a share and every evaluation value lie in [0, 1]; and (id, label)
pairs are unique within one response (per run on CON-20, where the two splits and the headline repeat ids by design).
The reader stamps every time field; these models only check that each carries a UTC offset.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable, Mapping, Sequence
from typing import Final, Literal, Self, get_args

from pydantic import AwareDatetime, BaseModel, ConfigDict, ValidationError, model_validator
from pydantic_core import PydanticCustomError

MeasureUnit = Literal["count", "ms", "share"]
MEASURE_UNITS: Final[tuple[str, ...]] = get_args(MeasureUnit)
SHARE_OUT_OF_RANGE: Final = "share_out_of_range"
RATIO_OUT_OF_RANGE: Final = "ratio_out_of_range"
DUPLICATE_MEASURE: Final = "duplicate_measure"
OWN_RULES: Final[frozenset[str]] = frozenset({SHARE_OUT_OF_RANGE, RATIO_OUT_OF_RANGE, DUPLICATE_MEASURE})
_FIELD: Final = "field"  # the context key our own rules use to name the field they refuse
_MAX_ERRORS: Final = 10


class ReadModel(BaseModel):
    """Plain BaseModel, not MeridianModel: values pass through unchanged (no whitespace stripping) and extras drop."""

    model_config = ConfigDict(extra="ignore", frozen=True, hide_input_in_errors=True)


def _in_unit_range(value: int | float | None) -> bool:
    return value is None or 0 <= value <= 1


class Measure(ReadModel):
    id: str
    label: str
    numerator: int | None
    denominator: int | None
    unit: MeasureUnit
    value: int | float | None
    null_reason: str | None
    kind: Literal["measured", "estimate"]
    case_refs: list[str]

    @model_validator(mode="after")
    def _share_in_range(self) -> Self:
        if self.unit == "share" and not _in_unit_range(self.value):
            raise PydanticCustomError(
                SHARE_OUT_OF_RANGE, "a share value must lie in [0, 1]", {_FIELD: "value"}
            )
        return self


class Tile(ReadModel):
    id: str
    label: str
    value: int | float | None
    unit: MeasureUnit
    numerator: int | None
    denominator: int | None
    null_reason: str | None

    @model_validator(mode="after")
    def _share_in_range(self) -> Self:
        if self.unit == "share" and not _in_unit_range(self.value):
            raise PydanticCustomError(
                SHARE_OUT_OF_RANGE, "a share value must lie in [0, 1]", {_FIELD: "value"}
            )
        return self


class EvalMeasure(ReadModel):
    id: str
    label: str
    numerator: int
    denominator: int
    value: int | float
    min: int | float | None
    max: int | float | None
    target: str | None

    @model_validator(mode="after")
    def _ratio_in_range(self) -> Self:
        if not _in_unit_range(self.value):
            raise PydanticCustomError(
                RATIO_OUT_OF_RANGE, "an evaluation value must lie in [0, 1]", {_FIELD: "value"}
            )
        return self


def _indexed(
    name: str, items: Sequence[Measure | Tile | EvalMeasure]
) -> list[tuple[str, Measure | Tile | EvalMeasure]]:
    return [(f"{name}[{index}]", item) for index, item in enumerate(items)]


def _refuse_duplicates(items: Iterable[tuple[str, Measure | Tile | EvalMeasure]]) -> None:
    """Raise on the second occurrence of an (id, label) pair, naming its path, never its values."""
    seen: set[tuple[str, str]] = set()
    for path, item in items:
        pair = (item.id, item.label)
        if pair in seen:
            raise PydanticCustomError(
                DUPLICATE_MEASURE, "(id, label) pairs must be unique within one response", {_FIELD: path}
            )
        seen.add(pair)


# -- CON-18 getOwnerMetrics ------------------------------------------------------------------------------------
class NorthStarLink(ReadModel):
    label: str
    path: Literal["/eval"]


class MissedPromise(ReadModel):
    reference: str
    due_at: AwareDatetime
    outcome: str


class CaseLine(ReadModel):
    reference: str
    reason: str
    status: str


class OwnerMetricsResponse(ReadModel):
    as_of: AwareDatetime  # demo clock, stamped by the reader (STF-22)
    seeds_included: bool
    seed_count: int
    in_scope_correct_resolution: Measure
    measured_north_star_link: NorthStarLink
    promises_kept_on_time: Measure
    handoffs: Measure
    outcomes: list[Measure]
    handoffs_by_reason: list[Measure]
    missed_promises: list[MissedPromise]
    cases: list[CaseLine]

    @model_validator(mode="after")
    def _unique_measures(self) -> Self:
        _refuse_duplicates(
            [
                ("in_scope_correct_resolution", self.in_scope_correct_resolution),
                ("promises_kept_on_time", self.promises_kept_on_time),
                ("handoffs", self.handoffs),
                *_indexed("outcomes", self.outcomes),
                *_indexed("handoffs_by_reason", self.handoffs_by_reason),
            ]
        )
        return self


# -- CON-19 getMonitoring --------------------------------------------------------------------------------------
class Spend(ReadModel):
    today_cents: int
    cap_cents: int
    day: Literal["America/Chicago midnight to midnight"]
    resets_at: AwareDatetime


class Correctness(ReadModel):
    containment_estimate: Tile
    escalations_by_reason: list[Tile]


class MonitorAlert(ReadModel):
    type: Literal[
        "spend_cap_reached",
        "p95_latency_over_12_5s",
        "health_check_restart",
        "zero_traffic",
        "failure_rate_over_2pct",
        "trace_export_failed",
    ]
    state: Literal["firing", "quiet"]
    fired_at: AwareDatetime | None
    decision_line: str


class QuietHours(ReadModel):
    start: str
    end: str
    timezone: str
    configurable: Literal[True]


class AlertConfig(ReadModel):
    zero_traffic_after_hours: int
    quiet_hours: QuietHours


class LastRestart(ReadModel):
    at: AwareDatetime
    kind: Literal["health_check"]


class MonitoringResponse(ReadModel):
    as_of: AwareDatetime  # wall clock, stamped by the reader (the OpenAPI's one documented exception)
    demo_now: AwareDatetime  # demo clock, stamped by the reader
    health: list[Tile]
    spend: Spend
    correctness: Correctness
    alerts: list[MonitorAlert]
    alert_config: AlertConfig
    last_restart: LastRestart | None
    trace_export: str
    redacted: Literal[True]

    @model_validator(mode="after")
    def _unique_tiles(self) -> Self:
        _refuse_duplicates(
            [
                *_indexed("health", self.health),
                ("correctness.containment_estimate", self.correctness.containment_estimate),
                *_indexed("correctness.escalations_by_reason", self.correctness.escalations_by_reason),
            ]
        )
        return self


# -- CON-20 getLatestEval --------------------------------------------------------------------------------------
class MixRow(ReadModel):
    category: str
    count: int
    origin: Literal["transcript", "synthetic"]
    tests: str | None


class DevFailure(ReadModel):
    case_id: str
    redacted_summary: str


class EvalRun(ReadModel):
    run_id: str
    date: dt.date
    agent_version: str
    size: int
    mix: list[MixRow]
    measures: list[EvalMeasure]
    dev_failures: list[DevFailure]

    @model_validator(mode="after")
    def _unique_measures(self) -> Self:
        _refuse_duplicates(_indexed("measures", self.measures))
        return self


class EvalSplits(ReadModel):
    dev: EvalRun | None
    held_out: EvalRun | None


class EvalResponse(ReadModel):
    splits: EvalSplits
    headline: EvalMeasure | None
    current_agent_version: str
    dev_label: str


# -- helpers the route (and AEA-53's tests) use ---------------------------------------------------------------
def _path(loc: Sequence[int | str]) -> str:
    out = ""
    for part in loc:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += f".{part}" if out else part
    return out


def describe_errors(exc: ValidationError) -> tuple[tuple[str, str], ...]:
    """(field, rule) per error, at most ten: the dotted location and the pydantic error type. Never an input value."""
    found: list[tuple[str, str]] = []
    for error in exc.errors(include_url=False, include_input=False, include_context=True)[:_MAX_ERRORS]:
        field = _path(error["loc"])
        named = (error.get("ctx") or {}).get(_FIELD) if error["type"] in OWN_RULES else None
        if isinstance(named, str):
            field = f"{field}.{named}" if field else named
        found.append((field or "(response)", error["type"]))
    return tuple(found)


def dropped_keys(raw: object, kept: object) -> tuple[str, ...]:
    """Dotted paths of keys in `raw` that are absent from `kept` (list positions written `[]`), sorted, unique."""
    found: set[str] = set()
    _walk(raw, kept, "", found)
    return tuple(sorted(found))


def _walk(raw: object, kept: object, at: str, found: set[str]) -> None:
    if isinstance(raw, Mapping) and isinstance(kept, Mapping):
        for key, value in raw.items():
            name = f"{at}.{key}" if at else str(key)
            if key in kept:
                _walk(value, kept[key], name, found)
            else:
                found.add(name)
    elif isinstance(raw, list | tuple) and isinstance(kept, list):
        for raw_item, kept_item in zip(raw, kept, strict=False):
            _walk(raw_item, kept_item, f"{at}[]", found)
