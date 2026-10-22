"""AEA-62, J-2 (`J-DRIVERS`) in Chrome on the production build: membership with a source chip (WP-1), the stale twin
never shown, billing after the code (WP-2), and the current warranty term (K-8). Level: integrated with a scripted
model. Every step asserts what Chrome shows (through AEA-58's selector module) and what the working copy stored.
Steps whose selector row, service or model cache is missing are recorded blocked with their owner, never passed.

This file also holds AEA-62's shared browser helpers; j3, j6 and j8 import them by name.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Collection, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn, cast
from zoneinfo import ZoneInfo

import pytest

from meridian.agent.prompts.routing import DANGER_FIELD
from meridian.agent.prompts.specialists import REPORT_FACTS_TOOL
from meridian.agent.tools.knowledge import KB_SEARCH_NAME, KbSearchArgs
from meridian.config import Settings
from meridian.domain.common import LLMFacing, Role
from meridian.domain.handoff import BriefExtraction
from meridian.domain.specialists import AccountReport, KnowledgeReport, ReportedPoint, SchedulingReport
from meridian.domain.turn import PlannerChoices, ResponderDraft
from meridian.policy.texts import TextId, render
from meridian.retrieval.settings import MIN_SCORE, SEARCH_K
from meridian.web.container import Key
from tests.integration.customer_support import (
    StepEntry,
    StepScript,
    built_index_dir,
    fastembed_offline,
    step_overrides,
)
from tests.journeys.browser.network import ApiExchange
from tests.journeys.browser.pages import PHONE, BrowserPage, BrowserRun
from tests.journeys.browser.selectors import locate, locate_in
from tests.journeys.browser.steps import (
    SIGN_IN_SELECTORS,
    BrowserLogin,
    browser_step,
    first_hop,
    sign_in_via_form,
)
from tests.journeys.j1.test_aea_57 import TURN_NEEDS
from tests.journeys.support.run import JourneyRun
from tests.journeys.support.scripted_model import RawToolCall, RawToolStep
from tests.journeys.support.steps import Missing, StepResult, blocked_message, owners_of, stop_blocked

if TYPE_CHECKING:
    from playwright.sync_api import Page

    from meridian.domain.records import Passage

pytest_plugins = ("tests.journeys.browser.plugin",)
pytestmark = pytest.mark.journey

# ---------------------------------------------------------------------------------------------------------------
# AEA-62 shared browser helpers
# ---------------------------------------------------------------------------------------------------------------
J2, J3, J6, J8 = "J-2", "J-3", "J-6", "J-8"
CHI = ZoneInfo("America/Chicago")
VERIFY_NEEDS = (*TURN_NEEDS, "identity_service")
HANDOFF_NEEDS = (*TURN_NEEDS, "handoff_service", "case_service")
STAFF_NEEDS = ("login_sessions", "staff_access", "case_service")
CHAT_SELECTORS = ("chat.ready", "chat.composer", "chat.send", "chat.entry.assistant", "chat.block.text")
IDENTITY_SELECTORS = (
    "chat.block.locate_prompt",
    "card.locate.name",
    "card.locate.phone",
    "card.locate.submit",
    "chat.block.code_prompt",
    "card.code.input",
    "card.code.submit",
    "screen.scr2",
    "inbox.message.active",
    "inbox.code",
)
EXCLUDED_FILES = frozenset({"faq/faq_old_copy.md"})  # plus every file under "archive/" (R-10, DEC-4)
SEED_REFS = ("MHC-C-0005", "MHC-C-0006", "MHC-C-0007", "MHC-C-0008")  # stage7/cases.md section 7
ROLES = ("customer", "representative", "supervisor", "owner")
Table = Mapping[Role, StepEntry]
Factory = Callable[..., AbstractContextManager[BrowserRun]]

PLANNER_DEFAULTS = {
    "knowledge": "no",
    "account": "none",
    "scheduling": "none",
    "handoff": "none",
    "topic": "other",
}


def planner(**choices: str) -> str:
    return PlannerChoices.model_validate({**PLANNER_DEFAULTS, **choices}).model_dump_json()


def classifier(label: str) -> str:
    return json.dumps({DANGER_FIELD: label})


NORMAL = classifier("normal")


def responder(text: str) -> str:
    return ResponderDraft(text=text).model_dump_json()


def brief(**fields: Any) -> str:
    return BriefExtraction(**fields).model_dump_json()


def tool(name: str, args: Mapping[str, Any], call_id: str = "call-1") -> RawToolCall:
    return RawToolCall(id=call_id, name=name, arguments=json.dumps(args))


def report(model: type[LLMFacing], **fields: Any) -> RawToolCall:
    return tool(REPORT_FACTS_TOOL, model(**fields).model_dump(mode="json"), call_id="call-report")


def step(*calls: RawToolCall, text: str = "") -> RawToolStep:
    return RawToolStep(text=text, calls=calls, stop_reason="tool_use" if calls else "end_turn")


# by_marker keys: each report schema's own field name, quoted as it appears in the request JSON.
KNOWLEDGE_MARKER = '"answered"'
ACCOUNT_MARKER = '"summary"'
SCHEDULING_MARKER = '"wanted_time"'
assert "answered" in KnowledgeReport.model_fields and "summary" in AccountReport.model_fields
assert "wanted_time" in SchedulingReport.model_fields


@dataclass(frozen=True)
class Turn:
    turn_id: str  # the turn_id Chrome sent (request body)
    body: dict[str, Any]  # the 200 TurnResponse
    exchange: ApiExchange
    roles_called: frozenset[Role]


def block_here(run: JourneyRun, journey: str, name: str, what: str, owner: str) -> NoReturn:
    """A blocked condition found mid-test is recorded with its owner and is never a pass."""
    missing = (Missing(what, owner),)
    run.collector.add_step(
        StepResult(journey, name, run.nodeid, "blocked", blocked_message(missing), owners_of(missing), 0.0)
    )
    stop_blocked(missing, strict=run.strict)


def page_text(page: Page) -> str:
    return str(page.evaluate("() => document.body.innerText"))


def page_post(bp: BrowserPage, path: str, body: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = bp.page.evaluate(
        "async ([p, b]) => { const r = await fetch(p, {method: 'POST', credentials: 'include', "
        "headers: {'content-type': 'application/json'}, body: b}); return {status: r.status, text: await r.text()}; }",
        [path, json.dumps(body)],
    )
    return result


def second_tab(bp: BrowserPage) -> BrowserPage:
    """Same context (same cookie, same login session); the context's NetworkLog sees its requests too."""
    return BrowserPage(device=bp.device, context=bp.context, page=bp.context.new_page(), net=bp.net)


