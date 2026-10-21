"""AEA-35b: SpecialistTask, KnowledgeSlice and AccountSlice live in domain/tools.py (graph-tools section 2)."""

from __future__ import annotations

import subprocess
import sys

import pydantic
import pytest

from meridian.domain.specialists import SchedulingSlice
from meridian.domain.tools import AccountSlice, KnowledgeSlice, SpecialistTask
from meridian.domain.turn import PlannedTask, TaskIntent


def _planned(specialist: str = "knowledge") -> PlannedTask:
    return PlannedTask.model_validate(
        {"order": 1, "specialist": specialist, "intent": TaskIntent.ANSWER_QUESTION, "needs_identity": False}
    )


def test_field_sets() -> None:
    assert set(SpecialistTask.model_fields) == {
        "task",
        "customer_text",
        "task_messages",
        "slice",
        "offer_quick_checks",
    }
    assert set(KnowledgeSlice.model_fields) == {"kind"}
    assert set(AccountSlice.model_fields) == {"kind"}


def test_slices_construct_without_arguments() -> None:
    assert KnowledgeSlice().kind == "knowledge"
    assert AccountSlice().kind == "account"


def test_frozen() -> None:
    task = SpecialistTask(task=_planned(), customer_text="hi", task_messages=(), slice=KnowledgeSlice())
    assert task.offer_quick_checks is False
    for obj, attr, value in ((task, "customer_text", "x"), (KnowledgeSlice(), "kind", "knowledge")):
        with pytest.raises(pydantic.ValidationError):
            setattr(obj, attr, value)


@pytest.mark.parametrize("slice_", [KnowledgeSlice(), AccountSlice()])
def test_round_trip(slice_: KnowledgeSlice | AccountSlice) -> None:
    task = SpecialistTask(
        task=_planned(slice_.kind),
        customer_text="my bill",
        task_messages=("a", "b"),
        slice=slice_,
        offer_quick_checks=True,
    )
    again = SpecialistTask.model_validate_json(task.model_dump_json())
    assert again == task
    assert type(again.slice) is type(slice_)


def test_scheduling_slice_round_trips_in_union() -> None:
    sched = SchedulingSlice(
        customer_zone=None,
        member=False,
        appointments=(),
        shown_slots=(),
        pending_change=False,
        bookings_left=2,
    )
    task = SpecialistTask(task=_planned("scheduling"), customer_text="t", task_messages=(), slice=sched)
    assert isinstance(SpecialistTask.model_validate_json(task.model_dump_json()).slice, SchedulingSlice)


@pytest.mark.parametrize("order", [("tools", "turn"), ("turn", "tools")])
def test_import_order_does_not_matter(order: tuple[str, str]) -> None:
    code = "; ".join(f"import meridian.domain.{m}" for m in order)
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stderr
