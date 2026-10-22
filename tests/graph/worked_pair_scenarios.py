"""AEA-51's worked-pair drivers: one function per scenario, each opening a chat on a `CustomerRun` and driving the real
app over HTTP with a per-step model script. Published for AEA-52 (plan 8 R-19): keep `wp4`, `wp7`, `ScenarioResult`
and the signatures stable. Expected values come from policy texts, the working copy and docs/data/worked-pairs.md.
"""

from __future__ import annotations

__all__ = [
    "BookVisitArgs",
    "FindWindowsArgs",
    "Key",
    "MoveVisitArgs",
    "Role",
    "card_id_of",
    "pick",
]

import json
import secrets
import threading
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

import httpx

from meridian.agent.prompts.routing import DANGER_FIELD
from meridian.agent.prompts.specialists import REPORT_FACTS_TOOL
from meridian.agent.tools.account import (
    READ_INVOICES_NAME,
    READ_MEMBERSHIP_NAME,
    READ_WARRANTY_NAME,
    ReadInvoicesArgs,
)
from meridian.agent.tools.knowledge import KB_SEARCH_NAME, KbSearchArgs
from meridian.agent.tools.scheduling import (
    BOOK_VISIT_NAME,
    CANCEL_VISIT_NAME,
    FIND_WINDOWS_NAME,
    MOVE_VISIT_NAME,
    REQUEST_VISIT_CHANGE_NAME,
    BookVisitArgs,
    CancelVisitArgs,
    FindWindowsArgs,
    MoveVisitArgs,
    RequestVisitChangeArgs,
)
from meridian.domain.common import LLMFacing, ProviderFailureKind, Role
from meridian.domain.handoff import BriefExtraction
from meridian.domain.specialists import (
    AccountReport,
    KnowledgeReport,
    ReportedPoint,
    SchedulingReport,
)
from meridian.domain.turn import PlannerChoices, ResponderDraft
from meridian.retrieval.settings import MIN_SCORE, SEARCH_K
from meridian.web.container import Key
from tests.fakes import ScriptedFailure
from tests.integration.customer_api import (
    Chat,
    blocks,
    card_id_of,
    newest_code,
    open_chat,
    pick,
    say,
    send_code,
    send_form,
)
from tests.integration.customer_support import CustomerRun, StepEntry
from tests.journeys.support.client import JourneyClient
from tests.journeys.support.env import letters
from tests.journeys.support.scripted_model import RawToolCall, RawToolStep

TOOLS: Mapping[str, str] = MappingProxyType(
    {
        "kb_search": KB_SEARCH_NAME,
        "invoice": READ_INVOICES_NAME,
        "membership": READ_MEMBERSHIP_NAME,
        "warranty": READ_WARRANTY_NAME,
        "find_windows": FIND_WINDOWS_NAME,
        "book": BOOK_VISIT_NAME,
        "move": MOVE_VISIT_NAME,
        "cancel": CANCEL_VISIT_NAME,
        "change_request": REQUEST_VISIT_CHANGE_NAME,
    }
)
Step = dict[Role, StepEntry]


def planner(**choices: str) -> str:
    base = {"knowledge": "no", "account": "none", "scheduling": "none", "handoff": "none", "topic": "other"}
    return PlannerChoices(**{**base, **choices}).model_dump_json()  # type: ignore[arg-type]


def classifier(label: str) -> str:
    return json.dumps({DANGER_FIELD: label})


def responder(text: str) -> str:
    return ResponderDraft(text=text).model_dump_json()


def brief(**fields: Any) -> str:
    return BriefExtraction(**fields).model_dump_json()


def tool(name: str, args: Mapping[str, Any], call_id: str = "call-1") -> RawToolCall:
    return RawToolCall(id=call_id, name=name, arguments=json.dumps(dict(args)))


def report(model: type[LLMFacing], **fields: Any) -> RawToolCall:
    return RawToolCall(
        id="call-report",
        name=REPORT_FACTS_TOOL,
        arguments=json.dumps(model(**fields).model_dump(mode="json")),
    )


def step(*calls: RawToolCall, text: str = "") -> RawToolStep:
    return RawToolStep(text=text, calls=tuple(calls))


NORMAL = classifier("normal")
BOOKING_PLAN = planner(scheduling="book_new", topic="booking")


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    thread_id: str
    turn_ids: tuple[str, ...]
    responses: tuple[httpx.Response, ...]
    customer_id: str | None
    case_refs: tuple[str, ...]
    extra: Mapping[str, Any] = field(default_factory=dict)
    codes: tuple[str, ...] = ()  # the codes read from the inbox for this chat (never printed)


# -- helpers -------------------------------------------------------------------------------------------------------


def find_args(service_type: str, **fields: Any) -> dict[str, Any]:
    """find_windows arguments, validated against the args model (a rename or a bad service type fails here)."""
    return FindWindowsArgs.model_validate({"service_type": service_type, **fields}).model_dump(mode="json")


def top_passage(run: CustomerRun, query: str) -> Any:
    """The first passage the real index returns for `query` (the same call the kb_search tool makes)."""
    index = run.container.get(Key[Any]("retrieval_index"))
    result = index.search(query, k=SEARCH_K, min_score=MIN_SCORE)
    assert not result.below_floor and result.passages, f"the index returned nothing for {query!r}"
    return result.passages[0]


def kb_steps(run: CustomerRun, query: str, summary: str) -> tuple[RawToolStep, RawToolStep]:
    """Round 0: kb_search; round 1: report_facts citing the first passage that search returns."""
    passage = top_passage(run, query)
    args = KbSearchArgs(query=query).model_dump()
    point = ReportedPoint(text=summary, passage_id=passage.passage_id)
    return (
        step(tool(TOOLS["kb_search"], args)),
        step(report(KnowledgeReport, points=[point], answered=True)),
    )