def blocks_of(body: Mapping[str, Any], kind: str) -> list[dict[str, Any]]:
    return [b for b in body["blocks"] if b["type"] == kind]


def chips_of(body: Mapping[str, Any]) -> list[dict[str, Any]]:
    chips: list[dict[str, Any]] = []
    for block in body["blocks"]:
        if block["type"] == "text":
            chips.extend(block.get("sources") or [])
        elif block["type"] == "source_chip":
            chips.append(block["source"])
    return chips


def steps(run: JourneyRun) -> StepScript:
    script = run.script
    assert isinstance(script, StepScript), "run was not opened with AEA-51's StepScript"
    return script


def expect_turn(
    run: JourneyRun,
    bp: BrowserPage,
    *,
    table: Table,
    must: Collection[Role],
    send: Callable[[], None],
    by_marker: Mapping[str, Table] | None = None,
) -> Turn:
    """One scripted turn (PA-1): the script disagreeing with production fails here; nothing leaks to the next turn."""
    script = steps(run)
    calls_mark = len(script.calls)
    net_mark = bp.net.mark()
    script.set_step(table, by_marker=by_marker)
    send()
    ex = bp.net.wait_for(bp.page, "submitTurn", since=net_mark, timeout_ms=70_000)
    assert ex.status == 200, f"submitTurn answered {ex.status}"
    assert ex.request_body is not None and ex.body is not None
    turn_id = json.loads(ex.request_body)["turn_id"]
    body = json.loads(ex.body)
    assert body["turn_id"] == turn_id
    called = script.calls_since(calls_mark)
    bad = [(c.role.value, c.result) for c in called if c.result in ("invalid_output", "exhausted")]
    assert not bad, f"script problems: {bad}"
    roles = frozenset(c.role for c in called)
    missing = set(must) - roles
    assert not missing, f"roles never called: {sorted(r.value for r in missing)}"
    script.set_step({})
    print(f"turn {turn_id}: roles {sorted(r.value for r in roles)}")
    return Turn(turn_id, body, ex, roles)


