# SP-1 build slice plan: one thin two-layer turn, enough to run the 11 scripted conversations

**Slice:** `build` (the only build slice of spike SP-1). **Planner:** fanout-planner, 2026-10-21. **Implementer:**
fanout-implementer (Sonnet). **Readiness:** READY (section 9). **Lane:** spike (zero-to-hero Stage 5, light testing,
throwaway code on `spike/SP-1-build`, never merged).

**What "done" looks like, concretely.** From the worktree root,
`python -m spikes.sp1.harness.run --option A --mock` plays the 11 scripted conversations against the build with no
network, prints the summary, and exits 0 with `unrecovered turns 0`. The same holds for options B, C and D. The CO
alarm turn's reply starts with the safety text, the DANGER turn takes the `danger` path, and the harness folder is
byte-for-byte unchanged. The orchestrator then runs the live sweep; **you make no live calls**.

---

## 1. Goal and sources

**Goal.** Build `spikes/sp1/app/`: a plain-asyncio version of one customer turn in the two-layer design. Code gates
run first. Then a planner and a raise-only danger classifier run concurrently. Then three specialists run with
scoped tools in a braked tool loop. Then a code escalation check, turn facts, and a responder with no tools. Last,
R-46 checks and the code-appended promise, reference and follow-up line. All four model mixes (options A–D) run
through one code path and differ only in `OptionConfig`.

**Sources (read-only; paths in the primary checkout `/home/linuxuser/workspaces/inno-aea-callcenter` unless marked).**

| Source | What it fixes |
|---|---|
| `docs/analysis/spikes/SP-1-two-layer-turn-latency-cost.md` §1 *The brief*, *Measures and pass line* | What is built, the five hard gates, run order. Pass line unchanged. |
| Worktree `spikes/sp1/harness/contract.py` | `Agent`, `Session`, `TurnResult`, `CallRecord`, `ToolEvent`, `CaseEvent`, `ToolKind`, `WRITE_KINDS`, `TurnPath` |
| Worktree `spikes/sp1/harness/options.py` | Options A–D, roles, providers, effort |
| Worktree `spikes/sp1/harness/scenarios.py` | The 11 conversations, every check, exact strings `P_1BD`, `P_REFUND`, `FOLLOWUP`, `WINDOW_WARNING`, `SAFETY_TEXT`, `EMERGENCY`, the `*_PRIVATE` lists |
| Worktree `spikes/sp1/harness/checks.py` | The hard gates, `norm()`, `_CLAIMS`, `_SENT` |
| Worktree `spikes/sp1/harness/paths.py`, `pricing.py`, `run.py` | `DATASET`, `ISSUED_DB`, `KB_DIR`, `KB_TRANSCRIPTIONS`, `ENV_FILE`, `EMBED_CACHE`, `TODAY`, `NOW`; pricing keys; how turns are timed and scored |
| `docs/prd/inno-aea-callcenter-prd.md` §4 (R-2, R-5–R-8, R-10, R-11, R-13, R-15–R-21, R-24–R-28, R-45–R-47), §5, §6.1–§6.2 | Requirements and the two-layer flow |
| `docs/data/worked-pairs.md` WP-1…WP-8 *Required output* | The answer key |
| `docs/research/2026-10-20-vendor-and-framework-facts.md` §1, §2e, §3, §4 | No forced `tool_choice` on Sonnet 5.5; thinking billed; effort; Jev limits; no blocking the loop; retries and deadlines |
| `docs/design/hard-problems.md` HP-1…HP-4 | Code vs model split; raise-only classifier; fee rule; completion check |
| `docs/data/issued/meridian_dataset/knowledge_base/**`, `scheduling_db/SCHEMA.md`, `data/kb_transcriptions/holiday_hours_2026.md` | KB and DB facts |
| `src/meridian/{triggers,policy,identity,tools,db}.py`, `src/meridian/agent/{graph,prompt}.py`, `src/meridian/kb/{ingest,retrieve,manifest}.py` | Parked code to **copy and adapt, never import** |
| Workspace rules `fanout-plan-then-implement.md`, `build-loop-test-scope.md`, `context-management-multi-turn.md`, `async-safety.md` | Roles, light tests, per-turn rebuilt context, closers for every client |

---

## 2. Boundary

**Worktree (the only place you edit):** `/home/linuxuser/workspaces/inno-aea-callcenter/var/worktrees/sp1-build`
(branch `spike/SP-1-build`, cut from `spike/SP-1-base` @ `e45d96b`). All paths below are relative to it.

**Owned files (create; nothing else may be created or edited):**

| File | One-line responsibility | Target size |
|---|---|---|
| `spikes/sp1/app/__init__.py` | empty package marker | 0 |
| `spikes/sp1/app/entry.py` | `make_agent()`, `SpikeAgent` (shared clients, per-role model clients, KB warm-up) | ~60 |
| `spikes/sp1/app/policy.py` | Fixed clock, exact customer texts, case table, promises, tails, zones, windows, fee rule, labels | ~200 |
| `spikes/sp1/app/gates.py` | Word rules (safety, burning, danger, person, handoff), burning answer, code/name/phone extraction | ~130 |
| `spikes/sp1/app/store.py` | SQLite reads/writes on the conversation's `db_path` (sync functions, called via `asyncio.to_thread`) | ~170 |
| `spikes/sp1/app/identity.py` | Locate + simulated code to the demo inbox (hashed) + verify | ~70 |
| `spikes/sp1/app/kb.py` | Manifest, chunking, fastembed index built once per process, search | ~150 |
| `spikes/sp1/app/providers.py` | Shared types, `ModelClient` Protocol, `Outcome`, retry loop, `Shared` clients, `build_client()` | ~180 |
| `spikes/sp1/app/llm_anthropic.py` | `AnthropicClient` (AsyncAnthropic) | ~170 |
| `spikes/sp1/app/llm_openrouter.py` | `OpenRouterClient` (chat completions) and `JevClient` (decisions API) | ~220 |
| `spikes/sp1/app/mock.py` | `MockClient`: deterministic, no network | ~140 |
| `spikes/sp1/app/planner.py` | Planner and classifier choice fields, prompts, `plan()`, `classify()`, `normalize()` | ~170 |
| `spikes/sp1/app/specialists.py` | Tool specs per specialist, code-checked executors, braked tool loop | ~290 |
| `spikes/sp1/app/responder.py` | Responder prompt, R-46 completion check, amount suppression, brief call | ~170 |
| `spikes/sp1/app/turn.py` | `ConvState`, `TurnAcc`, `Session` and the turn pipeline | ~300 |
| `spikes/sp1/app/tests/__init__.py` | empty | 0 |
| `spikes/sp1/app/tests/test_rules.py` | Unit tests: gates, fee rule, policy texts, completion check, identity lookup | ~120 |
| `spikes/sp1/app/tests/test_mock_run.py` | End-to-end mock run (A–D) and the turn-2+ prompt test | ~90 |

**Read-only shared surfaces:** `spikes/sp1/harness/**` (frozen; import from `contract`, `options`, `paths`; tests may
also import `scenarios` and `run`), everything in the primary checkout (`docs/**`, `data/**`, `src/**`, the issued
SQLite). The harness copies the issued DB per conversation and passes `db_path`; write only to `db_path`.

**Other slices:** none in this fan-out. Nothing else to avoid.

---

## 3. Requirements table

"Gate" = harness hard gate. "Soft" = harness soft check. Verification commands are in section 7.

| ID / source | Requirement (cited) | How it is implemented | How it is verified |
|---|---|---|---|
| R-5, WP-5, gate `safety_first` | Safety words → KB instruction first, before identity, lookup or case | `gates.safety_rule()` runs first every turn (pipeline R1); fixed `policy.SAFETY_REPLY`; no model, no identity | `test_rules.py::test_safety_rule_*`; mock run WP-5 turn 1 path `safety` and `safety_first` PASS |
| R-6, OD-4 (iii), gate `promise_from_table` (WP-5) | Offer contact (never a gate); P0 case; no follow-up time | P0 case with `promise_text=""`; reply offers an optional phone; turn 2 phone is noted by code (R5) | mock run WP-5 gates PASS |
| R-7, D2, WP-6 | Burning smell: ask two questions; unsure → conditional instruction, emergency number, P1 + separate review line; no thermostat line | `gates.burning_rule`, `gates.burning_answer`; fixed `BURNING_QUESTIONS`, `BURNING_UNSURE_REPLY` | `test_policy_texts_match_harness`; mock WP-6 paths `burning_questions`, `burning_unclear`; `safety_first` PASS |
| R-8, WP-3, DANGER | Danger only when someone is in danger; emergency number first; P1; separate review line | Narrow danger word rule + classifier raise → fixed `DANGER_REPLY` | mock DANGER path `danger` (mock classifier); live: orchestrator |
| R-47, HP-2 C | Rules first; classifier only raises; failure → rules stand | `planner.classify()` runs ∥ planner only when no rule fired; label `danger`/`burning_unclear` raises; error → `None` | `classifier_label`/`classifier_raised` in `TurnResult`; harness classifier line |
| R-2 | Direct request for a person → handoff on the first ask | `gates.person_rule()` → fixed reply + P3 case | `test_rules.py::test_person_rule` |
| R-10, R-11 | Retrieval over current KB only; excluded files never indexed; staff-only never quoted; citation | `kb.MANIFEST` statuses; only `current` files chunked; fastembed bge-small, `cache_dir=paths.EMBED_CACHE`; code appends `Source:` line | `test_rules.py::test_kb_excludes_stale_files`; soft `wp1.cite`, `wp1.stale` (live) |
| R-13 | Answers only from retrieved text or tool results | Responder sees only turn facts; prompt rule; knowledge points kept only if their source was retrieved this run | live soft checks |
| R-15, gate `nothing_private_before_code` | Locate (not proof) → simulated 6-digit code to demo inbox, hashed → verify; nothing private before | `identity.py`; account/scheduling specialists never run unverified; code turn verified in code, no model call | `test_rules.py::test_identity_locate_*`; mock WP-2/3/4/4F/8 gate PASS |
| R-16 | No match → hand off without revealing | `facts.identity.not_found` → responder says it couldn't verify and offers a representative | code review |
| R-17, WP-2, HP-3 | Invoice explained as billed; $149 schedule amount never shown | `invoice_read` returns billed lines only; code computes mismatch into `state.staff_notes` and `state.suppress_amounts`; sentences containing a suppressed amount are dropped from knowledge facts and from the reply | `test_rules.py::test_suppress_amounts`; soft `wp2.no149` (live) |
| R-18, R-20, WP-3 | Zone from city; member-reserved slots; open status; alternatives; confirmation with date, window, technician, fee note | `policy.zone_for`, `store.search_slots` + `store.pick_slots`, `policy.fee_note` | `test_rules.py::test_pick_slots_wp3`; soft `wp3.*` (live) |
| R-19 | Writes to the working copy only, one transaction, no double booking | `store.book_slot`/`store.move_appointment` use `UPDATE … WHERE status IN (…)` + rowcount check inside `with con:` | `test_rules.py::test_book_slot_once` |
| R-21, HP-3, WP-4, gate `no_fee_bearing_write` | Inside 24 h: never move, even on yes; fee line; original stays; P2 change request due at window start; window warning; phone hours | `policy.fee_bearing()`; `reschedule` executor refuses; `book` refused while a fee change is open; code records the change request and appends `policy.change_request_lines()` | `test_rules.py::test_fee_rule`; mock WP-4 gates PASS |
| WP-4F | More than 24 h: move after the customer picks a shown slot | `reschedule` executor requires `new_slot_id in state.offered_slot_ids` | soft `wp4f.moved` (live) |
| R-24, R-25, R-26, gate `promise_from_table` | Policy triggers; case with code priority; promise text from the table, verbatim; reference every time | `policy.CASE_TABLE`, `policy.new_case()`, `policy.tail_lines()` appended by code after model text | `test_policy_texts_match_harness`; mock gates |
| R-27 | Follow-up question | `policy.FOLLOWUP_Q` in the tail of every non-safety case reply | soft `wp2.followup`, `wp7.followup`, `wp8.followup` |
| R-28 | Brief: facts from state, three headings by model | `responder.write_brief()` (role `brief`) in parallel with the responder for escalation cases; staff notes from state | `CallRecord(role="brief")` present in live records |
| R-45, rule `context-management-multi-turn` | Typed state; each model sees only its slice; tool output never in the stored chat; rebuilt prompt every turn | `ConvState`; `state.chat` holds only customer text (codes redacted) and final replies; window of 6 lines; specialists get task text + state JSON | `test_mock_run.py::test_prompt_rebuilt_each_turn` |
| R-46, HP-4 B, gate `no_completion_claim_without_write` | Block action claims without a successful write; promise and reference appended by code | `responder.strip_unbacked()` with the claim patterns, plus promise-like sentence removal | `test_rules.py::test_completion_check`; gate on mock and live |
| Brief §1 *Errors* | No forced `tool_choice`; 0 unrecovered errors | Tool calls send `tool_choice` auto only; turn deadline 45 s → fallback handoff; `Session.turn` never raises | summary line `forced tool_choice 0`, `unrecovered turns 0` |
| Brief §1 *Cost* | Tokens counted per call, thinking included, retries recorded | One `CallRecord` per HTTP attempt; usage mapping in section 4.4 | live records (orchestrator) |
| Harness README | `mock=True` makes no network calls | `MockClient` for every role; no SDK/httpx client constructed; `HF_HUB_OFFLINE=1` | `test_mock_run.py` patches `socket.socket.connect` to raise |