def no_source_steps(query: str) -> tuple[RawToolStep, RawToolStep]:
    return (
        step(tool(TOOLS["kb_search"], KbSearchArgs(query=query).model_dump())),
        step(report(KnowledgeReport, points=[], answered=False)),
    )


def account_steps(*calls: RawToolCall, summary: str = "Read the record.") -> tuple[RawToolStep, RawToolStep]:
    return step(*calls), step(report(AccountReport, summary=summary))


def scheduling_steps(*calls: RawToolCall, appointment_id: int = 0, note: str = "") -> tuple[RawToolStep, ...]:
    return step(*calls), step(
        report(SchedulingReport, appointment_id=appointment_id, wanted_time="", note=note)
    )


def case_refs_of(run: CustomerRun, thread_id: str) -> tuple[str, ...]:
    rows = run.db.rows(
        "SELECT case_ref FROM cases WHERE thread_id = ? ORDER BY created_at, case_ref", (thread_id,)
    )
    return tuple(str(r["case_ref"]) for r in rows)


def _result(
    run: CustomerRun,
    name: str,
    chat: Chat,
    responses: list[httpx.Response],
    customer_id: str | None = None,
    **extra: Any,
) -> ScenarioResult:
    return ScenarioResult(
        name=name,
        thread_id=chat.thread_id,
        turn_ids=tuple(r.json()["turn_id"] for r in responses),
        responses=tuple(responses),
        customer_id=customer_id,
        case_refs=case_refs_of(run, chat.thread_id),
        extra=extra,
        codes=tuple(chat.codes),
    )


def _begin(run: CustomerRun, client: JourneyClient | None) -> Chat:
    return open_chat(run, client)


# -- WP-1 ----------------------------------------------------------------------------------------------------------

ARCHIVE_PRICE = "$149"
WP1_QUERY = "Comfort Club member repair discount"


