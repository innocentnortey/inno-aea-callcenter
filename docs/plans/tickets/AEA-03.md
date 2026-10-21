## [AEA-03] foundation: every fixed customer sentence

_Conventions for every inno-aea-callcenter issue (from the approved breakdown, `docs/plans/slice-plan.md`):_
repository `/home/linuxuser/workspaces/inno-aea-callcenter` (package `src/meridian/`, tests `tests/`, eval `eval/`); GitLab
`innocentnortey/inno-aea-callcenter`. Read first: `CLAUDE.md`, `.claude/README.md`, `.claude/reference/area-map.md`, the
slice plan's row for this issue, `docs/design/code-design.md` (DO-3) and `docs/design/contracts/internal-components.md`
(DO-4: exact types and signatures). Vocabulary: PRD R-n, US-n, WP-n, HP-n, WF-n, CAP-n, E-n, M-n, CON-n as their owner
documents define them. Workflow: `lane::build-loop` issues run plan (`fanout-planner`, plan meets
`to-tickets/templates/implementation-plan.md`) → implement (`fanout-implementer`) → test → `code-review-agent`; affected tests
only (`.claude/rules/build-loop-test-scope.md`); `risk::security` issues get frozen failing tests first and the security
agent at their wave merge. **Siblings in the same or a later wave are called through their DO-4 signature by injection
(constructor, `GraphDeps`, or `web/deps.py`) and tested with a double; a plan that needs more than that signature records
`blocked-on AEA-NN` instead of inventing behaviour.** Never: edit the briefing, issued data or `docs/archive/`; edit
`docs/ux/03-structure/ui-contracts.openapi.yaml` or `UI_CONTRACTS.md` (a needed change stops the issue and goes to
Innocent); touch `apps/web/**` or `docs/ux/**`; edit another issue's owned file (collision map, slice plan §3); put a
secret, verification code, card-like number or full phone number in code, logs, traces, fixtures or test names; call a
paid model in a default test (mark `live`); bind ports 4019 or 5184; `git add -A`. Evidence: every criterion names its
test or command and the result a reviewer should see; numbers come from runs, never from targets.

### What to build

> As a **homeowner**, I need the chat to say plainly that it is Meridian's automated assistant and to show the date it
> is working from, so that I never think I'm talking to a person and every "tomorrow" or "Friday" means what I think it
> means. (US-1; also US-3, US-25)

**Example pair (WP-5).** Input: "My carbon monoxide detector is going off." Expected output, the first text of the reply,
built by code from this module: "Leave the home immediately and call 911 or your gas utility from outside." then
"Don't flip switches, open windows near the furnace, or restart equipment." (SCREEN_SPECS SCR-1 copy notes, Meridian's
words from `policies/escalation_and_safety.md` with "their" → "your"), then "Once you're outside and safe, you can leave a
number here if you'd like." No follow-up time anywhere (R-6, R-26). WP-5's own text words the second line slightly
differently; UX owns customer copy (api-con-mapping UXR-18), so this module follows SCREEN_SPECS, and the eval's
`must_say` items quote the same SCREEN_SPECS wording (**settled, DAT-6**).

`policy/texts.py` (stage7/data.md §2): every fixed sentence the backend sends to a customer, word for word, behind
`render(text_id: TextId, /, **values: str) -> str`. Standard library only (DO-3 §4.1 "depends on: none").

- **`TextId`** is a `StrEnum` whose values are `"<group>.<name>"`, with the groups `greeting`, `safety`, `identity`,
  `promise`, `fee_change`, `followup`, `booking`, `limits`, `live`, `demo` (data.md §2). Named ids fixed by other
  contracts keep their spelling: `TextId.INBOX_CODE_BODY = "identity.inbox_code_body"`,
  `TextId.INBOX_CODE_GONE = "identity.inbox_code_gone"`, `booking.urgent_note` (data.md §2; graph-nodes §6).