def say(
    run: JourneyRun,
    bp: BrowserPage,
    text: str,
    *,
    table: Table,
    must: Collection[Role],
    by_marker: Mapping[str, Table] | None = None,
) -> Turn:
    locate(bp.page, "chat.ready").wait_for()

    def send() -> None:
        locate(bp.page, "chat.composer").fill(text)
        locate(bp.page, "chat.send").click()

    return expect_turn(run, bp, table=table, must=must, send=send, by_marker=by_marker)


def open_chat(run: JourneyRun, bp: BrowserPage) -> tuple[BrowserLogin, str]:
    first = bp.page.goto("/")
    assert first is not None and first_hop(first).status == 303
    mark = bp.net.mark()
    login = sign_in_via_form(run, bp)
    locate(bp.page, "screen.scr1").wait_for(state="visible")
    start = bp.net.wait_for(bp.page, "startChatSession", since=mark)
    assert start.status == 201 and start.body is not None
    return login, str(json.loads(start.body)["thread_id"])


def assert_no_excluded(run: JourneyRun, thread_id: str) -> list[str]:
    rows = run.db.rows("SELECT passage_ids FROM lookup_log WHERE thread_id = ?", (thread_id,))
    ids = [pid for r in rows for pid in json.loads(r["passage_ids"])]
    bad = [p for p in ids if is_excluded(p.split("#", 1)[0])]
    assert bad == []
    print(f"passage ids: {ids}")
    return ids


def is_excluded(file: str) -> bool:
    return file.startswith("archive/") or file in EXCLUDED_FILES


def _search(run: JourneyRun, query: str) -> Any:
    index = run.container.get(Key[Any]("retrieval_index"))  # the object the kb_search tool calls (AEA-51)
    return index.search(query, k=SEARCH_K, min_score=MIN_SCORE)


def first_passage(run: JourneyRun, query: str, file: str) -> Passage:
    result = _search(run, query)
    hits = [p for p in result.passages if p.file == file]
    assert not result.below_floor and hits, f"{query!r}: the index returned no passage from {file}"
    return cast("Passage", hits[0])


def top_passage(run: JourneyRun, query: str) -> Passage:
    result = _search(run, query)
    assert not result.below_floor and result.passages
    return cast("Passage", result.passages[0])


def passages_hold(run: JourneyRun, query: str, needles: Collection[str]) -> None:
    text = " ".join(p.text for p in _search(run, query).passages)
    missing = [n for n in needles if n not in text]
    assert not missing, (
        f"{query!r}: the passages lack {missing}; change the query wording, never the expected facts"
    )


def knowledge_table(
    run: JourneyRun, query: str, file: str, point_text: str, reply: str, *, topic: str
) -> Table:
    p = first_passage(run, query, file)
    return {
        Role.PLANNER: planner(knowledge="yes", topic=topic),
        Role.CLASSIFIER: NORMAL,
        Role.SPECIALIST: (
            step(tool(KB_SEARCH_NAME, KbSearchArgs(query=query).model_dump())),
            step(
                report(
                    KnowledgeReport,
                    points=[ReportedPoint(text=point_text, passage_id=p.passage_id)],
                    answered=True,
                )
            ),
        ),
        Role.RESPONDER: responder(reply),
    }


def assert_turn_records(run: JourneyRun, thread_id: str) -> None:
    """WF-1: every turn of the thread left its record, one gate event, and spend rows when models were called."""
    for t in run.db.rows("SELECT * FROM turns WHERE thread_id = ? ORDER BY sequence", (thread_id,)):
        tid = t["turn_id"]
        assert t["status"] == "completed", f"turn {t['sequence']} is {t['status']}"
        for column in ("gate_result", "outcome", "server_ms", "trace_export"):
            assert t[column] is not None, f"turn {t['sequence']} has no {column}"
        assert run.db.count("check_events", "turn_id = ? AND check_kind = 'gate'", (tid,)) == 1
        spend = run.db.count("spend_ledger", "turn_id = ?", (tid,))
        if t["model_calls"]:
            assert spend >= 1, f"turn {t['sequence']} called models but wrote no spend row"
        print(
            f"record seq {t['sequence']}: gate {t['gate_result']}, outcome {t['outcome']}, {t['server_ms']} ms, "
            f"trace {t['trace_export']}, lookups {run.db.count('lookup_log', 'turn_id = ?', (tid,))}, "
            f"checks {run.db.count('check_events', 'turn_id = ?', (tid,))}, spend {spend}"
        )


def next_message_id(run: JourneyRun) -> int:
    return int(run.db.scalar("SELECT COALESCE(MAX(id), 0) + 1 FROM messages"))