def wp1(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    chat = _begin(run, client)
    responses: list[httpx.Response] = []
    first, second = kb_steps(run, WP1_QUERY, "Members save 15% on repairs.")
    run.steps.set_step(
        {
            Role.PLANNER: planner(knowledge="yes", topic="membership"),
            Role.CLASSIFIER: NORMAL,
            Role.SPECIALIST: (first, second),
            Role.RESPONDER: responder(f"Members save 15% on repairs. The plan is {ARCHIVE_PRICE} a year."),
        }
    )
    responses.append(say(chat, "Do members get a discount on repairs?"))
    return _result(run, "wp1", chat, responses)


Driver = Callable[..., ScenarioResult]


# -- safety, danger, person words, refund ---------------------------------------------------------------------------

CO_TEXT = "My carbon monoxide detector is going off."
DANGER_TEXT = "my mother is 88 and it's 95 degrees in here"
REFUND_TEXT = "I want a refund for last week's visit."


def wp5(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    """No model entry is set: every role answers `exhausted`, so a model call would show as a problem."""
    chat = _begin(run, client)
    run.steps.set_step({})
    responses = [say(chat, CO_TEXT)]
    run.steps.set_step(
        {
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: planner(),
            Role.RESPONDER: responder("You're welcome. Please stay outside until it is safe."),
        }
    )
    responses.append(say(chat, "ok thanks"))
    return _result(run, "wp5", chat, responses)


def danger(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    chat = _begin(run, client)
    run.steps.set_step(
        {
            Role.PLANNER: planner(scheduling="book_new", topic="booking"),
            Role.CLASSIFIER: classifier("danger"),
        }
    )
    return _result(run, "danger", chat, [say(chat, DANGER_TEXT)])


def nodanger(
    run: CustomerRun, client: JourneyClient | None = None, *, classifier_fails: bool = False
) -> ScenarioResult:
    chat = _begin(run, client)
    run.steps.set_step(
        {
            Role.PLANNER: BOOKING_PLAN,
            Role.CLASSIFIER: ScriptedFailure(kind=ProviderFailureKind.BODY_ERROR, http_status=503)
            if classifier_fails
            else NORMAL,
            Role.RESPONDER: responder("I can help book a visit. First I need to find your account."),
        }
    )
    return _result(run, "nodanger", chat, [say(chat, "my AC isn't cooling")])


def person_words(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    chat = _begin(run, client)
    run.steps.set_step(
        {
            Role.RESPONDER: responder("A representative will take it from here."),
            Role.BRIEF: brief(
                needs=[{"message_id": next_message_id(run), "text": "can I talk to a person"}],
                claims=[],
                open_decision="Take over the conversation.",
            ),
        }
    )
    return _result(run, "person_words", chat, [say(chat, "can I talk to a person")])


def wp7(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    """Refund: planner `refund`, a brief whose amount is in no record and whose claim quote is in no message (PA-5)."""
    chat = _begin(run, client)
    next_message = int(run.db.scalar("SELECT COALESCE(MAX(id), 0) FROM messages")) + 1
    sentinel = "sentinel-quote-" + letters(10)
    extraction = brief(
        needs=[{"message_id": next_message, "text": REFUND_TEXT[:20]}],
        claims=[{"message_id": next_message, "text": sentinel}],
        open_decision="Decide on a refund of $212.00 or a warranty recall.",
    )
    run.steps.set_step(
        {
            Role.PLANNER: planner(handoff="refund", topic="billing"),
            Role.CLASSIFIER: NORMAL,
            Role.RESPONDER: responder(
                "I can't promise an outcome, but I have asked a representative to look at it."
            ),
            Role.BRIEF: extraction,
        }
    )
    responses = [say(chat, REFUND_TEXT)]
    return _result(run, "wp7", chat, responses, sentinel_quote=sentinel, refund_amount="$212.00")


# -- identity-first scenarios --------------------------------------------------------------------------------------


def verified_open(
    run: CustomerRun,
    chat: Chat,
    customer_id: str,
    text: str,
    *,
    first: Step,
    after_code: Step,
    form: Step | None = None,
) -> list[httpx.Response]:
    """The opening message (turn 1), the locate form (turn 2) and the code (turn 3). `after_code` is the step the code
    turn runs under: the resumed task's specialist and the responder."""
    run.steps.set_step(first)
    opening = say(chat, text)
    return [opening, *locate_and_code(run, chat, customer_id, opening, after_code=after_code, form=form)]


def locate_and_code(
    run: CustomerRun,
    chat: Chat,
    customer_id: str,
    opening: httpx.Response,
    *,
    after_code: Step,
    form: Step | None = None,
    wrong_codes: tuple[str, ...] = (),
) -> list[httpx.Response]:
    """From a response that carries the locate prompt: fill the form, then enter the code read from the inbox."""
    assert blocks(opening, "locate_prompt"), "the opening turn should ask to locate the record"
    row = run.db.one("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    block = blocks(opening, "locate_prompt")[0]
    wanted = {"name": row["name"], "phone": row["phone"], "customer_id": customer_id}
    field_set = next((fs for fs in block["field_sets"] if all(f in wanted for f in fs)), None)
    assert field_set is not None, f"no fillable field set in {block['field_sets']}"
    run.steps.set_step(form if form is not None else {Role.RESPONDER: responder("Thanks, I sent a code.")})
    sent = send_form(chat, block["card_id"], {f: str(wanted[f]) for f in field_set})
    out = [sent]
    card = card_id_of(sent, "code_prompt")
    for wrong in wrong_codes:
        run.steps.set_step({Role.RESPONDER: responder("That code did not match.")})
        again = send_code(chat, card, wrong)
        out.append(again)
        card = card_id_of(again, "code_prompt") if blocks(again, "code_prompt") else card
    run.steps.set_step(after_code)
    out.append(send_code(chat, card, newest_code(chat)))
    return out


def wp2(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    """Invoice question: locate, code, then the billed facts; then a dispute handing off at P3."""
    customer = "MHC-10002"
    chat = _begin(run, client)
    talk = {Role.CLASSIFIER: NORMAL}
    invoice_plan = planner(account="invoice", topic="billing")
    read, report_step = account_steps(
        tool(
            TOOLS["invoice"],
            ReadInvoicesArgs.model_validate({"invoice_number": "INV-204411"}).model_dump(mode="json"),
        ),
        summary="Read the invoice as billed.",
    )
    responses = verified_open(
        run,
        chat,
        customer,
        "What is this invoice for? INV-204411",
        first={
            **talk,
            Role.PLANNER: invoice_plan,
            Role.RESPONDER: responder("I need to find your record first."),
        },
        after_code={
            **talk,
            Role.PLANNER: invoice_plan,
            Role.SPECIALIST: (read, report_step),
            Role.RESPONDER: responder(
                "This invoice bills a diagnostic visit, a contactor replacement and a dispatch fee."
            ),
        },
    )
    run.steps.set_step(
        {
            **talk,
            Role.PLANNER: invoice_plan,
            Role.SPECIALIST: (read, report_step),
            Role.RESPONDER: responder(
                "The invoice lists three lines: the diagnostic visit, the part and the dispatch."
            ),
        }
    )
    responses.append(say(chat, "What is it for?"))
    run.steps.set_step(
        {
            **talk,
            Role.PLANNER: planner(handoff="billing_dispute", topic="billing"),
            Role.RESPONDER: responder("I have asked a representative to review that charge."),
            Role.BRIEF: brief(
                needs=[{"message_id": next_message_id(run), "text": "I don't think that charge is right"}],
                claims=[],
                open_decision="Review the disputed charge.",
            ),
        }
    )
    responses.append(say(chat, "I don't think that charge is right"))
    return _result(run, "wp2", chat, responses, customer)


def next_message_id(run: CustomerRun) -> int:
    return int(run.db.scalar("SELECT COALESCE(MAX(id), 0) FROM messages")) + 1


def wp3_prepare(
    run: CustomerRun, client: JourneyClient | None = None
) -> tuple[Chat, list[httpx.Response], str]:
    """WP-3 up to the windows: verified, and the slot card showing slots 56, 42 and 58. Returns (chat, responses, card)."""
    customer = "MHC-10001"
    chat = _begin(run, client)
    talk = {Role.CLASSIFIER: NORMAL}
    find = scheduling_steps(
        tool(
            TOOLS["find_windows"],
            FindWindowsArgs(service_type="hvac_repair", wanted_text="Saturday evening").model_dump(
                mode="json"
            ),
        ),
        note="Saturday 4 to 7 is not available.",
    )
    responses = verified_open(
        run,
        chat,
        customer,
        "My AC isn't cooling, can someone come Saturday evening?",
        first={
            **talk,
            Role.PLANNER: BOOKING_PLAN,
            Role.RESPONDER: responder("I can help with that. First I need to find your record."),
        },
        after_code={
            **talk,
            Role.PLANNER: BOOKING_PLAN,
            Role.SPECIALIST: find,
            Role.RESPONDER: responder("There is no Saturday evening window. Here are the earliest options."),
        },
    )
    return chat, responses, card_id_of(responses[-1], "slot_card")


BOOK_56_STEP: Step = {
    Role.SPECIALIST: scheduling_steps(
        tool(TOOLS["book"], BookVisitArgs(slot_id=56, issue="AC not cooling").model_dump())
    ),
    Role.RESPONDER: responder("Your visit is booked."),
}


def wp3(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    """AC not cooling, Saturday evening: windows (56, 42, 58), then slot 56 booked in one transaction."""
    chat, responses, card = wp3_prepare(run, client)
    run.steps.set_step(BOOK_56_STEP)
    responses.append(pick(chat, card, "56"))
    return _result(run, "wp3", chat, responses, "MHC-10001", slot_card=card)


def wp3_concurrent(run: CustomerRun, client: JourneyClient) -> ScenarioResult:
    """Two chats of one login both pick slot 56 at the same moment: one booking, one SLOT_TAKEN."""
    chat_a, responses_a, card_a = wp3_prepare(run, client)
    chat_b, responses_b, card_b = wp3_prepare(run, client)
    run.steps.set_step(BOOK_56_STEP)
    barrier = threading.Barrier(2)
    picked: dict[str, httpx.Response] = {}

    def go(label: str, chat: Chat, card: str) -> None:
        barrier.wait()
        picked[label] = pick(chat, card, "56")

    threads = [
        threading.Thread(target=go, args=("a", chat_a, card_a)),
        threading.Thread(target=go, args=("b", chat_b, card_b)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert set(picked) == {"a", "b"}, "a racing pick did not answer"
    result = _result(run, "wp3_concurrent", chat_a, [*responses_a, picked["a"]], "MHC-10001")
    return ScenarioResult(
        name=result.name,
        thread_id=result.thread_id,
        turn_ids=result.turn_ids,
        responses=result.responses,
        customer_id=result.customer_id,
        case_refs=result.case_refs,
        extra={
            "other_thread": chat_b.thread_id,
            "picks": picked,
            "other_responses": [*responses_b, picked["b"]],
        },
    )


def scheduled_appointment(run: CustomerRun, customer_id: str) -> dict[str, Any]:
    return run.db.one(
        "SELECT a.appointment_id, a.slot_id, s.slot_date, s.window, s.zone, s.service_type FROM appointments a "
        "JOIN appointment_slots s ON s.slot_id = a.slot_id WHERE a.customer_id = ? AND a.status = 'scheduled' "
        "ORDER BY s.slot_date, s.window LIMIT 1",
        (customer_id,),
    )


def open_slot(run: CustomerRun, zone: str, service_type: str, *, after: str) -> int:
    return int(
        run.db.scalar(
            "SELECT slot_id FROM appointment_slots WHERE zone = ? AND service_type = ? AND status = 'open' "
            "AND slot_date >= ? ORDER BY slot_date, window, slot_id LIMIT 1",
            (zone, service_type, after),
        )
    )


def _fee_bearing_scenario(
    run: CustomerRun,
    client: JourneyClient | None,
    name: str,
    opening: str,
    change: str,
    claim: str,
    confirm: str | None,
) -> ScenarioResult:
    customer = "MHC-57204"
    chat = _begin(run, client)
    appointment = scheduled_appointment(run, customer)
    app_id = int(appointment["appointment_id"])
    wanted = "Monday morning"
    refusal_tool = TOOLS["move"] if change == "move" else TOOLS["cancel"]
    refusal_args = (
        MoveVisitArgs(
            appointment_id=app_id, new_slot_id=open_slot(run, "central", "hvac_tune_up", after="2026-10-19")
        ).model_dump()
        if change == "move"
        else CancelVisitArgs(appointment_id=app_id).model_dump()
    )
    steps = (
        step(tool(refusal_tool, refusal_args)),
        step(
            tool(
                TOOLS["change_request"],
                RequestVisitChangeArgs(appointment_id=app_id, change=change, wanted_text=wanted).model_dump(),  # type: ignore[arg-type]
                call_id="call-2",
            ),
            report(SchedulingReport, appointment_id=app_id, wanted_time=wanted, note=claim),
        ),
    )
    reschedule = planner(scheduling="reschedule" if change == "move" else "cancel", topic="booking")
    talk = {Role.CLASSIFIER: NORMAL}
    responses = verified_open(
        run,
        chat,
        customer,
        opening,
        first={
            **talk,
            Role.PLANNER: reschedule,
            Role.RESPONDER: responder("I need to find your record first."),
        },
        after_code={
            **talk,
            Role.PLANNER: reschedule,
            Role.SPECIALIST: steps,
            Role.RESPONDER: responder(f"{claim} A representative will look at your request."),
            Role.BRIEF: brief(
                needs=[{"message_id": next_message_id(run), "text": opening[:30]}],
                claims=[],
                open_decision="Confirm or decline the change.",
            ),
        },
    )
    return _result(run, name, chat, responses, customer, appointment_id=app_id, original=appointment)


def wp4(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    """Reschedule inside 24 hours: the write is refused (fee_bearing) and a P2 staff request opens. Published (R-19)."""
    return _fee_bearing_scenario(
        run,
        client,
        "wp4",
        "I have a tech coming but something came up. Can I move it?",
        "move",
        "I've moved it to Monday.",
        None,
    )


def wp4_cancel(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    return _fee_bearing_scenario(
        run, client, "wp4_cancel", "Please cancel my visit today.", "cancel", "I've cancelled it.", None
    )


def wp4f_customer(run: CustomerRun) -> dict[str, Any]:
    """The first customer whose scheduled visit starts well after 24 hours and whose zone has an open slot (D3)."""
    rows = run.db.rows(
        "SELECT a.customer_id, a.appointment_id, s.slot_date, s.window, s.zone, s.service_type FROM appointments a "
        "JOIN appointment_slots s ON s.slot_id = a.slot_id WHERE a.status = 'scheduled' AND s.slot_date >= '2026-10-18' "
        "ORDER BY s.slot_date, s.window, a.appointment_id"
    )
    for row in rows:
        free = run.db.scalar(
            "SELECT COUNT(*) FROM appointment_slots WHERE zone = ? AND service_type = ? AND status = 'open' "
            "AND slot_date >= '2026-10-19'",
            (row["zone"], row["service_type"]),
        )
        if free:
            return row
    raise AssertionError("no customer with a far-off visit and an open slot in the zone")


MOVED_SENTENCE = "Yes, it's moved: Monday morning."


def wp4f_prepare(
    run: CustomerRun, client: JourneyClient | None = None
) -> tuple[Chat, list[httpx.Response], str, int, dict[str, Any]]:
    """WP-4F up to the windows: verified, the slot card shown. Returns (chat, responses, card, target slot, row)."""
    row = wp4f_customer(run)
    customer = str(row["customer_id"])
    chat = _begin(run, client)
    talk = {Role.CLASSIFIER: NORMAL}
    plan = planner(scheduling="reschedule", topic="booking")
    find = scheduling_steps(
        tool(
            TOOLS["find_windows"],
            find_args(str(row["service_type"]), wanted_text="Monday"),
        ),
        appointment_id=int(row["appointment_id"]),
    )
    responses = verified_open(
        run,
        chat,
        customer,
        "Can I move my visit?",
        first={**talk, Role.PLANNER: plan, Role.RESPONDER: responder("I need to find your record first.")},
        after_code={
            **talk,
            Role.PLANNER: plan,
            Role.SPECIALIST: find,
            Role.RESPONDER: responder("Here are the open windows."),
        },
    )
    card = card_id_of(responses[-1], "slot_card")
    target = int(blocks(responses[-1], "slot_card")[0]["options"][0]["option"])
    return chat, responses, card, target, row


def wp4f_pick(run: CustomerRun, chat: Chat, card: str, target: int, appointment_id: int) -> httpx.Response:
    run.steps.set_step(
        {
            Role.SPECIALIST: scheduling_steps(
                tool(
                    TOOLS["move"],
                    MoveVisitArgs(appointment_id=appointment_id, new_slot_id=target).model_dump(),
                ),
                appointment_id=appointment_id,
            ),
            Role.RESPONDER: responder("Done, your visit is moved."),
        }
    )
    return pick(chat, card, str(target))


def wp4f_followup(run: CustomerRun, chat: Chat, service_type: str, appointment_id: int) -> httpx.Response:
    """'Yes, please.' after the move. open_tasks is not advanced on card and code turns (finding F-1), so the resumed task
    runs its specialist again; it is scripted to show windows, which the assertions do not depend on."""
    run.steps.set_step(
        {
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: planner(topic="booking"),
            Role.SPECIALIST: scheduling_steps(
                tool(TOOLS["find_windows"], find_args(service_type)),
                appointment_id=appointment_id,
            ),
            Role.RESPONDER: responder(MOVED_SENTENCE),
        }
    )
    return say(chat, "Yes, please.")


def wp4f(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    """Fee-free move: windows, a pick that commits the move, then 'Yes, please.' keeps the moved sentence."""
    chat, responses, card, target, row = wp4f_prepare(run, client)
    app_id = int(row["appointment_id"])
    responses.append(wp4f_pick(run, chat, card, target, app_id))
    responses.append(wp4f_followup(run, chat, str(row["service_type"]), app_id))
    return _result(
        run, "wp4f", chat, responses, str(row["customer_id"]), appointment_id=app_id, target_slot=target
    )


BURNING_TEXT = "I smell something burning from the vents"


def _wp6(
    run: CustomerRun, client: JourneyClient | None, answer: str, *, verified_first: bool = True
) -> ScenarioResult:
    """`verified_first` signs the customer in with a membership question before the burning message: with an
    unverified customer the ruled-out plan is lost to the identity detour (finding F-1)."""
    chat = _begin(run, client)
    customer: str | None = None
    responses: list[httpx.Response] = []
    if answer == "no":
        customer = "MHC-10001"
    if customer is not None and verified_first:
        ask = planner(account="membership", topic="membership")
        responses += verified_open(
            run,
            chat,
            customer,
            "What does my membership include?",
            first={
                Role.CLASSIFIER: NORMAL,
                Role.PLANNER: ask,
                Role.RESPONDER: responder("I need to find your record first."),
            },
            after_code={
                Role.CLASSIFIER: NORMAL,
                Role.PLANNER: ask,
                Role.SPECIALIST: account_steps(
                    tool(TOOLS["membership"], {}), summary="Read the membership record."
                ),
                Role.RESPONDER: responder("Here is your membership."),
            },
        )
    run.steps.set_step({})
    burning_message = next_message_id(run)
    burning = say(chat, BURNING_TEXT)
    responses.append(burning)
    card = card_id_of(burning, "burning_check")
    if answer != "no":
        responses.append(pick(chat, card, answer))
    else:
        find = scheduling_steps(
            tool(
                TOOLS["find_windows"],
                FindWindowsArgs(service_type="hvac_repair", wanted_text="earliest").model_dump(mode="json"),
            ),
        )
        run.steps.set_step(
            {
                Role.SPECIALIST: find,
                Role.RESPONDER: responder("Thanks. Here are the earliest repair windows."),
                Role.BRIEF: brief(
                    needs=[{"message_id": burning_message, "text": BURNING_TEXT}],
                    claims=[],
                    open_decision="Confirm the urgent repair booking.",
                ),
            }
        )
        opened = pick(chat, card, "no")
        responses.append(opened)
        if not verified_first:
            responses += locate_and_code(
                run,
                chat,
                customer or "MHC-10001",
                opened,
                after_code={
                    Role.SPECIALIST: find,
                    Role.RESPONDER: responder("Here are the earliest repair windows."),
                },
            )
        slot_card = card_id_of(responses[-1], "slot_card")
        first = blocks(responses[-1], "slot_card")[0]["options"][0]["option"]
        run.steps.set_step(
            {
                Role.SPECIALIST: scheduling_steps(
                    tool(
                        TOOLS["book"],
                        BookVisitArgs(slot_id=int(first), issue="burning smell from the vents").model_dump(),
                    )
                ),
                Role.RESPONDER: responder("Your urgent visit is booked."),
            }
        )
        responses.append(pick(chat, slot_card, str(first)))
    return _result(run, f"wp6_{answer}", chat, responses, customer)


def wp6_yes(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    return _wp6(run, client, "yes")


def wp6_not_sure(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    return _wp6(run, client, "not_sure")


def wp6_no(
    run: CustomerRun, client: JourneyClient | None = None, *, verified_first: bool = True
) -> ScenarioResult:
    return _wp6(run, client, "no", verified_first=verified_first)


# Markers that tell the three specialists' requests apart (each appears only in its own report schema).
SPECIALIST_MARKERS: Mapping[str, str] = MappingProxyType(
    {"knowledge": '"answered"', "account": '"summary"', "scheduling": '"wanted_time"'}
)


def by_specialist(
    run: CustomerRun,
    *,
    knowledge: tuple[RawToolStep, ...] | None = None,
    account: tuple[RawToolStep, ...] | None = None,
    scheduling: tuple[RawToolStep, ...] | None = None,
) -> dict[str, Step]:
    """`by_marker` tables for one turn that runs several specialists at once."""
    tables: dict[str, Step] = {}
    for kind, entry in (("knowledge", knowledge), ("account", account), ("scheduling", scheduling)):
        if entry is not None:
            tables[SPECIALIST_MARKERS[kind]] = {Role.SPECIALIST: entry}
    return tables


def _locate_with_markers(
    run: CustomerRun,
    chat: Chat,
    customer_id: str,
    opening: httpx.Response,
    *,
    default: Step,
    markers: Mapping[str, Step],
) -> list[httpx.Response]:
    """As `locate_and_code`, running the code turn under `default` plus per-specialist tables."""
    assert blocks(opening, "locate_prompt")
    row = run.db.one("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    block = blocks(opening, "locate_prompt")[0]
    values = {"name": row["name"], "phone": row["phone"]}
    run.steps.set_step({Role.RESPONDER: responder("Thanks, I sent a code.")})
    sent = send_form(chat, block["card_id"], {k: str(v) for k, v in values.items()})
    run.steps.set_step(default, by_marker=markers)
    return [sent, send_code(chat, card_id_of(sent, "code_prompt"), newest_code(chat))]


def wp8(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    """Cancel membership: a verified customer; the system cannot complete it, so 'Done, auto-renew is off' is removed
    and a P3 request opens. (The identity-first variant loses the plan's handoff: plan 8 finding F-1.)"""
    customer = "MHC-10001"
    chat = _begin(run, client)
    ask = planner(account="membership", topic="membership")
    acct = account_steps(tool(TOOLS["membership"], {}), summary="Read the membership record.")
    responses = verified_open(
        run,
        chat,
        customer,
        "What does my membership include?",
        first={
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: ask,
            Role.RESPONDER: responder("I need to find your record first."),
        },
        after_code={
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: ask,
            Role.SPECIALIST: acct,
            Role.RESPONDER: responder("Here is your membership."),
        },
    )
    plan = planner(account="membership", handoff="membership_cancel", topic="membership")
    first, second = kb_steps(
        run,
        "cancel Comfort Club membership auto-renewal",
        "Auto-renewal can be cancelled before the renewal date.",
    )
    run.steps.set_step(
        {
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: plan,
            Role.RESPONDER: responder(
                "Done, auto-renew is off. Your renewal date is shown on your account card."
            ),
            Role.BRIEF: brief(
                needs=[{"message_id": next_message_id(run), "text": "Cancel my membership please"}],
                claims=[],
                open_decision="Switch off auto-renewal before the renewal date.",
            ),
        },
        by_marker=by_specialist(run, knowledge=(first, second), account=acct),
    )
    responses.append(say(chat, "Cancel my membership please"))
    return _result(run, "wp8", chat, responses, customer)


def planner_fallback(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    chat = _begin(run, client)
    bad = ScriptedFailure(kind=ProviderFailureKind.BODY_ERROR, http_status=503)
    run.steps.set_step(
        {
            Role.PLANNER: bad,
            Role.PLANNER_FALLBACK: planner(knowledge="yes", topic="membership"),
            Role.CLASSIFIER: NORMAL,
            Role.SPECIALIST: kb_steps(run, WP1_QUERY, "Members save 15% on repairs."),
            Role.RESPONDER: responder("Members save 15% on repairs."),
        }
    )
    return _result(run, "planner_fallback", chat, [say(chat, "Do members get a discount on repairs?")])


def planners_fail(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    chat = _begin(run, client)
    bad = ScriptedFailure(kind=ProviderFailureKind.BODY_ERROR, http_status=503)
    run.steps.set_step(
        {
            Role.PLANNER: bad,
            Role.PLANNER_FALLBACK: ScriptedFailure(kind=ProviderFailureKind.SERVER, http_status=500),
            Role.CLASSIFIER: NORMAL,
            Role.RESPONDER: responder("I could not work that out."),
            Role.BRIEF: brief(
                needs=[{"message_id": next_message_id(run), "text": "Do members get a discount"}],
                claims=[],
                open_decision="Answer the membership question.",
            ),
        }
    )
    return _result(run, "planners_fail", chat, [say(chat, "Do members get a discount on repairs?")])


def nodanger_classifier_fails(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    return nodanger(run, client, classifier_fails=True)


def no_source(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    chat = _begin(run, client)
    run.steps.set_step(
        {
            Role.PLANNER: planner(knowledge="yes", topic="other"),
            Role.CLASSIFIER: NORMAL,
            Role.SPECIALIST: no_source_steps("How long have you been in business?"),
            Role.RESPONDER: responder("I don't have that information."),
        }
    )
    return _result(run, "no_source", chat, [say(chat, "How long have you been in business?")])


def warranty(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    customer = "MHC-10003"
    chat = _begin(run, client)
    plan = planner(account="warranty", topic="warranty")
    acct = account_steps(tool(TOOLS["warranty"], {}), summary="Read the warranty record.")
    responses = verified_open(
        run,
        chat,
        customer,
        "Is my system still under warranty?",
        first={
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: plan,
            Role.RESPONDER: responder("I need to find your record first."),
        },
        after_code={
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: plan,
            Role.SPECIALIST: acct,
            Role.RESPONDER: responder("Here is what your warranty record shows."),
        },
    )
    return _result(run, "warranty", chat, responses, customer)


def three_tasks(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    """One message, three intents: a membership question, an invoice question and a booking (AC-29). Each specialist
    answers in one model call (tool and report in one step) so the six-call Sonnet brake is not reached."""
    customer = "MHC-10001"
    chat = _begin(run, client)
    plan = planner(knowledge="yes", account="invoice", scheduling="book_new", topic="booking")
    passage = top_passage(run, "Comfort Club what is included")
    know = (
        step(
            tool(TOOLS["kb_search"], KbSearchArgs(query="Comfort Club what is included").model_dump()),
            report(
                KnowledgeReport,
                points=[
                    ReportedPoint(
                        text="The Standard plan has two tune-ups a year.", passage_id=passage.passage_id
                    )
                ],
                answered=True,
            ),
        ),
    )
    acct = (
        step(
            tool(TOOLS["invoice"], ReadInvoicesArgs().model_dump(mode="json")),
            report(AccountReport, summary="Read the invoices."),
        ),
    )
    find = (
        step(
            tool(TOOLS["find_windows"], FindWindowsArgs(service_type="hvac_repair").model_dump(mode="json")),
            report(SchedulingReport, appointment_id=0, wanted_time="", note=""),
        ),
    )
    run.steps.set_step(
        {
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: plan,
            Role.RESPONDER: responder("I need to find your record first."),
        }
    )
    opening = say(chat, "What does my membership include, what is my invoice for, and can I book a repair?")
    responses = [opening]
    responses += _locate_with_markers(
        run,
        chat,
        customer,
        opening,
        default={
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: plan,
            Role.RESPONDER: responder("Here is what I found."),
        },
        markers=by_specialist(run, knowledge=know, account=acct, scheduling=find),
    )
    return _result(run, "three_tasks", chat, responses, customer)


def estimate(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    customer = "MHC-10001"
    chat = _begin(run, client)
    plan = planner(scheduling="book_new", topic="booking")
    find = scheduling_steps(
        tool(TOOLS["find_windows"], FindWindowsArgs(service_type="estimate").model_dump(mode="json"))
    )
    responses = verified_open(
        run,
        chat,
        customer,
        "I'd like an estimate for a new system",
        first={
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: plan,
            Role.RESPONDER: responder("I need to find your record first."),
        },
        after_code={
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: plan,
            Role.SPECIALIST: find,
            Role.RESPONDER: responder("Here are the estimate windows."),
        },
    )
    card = card_id_of(responses[-1], "slot_card")
    slot = int(blocks(responses[-1], "slot_card")[0]["options"][0]["option"])
    run.steps.set_step(
        {
            Role.SPECIALIST: scheduling_steps(
                tool(
                    TOOLS["book"], BookVisitArgs(slot_id=slot, issue="estimate for a new system").model_dump()
                )
            ),
            Role.RESPONDER: responder("Your estimate visit is booked."),
        }
    )
    responses.append(pick(chat, card, str(slot)))
    return _result(run, "estimate", chat, responses, customer, slot=slot)


def wrong_codes_for(real: str, count: int) -> tuple[str, ...]:
    out = [c for c in ("000000", "111111", "222222", "333333") if c != real]
    return tuple(out[:count])


def identity_failures(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    """Three ways to fail identity, each in its own chat of one login: no match, a real name with another phone, and
    three wrong codes. `extra` holds the response lists per case."""
    c = client if client is not None else None
    cases: dict[str, list[httpx.Response]] = {}
    threads: dict[str, str] = {}
    plan = planner(account="invoice", topic="billing")
    talk = {
        Role.CLASSIFIER: NORMAL,
        Role.PLANNER: plan,
        Role.RESPONDER: responder("I need to find your record first."),
    }
    real_row = run.db.one("SELECT * FROM customers WHERE customer_id = 'MHC-10001'")
    synthetic_name = "Zed " + letters(8).title()
    synthetic_phone = f"512-555-{secrets.randbelow(9000) + 1000}"

    def fail_locate(label: str, values: dict[str, str]) -> Chat:
        chat = open_chat(run, c)
        run.steps.set_step(talk)
        opened = say(chat, "I need my invoice explained")
        run.steps.set_step({Role.RESPONDER: responder("I could not find that record.")})
        failed = send_form(chat, blocks(opened, "locate_prompt")[0]["card_id"], values)
        cases[label] = [opened, failed]
        threads[label] = chat.thread_id
        return chat

    fail_locate("no_match", {"name": synthetic_name, "phone": synthetic_phone})
    fail_locate("real_name_other_phone", {"name": str(real_row["name"]), "phone": synthetic_phone})
    # three wrong codes on a located customer
    chat = open_chat(run, c)
    run.steps.set_step(talk)
    opened = say(chat, "I need my invoice explained")
    run.steps.set_step({Role.RESPONDER: responder("Thanks, I sent a code.")})
    sent = send_form(
        chat,
        blocks(opened, "locate_prompt")[0]["card_id"],
        {"name": str(real_row["name"]), "phone": str(real_row["phone"])},
    )
    real = newest_code(chat)
    out = [opened, sent]
    card = card_id_of(sent, "code_prompt")
    for wrong in wrong_codes_for(real, 3):
        run.steps.set_step(
            {
                Role.RESPONDER: responder("That code did not match."),
                Role.BRIEF: brief(
                    needs=[{"message_id": next_message_id(run), "text": "I need my invoice explained"}],
                    claims=[],
                    open_decision="Verify the customer another way.",
                ),
            }
        )
        out.append(send_code(chat, card, wrong))
        if blocks(out[-1], "code_prompt"):
            card = card_id_of(out[-1], "code_prompt")
    cases["wrong_codes"] = out
    threads["wrong_codes"] = chat.thread_id
    first = next(iter(cases.values()))[0]
    return ScenarioResult(
        name="identity_failures",
        thread_id=threads["wrong_codes"],
        turn_ids=tuple(r.json()["turn_id"] for r in out),
        responses=tuple(out),
        customer_id="MHC-10001",
        case_refs=case_refs_of(run, threads["wrong_codes"]),
        extra={"cases": cases, "threads": threads, "real_code": real, "first": first},
    )


def quick_checks(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    """A verified customer asks for a non-urgent repair: quick checks are offered once, declining books straight away."""
    customer = "MHC-10001"
    chat = _begin(run, client)
    ask = planner(account="membership", topic="membership")
    responses = verified_open(
        run,
        chat,
        customer,
        "What does my membership include?",
        first={
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: ask,
            Role.RESPONDER: responder("I need to find your record first."),
        },
        after_code={
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: ask,
            Role.SPECIALIST: account_steps(
                tool(TOOLS["membership"], {}), summary="Read the membership record."
            ),
            Role.RESPONDER: responder("Here is your membership."),
        },
    )
    find = scheduling_steps(
        tool(TOOLS["find_windows"], FindWindowsArgs(service_type="hvac_repair").model_dump(mode="json")),
    )
    run.steps.set_step(
        {
            Role.CLASSIFIER: NORMAL,
            Role.PLANNER: BOOKING_PLAN,
            Role.SPECIALIST: find,
            Role.RESPONDER: responder("Here are the windows."),
        }
    )
    offer = say(chat, "My upstairs vent is weak, can I book a repair?")
    responses.append(offer)
    after_offer = run.db.one("SELECT outcome FROM conversations WHERE thread_id = ?", (chat.thread_id,))[
        "outcome"
    ]
    # declining books straight away: the resumed task shows windows again, without a second offer
    run.steps.set_step({Role.SPECIALIST: find, Role.RESPONDER: responder("Here are the windows.")})
    declined = pick(chat, card_id_of(offer, "quick_checks"), "skip_and_book")
    responses.append(declined)
    slot_card = card_id_of(declined, "slot_card")
    slot = int(blocks(declined, "slot_card")[0]["options"][0]["option"])
    run.steps.set_step(
        {
            Role.SPECIALIST: scheduling_steps(
                tool(TOOLS["book"], BookVisitArgs(slot_id=slot, issue="weak airflow upstairs").model_dump())
            ),
            Role.RESPONDER: responder("Your visit is booked."),
        }
    )
    responses.append(pick(chat, slot_card, str(slot)))
    return _result(
        run,
        "quick_checks",
        chat,
        responses,
        customer,
        slot=slot,
        offer_turn=offer.json()["turn_id"],
        conversation_after_offer=after_offer,
    )


def urgent_no_heat(run: CustomerRun, client: JourneyClient | None = None) -> ScenarioResult:
    """The freezing no-heat message the classifier raises as danger: no quick checks are offered."""
    chat = _begin(run, client)
    run.steps.set_step({Role.PLANNER: BOOKING_PLAN, Role.CLASSIFIER: classifier("danger")})
    return _result(run, "urgent_no_heat", chat, [say(chat, "No heat at all and it's freezing")])


def run_dev_set(run: CustomerRun) -> tuple[ScenarioResult, ...]:
    """The first dev set on one app and one login, then CON-4 on the wp7 thread and on a fresh thread (AC-28, 30, 39, 42)."""
    client = run.login().client
    drivers = (wp1, wp2, wp3, wp4, wp4f, wp5, wp6_yes, wp6_not_sure, wp6_no, wp7, wp8, danger, nodanger)
    results = [driver(run, client) for driver in drivers]
    results.append(request_person(run, client, next(r for r in results if r.name == "wp7")))
    results.append(request_person(run, client, None))
    return tuple(results)


def request_person(run: CustomerRun, client: JourneyClient, on: ScenarioResult | None) -> ScenarioResult:
    """CON-4 on an existing scenario thread, or on a fresh one."""
    chat = (
        open_chat(run, client)
        if on is None
        else Chat(run=run, client=client, thread_id=on.thread_id, opened={})
    )
    run.steps.set_step({})
    turn_id = str(uuid.uuid4())
    response = client.call(
        "POST",
        f"/api/chat/sessions/{chat.thread_id}/handoff",
        operation_id="requestPerson",
        body={"turn_id": turn_id},
    )
    assert response.status_code == 200, f"requestPerson answered HTTP {response.status_code}"
    return ScenarioResult(
        name="con4_wp7" if on is not None else "con4_fresh",
        thread_id=chat.thread_id,
        turn_ids=(turn_id,),
        responses=(response,),
        customer_id=None,
        case_refs=case_refs_of(run, chat.thread_id),
    )