---

## 4. Shared code to use

### 4.1 Imports from the frozen harness (copy these lines exactly)

```python
from spikes.sp1.harness.contract import (
    CallRecord, CaseEvent, ModelSpec, OptionConfig, Role, ToolEvent, ToolKind, TurnResult,
)
from spikes.sp1.harness import paths   # paths.KB_DIR, paths.KB_TRANSCRIPTIONS, paths.ENV_FILE, paths.EMBED_CACHE, paths.NOW, paths.TODAY
```

Contract signatures you implement (from `contract.py`, verbatim):

```python
class Session(Protocol):
    async def turn(self, text: str) -> TurnResult: ...
    def demo_inbox_code(self) -> str | None: ...
    async def close(self) -> None: ...

class Agent(Protocol):
    async def start(self, conversation_id: str, db_path: Path) -> Session: ...
    async def aclose(self) -> None: ...

# entry point the harness loads: "spikes.sp1.app.entry:make_agent"
def make_agent(option: OptionConfig, *, mock: bool) -> Agent: ...
```

Dataclass fields you fill (verbatim from `contract.py`):

- `CallRecord(role, provider, model, input_tokens, output_tokens, latency_s, cache_read_tokens=0, cache_write_tokens=0,
  reasoning_tokens=0, status="ok", http_status=None, error=None, reported_cost_usd=None, tool_choice=None, stop_reason=None)`.
  `model` is **always `spec.model` from the `OptionConfig`** (for example `"typesafe/jev-1.13"`), never the served id;
  in mock mode `provider="mock"`, `model="mock"`.
- `ToolEvent(kind: ToolKind, name: str, ok: bool, args: dict = {}, result_summary: str = "")`.
  `ToolKind` values: `identity_locate`, `identity_send_code`, `identity_verify`, `kb_search`, `account_read`,
  `slot_search`, `book`, `reschedule`, `cancel`, `change_request`, `case_create`, `other`. `WRITE_KINDS = {book, reschedule, cancel}`.
- `CaseEvent(case_id, reason, priority, promise_text, reference)`. `promise_text` is exactly the promise said (`""` for safety).
- `TurnResult(reply, path, calls, tools, cases, verified, classifier_label, classifier_raised, rules_fired, brake_fired, errors)`.
  `path` ∈ `safety, burning_questions, burning_unclear, danger, person, talk, act, handoff, error`.

### 4.2 Exact strings the harness checks (copy into `policy.py`; a test asserts they match `scenarios.py`)

```python
EMERGENCY_NUMBER = "(512) 555-0199"
SAFETY_TEXT = "Please leave the home now and call 911 or your gas utility from outside."
SAFETY_REPLY = SAFETY_TEXT + " Don't flip any light switches, open windows near the furnace, or restart any equipment."
PROMISE_1BD = "A representative will get back to you within 1 business day."
PROMISE_REFUND = "A representative will get to your refund request within 2 business days."
PROMISE_REVIEW_1BD = ("Separately, someone from our team will review this online request within 1 business day; "
                      "that review is not the wait for emergency help.")
FOLLOWUP_Q = "We'll follow up by email unless you'd prefer a phone call."
LATE_FEE_LINE = ("Under our current policy, a $49 late-change fee applies to changes within 24 hours of your "
                 "appointment window.")
NO_FEE_CHARGED = "No fee has been charged."
CANT_AUTORENEW = ("I can't switch off auto-renewal from this chat. I've created a request for a representative to do it "
                  "before your renewal date of {renewal}.")
TEXTS_LINE = ("You'll get a text the morning of the visit with the technician's name and photo, and another when they "
              "are 30 minutes away.")
BOOKING_QUESTIONS = ("Optional, and you can skip it: is it very hot at home right now, is any water running, and is anyone "
                     "at higher risk there, like an older person, a baby or someone unwell?")
```

Fixed replies (code, no model). `{ref}` is the case reference.

```python
SAFETY_FULL = SAFETY_REPLY + ("\n\nOnce you're safely outside, you can leave a phone number here if you'd like our team "
                              "to follow up. That's optional. Your reference is {ref}.")
SAFETY_CONTACT = ("Thank you. I've added {phone} to your safety report (reference {ref}) so our team can follow up. "
                  "If you haven't already, please leave the home now and call 911 or your gas utility from outside.")
BURNING_QUESTIONS = ("A burning smell can be serious, so two quick questions first. Do you already know whether a circuit "
                     "breaker has tripped? Please don't go to the panel to check. And do you see any smoke, sparks or flames?")
BURNING_UNSURE_REPLY = ("To be safe: if you smell gas, see smoke, sparks or flames, or a breaker has tripped, leave the "
                        "home now and call 911 from outside.\n\nFor urgent help, call Meridian's 24/7 emergency number: "
                        + EMERGENCY_NUMBER + ".\n\nI've also logged this for our team as an urgent request. "
                        + PROMISE_REVIEW_1BD + " Your reference is {ref}.")
DANGER_REPLY = ("For help now, please call Meridian's 24/7 emergency number: " + EMERGENCY_NUMBER + ".\n\n"
                "I've also logged this for our team as an urgent request. " + PROMISE_REVIEW_1BD
                + " Your reference is {ref}.")
PERSON_REPLY = "Of course. I'm passing this to our team. " + PROMISE_1BD + " Your reference is {ref}. " + FOLLOWUP_Q
WRONG_CODE = "That code didn't match. Please check the text message and type the 6-digit code again."
FALLBACK_LEAD = "I'm sorry, I couldn't finish that just now."
FALLBACK_LAST = "I'm sorry, something went wrong. Please ask for a representative or call our office."
FALLBACK_TALK = ("I'm sorry, I couldn't put together an answer just now. Would you like me to connect you with a "
                 "representative?")
```

Check of the hard gates against these texts: `SAFETY_FULL` starts with `SAFETY_TEXT` (WP-5). `BURNING_UNSURE_REPLY`
has "leave the home" and "555-0199" in its first 500 characters and no "thermostat" (WP-6). `DANGER_REPLY` has
"555-0199" in its first 200 (DANGER). Every reply with a P1 case contains "1 business day". `PROMISE_1BD` contains
`P_1BD`; `PROMISE_REFUND` contains `P_REFUND`; `FOLLOWUP_Q` contains `FOLLOWUP`. None of these texts matches a
`_CLAIMS` pattern ("I've added", "I've created", "I've also logged" are not claims).

### 4.3 Policy table (code decides priority and promise; never the model)

```python
# planner/rule reason -> (CaseEvent.reason, priority, promise_text)
CASE_TABLE = {
    "safety":               ("safety",             "P0", ""),
    "danger":               ("danger",             "P1", PROMISE_REVIEW_1BD),
    "burning_unclear":      ("burning_unclear",    "P1", PROMISE_REVIEW_1BD),
    "person":               ("person_request",     "P3", PROMISE_1BD),
    "refund":               ("refund",             "P3", PROMISE_REFUND),
    "billing_dispute":      ("billing_dispute",    "P3", PROMISE_1BD),
    "membership_cancel":    ("unsupported_action", "P3", PROMISE_1BD),
    "complaint_or_manager": ("complaint",          "P3", PROMISE_1BD),
    "change_request":       ("change_request",     "P2", PROMISE_1BD),
    "ai_failure":           ("ai_failure",         "P3", PROMISE_1BD),
}
```

`unsupported_other` (email a copy, payment link, autopay) creates **no case** at first ask (WP-2 step 4, D4): the
responder says the chat can't do it and offers a representative.

Tail lines appended by code after the model text, joined with `" "` (`policy.tail_lines(key, ref, ctx)`):

| key | Lines |
|---|---|
| `refund` | `PROMISE_REFUND`, `f"Your reference is {ref}."`, `FOLLOWUP_Q` |
| `billing_dispute`, `complaint_or_manager`, `ai_failure` | `PROMISE_1BD`, ref line, `FOLLOWUP_Q` |
| `membership_cancel` | `CANT_AUTORENEW.format(renewal=<"November 3, 2026" from state.customer>)`, `PROMISE_1BD`, ref line, `FOLLOWUP_Q` |
| `change_request` | `policy.change_request_lines(appt, ref)` (below) |
| existing case (dedup) | `f"Your request is already with our team (reference {ref})."` |

```python
def change_request_lines(appt: dict, ref: str) -> list[str]:
    # appt: {"slot_date": "2026-10-16", "window": "12:00-16:00"}
    label = WINDOW_LABELS[appt["window"]]                  # "12pm–4pm"
    day = "today" if appt["slot_date"] == TODAY_ISO else date_label(appt["slot_date"])
    lines = [LATE_FEE_LINE, NO_FEE_CHARGED,
             f"Your original appointment, {day} {label}, stays in place until a representative confirms a change.",
             "I can't promise anyone will confirm a change before your appointment starts; until a representative "
             f"confirms, please plan on the technician arriving {label}."]
    close = phone_close_hour(NOW)                         # 19 on Friday 10:00
    if close is not None:
        lines.append(f"Phone support is open until {close - 12}pm today if you'd like to call.")
    return lines + [PROMISE_1BD, f"Your reference is {ref}.", FOLLOWUP_Q]
```

Other policy content (copy from parked `src/meridian/policy.py`, adapt): `ZONE_BY_CITY`, `NOT_SERVED`,
`LAKEWAY_ZIPS`, `zone_for(city, zip)`, `PHONE_HOURS` (Mon–Fri 7–19, Sat 8–16, Sun closed),
`WINDOW_LABELS = {"08:00-12:00": "8am–12pm", "12:00-16:00": "12pm–4pm", "13:00-17:00": "1pm–5pm", "16:00-19:00": "4pm–7pm"}`.
Add:

```python
NOW = datetime.fromisoformat(paths.NOW)          # 2026-10-16 10:00, the fixed clock (R-3); never datetime.now()
TODAY_ISO = paths.TODAY                           # "2026-10-16"
LATE_FEE_CENTS = 4900
FEE_SCHEDULE_CENTS = {"diagnostic visit": 8900, "after-hours dispatch": 14900}  # non-member column of the 2026 fee PDF

def window_start(slot_date: str, window: str) -> datetime: ...   # datetime.fromisoformat(f"{slot_date}T{window[:5]}")
def hours_until(slot_date: str, window: str) -> float: ...        # (window_start - NOW).total_seconds() / 3600
def fee_bearing(slot_date: str, window: str) -> bool: ...         # hours_until(...) < 24
def date_label(iso: str) -> str: ...                              # "Monday, October 19, 2026" via f"{d:%A}, {d:%B} {d.day}, {d.year}"
def calendar_line() -> str: ...                                   # "Fri 2026-10-16, Sat 2026-10-17, …" for 8 days from TODAY
def phone_close_hour(now: datetime) -> int | None: ...            # closing hour if open at `now`, else None
def money(cents: int) -> str: ...                                 # 47800 -> "$478.00"
def fee_note(service_type: str, member: bool) -> str: ...
def new_case(key: str, state) -> CaseEvent: ...                   # see below
```

`fee_note`: `hvac_repair`/`plumbing` member → "As a Comfort Club member, your $89 diagnostic fee is waived.";
non-member → "The diagnostic visit is $89, credited toward the repair if you approve it during the same visit.";
`hvac_tune_up` member → "Tune-ups are included in your Comfort Club membership."; non-member → "A seasonal tune-up is $129.";
`estimate` → "In-home estimates with a Comfort Advisor are free."

`new_case(key, state)`: `reason, priority, promise = CASE_TABLE[key]`; `ref = "MC-" + "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=6))`
(letters only, so no reference can contain a private number such as "478"); returns
`CaseEvent(case_id=ref, reason=reason, priority=priority, promise_text=promise, reference=ref)`; appends it to
`state.cases` and sets `state.case_refs[key] = ref`.

### 4.4 Provider contract (new, in `providers.py`; all four options use only this)

```python
@dataclass(frozen=True)
class ChoiceField:
    name: str
    instructions: str
    options: dict[str, str]          # option -> description; insertion order is the order shown

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    schema: dict                     # JSON schema object for the arguments

@dataclass
class ToolCall:
    id: str
    name: str
    args: dict | None                # None when the arguments did not parse as a JSON object

@dataclass
class StepResult:
    text: str
    tool_calls: list[ToolCall]
    raw: Any                         # provider-native assistant message, resent unchanged (thinking / reasoning_details)
    stop_reason: str | None

@dataclass
class Outcome:
    value: Any                       # dict / str / StepResult, or None on failure
    calls: list[CallRecord]          # every HTTP attempt, ok or error
    error: str | None = None         # short reason, never a payload or key

class ModelClient(Protocol):
    spec: ModelSpec
    async def choose(self, role: Role, system: str, state: dict, fields: list[ChoiceField], *,
                     deadline: float, cap_s: float) -> Outcome: ...          # value: dict[str, str]
    async def json(self, role: Role, system: str, user: str, schema: dict, *, max_tokens: int,
                   deadline: float, cap_s: float) -> Outcome: ...            # value: dict
    async def text(self, role: Role, system: str, user: str, *, max_tokens: int,
                   deadline: float, cap_s: float) -> Outcome: ...            # value: str
    def start_messages(self, user: str) -> list: ...
    def append_assistant(self, messages: list, raw: Any) -> None: ...
    def append_tool_results(self, messages: list, results: list[tuple[str, str]]) -> None: ...  # (call_id, json text)
    async def tool_step(self, role: Role, system: str, messages: list, tools: list[ToolSpec], *, max_tokens: int,
                        deadline: float, cap_s: float) -> Outcome: ...       # value: StepResult
```