def card_shot(brun: BrowserRun, bp: BrowserPage, key: str, label: str) -> Path:
    """Element screenshot: a card shot in a flow that showed identity values must not include the rest of the page."""
    return brun.screenshot_element(bp, locate(bp.page, key).last, label)


def _overrides(settings: Settings, script: Any, clock: Callable[[], Any] | None) -> Any:
    return step_overrides(settings, cast(StepScript, script), wall_clock=clock)


@contextmanager
def browser_run(
    factory: Factory, journey: str, *, index: bool = False, clock: bool = False
) -> Iterator[tuple[BrowserRun, Path | None]]:
    """Every AEA-62 run uses the step-scripted model; knowledge runs hold the offline fastembed environment."""
    kwargs: dict[str, Any] = {"with_clock": clock, "script": StepScript(), "overrides_for": _overrides}
    if not index:
        with factory(**kwargs) as brun:
            yield brun, None
        return
    with fastembed_offline():
        index_dir = built_index_dir()
        if index_dir is None:
            with factory(**kwargs) as brun:
                block_here(
                    brun.run,
                    journey,
                    "0 index",
                    "bge-small-en-v1.5 not cached in var/fastembed",
                    "environment (fastembed model cache)",
                )
        with factory(index_dir=index_dir, **kwargs) as brun:
            yield brun, index_dir


# ---------------------------------------------------------------------------------------------------------------
# J-2 membership (WP-1) and warranty (K-8)
# ---------------------------------------------------------------------------------------------------------------
MEMBERSHIP_FILE = "membership/comfort_club_overview.md"
WARRANTY_FILE = "warranty/warranty_policy.md"
ARCHIVE_WARRANTY = "archive/warranty_terms_2023.txt"
STALE = (
    "$149",
    "$12.99",
    "$219",
    "10% off",
    "cancel any time for a full prorated refund",
    "transfers to a new address",
)
VERDICT = ("bill is wrong", "charged incorrectly", "overcharged", "credit is owed", "owe you a credit")


@dataclass(frozen=True)
class Ask:
    text: str
    query: str
    point: str
    reply: str
    facts: tuple[str, ...]
    needles: tuple[str, ...]


ASKS = (
    Ask(
        "What does the Comfort Club membership actually include?",
        "What does the Comfort Club membership include?",
        "Standard includes two tune-ups a year, priority scheduling and 15% off repairs.",
        "Comfort Club Standard includes two tune-ups a year (cooling and heating), priority scheduling, the $89 "
        "diagnostic fee waived, 15% off repairs, no after-hours dispatch fee, and maintenance reminders. The plan "
        "is $149 a year.",
        ("two tune-ups", "priority scheduling", "$89", "15% off repairs", "after-hours", "reminders"),
        ("$89", "15%"),
    ),
    Ask(
        "And how much is it?",
        "How much does the Comfort Club membership cost?",
        "Standard is $189 a year or $16.99 a month with a 12-month minimum.",
        "Standard is $189 a year, or $16.99 a month with a 12-month minimum. Each additional system is $99 a year.",
        ("$189", "$16.99", "12-month minimum", "$99"),
        ("$189", "$16.99", "$99"),
    ),
    Ask(
        "Does it cover plumbing?",
        "Does the Comfort Club membership cover plumbing?",
        "Plus is $269 a year and adds plumbing items.",
        "Standard covers heating and cooling only. Comfort Club Plus is $269 a year and adds an annual water-heater "
        "flush and inspection, a plumbing inspection, and 15% off plumbing repairs.",
        ("$269", "water-heater flush", "plumbing inspection", "15% off plumbing repairs"),
        ("$269",),
    ),
)
AfterTurn = Callable[[BrowserPage, str, int, Ask, Turn], None]


def membership_leg(brun: BrowserRun, after_turn: AfterTurn) -> tuple[BrowserPage, str, list[Turn]]:
    run = brun.run
    bp = brun.open(PHONE)
    with browser_step(
        run,
        J2,
        "2a sign in and chat",
        needs=TURN_NEEDS,
        operations=("login", "startChatSession"),
        selectors=(*SIGN_IN_SELECTORS, "screen.scr1"),
    ):
        _, tid = open_chat(run, bp)
    turns: list[Turn] = []
    for n, ask in enumerate(ASKS, start=1):
        with browser_step(
            run,
            J2,
            f"2b turn {n}",
            needs=TURN_NEEDS,
            operations=("submitTurn",),
            selectors=(*CHAT_SELECTORS, "chat.source"),
        ):
            passages_hold(run, ask.query, ask.needles)
            table = knowledge_table(run, ask.query, MEMBERSHIP_FILE, ask.point, ask.reply, topic="membership")
            turns.append(
                say(
                    run,
                    bp,
                    ask.text,
                    table=table,
                    must={Role.PLANNER, Role.CLASSIFIER, Role.SPECIALIST, Role.RESPONDER},
                )
            )
        after_turn(bp, tid, n, ask, turns[-1])
    return bp, tid, turns