- **`render`** substitutes named placeholders only: `case_ref`, `due_label`, `window`, `digits`, `rep_name`, `n`,
  `amount` (data.md §2; `amount` added by R-W-7: the fee line's dollar figure, already formatted). An unknown id, a missing placeholder or an extra one raises **`TextRenderError(KeyError)`**, whose
  `text_id` and `placeholder` attributes hold names only, never a supplied value.
- **`format_usd(cents: int) -> str`** (data.md §2, R-W-7): the one money formatter for customer text: whole dollars
  without decimals ("$89", "$129"), otherwise two decimals ("$12.50"), thousands separated ("$1,250"); `ValueError` for a
  negative amount. The fee line is `render(<booking fee text>, amount=format_usd(row cents))` (cases.md §2
  `FeeNote.line`), so no amount is typed into a sentence and `render` itself never formats numbers.
- **"Fixed"** means a sentence code sends: in a CON-2 block, a notice, an error block, a CON-3 or CON-21 event line, a
  CON-4 handoff block, a CON-6 inbox body, or the CON-1 greeting. A label or hint the React app renders on its own is
  not in scope; when in doubt, the sentence is in scope if an OpenAPI response field carries it.

The groups, each with its word source (SCREEN_SPECS SCR-1/SCR-2 copy notes unless another is named):

- **`greeting` (R-1):** the SCR-1 greeting (CON-1 `greeting_text`, staff.md §12); the "Are you a person?" answer (marked
  proposal in SCREEN_SPECS).
- **`safety` (R-5…R-8):** the DANGER card lines and the quiet contact line; the burning-smell question; the WARNING
  conditional card and the emergency-number line with **(512) 555-0199 (demo number)**; the emergency-line card sentence;
  the three urgency questions.
- **`identity` (R-15, R-16):** the code prompt ("…ending in {digits}…"); "Thanks, you're verified for this chat."; the
  code-wrong line ("That code doesn't match. {n} tries left."); code-expired; the one NOT_VERIFIED / locked sentence "I
  can't confirm your account here. A representative will help." (identical for every failure, R-16); the two CON-6 inbox
  bodies: `INBOX_CODE_BODY` "Your Meridian Home Comfort verification code is {digits}. It expires in 10 minutes." (SCR-2)
  and `INBOX_CODE_GONE` "This code is no longer shown. Ask the chat for a new code if you need one." (proposal wording;
  data.md §2, DAT-29 (f); graph-tools C-5).
- **`promise` (R-26), word for word, the strings `PROMISE_TABLE` imports (cases.md §3.2):** `R26.unstaffed` (with
  `{due_label}` and `{case_ref}`); `R26.refund` "A representative will get to your refund request within 2 business
  days." and its extra line "I can't promise an outcome."; `R26.staffed` "A representative will join this chat when
  available. You can keep chatting with me while you wait, if you like."; `OD4.danger_review` "No representative is
  online right now, so someone will review this online request within 1 business day. That is not the wait for
  emergency help; for that, please use the emergency line." (SCREEN_SPECS line 147; cases A-11). `R26.safety_none` has
  no text ("").
- **`fee_change` (R-21, R-26):** "The $49 fee applies under current policy."; "Your original appointment stays until a
  representative confirms."; the can't-guarantee line with `{window}`; the phone-support line (cases A-11).
- **`followup` (R-27, R-34):** the legend, the saved line, "Demo: recorded, not sent" (cases A-11).
- **`booking`:** booked, slot taken, out of area, no window fits, identity-needed-before-write, fee-free cancel (only after
  a write); the fee lines the OpenAPI `fee_line` examples carry ("Standard diagnostic fee: $89", "There's no fee.";
  OpenAPI `ConfirmationBlock`, cases.md §2 `FeeNote.line`; the amount through the `amount` placeholder and
  `format_usd`, R-W-7, R-G-7); `booking.urgent_note`, the urgency mark
  on the burning-ruled-out booking (graph-nodes §6; DAT-29 (b)); the R-44 quick-checks `offer_text` (graph-nodes §8).
- **`limits`:** TURN_TIMEOUT "This is taking longer than it should." (UXR-18; not DO-1's "I'm sorry, …", code-design
  C-13); BUSY "A lot of people are chatting right now, so I can't take this message. A person can pick it up." (UXR-26,
  adopted in UI_CONTRACTS); RATE_LIMITED, BOOKING_CAP, SPEND_CAP_REACHED notices (web.md §9); "I don't have that
  information."; the two-misses failure offer; the card-not-taken reply (R-13).
- **`live`:** the four OpenAPI event lines, `{name}` written as the `rep_name` placeholder: "{rep_name} (demo
  representative) has joined.", "The assistant is paused while {rep_name} is here.", "{rep_name} handed the chat back to
  the automated assistant.", "{rep_name} closed this chat." (OpenAPI `EvRepresentativeJoined`, `EvAiPaused`,
  `EvAiResumed`, `EvChatClosed`; data.md §2, DAT-29 (a); staff.md §5); and `TextId.PERSON_REQUEST_LABEL =
  "live.person_request_label"`, "Talk to a person" (SCR-1's button label, as the greeting quotes it), the customer line a
  reloaded thread shows for a CON-4 request (data.md §2; web.md §14; R-W-6; AEA-40's `thread()` renders it).
- **`demo`:** shift ended, staffing changed, the staffing banner, demo reset; the CON-17 and CON-19 decision lines
  (cases A-11).

`PROMISE_TABLE` (which reason gets which promise) and the due rule are AEA-14's; this module holds the sentences they
point at, and AEA-14 imports them, never retypes them (cases.md §3.2).

**Resolved (residual pass 2026-10-21):** the fee-amount placeholder is `amount`, filled by `format_usd` (data.md §2,
R-W-7; R-G-7). The fee-line texts are written now; nothing waits.

### Source

- stage7/data.md §2 (`TextId`, `TextRenderError`, `render`, `amount`, `format_usd`, `PERSON_REQUEST_LABEL`, the named
  texts other topics asked for); decision ledger data DAT-6, DAT-29; residual rulings
  `docs/plans/7b-decisions/residuals-web.md` R-W-6, R-W-7 and `residuals-graph.md` R-G-7; stage7/cases.md §2
  (`FeeNote.line`); stage7/web.md §14 (history rebuild)
- Journey map: slice plan §0a; `.claude/rules/integrated-journeys.md`; `docs/plans/ux-join/backend-amendments.md` §3
- stage7/cases.md §3.2 (`PROMISE_TABLE` rows and the `OD4.danger_review` text), A-11; stage7/graph-nodes.md §6
  (`booking.urgent_note`), §8 (quick-checks `offer_text`); stage7/graph-tools.md §5, C-5 (inbox bodies);
  stage7/graph-core.md §14 (`VisitChange.fee_line`); stage7/staff.md §5 (live event lines), §12
  (`greeting_text`); stage7/web.md §9 (notices)
- SCREEN_SPECS SCR-1 *Copy notes*, *Flow states* sentences, *Copy rules that apply on every screen*; SCR-2 copy notes;
  UI_CONTRACTS named-error table (BUSY row), UXR-18 and UXR-26 rows; OpenAPI `Ev*` event examples, `ConfirmationBlock`
  `fee_line` examples (all read-only); api-con-mapping §0 *Fixed texts*, §2.1 UXR-18, §2.2 UXR-26
- DO-3 §2.4 (`triggers.py` row: safety text moves here), §4.1 (`policy/texts.py`: depends on none), §10 C-13
- DO-4 §11 (failure → customer table)
- PRD R-1, R-5, R-6, R-7, R-8, R-13, R-15, R-16, R-21, R-26, R-27, R-34
- KB `policies/escalation_and_safety.md` (issued, read-only); worked pairs WP-5 *Wording note*
- Slice plan §1 row AEA-03, §3 row `policy/texts.py` (frozen after wave 0)
- **Brief check:** serves "failure handling must be clean (agent admits uncertainty and hands off rather than guessing)"
  — every promise, safety line and limit sentence is fixed text, never model text; touches nothing out of scope;
  weakens nothing → proceed.

### Acceptance criteria

- [ ] AC-1 [invariant] Every sentence in `policy/texts.py` equals its entry in a fixture copied from its word source (each entry cites its SCREEN_SPECS line, OpenAPI example or "proposal"), and every fixture entry has a `TextId` — verify: `tests/unit/policy/test_texts.py::test_every_sentence_matches_its_source_fixture` — evidence: one-to-one, no unmatched entry either side (UXR-18).
- [ ] AC-2 [invariant] Every `TextId` value is `"<group>.<name>"` with a group from data.md §2's ten, and the ids other contracts name exist with their exact spelling (`identity.inbox_code_body`, `identity.inbox_code_gone`, `booking.urgent_note`, the four `live` lines, and `live.person_request_label` rendering "Talk to a person", R-W-6) — verify: `tests/unit/policy/test_texts.py::test_text_id_shape_and_named_ids` — evidence: passes; the group → count table printed.
- [ ] AC-3 [invariant] The R-26 promise sentences and the `OD4.danger_review` line are present word for word, and no other sentence in the module promises a time — verify: `tests/unit/policy/test_texts.py::test_promise_texts_word_for_word` — evidence: the promise variants and the fee-bearing can't-guarantee line render exactly; a scan finds no other "within" / "by {time}" sentence.
- [ ] AC-4 [invariant] The safety lines use the KB's "immediately" and "your", and the conditional and emergency-line cards carry (512) 555-0199 marked as a demo number — verify: `tests/unit/policy/test_texts.py::test_safety_lines` — evidence: passes.
- [ ] AC-5 [invariant] TURN_TIMEOUT and BUSY are the UX sentences (C-13, UXR-26) — verify: `tests/unit/policy/test_texts.py::test_timeout_and_busy_sentences` — evidence: both equal the fixture; DO-1's "I'm sorry, …" variant is absent.
- [ ] AC-6 [negative] Forbidden phrases appear in no sentence: "charged" in any form (including "No fee has been charged"), "shortly", "an agent will be with you", a wait time or a queue position, and "sent" for a follow-up — verify: `tests/unit/policy/test_texts.py::test_forbidden_phrases_absent` — evidence: scan over every text id finds none.
- [ ] AC-7 [failure/refusal] `render` with an unknown text id, a missing placeholder or an extra placeholder raises `TextRenderError` — verify: `tests/unit/policy/test_texts.py::test_render_refuses_unknown_missing_and_extra` — evidence: all three raise; `text_id` and `placeholder` attributes set.
- [ ] AC-8 [negative] A `TextRenderError` names the text id and the placeholder name only, never a supplied value: a distinctive reference value and a distinctive six-digit value (assembled at run time) passed in are absent from the error's message and attributes — verify: `tests/unit/policy/test_texts.py::test_render_error_holds_no_values` — evidence: neither sentinel found.
- [ ] AC-9 [invariant] `policy/texts.py` imports nothing beyond the standard library (DO-3 §4.1) — verify: `tests/unit/test_import_direction.py::test_texts_imports_stdlib_only` — evidence: passes; the scan lists every import it saw.
- [ ] AC-10 [invariant] One money formatter and an `amount` placeholder (data.md §2, R-W-7): `format_usd(8900) == "$89"`, `format_usd(1250) == "$12.50"`, `format_usd(125000) == "$1,250"`, a negative amount raises `ValueError`; `render(<booking fee text>, amount="$89")` gives "Standard diagnostic fee: $89" (OpenAPI `ConfirmationBlock` `fee_line` example), with the dollar figure coming only from `amount` — verify: `tests/unit/policy/test_texts.py::test_format_usd_and_fee_line_amount` — evidence: passes; the rendered fee line printed.
- [ ] AC-11 [journey] Runs no journey yet: wave 0 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-03.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1 (the greeting), J-5 (the safety instruction), J-6 (the promise text) and J-9 (the notice texts) as the journeys that will exercise this code once AEA-57, AEA-51 and AEA-52 land, so the seam audit knows where to look — verify: the record — evidence: the record's Level, Blocked-by and journey fields.
- [ ] AC-12 [regression/context] Context updated in the same change — verify: diff — evidence: area-map A0 row notes `policy/texts.py` planned → actual with the commit; DO-3 §3 status line notes it built; the ICM row *Routes verified against code and tests* names this ticket's tests once they pass; any sentence that could not be placed (ambiguous scope or no word source) is listed in the plan as a report to the UX session, not written or edited.

### Observability

N/A — a constants module: no entry point, no record, no span. The promise text it holds is stored on `promise` rows by
AEA-29 and checked against the policy table at CAP-3 (AEA-51), which asserts "a promise text from the model" is absent;
a reviewer could argue the text is observed data, but the record that carries it is AEA-29's.

### Evaluation

- Checks: the E-1, E-5 and E-6 `must_say` items for safety text, promises and the fee line are code checks against
  fixed sentences (DO-5 *Scoring*); AEA-06's cases quote these same sentences (DAT-6).
- Expected-answer authority: the KB safety policy for the safety words; the R-26 policy table for promises; SCREEN_SPECS
  copy notes for wording (UX owns customer copy, UXR-18), with the OpenAPI examples for the event and fee lines
  SCREEN_SPECS does not word.

### Metrics

- References: M-10 (promise text consistency compares `promise.text` with the table sentence held here); M-14 (safety
  instruction first: the KB instruction held here).
- Acceptance conditions: the sentences equal the fixture (AC-1, AC-3, AC-4), so M-10 and M-14 stay computable as exact
  string equality; no target is computed here.

### Blocked by

None (slice plan wave 0).

### Agent handoff

- Area / owner: A0 Foundation (area map row A0).
- Contracts and shared surfaces: produces `TextId`, `render` and `TextRenderError` for AEA-14 (`PROMISE_TABLE` imports
  the promise strings), AEA-13 (fee line through `amount` and `format_usd`, R-W-7), AEA-21 (compose: notices, halt replies,
  quick-checks offer), AEA-27 (code prompt), AEA-29/30/31 (event lines: shift ended, staffing, demo reset), AEA-36
  (safety, burning, danger, `booking.urgent_note`), AEA-38 (reply fallback text), AEA-40 (greeting, BUSY, TURN_TIMEOUT,
  RATE_LIMITED, `PERSON_REQUEST_LABEL` for the history rebuild, R-W-6), AEA-43 (inbox bodies), AEA-45/46 (recorded-not-sent, live event lines); AEA-06 copies the same strings
  into `must_say` items (DAT-6); AEA-50 hashes this file into `agent_version` (data.md §7). Frozen after wave 0: a
  missing sentence is a small ticket merged before its dependants. Must not edit: `docs/ux/**`, the OpenAPI file,
  `UI_CONTRACTS.md`, the KB.
- Scope boundary / refusal: no sentence invented or reworded; a sentence its word source lacks is reported, not
  written; no promise mapping (AEA-14); no front-end labels (`PERSON_REQUEST_LABEL` is in scope because a
  `getChatThread` response field carries it, web.md §14).
- Wave and gates: wave 0, in parallel with the AEA-04 → AEA-02 → AEA-05 chain (R-G-18); gate: none (the fee-amount
  placeholder was resolved by R-W-7).
- Lane: build-loop — the app loads these strings and tests compare them (`ticket-lanes`).
- Risk: None (slice plan).
- Entry points added or changed: None.
