# Plan — [FU-saveFollowUp-text] Follow-up sentence for email to a general destination (provisional wording)

**Status:** planned (READY).
**Issue:** none. This is a wave-fix item, not a ticket. It comes from the AEA-51 pass-1 full-suite run. This plan is its spec and its item note.
**Base revision:** main `9d12b8f` (context: wave 3 upkeep, AEA-60 audits and findings).
**Lane / risk:** `lane::build-loop`, no `risk::security`. The change is one fixed display sentence plus one branch that reads no contact value, so there are no frozen tests and no security review.
**Models:** planner `claude-opus-5-5`; implementer Sonnet.
**Exceptions granted by Innocent (2026-10-21, "just do whatever you recommend"):**
- Edit AEA-03's merged files `src/meridian/policy/texts.py`, `tests/unit/policy/texts_source_fixture.json` and `tests/unit/policy/test_texts.py`. This is the same pattern as AEA-03b.
- Edit AEA-29's merged `src/meridian/services/_case_actions.py`, **only the function `set_followup_in`**.

**Provisional wording (item note).** The wording below is provisional until the UX session. It is recorded here, in the journey record, and as a code comment in `texts.py`.
- Saved line: `"Follow-up saved: email, {window}."`, for example "Follow-up saved: email, any time."
- Destination label: `"a general contact"`.

## Goal

The OpenAPI example `EMAIL_GENERAL` is `{"channel": "email", "destination": "general", "window": "any"}`, from an unverified customer. `PUT /api/chat/sessions/{thread_id}/follow-up` (CON-5 `saveFollowUp`) with that body must return 200 with a body that validates against the OpenAPI, instead of 500.

Today `src/meridian/services/_case_actions.py` `set_followup_in` (lines 181–184) raises `NotImplementedError("follow-up text for email/general: blocked-on AEA-03 follow-up (UX wording)")` for every combination except phone on record.

This item makes three changes:
1. It adds one fixed customer sentence, `TextId.FOLLOWUP_SAVED_EMAIL_GENERAL`, with its source fixture entry and the count in `EXPECTED_COUNTS`.
2. It makes `set_followup_in` use that sentence for `channel == "email"` with `destination == "general"`.
3. It leaves every other combination exactly as it is. Phone on record stays byte-identical. Email on record and phone general still raise.

## Context

AEA-29 (merged `d3facfe`) built `CaseService.set_followup`. The text for email and general destinations was missing, so those branches raise (recorded gap O-15, `docs/design/contracts/stage7/cases.md` §5a).

AEA-59's server runner drives `saveFollowUp/email_general` through the real app. On main that drive is **skipped**, with `not bound: reply_composer`. I checked this at `9d12b8f`: both saveFollowUp success drives skip.

Once AEA-51 binds `reply_composer`, the drive reaches the service and returns 500. Innocent told us to add the missing sentence in the house style.

## Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Finding | AEA-51 pass-1 full suite: `tests/contract/test_openapi_server.py::test_success_matches_contract[saveFollowUp/email_general]` → 500 | The drive must pass with the real response validated against the OpenAPI |
| Signed UI contract (read only) | `docs/ux/03-structure/ui-contracts.openapi.yaml` `saveFollowUp` (lines 2795–2915); `FollowUpView` (lines 8334–8360); `FollowUpRequest` (9949–9971) | `FollowUpView` requires `channel` (email/phone), `destination_label` (string), `on_record` (bool), `window` (morning/afternoon/any) and `saved_line` (string, "Never says a message was sent"). There is no example 200 body for EMAIL_GENERAL and no fixed wording, so **no contract change is needed** |
| UX wording (read only) | `docs/ux/03-structure/SCREEN_SPECS.md` line 154 (SCR-1 copy notes, R-27) and line 161 ("Never on this screen: … 'sent' for a follow-up") | Saved line shape: "Follow-up saved: phone call, the number ending in 02, mornings." UX gives no email or general wording; that gap is what this item fills, provisionally |
| UI contract notes (read only) | `docs/ux/03-structure/UI_CONTRACTS.md` lines 218–226 | "an unverified customer can save `general` only … Nothing in any response says a message was sent (R-34)" |
| PRD | R-27 (`docs/prd/inno-aea-callcenter-prd.md` line 233), R-34 | Store channel, destination (on record or not) and window. Private details go only to a destination on record after verification. Nothing says sent |
| DO-4 | `docs/design/contracts/internal-components.md` line 964: `def set_followup(self, thread_id: ThreadId, choice: FollowUpChoice, now: datetime) -> FollowUp: ...   # CON-5` | Superseded by the stage7 addendum (next row) |
| Stage 7 addendum (wins over DO-4) | `docs/design/contracts/stage7/cases.md` §5a (lines 600–620) | `set_followup` returns `FollowUp \| CaseActionRejected`; refusals use `NOT_ALLOWED_IN_STATE` with `details.state` (O-4). O-15 records this gap. `FollowUpChoice` = `FollowUpRequest`, `FollowUp` = `FollowUpView` |
| Stage 7 addendum (texts) | `docs/design/contracts/stage7/data.md` §2 (header lines 1–14; texts at 95–122) | `TextId(StrEnum)` valued `"<group>.<name>"`. `render(text_id: TextId, /, **values: str) -> str`. Placeholders are named only, from `PLACEHOLDERS`. New texts are recorded in §2 (precedents: R-W-6, AEA-03b) |
| Web addendum | `docs/design/contracts/stage7/web.md` line 349 | `saveFollowUp` stays a direct `CaseService.set_followup` call. An unverified thread asking for `on_record` gets 409 `not_verified` (unchanged) |
| Existing double (consistency) | `tests/services/person_request_support.py` lines 314–335 (AEA-42's `CaseService` double) | For every non-phone-on-record choice it already returns label `"a general contact"` and line `f"Follow-up saved: {channel_word}, {window}."`, which is "Follow-up saved: email, any time." for EMAIL_GENERAL. **The real service will now say the same words as the double** |
| Test scope | `.claude/rules/build-loop-test-scope.md` with its AEA addition | Affected tests, then fast gates, then affected journeys before the commit. No full suite (see *Checks*) |
| Journeys | `.claude/rules/integrated-journeys.md` §3–§4 | Exactly one `[journey]` criterion with its level and *Blocked by*. Record in `docs/testing/journeys/` |
| Context upkeep | `.claude/rules/context-maintenance.md` rule 1 | data.md §2, cases.md §5a (O-15) and area-map row A0 change in the same item |
| DO-5 / DO-6 / DO-7 | evaluation plan, observability, metrics | n/a. No model behaviour, entry point, log or trace field, or metric changes. CAP-n untouched: the new branch reads no contact value |

## Source-contract reconciliation

| Obligation | Governing source | In item | Disposition | Plan step or owner |
|---|---|---|---|---|
| EMAIL_GENERAL returns 200, validated against the OpenAPI | finding; OpenAPI saveFollowUp | AC-1 | in-item | Steps 3, 7 |
| One new fixed sentence in `texts.py`, matched by a fixture entry, counted | AEA-03 tests `test_every_sentence_matches_its_source_fixture`, `test_fixture_quotes_its_source_files`, `test_text_id_shape_and_named_ids` | AC-2 | in-item | Steps 1, 2 |
| Plain, no-promise style; no "sent"; no time promise; no "I'm sorry" | SCREEN_SPECS line 161; R-34; `test_forbidden_phrases_absent`, `test_promise_texts_word_for_word` (time-promise regex), `test_timeout_and_busy_sentences` | AC-2, AC-4 | in-item | Step 1 wording, Step 4 test |
| Phone on record unchanged, byte for byte | item text ("no other follow-up combination changes") | AC-3 | in-item | Step 3, Step 4 `test_other_combinations_unchanged` |
| Email on record and phone general unchanged (still raise) | item text | AC-3 | in-item. Their wording is a **separate follow-up** (Risks R-1) | Step 3 |
| Unverified customer can save general only; `on_record` refusal unchanged | R-27; web.md line 349 | AC-3 | in-item (unchanged code path) | Step 3 |
| No contact value in the returned or stored follow-up | R-27; AEA-29 AC-12/AC-13 | AC-4 | added (plan-added test) | Step 4 |
| Stored row and case event written for the new branch | cases.md §5a; integrated-journeys §3 rule 2 ("a 2xx alone proves nothing") | AC-1 | added | Step 4 `test_wp7_email_general_saved` |
| Wording recorded as provisional | item text | AC-5 | in-item | Steps 1, 5, 6 |
| data.md §2, cases.md O-15 and area map updated | context-maintenance rule 1 | AC-5 | added | Step 6 |
| `CaseService.set_followup` docstring in `services/cases.py` line 549 still says "only the phone on record is built so far" | — | — | other-owner. Not in this item's exception (Risks R-3) | integrator |

## Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None (`saveFollowUp` already exists; only its service branch changes) | — | — | — |

## Acceptance criteria

- **AC-1 [journey]**, level `integrated with a scripted model` (API level, AEA-59 runner: real app on a first-boot DB copy, guards on, no model reached).
  - The criterion: `tests/contract/test_openapi_server.py::test_success_matches_contract[saveFollowUp/email_general]` passes, with the real response validated by `assert_response_matches` against the OpenAPI.
  - *Blocked by AEA-51 on main.* Without it the drive skips with `not bound: reply_composer`. The implementer verifies it on a local, uncommitted merge of the AEA-51 branch (Step 7). The wave-merge `CONTRACT_STRICT=1` run re-checks it.
  - Stored effect: `test_wp7_email_general_saved` (service level, `mock-tested`) proves the `followups` row and the `followup_saved` case event.
- **AC-2** `TextId.FOLLOWUP_SAVED_EMAIL_GENERAL = "followup.saved_email_general"` exists with template `"Follow-up saved: email, {window}."`, a fixture entry of kind `proposal`, and `EXPECTED_COUNTS["followup"] == 4` (78 texts in total).
  - Verify: `uv run pytest tests/unit/policy/test_texts.py -q`, all green.
- **AC-3** No other follow-up combination changes:
  - phone on record still returns "Follow-up saved: phone call, the number ending in 02, mornings." with label "the number ending in 02";
  - email on record and phone general still raise `NotImplementedError`;
  - the refusals `no_open_case` and `not_verified` are unchanged.
  - Verify: `tests/services/test_followup_text.py::test_other_combinations_unchanged` and `::test_email_general_no_open_case_refused`, plus the frozen `tests/services/test_cases.py::test_set_followup_rules` (unchanged, green).
- **AC-4 (plan-added)** The email/general result and stored row hold no phone, phone digits or email of the customer, and the saved line never says "sent".
  - Verify: `tests/services/test_followup_text.py::test_email_general_verified_customer_reads_no_contact`.
- **AC-5 (plan-added)** The wording is marked provisional pending the UX session in:
  - a comment in `texts.py`;
  - the journey record;
  - `docs/design/contracts/stage7/data.md` §2;
  - `docs/design/contracts/stage7/cases.md` §5a.
- **Fast gates:** `ruff check`, `ruff format --check` and `mypy` are clean.

**Worked pair (WP-7, follow-up leg, email/general).** This is AEA-42's example pair 2, `docs/plans/tickets/AEA-42.md` line 73, with the EMAIL_GENERAL body.
- **Input.** After WP-7's refund handoff, an unverified thread with an open case sends `PUT …/follow-up` with `{"channel": "email", "destination": "general", "window": "any"}`.
- **Output.**
  - Response: 200 with `followup = {"channel": "email", "destination_label": "a general contact", "on_record": false, "window": "any", "saved_line": "Follow-up saved: email, any time."}`.
  - Stored: one `followups` row with `channel="email"`, `destination="general"`, `on_record=False`, `window="any"` and the same label and line.
  - Case event: one `followup_saved` event with detail `{"channel": "email", "on_record": false, "window": "any"}`.
- **Tests.** Service level: `test_wp7_email_general_saved`. Through the app: AC-1.

## Boundary

**Owned files (the only files the implementer may create or edit):**

| File | Create / modify | Limit |
|---|---|---|
| `src/meridian/policy/texts.py` | modify | one `TextId` member and one `_TEXTS` entry, plus a comment |
| `tests/unit/policy/texts_source_fixture.json` | modify | one entry inserted |
| `tests/unit/policy/test_texts.py` | modify | `EXPECTED_COUNTS["followup"]` 3 → 4, plus one new test function at the end |
| `src/meridian/services/_case_actions.py` | modify | **function `set_followup_in` only** (lines 170–219). Nothing else in the file changes: not the imports, not `__all__`, not other functions |
| `tests/services/test_followup_text.py` | create | new test file |
| `docs/testing/journeys/2026-10-21-FU-saveFollowUp-text.md` | create | journey record |
| `docs/design/contracts/stage7/data.md` | modify | one header line and one §2 paragraph, both appended |
| `docs/design/contracts/stage7/cases.md` | modify | one bullet appended after the O-15 bullet (line 615); the O-15 bullet itself is not edited |
| `.claude/reference/area-map.md` | modify | row A0 only: one parenthetical extended (append-style) |

**Read only (never edit):**
- `src/meridian/services/cases.py`, `src/meridian/services/_case_rules.py` (`WINDOW_WORD`), `src/meridian/domain/views.py`, `src/meridian/domain/common.py`, `src/meridian/adapters/sqlite/rows.py`, `src/meridian/web/routes/handoff.py`;
- `tests/services/_case_fixtures.py`, `tests/services/person_request_support.py`, `tests/services/test_cases.py` (AEA-29 frozen tests), `tests/api/openapi_check.py`, `tests/contract/**`, `tests/journeys/**`.

**Forbidden:** the briefing, issued data, `docs/archive/`, `docs/parked/`, `docs/ux/**`, `apps/web/**`, `ui-contracts.openapi.yaml`, `UI_CONTRACTS.md`, `.env` files. Do not bind ports 4019 or 5184.

**Other slices:** AEA-51 (branch `aea-51-aea-51-customer-path`) touches `.claude/reference/area-map.md` (one line) and `tests/contract/test_model_ports_contract.py`, and none of the code files here. AEA-40 (branch `aea-40-aea-40-sessions-turns`) touches none of the owned files.

## Shared code to use (copied from main `9d12b8f`)

```python
# src/meridian/policy/texts.py
PLACEHOLDERS: Final[frozenset[str]] = frozenset(
    {"case_ref", "due_label", "window", "digits", "rep_name", "n", "amount"}
)
class TextId(StrEnum): ...                 # "<group>.<name>"
def render(text_id: TextId, /, **values: str) -> str: ...
# import-time guard: if set(_TEXTS) != set(TextId): raise RuntimeError(...)

# src/meridian/services/_case_rules.py line 147
WINDOW_WORD: Final[Mapping[str, str]] = MappingProxyType(
    {"morning": "mornings", "afternoon": "afternoons", "any": "any time"}
)

# src/meridian/domain/views.py line 313
class FollowUpChoice(MeridianModel):
    channel: Literal["email", "phone"]
    destination: Literal["on_record", "general"]
    window: Literal["morning", "afternoon", "any"]

# src/meridian/domain/common.py line 321
class FollowUp(MeridianModel):
    channel: Literal["email", "phone"]
    destination_label: str
    on_record: bool
    window: Literal["morning", "afternoon", "any"]
    saved_line: str

# src/meridian/adapters/sqlite/rows.py line 364
class FollowupRow(MeridianModel):
    case_ref: CaseRef
    thread_id: ThreadId
    channel: Literal["email", "phone"]
    destination_label: str
    destination: str | None = None  # raw destination for staff; never in a log
    on_record: bool
    window: Literal["morning", "afternoon", "any"]
    saved_line: str
    updated_at: datetime

# src/meridian/services/cases.py line 546 (calls set_followup_in; commits only a non-rejection)
def set_followup(self, thread_id: ThreadId, choice: FollowUpChoice, now: dt.datetime) -> FollowUp | CaseActionRejected

# tests/services/_case_fixtures.py
NOW = WORKED_PAIRS_NOW
OMAR = _CUSTOMER.validate_python("MHC-10002")
def store() -> Any                                       # context manager over temp_sqlite(); s.uow(write=True)
def services(uow, *, guidance_map=None, handoff_block=None) -> tuple[CaseService, HandoffService, BriefAssembler, StaffingDemo]
def followup_choice(channel: str, destination: str, window: str) -> FollowUpChoice
def new_thread(tx, *, customer_text: str | None = None, at=NOW, run_tag="live") -> tuple[ThreadId, int]
def set_identity(tx, thread, status: str, customer: CustomerId | None = None) -> None
def request(thread, reason: HandoffReason, *, priority=None, ..., verified_customer=...)  # used as request(t, HandoffReason.REFUND) and request(t, reason, verified_customer=OMAR)
def ctx(thread, turn, now=NOW) -> TurnContext
def contact_of(tx, customer=OMAR) -> tuple[str, str, str]   # (phone, phone digits only, email), from issued data
def is_rejected(result) -> bool; def code_of(result) -> str; def j(model) -> Any; def jtext(model) -> str

# tests/api/openapi_check.py
def load_document() -> Mapping[str, Any]     # the parsed OpenAPI; components/schemas/FollowUpView has no $ref
```

Repository reads used in tests (from `tests/services/test_cases.py`):
- `tx.cases.followups.get(case_ref) -> FollowupRow | None`
- `tx.cases.case_events.list_for_case(case_ref)` returns rows with `.kind` and `.detail`.

The open-case pattern, copied from `tests/services/test_cases.py` lines 471–477 and 492–493:

```python
with s.uow(write=True) as tx:
    thread, _ = new_thread(tx, customer_text="Please call me back.")
    set_identity(tx, thread, "verified", OMAR)      # only for a verified thread
    tx.commit()
req = request(thread, HandoffReason.REFUND, verified_customer=OMAR)   # unverified: request(thread, HandoffReason.REFUND)
case = handoff.open(req, ctx(thread, req.turn_id)).case               # case.case_ref
```

## File map

| File | Current | Change |
|---|---|---|
| `src/meridian/policy/texts.py` | 336 lines, 77 texts | +1 member, +1 entry, +1 comment → 78 texts |
| `tests/unit/policy/texts_source_fixture.json` | 945 lines | +1 entry (about 17 lines) after `followup.saved_phone` |
| `tests/unit/policy/test_texts.py` | 357 lines | count 3 → 4; +1 test (about 15 lines) |
| `src/meridian/services/_case_actions.py` | 299 lines | `set_followup_in` restructured (about +6 lines) |
| `tests/services/test_followup_text.py` | — | new, about 150 lines (`test_cases.py` is 926 lines and frozen, so it is not extended) |
| `docs/testing/journeys/2026-10-21-FU-saveFollowUp-text.md` | — | new |
| `docs/design/contracts/stage7/data.md`, `.../cases.md`, `.claude/reference/area-map.md` | — | append-only lines |

## Steps

**Step 0: worktree.** Work in your own worktree and branch from main `9d12b8f`. Run `export UV_LINK_MODE=hardlink`. Never copy a venv; no `node_modules`. Import check only, no baseline suite:

```bash
uv run python -c "import meridian.services.cases, meridian.policy.texts"
```

**Step 1: the text (`src/meridian/policy/texts.py`).**
1. In `class TextId`, directly after `FOLLOWUP_SAVED_PHONE = "followup.saved_phone"` (line 72), add:
   ```python
       FOLLOWUP_SAVED_EMAIL_GENERAL = "followup.saved_email_general"
   ```
2. In `_TEXTS`, directly after the `TextId.FOLLOWUP_SAVED_PHONE: …` entry (line 201), add exactly:
   ```python
       # Provisional wording pending the UX session (FU-saveFollowUp-text): the saved line's shape with no destination,
       # because a general destination holds no address.
       TextId.FOLLOWUP_SAVED_EMAIL_GENERAL: "Follow-up saved: email, {window}.",
   ```
3. Change nothing else in the file. Not the docstring, not `PLACEHOLDERS` (`window` is already in it), not `render`.

Invariant: the import-time check `set(_TEXTS) == set(TextId)` holds, and the only placeholder is `window`.

**Step 2: fixture and counts.**

1. In `tests/unit/policy/texts_source_fixture.json`, insert this entry between the `followup.saved_phone` entry (it ends at line 404 with `},`) and the `followup.recorded_not_sent` entry. Use 2-space indentation, matching the file. Keep the trailing comma, because another entry follows:

   ```json
       {
         "id": "followup.saved_email_general",
         "template": "Follow-up saved: email, {window}.",
         "source": {
           "kind": "proposal",
           "file": "docs/testing/journeys/2026-10-21-FU-saveFollowUp-text.md",
           "line": 5,
           "where": "FU-saveFollowUp-text provisional wording pending the UX session: SCR-1 saved-line shape with no destination (R-27), as AEA-42's CaseService double returns"
         },
         "example": {
           "values": {
             "window": "any time"
           },
           "rendered": "Follow-up saved: email, any time."
         }
       },
   ```

   Do not change the file's header (`schema`, `copied_at`).

2. In `tests/unit/policy/test_texts.py`, change `"followup": 3,` to `"followup": 4,` in `EXPECTED_COUNTS` (line 45).

3. Append this test at the end of the same file:

   ```python
   def test_followup_saved_email_general_text() -> None:
       """FU-saveFollowUp-text: the email/general saved line (provisional wording), one placeholder, no send claim."""
       assert TextId.FOLLOWUP_SAVED_EMAIL_GENERAL.value == "followup.saved_email_general"
       assert TEXTS[TextId.FOLLOWUP_SAVED_EMAIL_GENERAL] == "Follow-up saved: email, {window}."
       assert render(TextId.FOLLOWUP_SAVED_EMAIL_GENERAL, window="any time") == "Follow-up saved: email, any time."
       assert render(TextId.FOLLOWUP_SAVED_EMAIL_GENERAL, window="mornings") == "Follow-up saved: email, mornings."
       with pytest.raises(TextRenderError) as extra:
           render(TextId.FOLLOWUP_SAVED_EMAIL_GENERAL, window="any time", digits="02")
       assert extra.value.placeholder == "digits"
       assert render(TextId.FOLLOWUP_SAVED_PHONE, digits="02", window="mornings") == (
           "Follow-up saved: phone call, the number ending in 02, mornings."
       )
   ```

4. Create the journey record (Step 5's content) **now**, because `test_fixture_quotes_its_source_files` reads it. Check that `grep -n "Follow-up saved: email, any time." docs/testing/journeys/2026-10-21-FU-saveFollowUp-text.md` prints line `5`. If it prints another number, set the fixture's `"line"` to that number.

5. Run `uv run pytest tests/unit/policy/test_texts.py -q`. All tests must pass. These existing tests now also cover the new text:
   - `test_every_sentence_matches_its_source_fixture`
   - `test_fixture_quotes_its_source_files`
   - `test_text_id_shape_and_named_ids` (78 in total)
   - `test_promise_texts_word_for_word` (no "within" or "by …")
   - `test_forbidden_phrases_absent` (a `followup.*` text with no "sent")
   - `test_templates_use_known_placeholders_only`

**Step 3: the service branch (`src/meridian/services/_case_actions.py`, `set_followup_in` only).**

Replace the body of `set_followup_in` (lines 170–219) with the code below. The signature is unchanged. The upsert, the case event and the return statement are byte-identical to today; only the middle changes.

```python
def set_followup_in(
    tx: UnitOfWork, thread_id: ThreadId, choice: FollowUpChoice, now: dt.datetime
) -> FollowUp | CaseActionRejected:
    """Saves how and when the customer wants to be reached; phone on record and email general are built."""
    row = tx.cases.cases.get_for_thread_open(thread_id)
    if row is None:
        return rejected(ApiErrorCode.NOT_ALLOWED_IN_STATE, state="no_open_case")
    identity = tx.core.reads.identity_state(thread_id)
    on_record = choice.destination == "on_record"
    if on_record and identity.status != "verified":
        return rejected(ApiErrorCode.NOT_ALLOWED_IN_STATE, state="not_verified")
    if choice.channel == "email" and not on_record:
        # FU-saveFollowUp-text, provisional wording pending the UX session. No contact value is read or stored.
        label = "a general contact"
        saved = render(TextId.FOLLOWUP_SAVED_EMAIL_GENERAL, window=WINDOW_WORD[choice.window])
    elif choice.channel == "phone" and on_record:
        customer = tx.core.reads.customer(identity.customer_id) if identity.customer_id else None
        if customer is None:
            return rejected(ApiErrorCode.NOT_ALLOWED_IN_STATE, state="not_verified")
        digits = re.sub(r"[^0-9]", "", customer.phone)[-2:]
        label = f"the number ending in {digits}"
        saved = render(TextId.FOLLOWUP_SAVED_PHONE, digits=digits, window=WINDOW_WORD[choice.window])
    else:
        raise NotImplementedError(
            "follow-up text for email/on_record and phone/general: blocked-on a UX wording follow-up"
        )
    tx.cases.followups.upsert(
        FollowupRow(
            case_ref=row.case_ref,
            thread_id=thread_id,
            channel=choice.channel,
            destination_label=label,
            destination=choice.destination,
            on_record=on_record,
            window=choice.window,
            saved_line=saved,
            updated_at=now,
        )
    )
    tx.cases.case_events.append(
        CaseEventRow(
            case_ref=row.case_ref,
            kind="followup_saved",
            actor_role="system",
            detail={"channel": choice.channel, "on_record": on_record, "window": choice.window},
            at=now,
        )
    )
    return FollowUp(
        channel=choice.channel,
        destination_label=label,
        on_record=on_record,
        window=choice.window,
        saved_line=saved,
    )
```

What each part protects:
1. The order of the refusals (`no_open_case` first, then `not_verified` for `on_record`) is unchanged. This keeps AEA-29 AC-12 and the contract's 409 cases green.
2. The email/general branch never calls `tx.core.reads.customer`. That is why no phone, email or digits can enter the label, the line or the row (R-27, AC-4).
3. The phone-on-record branch is the old code moved under `elif`. Its output stays byte-identical (AC-3).
4. The `else` still raises: a stub fails loudly (workspace `async-safety.md` §1). Email on record and phone general are not silently given a made-up sentence.
5. `destination=choice.destination` stores `"general"` for the new branch, as the existing code stores `"on_record"`.

Imports are unchanged: `TextId`, `render`, `WINDOW_WORD` and `re` are already imported.

**Step 4: service tests (`tests/services/test_followup_text.py`, new).**

Module docstring:

> FU-saveFollowUp-text: `CaseService.set_followup` saves an email follow-up to a general destination.
> Labels: invariant, negative, regression. Level: mock-tested (real CaseService over a temp SQLite copy of the issued DB; no server, no model). Phone numbers and emails are read from the issued data at run time; none is written in this file.

Imports:
- `from __future__ import annotations`, `re`, `from typing import Any`, `jsonschema`, `pytest`;
- `from meridian.domain.handoff import HandoffReason`;
- `from tests.api.openapi_check import load_document`;
- from `tests.services._case_fixtures`: `NOW, OMAR, code_of, contact_of, ctx, followup_choice, is_rejected, j, jtext, new_thread, request, services, set_identity, store`.

Module constants:

```python
FOLLOW_UP_VIEW: dict[str, Any] = dict(load_document()["components"]["schemas"]["FollowUpView"])
SEND_CLAIM = re.compile(r"(?<!not )\bsent\b|sent you|emailed you|called you", re.IGNORECASE)
```

Helper:

```python
def _open_case(s: Any, handoff: Any, *, verified: bool) -> tuple[Any, Any]:
    with s.uow(write=True) as tx:
        thread, _ = new_thread(tx, customer_text="Please get back to me.")
        if verified:
            set_identity(tx, thread, "verified", OMAR)
        tx.commit()
    req = request(thread, HandoffReason.REFUND, verified_customer=OMAR) if verified else request(thread, HandoffReason.REFUND)
    return thread, handoff.open(req, ctx(thread, req.turn_id)).case
```

Wrap the long `req = …` line if ruff format asks.

Tests (exact names):

1. `test_wp7_email_general_saved()`. Label: invariant; this is the worked pair. With `store()` as `s`: `cases, handoff, _, _ = services(s.uow)`; open an **unverified** case; then `saved = cases.set_followup(thread, followup_choice("email", "general", "any"), NOW)`. Assert:
   - `not is_rejected(saved)`;
   - `j(saved) == {"channel": "email", "destination_label": "a general contact", "on_record": False, "window": "any", "saved_line": "Follow-up saved: email, any time."}`;
   - `jsonschema.validate(j(saved), FOLLOW_UP_VIEW)` raises nothing.

   Then in `with s.uow() as tx:` read `stored = tx.cases.followups.get(case.case_ref)` and `events = [e for e in tx.cases.case_events.list_for_case(case.case_ref) if e.kind == "followup_saved"]`. Assert:
   - `(stored.channel, stored.destination, stored.on_record, stored.window, stored.destination_label, stored.saved_line) == ("email", "general", False, "any", "a general contact", "Follow-up saved: email, any time.")`;
   - `len(events) == 1`;
   - `dict(events[0].detail) == {"channel": "email", "on_record": False, "window": "any"}`.

2. `test_email_general_window_words(window: str, word: str)`. Label: invariant. Parametrize `[("morning", "mornings"), ("afternoon", "afternoons"), ("any", "any time")]`. Unverified case, then assert `saved.saved_line == f"Follow-up saved: email, {word}."` and `saved.window == window`.

3. `test_email_general_verified_customer_reads_no_contact()`. Label: negative + security. Open a **verified** (OMAR) case and save email/general/morning. Assert:
   - `saved.saved_line == "Follow-up saved: email, mornings."`, `saved.on_record is False`, `saved.destination_label == "a general contact"`.
   - In a read `uow`: `phone, digits, email = contact_of(tx)` and `stored = tx.cases.followups.get(case.case_ref)`. For each blob in `(jtext(saved), stored.model_dump_json())`, assert `phone not in blob and digits not in blob and email not in blob`.
   - `not SEND_CLAIM.search(saved.saved_line)`.

4. `test_email_general_no_open_case_refused()`. Label: regression. A lone thread with no case: `refused = cases.set_followup(lone, followup_choice("email", "general", "any"), NOW)`. Assert:
   - `is_rejected(refused) and code_of(refused) == "NOT_ALLOWED_IN_STATE"`;
   - `j(refused)["details"] == {"state": "no_open_case"}`.

5. `test_other_combinations_unchanged()`. Label: regression; this guards "no other combination changes". Open a verified case.
   - `phone = cases.set_followup(thread, followup_choice("phone", "on_record", "morning"), NOW)`. Assert `phone.saved_line == "Follow-up saved: phone call, the number ending in 02, mornings."` and `phone.destination_label == "the number ending in 02"`.
   - For each of `("email", "on_record")` and `("phone", "general")`, use `with pytest.raises(NotImplementedError, match="blocked-on"):` around `cases.set_followup(thread, followup_choice(channel, destination, "any"), NOW)`.
   - Then the stored row is still the phone one: `stored.channel == "phone"` and `stored.saved_line` equals the phone line. The raising calls did not commit.
   - Give the test a docstring saying that whoever adds those two texts replaces the `pytest.raises` blocks.

Run: `uv run pytest tests/services/test_followup_text.py tests/services/test_cases.py -q`. All tests must pass. The frozen `test_set_followup_rules` must be unchanged and green.

**Step 5: journey record (`docs/testing/journeys/2026-10-21-FU-saveFollowUp-text.md`, new).**

Write it with exactly this layout. The wording bullet must be **line 5**.

```markdown
# Journey record — FU-saveFollowUp-text (email follow-up to a general destination)

Wording, **provisional pending the UX session** (Innocent 2026-10-21: "just do whatever you recommend"):

- `followup.saved_email_general`: "Follow-up saved: email, any time." (template `Follow-up saved: email, {window}.`; window words mornings, afternoons, any time)
- Destination label for an email to a general destination: "a general contact".
- Basis: SCREEN_SPECS SCR-1's saved line ("Follow-up saved: phone call, the number ending in 02, mornings.", R-27) with the destination left out, because a general destination holds no address. These are the same words AEA-42's CaseService double already returns. Plain, no promise, and nothing says a message was sent (R-34). Email on record and phone to a general destination are still unbuilt (they raise); their wording is a separate follow-up.

| Field | Value |
|---|---|
| Claim | FU-saveFollowUp-text: `saveFollowUp` with EMAIL_GENERAL (`email`, `general`, `any`) returns 200 with `saved_line` "Follow-up saved: email, any time." and stores the `followups` row and one `followup_saved` event. Journey: **J-7** follow-up leg (CON-5) |
| Level | <fill in: see Step 7> |
| Tested revision | <branch SHA>; for AC-1 also "+ aea-51-aea-51-customer-path <SHA> merged locally, uncommitted" |
| Environment | your worktree; `uv run`; service tests: temp SQLite copy of the issued DB, no server, no model; AC-1: AEA-59 runner `real_app` (first-boot DB copy, guards on, no model reached) |
| Command | `uv run pytest tests/unit/policy/test_texts.py tests/services/test_followup_text.py -q`; `uv run pytest "tests/contract/test_openapi_server.py::test_success_matches_contract[saveFollowUp/email_general]" "tests/contract/test_openapi_server.py::test_success_matches_contract[saveFollowUp/phone_mornings]" -q -rs`; `uv run python -m tests.journeys.affected --base main` |
| Result | <real counts> |
| Evidence location | this record; the implementer's report |
| Remaining limitations | Wording provisional (UX session). Email on record and phone general still raise `NotImplementedError` (500). No browser leg |
| Blocked by | AEA-51 (binds `reply_composer`; on main the contract drive skips with `not bound: reply_composer`) |
```

**Step 6: design records (append-only).**

1. `docs/design/contracts/stage7/data.md`: after line 11 (the `**AEA-03b (2026-10-21):** …` header line), add:

   `**FU-saveFollowUp-text (2026-10-21):** §2 gains `TextId.FOLLOWUP_SAVED_EMAIL_GENERAL` (provisional wording, 78 texts).`

   After the AEA-03b paragraph in §2 (the one ending "…the row never holds the code or the details.", about line 119), add one paragraph with a blank line on each side:

   `Text added by FU-saveFollowUp-text (wave fix, AEA-51 finding; Innocent 2026-10-21): `TextId.FOLLOWUP_SAVED_EMAIL_GENERAL = "followup.saved_email_general"`, "Follow-up saved: email, {window}.", the saved line for an email follow-up to a general destination (CON-5 EMAIL_GENERAL). Provisional wording pending the UX session. Its destination label is "a general contact"; the branch reads no contact value.`

2. `docs/design/contracts/stage7/cases.md`: directly after the O-15 bullet (line 615), add:

   `- **Changed by FU-saveFollowUp-text (2026-10-21):** email to a general destination is built: `saved_line` from `TextId.FOLLOWUP_SAVED_EMAIL_GENERAL` ("Follow-up saved: email, any time.", provisional pending the UX session), `destination_label` "a general contact", no contact value read. Email on record and phone to a general destination still raise `NotImplementedError` (O-15 stands for those two). [Decided 2026-10-21, Innocent; FU-saveFollowUp-text plan]`

3. `.claude/reference/area-map.md`, row A0: in the text `AEA-03b adds the `history` group, 2 texts, total 77)`, replace `total 77)` with:

   `total 77; FU-saveFollowUp-text adds `followup.saved_email_general`, provisional wording, total 78)`

   Change nothing else in the row.

**Step 7: fast gates, affected tests and journeys, then commit. Run cheapest first and stop at the first red.**

1. `uv run ruff check src tests` and `uv run ruff format --check src tests`.
2. `uv run mypy`. It uses `[tool.mypy] files = ["src/meridian", "tests", "eval"]`, strict; do not narrow it.
3. Affected tests (see *Checks* for the list).
4. Affected journeys: `uv run python -m tests.journeys.affected --base main`. Copy its summary into the record.
5. The contract drive on the branch: `uv run pytest "tests/contract/test_openapi_server.py::test_success_matches_contract[saveFollowUp/email_general]" -q -rs`. Expected on main's base: **skipped**, `not bound: reply_composer`.
6. Commit 1:
   - Stage exactly these paths: `git add src/meridian/policy/texts.py tests/unit/policy/texts_source_fixture.json tests/unit/policy/test_texts.py src/meridian/services/_case_actions.py tests/services/test_followup_text.py docs/testing/journeys/2026-10-21-FU-saveFollowUp-text.md docs/design/contracts/stage7/data.md docs/design/contracts/stage7/cases.md .claude/reference/area-map.md`
   - Message: `fix(FU-saveFollowUp-text): email follow-up to a general destination saves (provisional wording)`.
   - Body: one line saying the wording is provisional pending the UX session, and that email on record and phone general still raise.
   - Last line: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
7. AC-1 on a local, **uncommitted** merge with AEA-51:
   1. `git status --porcelain` must be empty.
   2. `git merge --no-commit --no-ff aea-51-aea-51-customer-path`.
      - If it reports conflicts, run `git merge --abort` and record AC-1 as "not run: merge conflict with AEA-51; blocked by AEA-51", at level `mock-tested`.
   3. If the merge is clean, run the two saveFollowUp success drives (Step 5's second command). Both must **pass**.
   4. **Always** run `git merge --abort` afterwards. Confirm `git rev-parse HEAD` equals commit 1 and `git status --porcelain` is empty. **Never commit while the merge is in progress.**
8. Fill the record's *Level*, *Tested revision* and *Result* rows:
   - Level `integrated with a scripted model` if step 7 passed; otherwise `mock-tested`, with *Blocked by* AEA-51.
   - Then commit 2: `git add docs/testing/journeys/2026-10-21-FU-saveFollowUp-text.md` with message `docs(FU-saveFollowUp-text): journey record results`, and the same `Co-Authored-By` last line.
   - Do not move line 5.
9. Do not push. Only the merge step pushes main. Never force-push.

## Data and fixtures

Synthetic and issued data only:
- the temp SQLite copy of the issued DB, through `store()` → `temp_sqlite()`;
- customer MHC-10002 (`OMAR`);
- `NOW = WORKED_PAIRS_NOW`.

No phone number, email, verification code or card-like number is written in any test, log or record. `contact_of` reads them at run time only so the test can assert they are absent. The new fixture entry's example values are `{"window": "any time"}`. There are no paid model calls: the contract runner reaches no model.

## Checks and evidence

| Check | Command | Passing looks like |
|---|---|---|
| Texts | `uv run pytest tests/unit/policy/test_texts.py -q` | all passed, including `test_followup_saved_email_general_text` |
| Service | `uv run pytest tests/services/test_followup_text.py -q` | 7 passed (5 functions; one is parametrized 3 ways) |
| Lint and format | `uv run ruff check src tests` and `uv run ruff format --check src tests` | clean |
| Type check | `uv run mypy` | 0 errors |
| Affected tests (every test file importing `meridian.policy.texts`, `meridian.services.cases` or `_case_actions`; `grep -rl` at `9d12b8f`), serial, or `-n 2` at most | `uv run pytest tests/unit/policy tests/unit/services tests/unit/test_import_direction.py tests/unit/agent/nodes/test_compose.py tests/unit/agent/nodes/test_compose_blocks.py tests/unit/web/test_register_cases.py tests/services/test_followup_text.py tests/services/test_cases.py tests/services/test_cases_contract.py tests/services/test_handoff.py tests/services/test_demo.py tests/services/test_reset.py tests/services/test_scheduling.py tests/services/test_session.py tests/services/test_person_request.py tests/api/test_chat.py tests/api/test_demo_flows.py tests/api/test_demo_routes.py tests/api/test_staff_cases_refusals.py tests/api/test_handoff_routes.py tests/api/test_contract_cases_handoff.py tests/integration/test_staff_cases.py tests/integration/test_staff_composition.py tests/integration/test_staff_streams.py tests/deploy/test_agent_version.py tests/contract/test_openapi_server.py -q -rs` | 0 failed; skips only with their stated `not bound:` / blocked-on reasons |
| Affected journeys | `uv run python -m tests.journeys.affected --base main` | exit 0; 0 failed (skips blocked on AEA-51 and others are expected) |
| AC-1 (integrated) | Step 7.7 (local uncommitted merge with AEA-51) | `saveFollowUp/email_general` and `saveFollowUp/phone_mornings` pass |

**No full suite.** The change is additive: one enum member and one dict entry, checked at import time by any importer, plus one service branch. It touches no `conftest.py`, settings, dependency or lockfile, and no seam across packages. The pre-deploy full suite covers it later.

## Risks and requests

- **R-1 (follow-up for the integrator; not this item).** Email on record and phone to a general destination still raise `NotImplementedError`, which becomes a 500 once AEA-51 binds the route. Both are reachable from the real UI:
  - `compose.py` `_GENERAL_FOLLOWUP` offers "Phone call" with `on_record=False`, which sends phone/general;
  - SCREEN_SPECS line 154 offers "Email · the address on your account" to a verified customer, which sends email/on_record.

  No contract case drives them today, so the contract run stays green. Recommended next wave-fix, provisional, same style:
  - phone/general: `"Follow-up saved: phone call, {window}."`, which matches the AEA-42 double;
  - email/on_record: `"Follow-up saved: email, the address on your account, {window}."`, the UX option label;

  each with one `TextId` and a fixture entry. This item does not do it, because its acceptance says "no other follow-up combination changes".
- **R-2.** The destination label "a general contact" lives inline in `set_followup_in`, as the phone label does. It is shown to staff in SCR-6's PromiseCard as "a general contact [Not on record]". If the UX session changes it, it changes there, not in `texts.py`.
- **R-3 (stale docstring, not owned).** `src/meridian/services/cases.py` line 549, `CaseService.set_followup`, says "only the phone on record is built so far". The exception covers `_case_actions.set_followup_in` only. The integrator or the next `cases.py` change should update it to "phone on record and email general are built".
- **R-4 (collision).** `.claude/reference/area-map.md` is also changed by AEA-51 (another line). This is append-style: keep both sides on conflict. No other owned file overlaps an open branch (checked against `aea-51-aea-51-customer-path` and `aea-40-aea-40-sessions-turns`).
- **R-5.** AC-1 cannot pass on main alone (the drive skips). Its integrated evidence depends on the local AEA-51 merge in Step 7.7 and on the wave-merge `CONTRACT_STRICT=1` run.
- **No signed-contract change.** `FollowUpView.saved_line` and `destination_label` are free strings, and the OpenAPI has no 200 example body for EMAIL_GENERAL. Nothing in `docs/ux/**` or the OpenAPI is edited.

## What the implementer must not do

- Do not edit anything in `_case_actions.py` outside `set_followup_in`.
- Do not edit `test_cases.py` (frozen), `person_request_support.py`, `_case_fixtures.py`, any `tests/contract/**` or `tests/journeys/**` file, `cases.py`, `docs/ux/**`, `apps/web/**`, the OpenAPI or `UI_CONTRACTS.md`.
- Do not add a placeholder to `PLACEHOLDERS`. Do not add texts for email on record or phone general.
- Do not put "sent", "within", "by <day>", "I'm sorry", "shortly" or any promise in the sentence.
- Do not commit during the temporary AEA-51 merge. Do not `git add -A`. Do not push or force-push. Do not run the full suite.

## Gates

None. No human, paid or live gate.

## Readiness

**READY.** Every decision is made: the wording, the label, the scope (email/general only) and the file placement. Nothing is blocked for the build. AC-1's integrated evidence needs AEA-51's branch, merged only locally and uncommitted, for verification.