def test_j2_membership_with_source(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J2, index=True) as (brun, _):
        run = brun.run

        def check(bp: BrowserPage, tid: str, n: int, ask: Ask, turn: Turn) -> None:
            with browser_step(
                run,
                J2,
                f"2c checks {n}",
                operations=("submitTurn",),
                selectors=(
                    "chat.entry.assistant",
                    "chat.source",
                    "chat.source.toggle",
                    "chat.source.excerpt",
                ),
            ):
                entry = locate(bp.page, "chat.entry.assistant").last
                text = entry.inner_text()
                assert [f for f in ask.facts if f not in text] == []
                chips = chips_of(turn.body)
                mine = [c for c in chips if c["file"] == MEMBERSHIP_FILE]
                assert mine and not [c for c in chips if is_excluded(c["file"])]
                chip = locate_in(entry, "chat.source").first
                assert MEMBERSHIP_FILE in chip.inner_text()
                locate_in(chip, "chat.source.toggle").click()
                assert (
                    locate_in(entry, "chat.source.excerpt").first.inner_text().strip()
                    == mine[0]["excerpt"].strip()
                )
                rows = run.db.rows("SELECT passage_ids FROM lookup_log WHERE turn_id = ?", (turn.turn_id,))
                ids = {pid for r in rows for pid in json.loads(r["passage_ids"])}
                assert {c["passage_id"] for c in chips} <= ids
                print(f"turn {n}: chip files {sorted({c['file'] for c in chips})} | lookup ids {sorted(ids)}")

        bp, tid, _turns = membership_leg(brun, check)
        with browser_step(run, J2, "2d stored and screenshot", selectors=("chat.entry.assistant",)):
            assert run.db.count("actions", "thread_id = ? AND kind = 'verified'", (tid,)) == 0
            assert run.db.count("cases", "thread_id = ?", (tid,)) == 0
            assert (
                run.db.scalar("SELECT outcome FROM conversations WHERE thread_id = ?", (tid,)) != "handed_off"
            )
            brun.screenshot(bp, "after-third-reply")
        with browser_step(run, J2, "2e records"):
            assert_turn_records(run, tid)


def test_j2_stale_values_absent(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J2, index=True) as (brun, _):
        run = brun.run

        def check(bp: BrowserPage, tid: str, n: int, ask: Ask, turn: Turn) -> None:
            with browser_step(run, J2, f"3a stale strings {n}", selectors=("chat.entry.assistant",)):
                text = page_text(bp.page).lower()
                hits = {s: text.count(s.lower()) for s in STALE}
                print(f"turn {n}: stale hits {hits}")
                assert not any(hits.values())

        _bp, tid, turns = membership_leg(brun, check)
        with browser_step(run, J2, "3b fact check removed $149"):
            rows = run.db.rows(
                "SELECT * FROM check_events WHERE turn_id = ? AND check_kind = 'fact' AND result = 'trimmed'",
                (turns[0].turn_id,),
            )
            assert len(rows) == 1 and rows[0]["removed"] >= 1
            assert "$149" not in json.dumps(rows[0])
        with browser_step(run, J2, "3c no excluded source"):
            assert_no_excluded(run, tid)
            assert not [c for t in turns for c in chips_of(t.body) if is_excluded(c["file"])]