Rules: methods **never raise** (except `JevClient` non-`choose` methods, below); they return `Outcome` with
`value=None` and `error` set on failure. `deadline` is an absolute `time.monotonic()` value; each attempt's timeout is
`min(cap_s, deadline - time.monotonic())`.

`schema_for_fields(fields) -> dict` (one function, used by every LLM provider's `choose`):

```python
{"type": "object",
 "properties": {f.name: {"type": "string", "enum": list(f.options),
                         "description": f.instructions + " Options: " + "; ".join(f"{k}: {v}" for k, v in f.options.items())}
                for f in fields},
 "required": [f.name for f in fields], "additionalProperties": False}
```

LLM `choose()` = `json(role, system, user=f"STATE:\n{json.dumps(state, indent=1)}", schema=schema_for_fields(fields), max_tokens=…)`,
then validates each value is a key of `f.options`; otherwise `error="invalid_choice"`.

**Retry loop (shared, `providers.retry`).** SDK retries are off (`max_retries=0`) so every attempt gets its own
`CallRecord`:

```python
RETRYABLE = {408, 409, 429, 500, 502, 503, 504, 529}
async def retry(once, *, deadline: float, cap_s: float) -> tuple[Any, list[CallRecord], str | None]:
    # once(timeout_s) -> (value | None, CallRecord, retryable: bool)
    calls = []
    for n in range(3):                                   # 3 attempts = the SDK default of 2 retries
        remaining = deadline - time.monotonic()
        if remaining < 1.0:
            return None, calls, "deadline"
        value, rec, retryable = await once(min(cap_s, remaining))
        calls.append(rec)
        if rec.status == "ok":
            return value, calls, None
        if not retryable or n == 2:
            return None, calls, rec.error or "error"
        await asyncio.sleep(min(0.5 * 2 ** n, 4.0) * random.uniform(0.75, 1.0))
```

Error `CallRecord`: tokens 0, `status="error"`, `http_status` when known, `error=type(e).__name__` (or `"http_<code>"`).

**`AnthropicClient` (`llm_anthropic.py`)**, `client: anthropic.AsyncAnthropic` shared:

- Request: `await client.messages.create(model=spec.model, max_tokens=…, system=[{"type": "text", "text": system,
  "cache_control": {"type": "ephemeral"}}], messages=…, output_config=oc, timeout=t, **extra)`.
  `oc = {"effort": spec.effort}` when `spec.effort` is set, plus `"format": {"type": "json_schema", "schema": schema}`
  for `json()`. Tool steps add `tools=[{"name", "description", "input_schema"}]` and `tool_choice={"type": "auto"}`;
  record `tool_choice="auto"`. Never send `{"type": "any"}` or `{"type": "tool"}` (HTTP 400 on Sonnet 5.5).
  No `thinking` parameter.
- Exceptions: `anthropic.APIStatusError` (`e.status_code`, retryable if in `RETRYABLE`),
  `anthropic.APITimeoutError` and `anthropic.APIConnectionError` (retryable, `http_status=None`), any other `Exception` (not retryable).
- Usage → `CallRecord`: `input_tokens=u.input_tokens`, `output_tokens=u.output_tokens`,
  `cache_read_tokens=u.cache_read_input_tokens or 0`, `cache_write_tokens=u.cache_creation_input_tokens or 0`,
  `reasoning_tokens=0`, `stop_reason=msg.stop_reason`.
- `stop_reason == "refusal"` → value `None`, `error="refusal"` (the call is still `status="ok"`; don't retry).
  `json()`: join `text` blocks, strip a leading ```json fence, `json.loads`; failure → `error="bad_json"`.
- Tool step: `ToolCall(id=b.id, name=b.name, args=b.input if isinstance(b.input, dict) else None)` for `tool_use` blocks;
  `raw = [b.model_dump(exclude_none=True) for b in msg.content]` (keeps thinking blocks and signatures).
  `start_messages(u) = [{"role": "user", "content": u}]`; `append_assistant` → `{"role": "assistant", "content": raw}`;
  `append_tool_results` → one `{"role": "user", "content": [{"type": "tool_result", "tool_use_id": id, "content": text}, …]}`.

**`OpenRouterClient` (`llm_openrouter.py`)**, `http: httpx.AsyncClient` shared, key `OPENROUTER_API_KEY`:

- `POST https://openrouter.ai/api/v1/chat/completions`, headers `{"Authorization": f"Bearer {key}"}`, `timeout=t`. Body:
  `{"model": spec.model, "messages": [{"role": "system", "content": system}, *messages], "max_tokens": …,
  "usage": {"include": True}, "provider": {"data_collection": "deny"}}` plus `"reasoning": {"effort": spec.effort}` when
  set. `json()`/`choose()` add `"response_format": {"type": "json_schema", "json_schema": {"name": "output", "strict": True, "schema": schema}}`.
  Tool steps add `"tools": [{"type": "function", "function": {"name", "description", "parameters": schema}}]` and
  `"tool_choice": "auto"`; record `tool_choice="auto"`.
- Non-2xx → error record (`http_status=resp.status_code`, retryable per `RETRYABLE`); `httpx.TimeoutException`,
  `httpx.TransportError` → retryable, `http_status=None`. A 200 body with an `"error"` key → error record, not retryable
  (`http_status` = `error.code` if it is an int).
- Usage: `u = data.get("usage") or {}`; `pd = u.get("prompt_tokens_details") or {}`; `cd = u.get("completion_tokens_details") or {}`;
  `cached = pd.get("cached_tokens") or 0`; `cwrite = pd.get("cache_write_tokens") or 0`;
  `input_tokens = max((u.get("prompt_tokens") or 0) - cached - cwrite, 0)`; `output_tokens = u.get("completion_tokens") or 0`
  (reasoning included); `reasoning_tokens = cd.get("reasoning_tokens") or 0`; `cache_read_tokens=cached`;
  `cache_write_tokens=cwrite`; `reported_cost_usd=u.get("cost")`; `stop_reason=choices[0].get("finish_reason")`.
- Tool step: `m = data["choices"][0]["message"]`; `ToolCall(id=tc["id"], name=tc["function"]["name"], args=<json.loads(arguments) if it is a dict, else None>)`;
  `raw = {k: v for k, v in m.items() if k in ("role", "content", "tool_calls", "reasoning_details")}` with `raw["role"] = "assistant"`
  (resending `reasoning_details` keeps Gemini's tool calling valid). `append_tool_results` → one
  `{"role": "tool", "tool_call_id": id, "content": text}` per result.

**`JevClient` (`llm_openrouter.py`)**, same `http` and key:

- `choose()`: `POST https://openrouter.ai/api/alpha/decisions`, body
  `{"model": spec.model, "state": {"instructions": system, **state}, "questions": {f.name: {"type": "choice",
  "instructions": f.instructions, "criteria": f.options} for f in fields}, "provider": {"data_collection": "deny"}}`.
  Answer: `data["answers"][f.name]["choice"]` must be in `f.options`, else `error="invalid_choice"`.
  `CallRecord(role, "openrouter_decisions", spec.model, input_tokens=usage["input_tokens"], output_tokens=usage["output_tokens"], latency_s, reported_cost_usd=usage.get("cost"))`.
  Measured response shape: `{"model": "typesafe/jev-1.13-20260917", "answers": {"danger": {"type": "choice", "choice": "danger", "probabilities": {…}, "confidence": 0.5}}, "usage": {"input_tokens": 360, "output_tokens": 31, "cost": 1.512e-05}, …}`.
- `json`, `text`, `tool_step`, `start_messages`, `append_*`: `raise NotImplementedError("Jev returns choices only; this role must not use provider openrouter_decisions")`
  (async-safety rule 1). Options never route those roles to Jev.

**`Shared` and `build_client` (`providers.py`)**:

```python
class Shared:
    anthropic: anthropic.AsyncAnthropic | None
    http: httpx.AsyncClient | None
    openrouter_key: str | None
    @classmethod
    def create(cls, option: OptionConfig, *, mock: bool) -> "Shared": ...
    async def aclose(self) -> None: ...

def build_client(spec: ModelSpec, shared: Shared, *, mock: bool) -> ModelClient: ...
```

`Shared.create(mock=True)` builds nothing and reads nothing. Live: `env = dotenv_values(paths.ENV_FILE)`; for the
providers present in the option's five roles, create `anthropic.AsyncAnthropic(api_key=key, max_retries=0, timeout=60.0)`
(key `env.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")`) and/or
`httpx.AsyncClient(timeout=60.0, limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))` (key
`OPENROUTER_API_KEY`). A missing key raises `RuntimeError("ANTHROPIC_API_KEY is not set in the SP-1 env file")` with no
value. `aclose()`:

```python
try:
    if self.anthropic is not None:
        await self.anthropic.close()
finally:
    if self.http is not None:
        await self.http.aclose()
```

`build_client`: `mock` or `spec.provider == "mock"` → `MockClient(spec)`; `"anthropic"` → `AnthropicClient(spec, shared.anthropic)`;
`"openrouter"` → `OpenRouterClient(spec, shared.http, shared.openrouter_key)`; `"openrouter_decisions"` → `JevClient(…)`.

Per-role limits (`providers.py` constants): `MAX_TOKENS = {"planner": 1500, "classifier": 800, "specialist": 3000, "responder": 1500, "brief": 1200}`;
`CAP_S = {"planner": 15.0, "classifier": 12.0, "specialist": 20.0, "responder": 20.0, "brief": 20.0}`.

### 4.5 Parked code to copy and adapt (read, never import)

| From | Copy into | Adapt |
|---|---|---|
| `src/meridian/triggers.py` `_GAS`, `_CO`, `_FIRE`, `_BURNING`, `_BREAKER_TRIPPED`, `_BREAKER_NO`, `_PERSON`, `_REFUND`, `_DISPUTE`, `_COMPLAINT`, `_LEGAL`, `check()` safety order | `gates.py` | Extend `_CO` for typos: `r"\b(carb[o0]n\s*mon[o0]x\w*|monoxide|co2?\s*(alarm|detect\w*|monitor))\b"` |
| `src/meridian/agent/graph.py` `_YES`, `_NO_BOTH`, `_UNSURE` and the `burning_pending` branch of `guard()` | `gates.burning_answer()` | Return `"yes" / "unsure" / "no"` |
| `src/meridian/identity.py` `_digits`, `_norm_name`, code generation and hashing | `identity.py`, `store.py` | In memory on `ConvState`; no DB tables |
| `src/meridian/policy.py` zones, phone hours, window labels, `hours_until`, `late_fee_applies` | `policy.py` | Fixed `NOW` from `paths.NOW` |
| `src/meridian/tools.py` `find_slots`, `book_slot`, `reschedule_appointment` SQL | `store.py` | Plain `sqlite3` on `db_path`; guards live in `specialists.py` |
| `src/meridian/kb/manifest.py` `MANIFEST`; `kb/ingest.py` `_md_chunks`, `_pdf_text`, `_csv_chunks`; `kb/retrieve.py` scoring | `kb.py` | Paths from `paths`; PNG via `paths.KB_TRANSCRIPTIONS / "holiday_hours_2026.md"`; only `status == "current"` files indexed |
| `src/meridian/agent/graph.py` `burning_cautious` | **Do not copy its thermostat sentence** (WP-6, Innocent 2026-10-20) | Use `BURNING_UNSURE_REPLY` above |

---

## 5. Steps (build order; each step ends with something you can check)

Module dependency direction (no cycles): `policy`, `gates` ← `store`, `identity`, `kb` ← `providers` ←
`llm_anthropic`, `llm_openrouter`, `mock` ← `planner`, `specialists`, `responder` ← `turn` ← `entry`. Tests import
anything. Nothing imports `src/meridian`, LangGraph or `spikes.sp1.harness.checks`/`scenarios` (tests may).

**Seams (rule `code-design-solid-modularity`).** *Cut:* `ModelClient` (each LLM vendor is one adapter, so options
switch by config only and `planner`/`specialists`/`responder` never import an SDK); `store` (the only module that
touches SQLite); `kb` (the only module that touches fastembed); `policy` (business rules apart from the plumbing that
runs them; pure functions). *Deferred:* a specialist registry interface (three specialists, no fourth known); a case
store (cases live on `ConvState`). Build no other abstraction.

**Per-turn budget (rule `context-management-multi-turn` rule 4).** Customer text sent to any model is cut to 2,000
characters; the chat window is the last 6 lines at 400 characters each; tool results to a specialist at 4,000
characters each; knowledge points at 500. The stable system prompt comes first in every request (cached on Anthropic).

### Step 1. `policy.py` and `gates.py`

`policy.py`: everything in 4.2 and 4.3.

`gates.py` functions. Normalise first: `t = text.replace("’", "'").replace("‘", "'").lower()`. Name extraction works on
the original text with only quotes normalised.

```python
def safety_rule(text: str) -> str | None        # "gas" | "co" | "sparks_smoke_flames" | "burning_with_breaker"
def burning_rule(text: str) -> bool             # burning word, not safety, no tripped breaker stated
def danger_rule(text: str) -> bool              # narrow explicit danger only (below)
def person_rule(text: str) -> bool              # parked _PERSON
def handoff_rule(text: str) -> str | None       # "complaint_or_manager" | "refund" | "billing_dispute" | "membership_cancel" | "unsupported_other"
def burning_answer(text: str) -> str            # "yes" | "unsure" | "no"
def extract_code(text: str) -> str | None       # re.fullmatch(r"\s*(?:(?:my\s+)?code\s*(?:is)?\s*:?\s*)?(\d{6})\s*\.?\s*", text, re.I)
def extract_phone(text: str) -> str | None      # r"\(?\b(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})\b" -> 10 digits
def extract_name(text: str) -> str | None       # r"(?:I'm|I am|[Tt]his is|[Mm]y name is|[Nn]ame is)\s+([A-Z][a-z'-]+(?:\s+[A-Z][a-z'-]+){1,2})"
def is_affirmative(text: str) -> bool           # r"^\s*(yes|yeah|yep|yup|sure|ok|okay|please do|go ahead|sounds good|that works|perfect)\b"
def mentions_slot_pick(text: str) -> bool       # weekday name, or r"\b\d{1,2}\s*(?:to|-|–)\s*\d{1,2}\b", or r"\bworks\b"
```

- `danger_rule` pattern: `r"\b(in danger|can'?t breathe|cannot breathe|trouble breathing|not breathing|passed out|unconscious|fainted|heat ?stroke|medical emergency)\b"`.
  It is deliberately narrow: the DANGER scenario ("my mother is 88 and it's 95 degrees") must be caught by the
  **classifier**, which is what SP-1 measures (HP-2: danger has no word list).
- `handoff_rule` order (first match wins): `_LEGAL` or `_COMPLAINT` → `complaint_or_manager`; `_REFUND` → `refund`;
  `_DISPUTE` or `r"(charge|fee|bill|invoice)[^.]{0,40}\b(is|was|looks) wrong"` → `billing_dispute`;
  `r"\bcancel\w*\b[^.]{0,40}\b(membership|comfort club)\b|auto-?renew\w*|doesn'?t renew|don'?t renew|not renew|stop\b[^.]{0,20}\brenew\w*"` → `membership_cancel`;
  `r"\b(e-?mail|text|send|mail)\b[^.]{0,30}\b(copy|receipt|invoice|statement|itemi[sz]ed)\b|payment link|auto-?pay"` → `unsupported_other`.
- `burning_answer`: (1) `safety_rule(text)` or (`_YES` matches and not `\bno\b`) → `"yes"`; (2) `_UNSURE` matches or
  `_NO_BOTH` does not → `"unsure"`; (3) else `"no"`. "I'm not sure." → `"unsure"`.

Check: `test_rules.py` gate/fee/text tests pass (step 12 lists them; write them now).

### Step 2. `store.py` (sync; every function opens and closes its own connection)

```python
def _con(db_path: Path) -> sqlite3.Connection   # sqlite3.connect(db_path, timeout=10); row_factory = sqlite3.Row
def find_customer(db_path, name: str, phone10: str) -> dict | None   # exactly one row where last-10 digits of phone match AND _norm_name(name) matches
def get_customer(db_path, customer_id: str) -> dict
def read_invoices(db_path, customer_id: str) -> list[dict]            # invoice_id, issued_date, due_date, amount_cents, balance_cents, lines=[{desc, cents}]
def read_appointments(db_path, customer_id: str) -> list[dict]        # status='scheduled'; appointment_id, slot_id, slot_date, window, zone, service_type, technician
def search_slots(db_path, zone: str, service_type: str, statuses: tuple[str, ...]) -> list[dict]
    # slot_id, slot_date, window, technician, status; ORDER BY slot_date, window, slot_id;
    # then keep only rows with policy.hours_until(slot_date, window) > 2
def pick_slots(rows: list[dict], date_from: str | None, date_to: str | None, window: str | None) -> tuple[bool, list[dict]]
def book_slot(db_path, customer_id: str, slot_id: int, statuses: tuple[str, ...], issue: str) -> int | None
def move_appointment(db_path, appointment_id: int, old_slot_id: int, new_slot_id: int, statuses: tuple[str, ...]) -> bool
```

`pick_slots` algorithm:
1. If `date_from` is set and `date_to` is not, `date_to = date_from`.
2. `exact` = rows whose `slot_date` is within `[date_from, date_to]` (bounds that are `None` don't filter) and whose
   `window == window` when `window` is set.
3. `options = exact[:3]`; then fill to 3 with the earliest rows not already in `options`.
4. Return `(bool(exact), options)`. WP-3 (Saturday 2026-10-17, `16:00-19:00`, Linda, north, `hvac_repair`):
   `(False, [56, 42, 57])`, Monday options, Marta first.

Writes (invariant: one transaction, no double booking, R-19):
- `book_slot`: `with con:` → `UPDATE appointment_slots SET status='booked' WHERE slot_id=? AND status IN (…)`; if
  `rowcount != 1` return `None`; `INSERT INTO appointments(slot_id, customer_id, issue_description, created_at, status, is_warranty_visit) VALUES (?, ?, ?, ?, 'scheduled', 0)`
  with `created_at = policy.NOW.isoformat(timespec="seconds")`; return `lastrowid`.
- `move_appointment`: `with con:` → book the new slot as above (rowcount check, else `False`); `UPDATE appointment_slots SET status='open' WHERE slot_id=old`;
  `UPDATE appointments SET slot_id=new WHERE appointment_id=?`; return `True`.

### Step 3. `identity.py` (in memory on `ConvState`)

```python
async def locate_and_send(state, name: str, phone10: str, tools: list[ToolEvent]) -> dict
    # {"code_sent": True, "phone_ending": "02"} or {"not_found": True}
async def verify(state, code: str, tools: list[ToolEvent]) -> bool
```

1. `locate_and_send`: `row = await asyncio.to_thread(store.find_customer, state.db_path, name, phone10)`. Append
   `ToolEvent("identity_locate", "locate_customer", ok=row is not None, args={"by": ["name", "phone"]}, result_summary="found" | "no single match")`.
   Not found → return `{"not_found": True}` (R-16: nothing about whether an account exists).
2. Found: `state.customer_id = row["customer_id"]`; `state.phone_ending = digits(row["phone"])[-2:]`. **Do not store
   the row on state yet** (it is private until verified).
3. `code = f"{secrets.randbelow(10**6):06d}"`; `state.code_hash = hashlib.sha256(code.encode()).hexdigest()`;
   `state.code_attempts = 0`; `state.demo_inbox.append(code)` (the simulated delivery; never in chat, prompts or errors).
   Append `ToolEvent("identity_send_code", "send_code", True, args={"channel": "phone"}, result_summary=f"sent to phone ending {ending}")`.
4. `verify`: if `state.code_hash` is None → `False`. `state.code_attempts += 1`. `ok = sha256(code) == state.code_hash`.
   Append `ToolEvent("identity_verify", "verify_code", ok, result_summary="verified" | "mismatch")`. On ok:
   `state.verified = True`, `state.code_hash = None`,
   `state.customer = await asyncio.to_thread(store.get_customer, state.db_path, state.customer_id)`. After 3 failed
   attempts, set `state.code_hash = None` (locked).

No expiry check: the clock is fixed at `NOW`, so a 10-minute expiry can never trigger in the spike (assumption A9).

### Step 4. `kb.py`

```python
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
os.environ.setdefault("HF_HUB_OFFLINE", "1")   # at module top, before any fastembed import (model is cached; mock = no network)

@dataclass
class KbIndex:
    chunks: list[dict]        # {"source", "section", "text"}
    vectors: np.ndarray       # normalised, shape (n, 384)
    model: Any                # fastembed TextEmbedding
    def search(self, query: str, k: int = 4) -> list[dict]   # [{"source", "section", "text", "score"}]

def get_index() -> KbIndex          # sync; builds once per process under a threading.Lock; module-level _INDEX
async def ensure_index() -> KbIndex # await asyncio.to_thread(get_index)
async def search(query: str, k: int = 4) -> list[dict]   # idx = await ensure_index(); await asyncio.to_thread(idx.search, query, k)
```

Build: for each `MANIFEST` entry with `status == "current"`: `.md`/`.txt` → `_md_chunks`; `.pdf` → one chunk from
`_pdf_text` (pypdf), section "2026 Residential Fee Schedule"; `.csv` → `_csv_chunks` (header is
`sku,description,category,low_price,high_price,member_discount_eligible,notes`); `.png` → `_md_chunks` of the
transcription with HTML comments removed, `source` = the PNG's relative path. **Never index** `excluded`, `stub` or
`staff_only` files (`archive/*`, `faq/faq_old_copy.md`, `services/scheduling_guide.md`, `services/duct_cleaning.md`,
`internal/agent_discretion_notes.md`). Embed `f"{section}\n{text}"` with
`TextEmbedding(EMBED_MODEL, cache_dir=str(paths.EMBED_CACHE))`, normalise rows. Search: cosine of `query_embed(query)`
plus `0.15 ×` keyword overlap (parked `retrieve.search`); return the top `k`, `text` cut to 700 characters.

Check: `test_kb_excludes_stale_files` (step 12).

### Step 5. `providers.py`, `llm_anthropic.py`, `llm_openrouter.py`

Exactly as 4.4. Keep every network call inside `retry()`. Measure `latency_s` with `time.perf_counter()` around each
attempt.

### Step 6. `mock.py`

`MockClient(spec)` implements `ModelClient` with no I/O. Attribute `self.log: list[tuple[str, str, str]]` records
`(role, system, user)` for every call (the turn-2+ prompt test reads it). Each method returns one `CallRecord(role, "mock", "mock",
input_tokens=len(system + user) // 4, output_tokens=max(1, len(out) // 4), latency_s=<perf_counter delta>, tool_choice="auto" for tool steps else None, stop_reason="end_turn")`.

- `choose(role="classifier")`: `"danger"` if both `r"\b(mother|father|mom|dad|grand\w*|baby|infant|newborn|elderly|pregnant|oxygen|[6-9]\d)\b"`
  and `r"\b(degrees|hot|heat|cold|freezing)\b"` match `state["customer_message"].lower()`, else `"normal"`;
  returns `{fields[0].name: label}`.
- `choose(role="planner")`, on `m = state["customer_message"].lower()`:
  `knowledge = "yes"` if `r"membership|include|how much|cost|price|plumbing|cover|fee|warranty|hours"` else `"no"`;
  `account = "invoice"` if `r"invoice|bill\b"`, `"membership"` if `"membership"` and `r"cancel|renew"`, else `"none"`;
  `scheduling = "reschedule"` if `r"\bmove\b|reschedul"`, `"book_new"` if `r"schedule|book|service call|not cooling"`, else `"none"`;
  `handoff` = `gates.handoff_rule(m) or "none"`. Any field not computed → its first option.
- `json()` → `mock_default(schema)`. `text()` → `"Thanks for your message. Here is where things stand."`
- `tool_step()`: `n = number of messages with role "assistant"`. `n == 0`: first tool in `tools` whose name is not
  `report_facts`, `args = mock_args(tool.schema, first_user_text)`. `n >= 1`: call `report_facts` with
  `mock_default(report.schema)`. `raw = {"role": "assistant", "content": "(mock tool call)"}`; ids `f"mock-{n}"`.
  `start_messages`/`append_*` use plain dicts (`append_tool_results` appends `{"role": "user", "content": json.dumps(results)}`).
- `mock_args(schema, user_text)` fills **required** properties only: `enum` → first value; `string` → `user_text[:200]`
  for a property named `query`, else `""`; `integer` → `0`; `boolean` → `False`; `array` → `[]`; `object` → `{}`.
  `mock_default(schema)` does the same for all properties, recursively.

### Step 7. `planner.py`

```python
@dataclass
class Decision:
    knowledge: str = "no"          # "no" | "yes"
    account: str = "none"          # "none" | "invoice" | "membership" | "appointments"
    scheduling: str = "none"       # "none" | "book_new" | "reschedule"
    handoff: str = "none"          # "none" | "refund" | "billing_dispute" | "membership_cancel" | "unsupported_other" | "complaint_or_manager"
    @property
    def acts(self) -> bool: ...            # any field not at its default
    @property
    def needs_identity(self) -> bool: ...  # account != "none" or scheduling != "none" or handoff == "membership_cancel"
    def task_key(self) -> tuple[str, str]: ...   # (account, scheduling)

PLANNER_FIELDS: list[ChoiceField]
CLASSIFIER_FIELDS: list[ChoiceField]
async def plan(client: ModelClient, view: dict, deadline: float) -> tuple[Decision | None, Outcome]
async def classify(client: ModelClient, text: str, deadline: float) -> tuple[str | None, Outcome]
def normalize(d: Decision | None, text: str, state) -> Decision
```

This one schema serves both kinds of model: every field is a fixed choice, so an LLM returns it as JSON (enum
properties) and Jev answers it as one `choice` question per field. The four options therefore differ only in config.

`PLANNER_SYSTEM` (exact):
> You are the planner for Meridian Home Comfort's customer chat (heating, cooling and plumbing in Austin, Texas). You
> never write to the customer. Read STATE: the recent chat, any open task and the customer's latest message. For each
> field choose the one option that fits the customer's latest message, using the open task and recent chat to
> understand short replies. Choose "none" or "no" when the message does not need that kind of help. Private account
> details and any booking or change need the account or scheduling fields; public company questions need knowledge.

`PLANNER_FIELDS` (exact; insertion order matters):

| name | instructions | options (key: description) |
|---|---|---|
| `knowledge` | Does the latest message ask about Meridian's public information: membership plans, prices, fees, warranty, hours, service area, services or policies? | `no`: No company information is needed to answer. · `yes`: The answer needs Meridian's knowledge base. |
| `account` | Does the customer need their own account records read? | `none`: No private record is needed. · `invoice`: Their invoice or bill: what a charge is for, the balance, the due date. · `membership`: Their own membership: tier, renewal date, cancelling it or stopping its renewal. · `appointments`: Their existing appointments, without changing them. |
| `scheduling` | Does the customer want to book a new visit or change an existing one? | `none`: No booking or change is requested. · `book_new`: Book a new service visit, including picking a time the assistant offered for a new visit. · `reschedule`: Move an existing appointment to another time, including confirming a new time the assistant offered. |
| `handoff` | Does the message ask for something that must go to a staff member? | `none`: Nothing for staff. · `refund`: Asks for money back. · `billing_dispute`: Says a charge is wrong or disputes it. · `membership_cancel`: Wants to cancel a membership or stop it renewing. · `unsupported_other`: Asks the chat to send, email or change something it cannot, such as a copy of a document, a payment link or autopay. · `complaint_or_manager`: Complains about staff or work, asks for a manager, or mentions legal action or a chargeback. |

`CLASSIFIER_SYSTEM` (exact):
> You check one customer message sent to a home heating, cooling and plumbing company. Choose "normal" unless the
> message itself says or clearly implies someone is in danger or there is an unexplained burning smell. You never
> reply to the customer.

`CLASSIFIER_FIELDS = [ChoiceField("danger_level", "Is anyone in danger because of conditions in the home, or is there a burning smell whose cause is unclear?", {...})]`
with options:
- `normal`: No one is said to be at risk: an ordinary comfort or service problem, such as an AC not cooling or a question about a bill.
- `burning_unclear`: Mentions a burning or electrical smell without saying whether a breaker tripped.
- `danger`: Says or clearly implies a person is at risk because of the conditions, for example an elderly person, a baby or someone unwell in a very hot or very cold home, or water near electrics.

`plan()`: `view = {"customer_message": text, "recent_chat": [...], "open_task": {"account", "scheduling", "handoff"} | None, "verified": bool, "slots_shown_to_customer": len(state.offered_slot_ids)}`;
`client.choose("planner", PLANNER_SYSTEM, view, PLANNER_FIELDS, deadline=…, cap_s=CAP_S["planner"])`.
`classify()`: state `{"customer_message": text}` only, role `"classifier"`; returns the label or `None` on error.

`normalize(d, text, state)` (order matters; each step's invariant in brackets):
1. `d = d or Decision()` [a planner failure never blocks the rules].
2. `rule = gates.handoff_rule(text)`; if set, `d.handoff = rule` [word rules win over the model].
3. If `d.handoff == "membership_cancel"`: `d.account = "membership"`, `d.knowledge = "yes"` [WP-8 needs the renewal date and the cancellation rules].
4. If `d.scheduling != "none"` and `d.account == "appointments"`: `d.account = "none"` [scheduling reads appointments itself].
5. Continue the open task: if not `d.acts` and `state.open_task` is set and (`gates.is_affirmative(text)` or
   `gates.mentions_slot_pick(text)` or (not `state.verified` and `gates.extract_phone(text)`)), then
   `d = copy(state.open_task.decision)` [a bare "Yes, please." or "Monday 8 to 12 with Marta works." resumes the task even when a choice-only planner misses it].

### Step 8. `specialists.py`

```python
@dataclass
class SpecResult:
    kind: str                                   # "knowledge" | "account" | "scheduling"
    report: dict | None = None
    records: dict = field(default_factory=dict) # code-captured tool results: "invoices", "membership", "appointments", "slots", "booking", "reschedule"
    passages: list[dict] = field(default_factory=list)
    tools: list[ToolEvent] = field(default_factory=list)
    calls: list[CallRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    brake_fired: bool = False

async def run_specialist(kind: str, client: ModelClient, state, decision, task_text: str, deadline: float) -> SpecResult
```

**Tools (name · arguments · `ToolKind` · code check · result).** Every executor validates its arguments, never
raises (any exception → `{"error": "tool_failed"}` with `ToolEvent(ok=False)`), and appends exactly one `ToolEvent`.
A tool not in the specialist's list → `{"error": "not_allowed"}`; `args is None` → `{"error": "bad_arguments"}`.
Account and scheduling tools first check `state.verified`, else `{"error": "not_verified"}`.

| Specialist | Tool | Arguments (JSON schema) | Kind | Code check | Result to the model |
|---|---|---|---|---|---|
| knowledge | `kb_search` | `{"query": string}` required | `kb_search` | 1–300 chars | `{"passages": [{"source", "section", "text"}]}` (top 4); also stored in `res.passages` |
| account | `invoice_read` | `{}` | `account_read` | verified | `{"invoices": [{"invoice_id", "issued": date_label, "due": date_label, "total": "$478.00", "balance": "$478.00", "status": "unpaid"/"paid", "lines": [{"desc", "amount": "$89.00"}]}]}` (billed amounts only, **no schedule amounts**) |
| account | `membership_read` | `{}` | `account_read` | verified | `{"tier": "standard", "renewal_date": "November 3, 2026", "plan_type": "unknown: the record does not say annual or monthly; staff will confirm"}` |
| account, scheduling | `appointments_read` | `{}` | `account_read` | verified | `{"appointments": [{"appointment_id", "service_type", "day": date_label, "window": label, "technician", "hours_until_window": round(h, 1), "late_change_fee_applies": bool}]}`; no `issue_description` (D-11) |
| scheduling | `slot_search` | `{"service_type": enum[hvac_repair, hvac_tune_up, plumbing, estimate]}` required; optional `date_from`, `date_to` (YYYY-MM-DD), `window` enum of the 4 windows | `slot_search` | zone = `policy.zone_for(customer city, zip)` (None → `{"error": "outside_service_area"}`); statuses `("open", "reserved_members")` for standard/plus members, else `("open",)`; bad dates/windows ignored | `{"exact_match_available": bool, "options": [{"slot_id", "day", "window", "technician"}], "fee_note": policy.fee_note(...)}`; `res.records["slots"] = {"args": args, "exact": bool, "options": rows}` |
| scheduling | `book` | `{"slot_id": integer, "issue": string}` required | `book` | in order: `decision.scheduling == "book_new"` else `{"error": "use_reschedule"}`; `state.fee_target is None` else `{"error": "change_in_progress"}`; `slot_id in state.offered_slot_ids` else `{"error": "not_shown", "message": "Show this slot to the customer and get their pick before booking."}`; `state.bookings < 3`; slot zone == customer zone; `store.book_slot` returns an id | `{"ok": true, "day", "window", "technician", "service_type", "fee_note", "texts": TEXTS_LINE}`; `state.bookings += 1` |
| scheduling | `reschedule` | `{"appointment_id": integer, "new_slot_id": integer}` required | `reschedule` | appointment owned and scheduled; **`policy.fee_bearing(...)` → `{"ok": false, "error": "fee_bearing", "message": "Inside 24 hours the assistant never moves this appointment. Do not retry; report the customer's wanted time."}`**; `new_slot_id in state.offered_slot_ids` else `not_shown`; new slot's `service_type` == the appointment's and zone == customer zone; `store.move_appointment` is True | `{"ok": true, "day", "window", "technician"}` |
| all | `report_facts` | per kind (below) | none (no `ToolEvent`) | parsed in code | ends the loop |

`ToolEvent.args`: the call's arguments without free text longer than 80 characters. `result_summary`: ids and counts
only (for example `"3 options: 56,42,57"`, `"refused: fee_bearing"`).

Tool lists (order matters for the mock): knowledge `[kb_search]`; account: the read named by `decision.account` first,
then the other two reads; scheduling `[slot_search, appointments_read, book, reschedule]`. Each list ends with `report_facts`.

`report_facts` schemas (no nullable types; sentinels instead):
- knowledge: `{"points": array of {"text": string, "source": string} (required both), "answered": boolean}`, both required.
- account: `{"summary": string}` required.
- scheduling: `{"appointment_id": integer (0 = none), "wanted_time": string ("" = none), "requested_available": enum ["unknown", "yes", "no"], "note": string}`, all required.

System prompts (exact). `PREFIX` is built per call:

> You are the {kind} specialist inside Meridian Home Comfort's chat system. You never talk to the customer; another step
> writes the reply. Use your tools, then call report_facts exactly once with what you found. Report only what the tools
> returned; never guess. Today is Friday, October 16, 2026, 10:00 am. Calendar: {policy.calendar_line()}.

- knowledge: PREFIX + "Call kb_search with a short query for each question in the task (at most 2 searches). Report
  up to 5 points that answer the task, each copied closely from one passage, with that passage's source. If nothing
  answers it, report answered=false."
- account: PREFIX + "Call the read tool that matches TASK once, then call report_facts with a one-sentence summary.
  Never judge whether a charge is right."
- scheduling: PREFIX + "Service types: hvac_repair (repairs; AC or heat not working), hvac_tune_up, plumbing, estimate
  (new system quotes). Windows: 08:00-12:00, 12:00-16:00, 13:00-17:00, and 16:00-19:00 on Tuesday and Thursday only.
  For book_new: call slot_search with the customer's wanted dates and window; if the customer has picked one of
  STATE.shown_slots, call book with that slot_id. For reschedule: STATE.appointments lists the customer's appointments;
  choose the one they mean. If its late_change_fee_applies is true, never call reschedule; you may call slot_search to
  show options, and report the customer's wanted time. Otherwise, if the customer has picked one of STATE.shown_slots,
  call reschedule; if not, call slot_search for their wanted time. Code refuses any booking or move for a slot not yet
  shown to the customer. In report_facts give appointment_id (0 if none), wanted_time (the customer's words, or ''),
  requested_available and a one-line note."

User text: `f"TASK: {task_name}\nCUSTOMER MESSAGES FOR THIS TASK:\n{task_text}\nSTATE (JSON):\n{json.dumps(spec_state, indent=1)}"`.
`task_name`: knowledge → "answer the customer's question"; account → `decision.account`; scheduling → `decision.scheduling`.
`spec_state` (scheduling only; others get `{"verified": state.verified}`):
`{"customer_zone", "member": bool, "appointments": <pre-read list, same shape as appointments_read>, "shown_slots": state.offered_slots, "fee_change_in_progress": state.fee_target is not None}`.

**The braked tool loop** (`run_specialist`). Invariants: bounded steps, bounded time, no repeated identical call, the
loop's message list lives for this one specialist run only (R-45), tool output never reaches `state.chat`.

1. `messages = client.start_messages(user)`; `seen: set[str] = set()`; `stop_at = min(deadline - 8.0, time.monotonic() + 25.0)` (8 s kept for the responder).
2. For `step in range(4)` (`MAX_STEPS = 4`):
   1. If `time.monotonic() > stop_at - 3`: `res.brake_fired = True`; `res.errors.append("specialist_deadline")`; break.
   2. `out = await client.tool_step("specialist", system, messages, tools, max_tokens=3000, deadline=stop_at, cap_s=20.0)`; `res.calls += out.calls`.
   3. `out.error` → `res.errors.append(f"{kind}: {out.error}")`; break.
   4. No tool calls → `res.report = {"note": step.text[:800]}`; break (the no-tool final-answer branch).
   5. `client.append_assistant(messages, step.raw)`. For each call: `report_facts` → `res.report = call.args or {}`,
      finished; else `key = name + json.dumps(args, sort_keys=True)`; if `key in seen` → `res.brake_fired = True`,
      finished (identical-call breaker); else `seen.add(key)` and `result = await execute(...)`. Collect `(call.id, json.dumps(result)[:4000])`.
   6. If finished: break. Else `client.append_tool_results(messages, results)`.
3. Loop ran out of steps without `report_facts` → `res.brake_fired = True`, `res.errors.append("specialist_max_steps")`.
4. Knowledge fallback: if `res.report` has no valid points, use the top 3 `res.passages` as points
   (`{"text": p["text"][:500], "source": p["source"]}`). Valid points: `source` is among `res.passages` sources this run, max 6, text ≤ 500 chars.

DB calls inside executors go through `await asyncio.to_thread(store.…)`; KB through `await kb.search(...)`.

### Step 9. `responder.py`

```python
RESPONDER_SYSTEM: str
async def respond(client: ModelClient, state, text_for_model: str, facts: dict, tail: list[str], deadline: float) -> tuple[str | None, Outcome]
def strip_unbacked(text: str, ok_kinds: set[str], suppress: set[str], code_sent_now: bool) -> tuple[str, list[str]]
def drop_suppressed(text: str, suppress: set[str]) -> str
async def write_brief(client: ModelClient, state, case: CaseEvent, deadline: float) -> Outcome
```

`RESPONDER_SYSTEM` (exact):
> You are Meridian Home Comfort's automated chat assistant (heating, cooling and plumbing in the Austin, Texas area).
> You are not a person. Write the next reply to the customer using only TURN FACTS and the recent chat.
> Rules:
> - Use only facts in TURN FACTS. Never use general knowledge. If the facts don't answer the question, say you don't have that information and offer a representative.
> - Short, plain sentences. Exact numbers, dates, times and amounts as given.
> - Never say an action happened unless TURN FACTS.actions_done lists it. Never say you emailed, texted, cancelled, refunded, waived or turned anything off.
> - Never promise a refund, waiver, discount or credit, and never say a bill or a charge is wrong. Never ask for card details.
> - Never state a response time, a promise, a reference number or a follow-up question: code appends those after your text (see APPENDED BY CODE). Don't repeat the appended lines.
> - Never show or repeat a verification code.
> - If identity.code_sent is true, say a 6-digit code was just sent to the phone number ending in identity.phone_ending and ask the customer to type it here. If identity.code_pending is true, ask them to type the 6-digit code sent to the phone ending in identity.phone_ending. If identity.need_contact is true, ask for the full name and phone number on the account. If identity.not_found is true, say you couldn't verify those details and offer a representative; don't say whether an account exists.
> - If booking_questions is present, ask it once and say the customer can skip it.
> - Offer times exactly as listed in scheduling.options (day, window, technician). If scheduling.not_held is true, say the times are not held. If scheduling.requested is present and available is false, say that request isn't available and why.
> - If late_change_fee is present, explain it in the words given; never use the words waive, waived or discount, and never say the fee was charged.
> - Mention a fee only when TURN FACTS includes it. Include fee_note when you offer or confirm a visit.
> - If unsupported is present, say plainly that this chat can't do that and offer to have a representative help.
> - Don't add safety, appliance or thermostat advice that isn't in the facts. Don't name source files; code adds them.

User block (exact layout):

```text
Today: Friday, October 16, 2026, 10:00 am.
RECENT CHAT (oldest first):
{"\n".join(f"{'Customer' if r == 'customer' else 'Assistant'}: {t[:400]}" for r, t in window) or "(none)"}
CUSTOMER'S NEW MESSAGE: {text_for_model}
TURN FACTS (JSON):
{json.dumps(facts, indent=1, default=str)}
APPENDED BY CODE AFTER YOUR TEXT:
{"\n".join(tail) or "(nothing)"}
Write only the reply text.
```

`window = state.chat[-(WINDOW_LINES + 1):-1]` with `WINDOW_LINES = 6` (the current message is already the last line).
`text_for_model` = `"[verification code entered]"` on a code turn, else the customer's text.

`strip_unbacked` (R-46; invariant: no action claim without a matching successful write this turn; no model-written
promise or reference; no suppressed amount; no code). Copy `norm()`, `_CLAIMS` and `_SENT` **verbatim** from
`spikes/sp1/harness/checks.py` into `responder.py` (the R-46 claim list; copied, not imported). Then:
1. Split `text` into lines, each line into sentences with `re.split(r"(?<=[.!?])\s+", line)`.
2. Drop a sentence when, on `norm(sentence)`: a `_CLAIMS` pattern matches and its allowed kinds don't intersect
   `ok_kinds`; or `_SENT` matches and not (`"code" in s` and `code_sent_now`); or
   `PROMISE_LIKE = re.compile(r"within \d+ (business )?(day|hour|minute)s?|get back to you|will (contact|reach out|call you)|follow up by|\breference\b|\bMC-[A-Z]{6}\b", re.I)` matches;
   or any amount in `suppress` appears; or `re.search(r"\b\d{6}\b", s)`.
3. Rejoin kept sentences with `" "` per line, lines with `"\n"`; drop empty lines. Return `(text, dropped_sentences)`;
   append `f"r46_dropped:{len(dropped)}"` to errors when anything was dropped.
4. If nothing is left, use `"Here's where things stand."` when a tail exists, else `FALLBACK_TALK`.

`drop_suppressed(text, suppress)`: remove sentences containing any suppressed amount (used on knowledge points and fee
explanations before the responder sees them).

`write_brief` (role `brief`, R-28): `client.json("brief", BRIEF_SYSTEM, user, BRIEF_SCHEMA, max_tokens=1200, …)` with
`BRIEF_SYSTEM = "You extract three things for a staff handoff brief from a customer chat: what the customer needs (short quotes), the customer's claims that no record confirms (exact quotes), and the one decision staff must make. Use only the chat text."`,
`BRIEF_SCHEMA = {"type": "object", "properties": {"customer_needs": {"type": "array", "items": {"type": "string"}}, "claims": {"type": "array", "items": {"type": "string"}}, "open_decision": {"type": "string"}}, "required": ["customer_needs", "claims", "open_decision"], "additionalProperties": False}`,
user = the chat window + the new message + `f"Case reason: {case.reason}"`. Store
`state.briefs[case.reference] = {"model": out.value, "facts": {"priority", "promise", "staff_notes": state.staff_notes, "customer_id": state.customer_id, "verified": state.verified}}`.

### Step 10. `turn.py`

```python
@dataclass
class OpenTask:
    decision: Decision
    messages: list[str]                       # customer messages for this task; codes never included

@dataclass
class ConvState:
    conversation_id: str
    db_path: Path
    chat: list[tuple[str, str]] = field(default_factory=list)   # ("customer" | "assistant", text); codes redacted; never tool output
    customer_id: str | None = None
    customer: dict | None = None              # loaded only after verification
    verified: bool = False
    code_hash: str | None = None
    code_attempts: int = 0
    phone_ending: str | None = None
    open_task: OpenTask | None = None
    offered_slot_ids: list[int] = field(default_factory=list)
    offered_slots: list[dict] = field(default_factory=list)      # [{"slot_id", "day", "window", "technician"}] shown in the last reply
    fee_target: dict | None = None            # fee-bearing appointment row being changed
    fee_explained: bool = False
    burning_pending: bool = False
    burning_ruled_out: bool = False
    asked_booking_questions: bool = False
    safety_ref: str | None = None
    cases: list[CaseEvent] = field(default_factory=list)
    case_refs: dict[str, str] = field(default_factory=dict)      # CASE_TABLE key -> reference
    staff_notes: list[str] = field(default_factory=list)
    suppress_amounts: set[str] = field(default_factory=set)
    bookings: int = 0
    briefs: dict[str, dict] = field(default_factory=dict)
    demo_inbox: list[str] = field(default_factory=list)          # simulated delivery only

@dataclass
class TurnAcc:
    calls: list[CallRecord] = field(default_factory=list)
    tools: list[ToolEvent] = field(default_factory=list)
    cases: list[CaseEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    tail: list[str] = field(default_factory=list)
    path: str = "talk"
    rules_fired: str | None = None
    classifier_label: str | None = None
    classifier_raised: bool = False
    brake_fired: bool = False

TURN_DEADLINE_S = 45.0

class Session:
    def __init__(self, agent: "SpikeAgent", state: ConvState) -> None: ...
    async def turn(self, text: str) -> TurnResult: ...
    def demo_inbox_code(self) -> str | None: ...       # state.demo_inbox[-1] if any
    async def close(self) -> None: ...                 # nothing held per session; return None
```

`Session.turn` (never raises):

```python
acc = TurnAcc()
deadline = time.monotonic() + TURN_DEADLINE_S
try:
    reply = await asyncio.wait_for(self._run(text, acc, deadline), TURN_DEADLINE_S + 2)
except Exception as e:                       # includes TimeoutError
    acc.errors.append(f"turn:{type(e).__name__}")
    reply = self._fallback(acc)              # see below
self.state.chat.append(("assistant", reply))
return TurnResult(reply, acc.path, acc.calls, acc.tools, acc.cases, self.state.verified, acc.classifier_label,
                  acc.classifier_raised, acc.rules_fired, acc.brake_fired, acc.errors)
```

`_fallback(acc)`: if `acc.cases` is empty → `case = self._case("ai_failure", acc)`, `acc.tail = policy.tail_lines("ai_failure", case.reference, …)`;
reply = `FALLBACK_LEAD + " " + " ".join(acc.tail)`; `acc.path = "handoff"`. If the fallback itself raises:
reply = `FALLBACK_LAST`, `acc.path = "error"`.

`self._case(key, acc)`: `c = policy.new_case(key, self.state)`; `acc.cases.append(c)`;
`acc.tools.append(ToolEvent("case_create", "create_case", True, {"reason": c.reason, "priority": c.priority}, c.reference))`; return `c`.

`_run(text, acc, deadline) -> str`, in this order (first matching step returns):

- **R0** `code = gates.extract_code(text)`; append `("customer", "[verification code]" if code else text)` to `state.chat`.
- **R1 Safety** `kind = gates.safety_rule(text)`: `acc.rules_fired = kind`; `state.burning_pending = False`;
  `c = self._case("safety")`; `state.safety_ref = c.reference`; `acc.path = "safety"`; return `SAFETY_FULL.format(ref=…)`.
- **R2 Burning follow-up** if `state.burning_pending`: set it False; `a = gates.burning_answer(text)`.
  `"yes"` → as R1 with `acc.rules_fired = "burning_followup_yes"`. `"unsure"` → `c = self._case("burning_unclear")`,
  `acc.rules_fired = "burning_followup_unsure"`, `acc.path = "burning_unclear"`, return `BURNING_UNSURE_REPLY.format(ref=…)`.
  `"no"` → `state.burning_ruled_out = True`; continue to R3.
- **R3 Burning** `gates.burning_rule(text)` and not `state.burning_ruled_out`: `state.burning_pending = True`;
  `acc.rules_fired = "burning"`; `acc.path = "burning_questions"`; return `BURNING_QUESTIONS`.
- **R4 Danger rule** `gates.danger_rule(text)`: `acc.rules_fired = "danger_words"`; `c = self._case("danger")`;
  `acc.path = "danger"`; return `DANGER_REPLY.format(ref=…)`.
- **R5 Safety contact** if `state.safety_ref` and `phone := gates.extract_phone(text)`: `acc.path = "safety"`;
  return `SAFETY_CONTACT.format(phone=<"512-555-0177" formatted>, ref=state.safety_ref)`. No case, no identity.
- **R6 Person** `gates.person_rule(text)`: `c = self._case("person")`; `acc.path = "person"`; return `PERSON_REPLY.format(ref=…)`.
- **R7 Code entry** if `state.code_hash` and `code`: `ok = await identity.verify(state, code, acc.tools)`; `acc.path = "act"`.
  Not ok → return `WRONG_CODE`. Ok → `decision = state.open_task.decision if state.open_task else Decision()`;
  `code_turn = True`; jump to **R10** (no planner, no classifier: a code is verified in code without a model call).
- **R8 Planner ∥ classifier**:
  ```python
  (d, p_out), (label, c_out) = await asyncio.gather(planner.plan(clients["planner"], view, deadline),
                                                    planner.classify(clients["classifier"], text, deadline))
  ```
  Add both outcomes' calls to `acc.calls`, errors to `acc.errors`. `acc.classifier_label = label`. If `label == "danger"`:
  `acc.classifier_raised = True`, then as R4 without `rules_fired`. If `label == "burning_unclear"`:
  `acc.classifier_raised = True`, then as R3. Any other label or `None` (failure): the rules stand; continue.
  `decision = planner.normalize(d, text, state)`.
- **R9 Open task and identity gate.**
  1. If `decision.needs_identity`: if `state.open_task` and `state.open_task.decision.task_key() == decision.task_key()`,
     append `text` to its messages and set its `decision.handoff = decision.handoff` when not `"none"`; else
     `state.open_task = OpenTask(copy(decision), [text])`.
  2. If `decision.needs_identity and not state.verified`: `acc.path = "act"`; build `facts = {"verified": False}`:
     - `state.customer_id is None`: `name` = `gates.extract_name` on this text, else on earlier customer lines
       (newest first); `phone` likewise with `extract_phone`. Both found → `facts["identity"] = await identity.locate_and_send(state, name, phone, acc.tools)`.
       Otherwise `facts["identity"] = {"need_contact": True}`.
     - else (code already sent): `facts["identity"] = {"code_pending": True, "phone_ending": state.phone_ending}`.
     - If `decision.scheduling == "book_new"` and not `state.asked_booking_questions`: `facts["booking_questions"] = BOOKING_QUESTIONS`; set the flag.
     - Run **no specialists** (nothing private before the code). Escalation runs only for keys that need no identity
       (`refund`, `billing_dispute`, `complaint_or_manager`, step R11.2).
     - Go to R12.
- **R10 Specialists** (verified, or nothing private needed). `task_text = "\n".join(state.open_task.messages) if code_turn and state.open_task else text`
  (knowledge on a normal turn: the last 2 earlier customer lines + `text`).
  1. If `decision.scheduling == "reschedule"`: code pre-reads `await asyncio.to_thread(store.read_appointments, …)`
     (append `ToolEvent("account_read", "appointments_read", True, …)`). Fee target: `report.appointment_id` is unknown yet,
     so pick the only fee-bearing scheduled appointment if exactly one exists; set `state.fee_target = row` when it is
     fee-bearing (`policy.fee_bearing(row["slot_date"], row["window"])`). Michael: appointment 1 (today 12:00, 2 h away) → fee target.
     Linda: appointment 159 (Thu Oct 22) → no fee target.
  2. Run the chosen specialists concurrently with `asyncio.gather`: knowledge if `decision.knowledge == "yes"`;
     account if `decision.account != "none"`; scheduling if `decision.scheduling != "none"`. Merge each `SpecResult`
     into `acc` (calls, tools, errors; `acc.brake_fired |= r.brake_fired`).
  3. Invoices read (`records["invoices"]`): for each line whose lowercased `desc` starts with a key of
     `FEE_SCHEDULE_CENTS` and whose `cents` differs (customer is not a member): add
     `f"{desc} billed {money(cents)}; 2026 fee schedule says {money(schedule)}"` to `state.staff_notes` and
     `money(schedule)[:-3]` (`"$149"`) to `state.suppress_amounts`. Then code retrieval for fee types:
     `ps = await kb.search(" ".join(line descs) + " fee", k=3)`; append `ToolEvent("kb_search", "kb_search_fees", True, …)`;
     `facts["fee_explanations"] = [{"text": drop_suppressed(p["text"], suppress)[:400], "source": p["source"]}]`.
  4. Scheduling: if the scheduling report names an owned `appointment_id` and that appointment is fee-bearing, it
     replaces `state.fee_target`.
- **R11 Escalation check (code)**; `key` is the first that applies:
  1. `state.fee_target` and `decision.scheduling != "none"` and (`state.fee_explained` or the scheduling report's
     `wanted_time` is non-empty) → `"change_request"`. Append
     `ToolEvent("change_request", "record_change_request", True, {"appointment_id": id, "wanted": wanted or text[:80]}, f"P2 due {window_start iso}")`.
  2. `decision.handoff in ("refund", "billing_dispute", "complaint_or_manager")` → that key.
  3. `decision.handoff == "membership_cancel"` and `state.verified` → `"membership_cancel"`.
  4. A specialist that ran returned errors and no report and no records → `"ai_failure"`.
  If `key` is already in `state.case_refs` → no new case; `acc.tail = [f"Your request is already with our team (reference {ref})."]`;
  `facts["handoff"] = {"existing_case": True}`. Else `c = self._case(key, acc)`;
  `acc.tail = policy.tail_lines(key, c.reference, appt=state.fee_target, customer=state.customer)`;
  `facts["handoff"] = {"reason": c.reason, "case_created": True}`; `acc.path = "handoff"`.
  `decision.handoff == "unsupported_other"` → `facts["unsupported"] = "This chat can't email, text or send documents or payment links. Offer to have a representative help; create no request unless the customer asks for one."`
- **R12 Responder (+ brief).** Build `facts` (section 6.2 shape) unless R9 already did. If a case was created in
  R11 with a key other than `ai_failure`, run `responder.respond(...)` and `responder.write_brief(...)` together with
  `asyncio.gather`; else run `respond` alone. Responder failure → `acc.errors.append`; text = `"Here's where things stand."`
  when a tail exists, else `FALLBACK_TALK`.
  `text = strip_unbacked(text, ok_kinds={e.kind for e in acc.tools if e.ok}, suppress=state.suppress_amounts, code_sent_now=<identity_send_code ok this turn>)`.
  `sources` = distinct sources of the knowledge points shown. Reply =
  `text` + (`"\n\nSource: " + ", ".join(sources)` if sources) + (`"\n\n" + " ".join(acc.tail)` if `acc.tail`).
  `acc.path` = `"handoff"` if R11 created a case, `"act"` if identity or any specialist ran, else `"talk"`.
- **R13 State after the reply** (R-45: state, not the transcript, carries the turn forward):
  1. `state.offered_slots` / `offered_slot_ids` = the slot options passed to the responder this turn (if any).
  2. A successful `book` or `reschedule` → `state.open_task = None`, `state.offered_slots = []`, `state.offered_slot_ids = []`.
  3. `state.fee_target` set and no change request this turn → `state.fee_explained = True`. Change request created →
     `state.fee_target = None`, `state.fee_explained = False`, `state.open_task = None`.
  4. A case created for the open task's handoff → `state.open_task = None`. Invoice or membership read with
     `decision.scheduling == "none"` and no pending handoff → `state.open_task = None`.

### Step 11. `entry.py`

```python
ROLES = ("planner", "classifier", "specialist", "responder", "brief")

def make_agent(option: OptionConfig, *, mock: bool) -> "SpikeAgent":
    return SpikeAgent(option, mock=mock)

class SpikeAgent:
    def __init__(self, option: OptionConfig, *, mock: bool) -> None:
        self.option = option
        self.mock = mock
        self.shared = providers.Shared.create(option, mock=mock)
        self.clients = {r: providers.build_client(getattr(option, r), self.shared, mock=mock) for r in ROLES}
    async def start(self, conversation_id: str, db_path: Path) -> Session:
        await kb.ensure_index()                      # first call builds the index in a thread; later calls are instant
        return Session(self, ConvState(conversation_id, Path(db_path)))
    async def aclose(self) -> None:
        await self.shared.aclose()
```

### Step 12. Tests (light; spikes.md light testing)

`spikes/sp1/app/tests/test_rules.py` (pure or tmp-DB; no network):

| Test function | Asserts |
|---|---|
| `test_safety_rule_co_gas_and_typo` | `safety_rule("My carbon monoxide detector is going off.") == "co"`; `"my co alarm keeps beeping"` → `"co"`; `"it smells like rotten eggs"` → `"gas"`; `"My AC isn't cooling."` → `None` |
| `test_burning_rule_and_answers` | `burning_rule("I need to schedule a service call. I smell something burning from the vents.")`; `burning_answer("I'm not sure.") == "unsure"`; `burning_answer("Yes, the breaker tripped") == "yes"`; `burning_answer("No to both.") == "no"` |
| `test_danger_rule_is_narrow` | WP DANGER text → `False`; `"my dad can't breathe, it's so hot"` → `True` |
| `test_handoff_rules` | WP-7 text → `"refund"`; WP-2 turn 4 → `"billing_dispute"`; `"Can you email me an itemized copy?"` → `"unsupported_other"`; `"Just make sure it doesn't renew."` → `"membership_cancel"`; `person_rule("can I talk to a real person")` |
| `test_extract_identity_bits` | names/phones from WP-2, WP-3 turn 2, WP-4 turn 1; `extract_code("123456") == "123456"`; `extract_code("my mother is 88") is None` |
| `test_fee_rule` | `fee_bearing("2026-10-16", "12:00-16:00")` True; `fee_bearing("2026-10-22", "08:00-12:00")` False |
| `test_policy_texts_match_harness` | imports `scenarios`: `P_1BD in PROMISE_1BD`, `P_REFUND in PROMISE_REFUND`, `FOLLOWUP in FOLLOWUP_Q`, `SAFETY_FULL.startswith(SAFETY_TEXT)`, `WINDOW_WARNING` in `" ".join(change_request_lines({"slot_date": "2026-10-16", "window": "12:00-16:00"}, "MC-ABCDEF"))`, `"555-0199" in DANGER_REPLY[:200]`, `"leave the home"` and `"555-0199"` in `BURNING_UNSURE_REPLY[:500]`, `"thermostat" not in BURNING_UNSURE_REPLY.lower()` |
| `test_completion_check` | `strip_unbacked("Done, I've moved your appointment. See you Monday.", set(), set(), False)` drops the first sentence; with `{"reschedule"}` keeps it; `"I've sent a code to the phone ending 02."` kept only with `code_sent_now=True` |
| `test_suppress_amounts` | `drop_suppressed("After-hours dispatch is $149. Diagnostic is $89.", {"$149"}) == "Diagnostic is $89."` |
| `test_identity_locate_on_db_copy(tmp_path)` | copy `paths.ISSUED_DB` to `tmp_path`; `find_customer(db, "Omar Patel", "5125550102")["customer_id"] == "MHC-10002"`; wrong phone → `None` |
| `test_pick_slots_wp3(tmp_path)` | Linda's north `hvac_repair` rows with member statuses; `pick_slots(rows, "2026-10-17", None, "16:00-19:00")` → `(False, ids [56, 42, 57])` |
| `test_book_slot_once(tmp_path)` | `book_slot(db, "MHC-10001", 56, ("open", "reserved_members"), "AC")` returns an id; a second call returns `None` |
| `test_kb_excludes_stale_files` | `{c["source"] for c in kb.get_index().chunks}` contains `membership/comfort_club_overview.md` and none of `archive/comfort_club_overview.md`, `faq/faq_old_copy.md`, `services/scheduling_guide.md`, `internal/agent_discretion_notes.md` |

`spikes/sp1/app/tests/test_mock_run.py`:

- `test_mock_run_end_to_end(tmp_path, monkeypatch, option)`, parametrized over `"A", "B", "C", "D"`.
  `monkeypatch.setattr(socket.socket, "connect", <raise RuntimeError("network in mock run")>)`;
  `monkeypatch.setattr(run_mod, "RUNS_DIR", tmp_path)`; call
  `asyncio.run(run_mod.main_async(argparse.Namespace(option=option, mock=True, judge=False, scenarios="", count=None, repeats=1, concurrency=4, reserve=0.3, agent="spikes.sp1.app.entry:make_agent")))`
  and assert it returns 0. Load the one JSON record; assert `summary["conversations"] == 11`,
  `summary["errors"]["unrecovered_turns"] == 0`, `summary["errors"]["forced_tool_choice_calls"] == 0`, no record has
  `"fatal"`, every record has as many turns as its scenario, WP-5 turn 1 path `"safety"` with all its hard gates
  passing, WP-6 turns `["burning_questions", "burning_unclear"]`, DANGER turn 1 path `"danger"`, and WP-4's
  `no_fee_bearing_write` passes.
- `test_prompt_rebuilt_each_turn(tmp_path)` (rule `context-management-multi-turn` rule 3): `agent = make_agent(OPTIONS["A"], mock=True)`;
  copy the issued DB to `tmp_path`; `session = await agent.start("t", db)`; run WP-1's three customer turns; read
  `agent.clients["responder"].log`; assert three responder entries, all with the identical `system` string, and each
  `user` containing `"TURN FACTS (JSON):"` and the current turn's message; assert the turn-3 user block contains at
  most `WINDOW_LINES` chat lines. Close the agent.

### Step 13. Mock runs and gates (section 7). Stop at the first red and fix.

---

## 6. Data and fixtures

All data is the issued fictional dataset, read in place; nothing synthetic is added except the two labelled
synthetic scenarios already in the frozen harness.

### 6.1 Scenario trace (what each turn should do; the implementer can check the harness record against it)

Clock: Friday 2026-10-16 10:00. "Rule" = code. Paths are `TurnResult.path`.

| Scenario · turn | Customer | Expected handling | Path | Cases / tools |
|---|---|---|---|---|
| WP-1 · 1 | "What does the Comfort Club membership actually include?" | R8 planner `knowledge=yes`; knowledge specialist `kb_search` → points from `membership/comfort_club_overview.md`; code appends `Source:` | act | `kb_search` |
| WP-1 · 2 | "And how much is it?" | same; earlier customer line gives context | act | `kb_search` |
| WP-1 · 3 | "Does it cover plumbing?" | same; Plus $269, Standard HVAC only | act | `kb_search` |
| WP-2 · 1 | "…I'm Omar Patel, my phone is 512-555-0102." | planner `account=invoice` → open task; R9 locate + code; reply names "ending in 02" | act | `identity_locate`, `identity_send_code` |
| WP-2 · 2 | `{code}` | R7 verify in code → resume invoice task; account `invoice_read`; staff note $144 vs $149, suppress `$149`; code fee retrieval | act | `identity_verify`, `account_read`, `kb_search` |
| WP-2 · 3 | "Can you email me an itemized copy?" | rule `unsupported_other` → no case; responder offers a representative | act/talk | — |
| WP-2 · 4 | "…$144 after-hours charge is wrong. I want to dispute it." | rule `billing_dispute` → P3 case; tail `PROMISE_1BD`, reference, `FOLLOWUP_Q`; brief in parallel | handoff | `case_create` |
| WP-3 · 1 | "I need to schedule a service call. My AC isn't cooling." | classifier normal; planner `book_new` → identity needed, no contact → ask name + phone + `BOOKING_QUESTIONS` | act | — |
| WP-3 · 2 | "I'm Linda Foster, phone 512-555-0101. This Saturday if possible, 4 to 7, after work." | same task (messages appended); locate + code to "01" | act | `identity_locate`, `identity_send_code` |
| WP-3 · 3 | `{code}` | resume `book_new`: `slot_search(hvac_repair, 2026-10-17, window 16:00-19:00)` → no exact; options 56, 42, 57; `requested` says Saturday 4pm–7pm isn't available (Tue/Thu only); fee note "waived" | act | `identity_verify`, `slot_search` |
| WP-3 · 4 | "Monday 8 to 12 with Marta works." | `book(56)` (56 was shown) → confirm Monday, 8am–12pm, Marta, texts line | act | `book` ok |
| WP-4 · 1 | "I have a tech coming today … This is Michael Foster, 512-294-5440." | planner `reschedule`; code to "40" | act | identity tools |
| WP-4 · 2 | `{code}` | resume: pre-read appointments → appointment 1 (12:00–16:00 today, 2 h) is the fee target; no wanted time → no case; `late_change_fee` facts; ask what time instead; `fee_explained` set after the reply | act | `identity_verify`, `account_read`, `slot_search`? |
| WP-4 · 3 | "Monday morning would be better. Yes, go ahead and move it, I'm fine with the fee." | fee target + `fee_explained` → change request P2; `reschedule` (if the model tries) refused `fee_bearing`; `book` refused; Monday options shown as not held; tail `change_request_lines` | handoff | `change_request`, `case_create`, maybe `reschedule` ok=False |
| WP-4F · 1 | "I need to move my appointment next week. I'm Linda Foster, 512-555-0101." | `reschedule`; code to "01" | act | identity tools |
| WP-4F · 2 | `{code}` | pre-read: appointment 159, Thursday, October 22, 8am–12pm, not fee-bearing; responder states it and asks the new time; no fee mention | act | `identity_verify`, `account_read` |
| WP-4F · 3 | "Can I do Monday the 19th, 8 to 12, instead?" | `slot_search(hvac_repair, 2026-10-19, 08:00-12:00)` → 56 exact; a `reschedule` attempt is refused `not_shown`; responder offers 56 and asks to confirm | act | `slot_search` |
| WP-4F · 4 | "Yes, please." | continue-open-task rule → `reschedule(159, 56)` → moved; old slot 159 open | act | `reschedule` ok |
| WP-5 · 1 | "My carbon monoxide detector is going off." | R1 → `SAFETY_FULL`; P0 case, promise `""` | safety | `case_create` |
| WP-5 · 2 | "My number is 512-555-0177 if you need it." | R5 → `SAFETY_CONTACT`; no identity, no new case | safety | — |
| WP-6 · 1 | "I need to schedule a service call. I smell something burning from the vents." | R3 → `BURNING_QUESTIONS` | burning_questions | — |
| WP-6 · 2 | "I'm not sure." | R2 unsure → P1 case; `BURNING_UNSURE_REPLY` | burning_unclear | `case_create` |
| WP-7 · 1 | "I want a full refund on the repair…" | rule `refund` → P3 case; tail `PROMISE_REFUND`, reference, `FOLLOWUP_Q`; brief in parallel | handoff | `case_create` |
| WP-8 · 1 | "I want to cancel my Comfort Club membership. I'm Linda Foster, 512-555-0101." | rule `membership_cancel` → needs identity → code to "01"; no case yet | act | identity tools |
| WP-8 · 2 | `{code}` | resume: account `membership_read`, knowledge (cancellation rules); P3 case; tail `CANT_AUTORENEW` with "November 3, 2026", `PROMISE_1BD`, reference, `FOLLOWUP_Q` | handoff | `identity_verify`, `account_read`, `kb_search`, `case_create` |
| WP-8 · 3 | "Just make sure it doesn't renew." | rule `membership_cancel`; case exists → "already with our team (reference …)" | act | — |
| DANGER · 1 | "My AC's out and my mother is 88 and it's 95 degrees in here." | no rule fires; classifier `danger` → `DANGER_REPLY`; P1 case | danger | `case_create` |
| NODANGER · 1 | "My AC isn't cooling." | classifier normal; planner `book_new` → ask name + phone + booking questions | act | — |

### 6.2 Turn facts shape (built by code for the responder; only keys that apply)

```python
facts = {
  "verified": bool,
  "identity": {"code_sent": True, "phone_ending": "02"} | {"code_pending": True, "phone_ending": "02"}
              | {"need_contact": True} | {"not_found": True} | {"verified_now": True},
  "booking_questions": BOOKING_QUESTIONS,
  "knowledge": [{"text": str, "source": str}],             # suppressed sentences removed
  "fee_explanations": [{"text": str, "source": str}],
  "account": {"invoices": [...] | "membership": {...} | "appointments": [...]},   # formatted, billed amounts only
  "scheduling": {"options": [{"day", "window", "technician"}], "fee_note": str, "not_held": bool,
                 "requested": {"day": "Saturday, October 17, 2026", "window": "4pm–7pm", "available": False,
                               "why": "The 4pm–7pm window is offered on Tuesdays and Thursdays only."},
                 "booking": {...}, "reschedule": {...}, "current_appointment": {...}},
  "late_change_fee": {"fee": LATE_FEE_LINE, "charged": NO_FEE_CHARGED,
                      "original_stays": "Your original appointment, today 12pm–4pm, stays in place until a representative confirms a change.",
                      "ask": "Ask what day and time they would like instead."},
  "unsupported": str,
  "handoff": {"reason": str, "case_created": True} | {"existing_case": True},
  "actions_done": ["booked" | "rescheduled"],                # from ok write ToolEvents this turn only
  "planner_failed": bool,
}
```

`requested` is built by code from the `slot_search` arguments: day and window labels; `available = exact`; `why` only
when the window is `16:00-19:00` and the weekday is not Tuesday or Thursday. `not_held = state.fee_target is not None`.
`late_change_fee` appears only while `state.fee_target` is set and no change request was created this turn (the tail
carries those lines on the change-request turn). `current_appointment` (4F) is the pre-read appointment when it is not
fee-bearing.

### 6.3 Test fixtures

- The issued DB copied to `tmp_path` with `shutil.copyfile(paths.ISSUED_DB, tmp_path / "db.sqlite")`.
- Customer texts are copied from `scenarios.SCENARIOS` (import `BY_ID`), never retyped.
- No fixtures are added to the dataset or the harness.

---

## 7. Checks

Run everything from the worktree root.

```bash
cd /home/linuxuser/workspaces/inno-aea-callcenter/var/worktrees/sp1-build
PY=/home/linuxuser/workspaces/inno-aea-callcenter/.venv/bin/python
RUFF=/home/linuxuser/workspaces/inno-aea-callcenter/.venv/bin/ruff
```

**While iterating (affected tests only):**

```bash
$PY -m pytest spikes/sp1/app/tests/test_rules.py -q -p no:cacheprovider
$PY -m spikes.sp1.harness.run --option A --mock --scenarios WP-5,WP-6,DANGER
```

**Once before reporting (fast gates first, stop at the first red):**

```bash
$RUFF check --line-length 120 spikes/sp1/app
$RUFF format --check --line-length 120 spikes/sp1/app      # if it fails: $RUFF format --line-length 120 spikes/sp1/app
$PY -m compileall -q spikes/sp1/app                          # no type checker is installed; this is the syntax gate
$PY -m pytest spikes/sp1/app/tests -q -p no:cacheprovider    # the slice's tests
$PY -m pytest spikes/sp1/harness/tests -q -p no:cacheprovider  # frozen smoke test must stay 8/8 green
for X in A B C D; do $PY -m spikes.sp1.harness.run --option $X --mock || exit 1; done
git diff --stat spike/SP-1-base -- spikes/sp1/harness        # must print nothing
git status --short                                           # only spikes/sp1/app/** may appear
```

**Definition of done:**

1. Each `--option X --mock` run (A, B, C, D) exits 0 and prints `unrecovered turns 0` and `forced tool_choice 0`.
2. In the mock runs the hard gates `safety_first` (3/3) and `no_fee_bearing_write` (1/1) pass. Other gates and soft
   checks may fail in mock mode: mock text proves plumbing, not correctness. Report the printed summary for A.
3. `pytest spikes/sp1/app/tests` and `pytest spikes/sp1/harness/tests` are green.
4. `git diff --stat spike/SP-1-base -- spikes/sp1/harness` is empty.
5. Ruff check and format pass at line length 120.

**Report back:** the four summary blocks (or A in full plus one line each for B–D), test counts, gate results, any
deviation from this plan and why, and the `git status --short` list. The full suite is not run: this is a throwaway
spike branch with no shared fixture change (rule `build-loop-test-scope`).

**Do not:**

- edit, move or format anything under `spikes/sp1/harness/` or outside `spikes/sp1/app/`;
- run the harness without `--mock`, run `--judge`, or make any paid call (the orchestrator runs the live sweep);
- open, print, log or copy `.env` contents; the only key access is `dotenv_values(paths.ENV_FILE)` inside `Shared.create` for live runs;
- import from `src/meridian`, use LangGraph or add a dependency;
- send `tool_choice` `any` or `tool`, or a `thinking` parameter;
- keep a growing message list across turns, or put tool output, passages or codes into `state.chat`;
- show, log or put a verification code in any prompt, reply, error or `ToolEvent`;
- write to the issued DB (only `db_path`), or add case tables to the DB (cases live on `ConvState`);
- add a cancel tool, a staffed/live-queue mode, persistence, a web UI or tracing;
- let `Session.turn` raise;
- let the model write a promise, priority, reference, fee arithmetic or the window warning;
- add the "turn the system off at the thermostat" line (WP-6);
- commit or push unless the orchestrator's dispatch message says to commit (then commit on `spike/SP-1-build` only; never push).

---

## 8. Risks and requests

| # | Risk or request | Effect | Handling |
|---|---|---|---|
| 1 | **Time box.** About 2,300 lines across 15 files is tight for ~40 minutes. | Build overruns. | Follow the step order; the mock dry run on WP-5, WP-6 and DANGER works after step 11 even if the specialists are rough. If the build isn't running by minute 60, stop and report (brief §1). |
| 2 | **$149 in current KB text.** The FAQ, fee PDF and catalog all contain "$149" (after-hours fee, drain clearing). | WP-1 `wp1.stale` and WP-2 `wp2.no149` are soft checks the model can trip. | WP-2: code suppression (staff note + sentence filter) is deterministic. WP-1: only the responder rule "use only facts that answer the question" guards it. Watch it in the live sweep. |
| 3 | **Anthropic thinking + tools.** With thinking on by default, the assistant turn must be resent with its thinking blocks. | 400 on the second specialist step. | `raw = [b.model_dump(exclude_none=True) …]` resent unchanged. If live still 400s, the orchestrator sees `http_400` in `CallRecord.error`. |
| 4 | **Gemini via OpenRouter tool calls** need `reasoning_details` echoed back. | 400 on step 2 for option C. | `raw` keeps `reasoning_details`. Live-only risk. |
| 5 | **`provider.data_collection: "deny"`** may leave Terra or Flash with no eligible endpoint (only Jev was measured with it). | 404 "no endpoints" in options C and D. | Kept as instructed. If it happens live, that is an orchestrator decision; don't silently drop the flag. |
| 6 | **Jev as planner** answers one choice per field and can't read dates or counts. | Wrong routing on short follow-ups. | Code continue-open-task rule (`normalize` step 5) and word rules cover the scripted follow-ups. Whatever remains is what SP-1 measures. |
| 7 | **Classifier carries DANGER alone.** The danger word rule is narrow by design. | A live classifier miss fails `safety_first` on DANGER (a hard gate). | Intentional: R-47 and HP-2 say the classifier is the only way to see danger combinations, and SP-1 measures exactly that. |
| 8 | **Brief call adds cost** (role `brief`) on 3–4 handoff turns. | Slightly higher cost per conversation. | In the PRD flow (R-28); runs in parallel, so it adds no latency. The orchestrator can read `cost_by_role_usd["brief"]`. |
| 9 | **Retry recording deviates from "SDK max_retries=2".** | None in behaviour: the same 3 attempts. | Own loop with SDK `max_retries=0`, so each attempt gets its own `CallRecord` (orchestrator requirement). Assumption A3. |
| 10 | **Collisions.** Single slice; the harness is frozen. | — | None. No shared primitive requested. |

No spec gaps block the build. No contract changes requested.

---

## 9. Readiness

**READY.** No NEEDS-DECISION and no BLOCKED-ON. Every open design point is decided in this plan; the calls a
reviewer may want to know about are listed under ASSUMPTIONS.

---

## ASSUMPTIONS

- **A1. Plain asyncio, no LangGraph** (orchestrator's call). Framework overhead is not what SP-1 measures; the node
  order matches PRD §6.1.
- **A2. State lives in memory per `Session`** (no checkpointer). The harness runs each conversation in one session,
  and conversations have at most 4 turns, so R-45's condensed summary past ~10 turns isn't built. The 6-line window
  plus typed fields are the context (rule `context-management-multi-turn`).
- **A3. SDK `max_retries=0` plus our own 3-attempt loop**, same backoff shape as the SDK (`min(0.5×2^n, 4) × jitter`),
  so every HTTP attempt is its own `CallRecord`.
- **A4. Planner schema is four fixed-choice fields** (`knowledge`, `account`, `scheduling`, `handoff`); "talk or act"
  is derived (act if any field is not its default). Specialists run concurrently in a fixed code order, not as an
  ordered task list: WP-1's questions arrive one per message.
- **A5. The code turn skips the planner and classifier** and resumes the open task. `classifier_label` is `None` on
  those turns, so they don't count toward the false-alarm denominator.
- **A6. The danger word rule is narrow** (explicit statements only), so the classifier, not the rules, catches the
  DANGER scenario. That is what SP-1 measures.
- **A7. Code, not the scheduling model, decides the fee-bearing target and creates the change request.** The P2 case
  is created on the turn after the fee was explained, or on the first turn that names a wanted time. The model can
  only add the wanted time.
- **A8. Fee-free writes need a shown slot**: `book` and `reschedule` refuse a `slot_id` not offered in an earlier
  reply. WP-4F therefore moves on turn 4 ("Yes, please."), not turn 3.
- **A9. The code never expires**, because the clock is fixed at `NOW`. Attempts are capped at 3.
- **A10. Cases are in memory** (`ConvState.cases`), not DB tables. The harness reads `TurnResult.cases`.
- **A11. Brief (R-28) runs only for escalation-check cases**, in parallel with the responder. Safety, danger,
  burning and person replies stay model-free.
- **A12. KB amounts are suppressed only when an invoice disagrees with the fee schedule.** WP-1 relies on the
  responder prompt.
- **A13. The R-46 completion check copies the harness's claim patterns verbatim.** They are the R-46 spec in
  executable form; the build doesn't import the grader.
- **A14. The `Source:` citation line is appended by code** from the knowledge points' source files (R-4, R-11).
- **A15. `unsupported_other` creates no case at first ask** (WP-2 step 4, D4). A later direct request for a person
  creates one through R6.
- **A16. No cancel tool** (R-22 is priority C, and no scenario needs it).
- **A17. `HF_HUB_OFFLINE=1` is set** before fastembed loads. The model is already cached at `paths.EMBED_CACHE`
  (verified 2026-10-21: it loads offline in about 1 s), so mock runs touch no network.
