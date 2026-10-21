"""AEA-02 AC-6: Brief accepts only the fixed eight-heading shape."""

from __future__ import annotations

import datetime as dt
from typing import Any

import pytest
from pydantic import ValidationError

from meridian.domain.common import SafeError
from meridian.domain.handoff import BRIEF_KEYS, BRIEF_ORIGINS, BRIEF_TITLES, Brief

THREAD = "3f1c2a4e-8b7d-4e21-9a6b-5c0d7e8f9a10"


def _heading(index: int, **overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "number": index + 1,
        "key": BRIEF_KEYS[index],
        "title": BRIEF_TITLES[index],
        "origin": BRIEF_ORIGINS[index],
        "checked": index != 3,
        "items": (),
        "trimmed": False,
        "trim_note": None,
        "not_generated": False,
    }
    base.update(overrides)
    return base


def _brief(headings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "case_ref": "MHC-C-0001",
        "thread_id": THREAD,
        "assembled_at": dt.datetime(2026, 10, 16, 10, 0, tzinfo=dt.UTC),
        "status": "ready",
        "headings": headings,
    }


def _valid() -> list[dict[str, Any]]:
    return [_heading(i) for i in range(8)]


def _with(index: int, **overrides: Any) -> list[dict[str, Any]]:
    headings = _valid()
    headings[index] = _heading(index, **overrides)
    return headings


@pytest.mark.parametrize(
    ("headings", "valid"),
    [
        (_valid(), True),
        (_valid()[:7], False),
        ([*_valid(), _heading(0)], False),
        ([*_valid()[1::-1], *_valid()[2:]], False),
        (_with(2, title="Something else"), False),
        (_with(2, key="says"), False),
        (_with(1, origin="state"), False),
        (_with(3, checked=True), False),
        (_with(0, not_generated=True), False),
        (_with(1, not_generated=True), True),
    ],
    ids=[
        "valid",
        "seven",
        "nine",
        "out-of-order",
        "wrong-title",
        "wrong-key",
        "wrong-origin-2",
        "heading-4-checked",
        "not-generated-on-1",
        "not-generated-on-2",
    ],
)
def test_brief_shape(headings: list[dict[str, Any]], valid: bool) -> None:
    if valid:
        assert Brief.model_validate(_brief(headings))
        return
    with pytest.raises(ValidationError) as caught:
        Brief.model_validate(_brief(headings))
    problems = SafeError.from_validation_error(caught.value)
    print([(p.code, p.constraint) for p in problems])
    assert any(p.code == "brief_shape" for p in problems)