def test_j2_invoice_after_code_as_billed(browser_journey_factory: Factory) -> None:
    with browser_run(browser_journey_factory, J2) as (brun, _):
        from tests.journeys.j3.test_aea_62 import (  # function-local: j3 imports j2
            INVOICE_VALUES,
            billing_through_code,
        )

        run = brun.run
        bp = brun.open(PHONE)
        with browser_step(
            run,
            J2,
            "4a sign in and chat",
            needs=TURN_NEEDS,
            operations=("login", "startChatSession"),
            selectors=(*SIGN_IN_SELECTORS, "screen.scr1"),
        ):
            _, tid = open_chat(run, bp)
        with browser_step(
            run,
            J2,
            "4b ask, locate, code",
            needs=VERIFY_NEEDS,
            operations=("submitTurn", "listDemoInbox"),
            selectors=(*CHAT_SELECTORS, *IDENTITY_SELECTORS, "chat.block.account_card"),
        ):
            v = billing_through_code(run, bp)
        with browser_step(
            run, J2, "4c page, api and stored", selectors=("chat.block.account_card", "chat.entry.assistant")
        ):
            assert render(TextId.VERIFIED) in locate(bp.page, "chat.entry.assistant").last.inner_text()
            card_text = locate(bp.page, "chat.block.account_card").last.inner_text()
            assert [s for s in ("INV-204411", *INVOICE_VALUES) if s not in card_text] == []
            invoice = blocks_of(v.code_turn.body, "account_card")[-1]["invoice"]
            assert invoice["invoice_id"] == "INV-204411"
            assert [ln["amount"]["display"] for ln in invoice["lines"]] == ["$89.00", "$245.00", "$144.00"]
            assert invoice["total"]["display"] == "$478.00" and invoice["due_on"] == "2026-11-01"
            text = page_text(bp.page).lower()
            assert "$149" not in text and not [w for w in VERDICT if w in text]
            ver = run.db.one(
                "SELECT a.turn_id, t.sequence FROM actions a JOIN turns t ON t.turn_id = a.turn_id "
                "WHERE a.thread_id = ? AND a.kind = 'verified'",
                (tid,),
            )
            looks = run.db.rows(
                "SELECT l.id, l.record_ids, t.sequence FROM lookup_log l JOIN turns t ON t.turn_id = l.turn_id "
                "WHERE l.thread_id = ?",
                (tid,),
            )
            inv = [r for r in looks if "INV-204411" in json.loads(r["record_ids"])]
            assert inv and all(r["sequence"] >= ver["sequence"] for r in inv)
            assert run.db.count("cases", "thread_id = ?", (tid,)) == 0
            assert_no_excluded(run, tid)
            print(
                f"verified at sequence {ver['sequence']}; invoice lookups {[(r['id'], r['sequence']) for r in inv]}"
            )
            card_shot(brun, bp, "chat.block.account_card", "account-card")
        with browser_step(run, J2, "4d records"):
            assert_turn_records(run, tid)


def test_j2_warranty_current_policy(browser_journey_factory: Factory) -> None:
    query = "How long is the repair warranty?"
    with browser_run(browser_journey_factory, J2, index=True) as (brun, _):
        run = brun.run
        bp = brun.open(PHONE)
        with browser_step(
            run,
            J2,
            "5a sign in and chat",
            needs=TURN_NEEDS,
            operations=("login", "startChatSession"),
            selectors=(*SIGN_IN_SELECTORS, "screen.scr1"),
        ):
            _, tid = open_chat(run, bp)
        with browser_step(
            run,
            J2,
            "5b turn",
            needs=TURN_NEEDS,
            operations=("submitTurn",),
            selectors=(*CHAT_SELECTORS, "chat.source"),
        ):
            passages_hold(run, query, ("1",))
            table = knowledge_table(
                run,
                query,
                WARRANTY_FILE,
                "Repairs carry a 1-year labor warranty on the part repaired.",
                "Repairs come with a 1-year labor warranty on the part we repaired.",
                topic="warranty",
            )
            turn = say(
                run,
                bp,
                query,
                table=table,
                must={Role.PLANNER, Role.CLASSIFIER, Role.SPECIALIST, Role.RESPONDER},
            )
        with browser_step(run, J2, "5c checks", selectors=("chat.entry.assistant", "chat.source")):
            entry = locate(bp.page, "chat.entry.assistant").last
            assert "1-year" in entry.inner_text()
            mine = [c for c in chips_of(turn.body) if c["file"] == WARRANTY_FILE]
            assert mine and "2025-06-15" in (mine[0]["version_date"] or "") + (mine[0]["version_label"] or "")
            assert WARRANTY_FILE in locate_in(entry, "chat.source").first.inner_text()
            text = page_text(bp.page).lower()
            assert "90-day" not in text and "90 days" not in text
            ids = assert_no_excluded(run, tid)
            assert any(i.startswith(WARRANTY_FILE + "#") for i in ids)
            assert not [i for i in ids if i.startswith(ARCHIVE_WARRANTY)]
            assert run.db.count("actions", "thread_id = ? AND kind = 'verified'", (tid,)) == 0
        with browser_step(run, J2, "5d records"):
            assert_turn_records(run, tid)
