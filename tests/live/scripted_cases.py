"""Scripted good and bad step tables for the six smoke cases (AEA-61 part B).

The free journeys and the not-an-E-run dry run play a smoke case against AEA-51's scripted app and run the same checks
the paid run uses. A "good" table follows each case's required output; a "bad" table skips one required tool call or
write, and the live assertion must catch it. Only the model output is scripted; every encoding comes from AEA-51's
building blocks. Script texts are read from the case files, never rewritten here.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, Final, Literal

from eval.cases.models import ScriptedTurn
from meridian.agent.tools.account import ReadInvoicesArgs
from meridian.agent.tools.scheduling import MoveVisitArgs, RequestVisitChangeArgs
from meridian.domain.common import Role
from meridian.domain.specialists import SchedulingReport
from tests.graph.worked_pair_scenarios import (
    MOVED_SENTENCE,
    NORMAL,
    TOOLS,
    Step,
    account_steps,
    brief,
    classifier,
    find_args,
    kb_steps,
    next_message_id,
    open_slot,
    planner,
    report,
    responder,
    scheduled_appointment,
    scheduling_steps,
    step,
    tool,
)
from tests.integration.customer_support import CustomerRun
from tests.live.smoke_cases import SmokeCase
from tests.live.smoke_checks import WP4F_TARGET_SLOT
from tests.live.smoke_player import BeforeTurn

Variant = Literal["good", "bad"]
StepFactory = Callable[[ScriptedTurn], Step]  # built just before its turn: next_message_id reads the DB then
MONDAY: Final = "2026-10-19"
MONDAY_MORNING: Final = "08:00-12:00"

_TALK: Final[Step] = {Role.CLASSIFIER: NORMAL}
_LOCATE_WAIT: Final = responder("I need to find your record first.")
_CODE_SENT: Final[Step] = {Role.RESPONDER: responder("Thanks, I sent a code.")}

_MEMBERSHIP_QUERIES: Final = (
    (
        "Comfort Club membership benefits tune-ups repairs",
        "Members get two seasonal tune-ups a year and 15% off all repairs.",
    ),
    ("Comfort Club membership price per year", "The Comfort Club is $189 per year per system."),
    (
        "Comfort Club Plus plumbing inspection plumbing repairs",
        "Comfort Club Plus adds an annual whole-home plumbing inspection and 15% off plumbing repairs.",
    ),
)


def scripted_turns(case: SmokeCase, run: CustomerRun, *, variant: Variant = "good") -> BeforeTurn:
    factories = case_steps(case, run, variant)
    n = len(case.script.turns)
    assert len(factories) == n, f"{case.case_id}: {len(factories)} scripted steps for {n} turns"

    def before_turn(i: int, turn: ScriptedTurn, exchanges: Sequence[Any]) -> None:
        run.steps.set_step(factories[i](turn))

    return before_turn


def case_steps(case: SmokeCase, run: CustomerRun, variant: Variant) -> tuple[StepFactory, ...]:
    builders: dict[str, Callable[[SmokeCase, CustomerRun, Variant], tuple[StepFactory, ...]]] = {
        "membership": _membership,
        "billing": _billing,
        "warranty": _warranty,
        "booking with follow-up": _follow_up,
        "safety": _safety,
        "fee-bearing change": _fee_bearing,
    }
    return builders[case.label](case, run, variant)


def _constant(entry: Step) -> StepFactory:
    return lambda _turn: entry


def _fixed(entries: Sequence[Step]) -> tuple[StepFactory, ...]:
    return tuple(_constant(entry) for entry in entries)


def _appointment(case: SmokeCase, run: CustomerRun) -> tuple[dict[str, Any], str, int]:
    appt = scheduled_appointment(run, str(case.script.seeded_customer))
    return appt, str(appt["service_type"]), int(appt["appointment_id"])


def _membership(case: SmokeCase, run: CustomerRun, variant: Variant) -> tuple[StepFactory, ...]:
    entries: list[Step] = []
    for i, (query, summary) in enumerate(_MEMBERSHIP_QUERIES):
        full = kb_steps(run, query, summary)
        rounds = (
            (full[1],) if variant == "bad" and i == 0 else full
        )  # bad: the report step only, no kb_search
        entries.append(
            {
                **_TALK,
                Role.PLANNER: planner(knowledge="yes", topic="membership"),
                Role.SPECIALIST: rounds,
                Role.RESPONDER: responder(summary),
            }
        )
    return _fixed(entries)


def _billing(case: SmokeCase, run: CustomerRun, variant: Variant) -> tuple[StepFactory, ...]:
    if variant == "bad":
        raise ValueError(f"no bad table for {case.label}")
    invoice_plan = planner(account="invoice", topic="billing")
    read = account_steps(
        tool(
            TOOLS["invoice"],
            ReadInvoicesArgs.model_validate({"invoice_number": "INV-204411"}).model_dump(mode="json"),
        ),
        summary="Read the invoice as billed.",
    )

    def dispute(turn: ScriptedTurn) -> Step:
        return {
            **_TALK,
            Role.PLANNER: planner(handoff="billing_dispute", topic="billing"),
            Role.RESPONDER: responder("I have asked a representative to review that charge."),
            Role.BRIEF: brief(
                needs=[{"message_id": next_message_id(run), "text": (turn.text or "")[:30]}],
                claims=[],
                open_decision="Review the disputed charge.",
            ),
        }

    return (
        *_fixed(
            [
                {**_TALK, Role.PLANNER: invoice_plan, Role.RESPONDER: _LOCATE_WAIT},
                _CODE_SENT,
                {
                    **_TALK,
                    Role.PLANNER: invoice_plan,
                    Role.SPECIALIST: read,
                    Role.RESPONDER: responder(
                        "This invoice bills a diagnostic visit, a contactor replacement and a dispatch fee."
                    ),
                },
                {
                    **_TALK,
                    Role.PLANNER: invoice_plan,
                    Role.SPECIALIST: read,
                    Role.RESPONDER: responder(
                        "I can't email a copy from this chat. The invoice lists three lines: the diagnostic "
                        "visit, the part and the dispatch."
                    ),
                },
            ]
        ),
        dispute,
    )


def _warranty(case: SmokeCase, run: CustomerRun, variant: Variant) -> tuple[StepFactory, ...]:
    if variant == "bad":
        raise ValueError(f"no bad table for {case.label}")
    plan = planner(account="warranty", topic="warranty")
    return _fixed(
        [
            {**_TALK, Role.PLANNER: plan, Role.RESPONDER: _LOCATE_WAIT},
            _CODE_SENT,
            {
                **_TALK,
                Role.PLANNER: plan,
                Role.SPECIALIST: account_steps(
                    tool(TOOLS["warranty"], {}), summary="Read the warranty record."
                ),
                Role.RESPONDER: responder("Here is what your warranty record shows."),
            },
        ]
    )


def _follow_up(case: SmokeCase, run: CustomerRun, variant: Variant) -> tuple[StepFactory, ...]:
    _, svc, app_id = _appointment(case, run)
    move_plan = planner(scheduling="reschedule", topic="booking")
    monday = find_args(
        svc,
        earliest=MONDAY,
        latest=MONDAY,
        window=MONDAY_MORNING,
        wanted_text="Monday the 19th, 8 to 12",
    )
    shown = step(tool(TOOLS["find_windows"], monday))
    done = step(
        report(SchedulingReport, appointment_id=app_id, wanted_time="Monday the 19th, 8 to 12", note="moved")
    )
    move = step(
        tool(
            TOOLS["move"],
            MoveVisitArgs(appointment_id=app_id, new_slot_id=WP4F_TARGET_SLOT).model_dump(),
            call_id="call-2",
        )
    )
    moving = (shown, done) if variant == "bad" else (shown, move, done)  # bad: no move
    return _fixed(
        [
            {**_TALK, Role.PLANNER: move_plan, Role.RESPONDER: _LOCATE_WAIT},
            _CODE_SENT,
            {
                **_TALK,
                Role.PLANNER: move_plan,
                Role.SPECIALIST: scheduling_steps(
                    tool(TOOLS["find_windows"], find_args(svc)), appointment_id=app_id
                ),
                Role.RESPONDER: responder("Here are the open windows."),
            },
            {
                **_TALK,
                Role.PLANNER: move_plan,
                Role.SPECIALIST: moving,
                Role.RESPONDER: responder(
                    "Done. Your visit is moved to Monday, October 19, 8:00 am to 12:00 pm."
                ),
            },
            {
                **_TALK,
                Role.PLANNER: planner(topic="booking"),
                Role.SPECIALIST: scheduling_steps(
                    tool(TOOLS["find_windows"], find_args(svc)), appointment_id=app_id
                ),
                Role.RESPONDER: responder(MOVED_SENTENCE),
            },
        ]
    )


def _safety(case: SmokeCase, run: CustomerRun, variant: Variant) -> tuple[StepFactory, ...]:
    plan = planner(scheduling="book_new", topic="booking")
    if variant == "bad":  # no raise: the classifier says normal and the booking path answers
        return _fixed(
            [
                {
                    Role.PLANNER: plan,
                    Role.CLASSIFIER: NORMAL,
                    Role.RESPONDER: responder("I can help book a visit. First I need to find your account."),
                }
            ]
        )
    return _fixed([{Role.PLANNER: plan, Role.CLASSIFIER: classifier("danger")}])


def _fee_bearing(case: SmokeCase, run: CustomerRun, variant: Variant) -> tuple[StepFactory, ...]:
    appt, svc, app_id = _appointment(case, run)
    move_plan = planner(scheduling="reschedule", topic="booking")
    target = open_slot(run, str(appt["zone"]), svc, after=MONDAY)
    refused_move = step(
        tool(TOOLS["move"], MoveVisitArgs(appointment_id=app_id, new_slot_id=target).model_dump())
    )
    asked = report(
        SchedulingReport, appointment_id=app_id, wanted_time="Monday morning", note="change request"
    )
    request = step(
        tool(
            TOOLS["change_request"],
            RequestVisitChangeArgs(
                appointment_id=app_id, change="move", wanted_text="Monday morning"
            ).model_dump(),
            call_id="call-2",
        ),
        asked,
    )
    rounds = (
        (refused_move, step(asked)) if variant == "bad" else (refused_move, request)
    )  # bad: no change_request

    def ask(turn: ScriptedTurn) -> Step:
        return {
            **_TALK,
            Role.PLANNER: move_plan,
            Role.SPECIALIST: rounds,
            Role.RESPONDER: responder("I've sent your change request to a representative."),
            Role.BRIEF: brief(
                needs=[{"message_id": next_message_id(run), "text": (turn.text or "")[:30]}],
                claims=[],
                open_decision="Confirm or decline the change.",
            ),
        }

    monday_windows = find_args(
        svc, earliest=MONDAY, latest=MONDAY, window=MONDAY_MORNING, wanted_text="Monday morning"
    )
    return (
        *_fixed(
            [
                {**_TALK, Role.PLANNER: move_plan, Role.RESPONDER: _LOCATE_WAIT},
                _CODE_SENT,
                {
                    **_TALK,
                    Role.PLANNER: move_plan,
                    Role.SPECIALIST: scheduling_steps(
                        tool(TOOLS["find_windows"], find_args(svc)), appointment_id=app_id
                    ),
                    Role.RESPONDER: responder("When would you like to move your visit to?"),
                },
                {
                    **_TALK,
                    Role.PLANNER: move_plan,
                    Role.SPECIALIST: scheduling_steps(
                        tool(TOOLS["find_windows"], monday_windows), appointment_id=app_id
                    ),
                    Role.RESPONDER: responder(
                        "Here are the Monday morning windows. They are shown, not held."
                    ),
                },
            ]
        ),
        ask,
    )
