## [AEA-04] privacy: one redaction function, five profiles

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

> As a **homeowner** asking about my bill, I need to receive a one-time code at the phone or email on my account and
> type it in the chat, so that nobody else can read my account by guessing my name. (US-8; R-15, R-16)

**Example pair (WP-2, seeded MHC-10002 Omar Patel, INV-204411).** Input: the customer's free-text message "my name is
Omar Patel", the phone on record ending in 02, and, in a later turn, a message containing a card-like number. Expected
output, per profile: **JEV** — `[name]`, `[phone]`, `[customer id]`, `[invoice id]` in place of the name, the phone and
any `MHC-…` / `INV-…` ID, so the planner sees none of them; **SONNET** — the phone as `[phone ending 02]`, emails and
the street line masked, the name and `INV-204411` kept (the responder needs them, DAT-5); **TRACE** — `[name]`, the phone
as `[phone ending 02]` (the UI's "phone ending 02"), the invoice amounts ($89, $245, $144, $478.00) and the due date
2026-11-01 left as they are; **every profile but LOG** — the card-like number as `[card number removed]`, never stored,
sent or exported; **LOG** — no text at all, its length only.

`privacy/redact.py`, exactly as stage7/data.md §1 signs it. Standard library only (DO-3 §4.1; so `enum` / `dataclass`,
not pydantic):

- `RedactionKind(StrEnum)`: `card`, `code`, `phone`, `email`, `address`, `name`, `customer_id`, `invoice_id`, `free_text`
  (LOG only).
- `RedactionProfile(StrEnum)`: `store`, `sonnet`, `jev`, `trace`, `log` (names fixed by DO-3 §4.1 and DO-4 §12
  `RoleSpec.redaction`).
- `Redacted` (frozen dataclass): `text` (LOG: `""`), `replaced: Mapping[RedactionKind, int]` (counts, never a value),
  `length` (`len(input)`, the only thing LOG keeps); its `__repr__` shows counts and length only.
- `UnknownRedactionProfile(ValueError)`: its message names the profile value only, never the text.
- `redact(text: str, profile: RedactionProfile) -> Redacted`: pure and idempotent
  (`redact(redact(x, p).text, p).text == redact(x, p).text`, system design §10 "applied again at export").
- `Redactor = Callable[[str, RedactionProfile], Redacted]`, the type of `redact` that the gateway (DO-4 §12) and
  `LangfuseTraceSink` (models.md §4) take (merge-clashes MC-23). A one-profile consumer (staff.md §5 `redact_store`) is
  bound by the container as `lambda t: redact(t, RedactionProfile.STORE).text`, not here.

**What each profile replaces** (data.md §1; ✓ replaced, · left; LOG drops all text):

| Kind | STORE | SONNET | JEV | TRACE |
|---|---|---|---|---|
| card-like: 13–19 digits, spaces or dashes allowed, no checksum (DO-6; covers system design §10's "Luhn-shaped digit runs") | ✓ | ✓ | ✓ | ✓ |
| code: a standalone run of six digits (DO-6: never raw in any record) | ✓ | ✓ | ✓ | ✓ |
| phone | · | ✓ last two digits kept | ✓ | ✓ last two digits kept |
| email | · | ✓ | ✓ | ✓ |
| street address (the street line only; city and the five-digit ZIP stay) | · | ✓ | ✓ | ✓ |
| name, by introduction patterns (DAT-1) | · | · | ✓ | ✓ |
| `MHC-\d{5}`, `INV-\d{6}` | · | · | ✓ | · |

SONNET's contact row follows system design §3.2 and §10 *What each vendor sees* (**settled by source, DAT-5**); DO-4 §5's
comment "card-like numbers and codes masked" is the stale half (AEA-08 fixes the line). Account facts (amounts, dates,
windows, tier words, `MHC-C-` case references) are left by every profile except LOG.

**Placeholders** (data.md §1, DAT-28): one token per kind, the same on every call and turn (workspace rule
`context-management-multi-turn` 5), none of which matches a pattern again: `[card number removed]` (DO-6 step 1 wording),
`[code]`, `[phone]` (JEV), `[phone ending NN]` (SONNET, TRACE), `[email]`, `[address]`, `[name]`, `[customer id]`,
`[invoice id]`. AEA-35 AC-9 and AEA-51 CAP-1 assert on these tokens.

**Names** are found by introduction patterns only: "my name is …", "this is …", "I'm …" followed by capitalised words
(SP-1 build §5 `extract_name`), plus a street-address pattern (number, street name, suffix). These are in every option
of DAT-1, so they are built now; AC-2's name cases use introductions only until DAT-1 is answered.

### Source

- stage7/data.md §1 (types, signature, placeholder table, profile matrix); decision ledger data DAT-1, DAT-5, DAT-28;
  merge-clashes MC-23
- DO-6 *Content and redaction* (the table, "Where redaction happens, in order", "What leaves the environment"),
  *Capture verification* CAP-1
- DO-4 §3 (`Intake.text_store`, `PlannerInput` JEV profile), §5 (SONNET profile, stale comment), §12
  (`RoleSpec.redaction`, `ModelGateway(…, redact: Redactor, …)`)
- stage7/models.md §4 (`LangfuseTraceSink(settings, redact: Redactor, …)`); stage7/staff.md §5 (`redact_store`)
- DO-3 §4.1 (`privacy/redact.py`), §7 R-13, R-15, R-16, R-36 rows, §8 note on why it stays in A0
- System design §3.2 (what Jev and Anthropic see), §10 *Redaction (R-36)* and *What each vendor sees*
- PRD R-13 (never accept card numbers), R-15 (no code in chat, logs or traces), R-16, R-36 (redacted traces and logs)
- Workspace rule `context-management-multi-turn` rule 5; project rules `safe-validation-errors`,
  `verification-evals-observability` (rule 19)
- Slice plan §1 row AEA-04; residual ruling `docs/plans/7b-decisions/residuals-graph.md` R-G-18 (wave-0 merge order)
- Journey map: slice plan §0a; `.claude/rules/integrated-journeys.md`; `docs/plans/ux-join/backend-amendments.md` §3
- **Brief check:** serves "Production-thinking expected: system should be able to run unmanned for a month, failures
  should be observable" — traces and logs a month of strangers' messages can safely flow into; touches nothing out of
  scope; weakens nothing → proceed.

### Acceptance criteria

`risk::security`: `test-writer-agent` freezes AC-1…AC-9 as failing tests before the implementer starts.

- [ ] AC-1 [invariant] `STORE` replaces every card-like number (13, 16 and 19 digits; plain, spaced, dashed) with `[card number removed]` and every standalone six-digit code with `[code]`, and keeps names, phones, emails and addresses unchanged — verify: `tests/unit/privacy/test_redact.py::test_store_masks_cards_and_codes_keeps_contact` — evidence: passes for each format.
- [ ] AC-2 [invariant] `JEV` replaces introduced names, phones, emails, street addresses, `MHC-\d{5}`, `INV-\d{6}`, six-digit codes and card-like numbers with data.md §1's tokens, and the same kind maps to the same token across two separate calls — verify: `tests/unit/privacy/test_redact.py::test_jev_masks_every_identifier` and `::test_placeholders_stable_across_calls` — evidence: passes; name cases are introductions only (DAT-1).
- [ ] AC-3 [invariant] `SONNET` masks cards, codes, emails and the street line, turns a phone into `[phone ending NN]`, and keeps names, `MHC-`/`INV-` IDs and account facts (DAT-5) — verify: `tests/unit/privacy/test_redact.py::test_sonnet_masks_contact_keeps_ids` — evidence: passes.
- [ ] AC-4 [invariant] `TRACE` keeps a phone's last two digits only (`[phone ending NN]`), masks introduced names, emails and the street line, and leaves account facts untouched (amounts such as $478.00, dates such as 2026-11-01, windows such as 8:00 am – 12:00 pm, tier words, `MHC-C-` case references, customer and invoice IDs) — verify: `tests/unit/privacy/test_redact.py::test_trace_profile` — evidence: passes.
- [ ] AC-5 [invariant] `LOG` returns `text == ""`, `length == len(input)` and `replaced == {free_text: 1}` for non-empty input — verify: `tests/unit/privacy/test_redact.py::test_log_profile_is_length_only` — evidence: passes; no input substring longer than one character appears in the result or its repr.
- [ ] AC-6 [negative] For every profile, seeded distinctive values — a card-like number, a six-digit code, a phone, an email, a customer ID, an invoice ID, a street address and an introduced name, each assembled in the test at run time (no literals, per the conventions) — are absent from the output text, from `repr(Redacted)` and from any exception text, wherever data.md §1's matrix marks that kind replaced — verify: `tests/unit/privacy/test_redact.py::test_seeded_values_absent[<profile>]` — evidence: one pass per profile; the matrix of kind × profile printed.
- [ ] AC-7 [negative] Non-private values are not masked by mistake: a five-digit ZIP (78620), a city name, dollar amounts, ISO dates, slot numbers and 12-hour times survive `TRACE`, `SONNET` and `STORE`; a ten-digit phone is never treated as a card — verify: `tests/unit/privacy/test_redact.py::test_non_private_values_survive` — evidence: passes.
- [ ] AC-8 [invariant] Idempotent, and no token matches a pattern again: `redact(redact(x, p).text, p).text == redact(x, p).text` and the second call's `replaced` counts are all zero, for every profile over the AC-6 inputs — verify: `tests/unit/privacy/test_redact.py::test_idempotent[<profile>]` — evidence: passes.
- [ ] AC-9 [failure/refusal] An unknown profile raises `UnknownRedactionProfile` whose message holds the profile value only, no part of the input text — verify: `tests/unit/privacy/test_redact.py::test_unknown_profile_refused_without_echo` — evidence: raises; sentinel text absent from the message.
- [ ] AC-10 [invariant] Pure and typed: no I/O, no imports beyond the standard library (DO-3 §4.1), and `redact` satisfies the `Redactor` alias in the type check — verify: `tests/unit/test_import_direction.py::test_redact_imports_stdlib_only` and the type check over `tests/unit/privacy/test_redactor_alias.py` — evidence: passes; type check clean.
- [ ] AC-11 [journey] Runs no journey yet: wave 0 comes before AEA-57's harness (slice plan §0a; `integrated-journeys.md` §3 rule 1), so this issue's evidence is its unit and contract tests. The record `docs/testing/journeys/YYYY-MM-DD-AEA-04.md` states level `mock-tested`, *Blocked by* AEA-57, and names J-1 and J-3 (the stored "[code entered]" and "[details submitted]") as the journeys that will exercise this code once AEA-57 and AEA-51 land, so the seam audit knows where to look — verify: the record — evidence: the record's Level, Blocked-by and journey fields.
- [ ] AC-12 [regression/context] Context updated in the same change — verify: diff — evidence: area-map A0 row notes `privacy/redact.py` planned → actual with the commit; DO-3 §3 status line notes it built; the ICM row *Routes verified against code and tests* names this ticket's tests once they pass; DO-6 *Content and redaction* gains one line recording the name-masking limit as Innocent decides DAT-1 (option A: "loose names in free chat may reach Jev, under `data_collection: deny`, and the project's own Langfuse").

### Observability

- Responsibilities: this is the masker behind every DO-6 *Content and redaction* row, for every workflow that writes
  text (WF-1, WF-2, WF-4 and the eval runs WF-9, WF-10 that drive WF-1): `STORE` at intake, `JEV` and `SONNET` on every
  model input ("What leaves the environment"), `TRACE` in the export hook, `LOG` in the log formatter. It emits no
  record itself and adds no entry point.
- Capture evidence: AC-6 is the component-level guard and never stands in for a consumer. CAP-1 (AEA-51) drives CON-1
  and CON-2 through WP-2 with a seeded card-like number and asserts the code, the card-like number, the full phone and
  every key value absent from DB text, spans and logs. The wiring is owned by AEA-12 (`STORE` at intake), AEA-19
  (`TRACE` in `mask_otel_spans`), AEA-20 (`JEV` / `SONNET` per role in the gateway), AEA-22 (lookup-log snapshots),
  AEA-23 (`LOG` in the log formatter), AEA-27 (identity) and AEA-40 (turn service).

### Evaluation

N/A — no E-1…E-8 suite scores masking: DO-5's "nothing private before the code turn" is the identity gate (AEA-27,
AEA-36), not redaction, and a leak is proven or disproven by the capture checks (CAP-1, CAP-6, CAP-7 "held-out keys
absent"), not by an eval case.

### Metrics

N/A — DO-7 has no redaction metric; a leaked value is a CAP-1 failure, not a rate. M-29 counts trace exports, not what
they contain.

### Blocked by

None (slice plan wave 0). **Wave-0 merge order: AEA-04 → AEA-02 → AEA-05** (R-G-18, graph-core §12): this ticket merges
first, because AEA-02's `config.py` types `RoleSpec.redaction` as this file's `RedactionProfile` (no type moves). The
edge is inside wave 0; no wave moves.

### Agent handoff

- Area / owner: A0 Foundation (area map row A0; DO-3 §8 keeps it in A0 because A1, A2, A8 and A10a all use it).
- Contracts and shared surfaces: produces `redact`, `Redactor`, `RedactionProfile`, `RedactionKind`, `Redacted`,
  `UnknownRedactionProfile` for AEA-02 (`RoleSpec.redaction` is typed `RedactionProfile`; AEA-02's `config.py` imports it,
  so it is the one wave-0 import into this file), AEA-12 (intake), AEA-19 (trace hook), AEA-20 (gateway), AEA-22
  (lookup-log snapshots), AEA-23 (log formatter), AEA-27 (identity), AEA-40 (turn service), AEA-44/46 (`redact_store`
  bound by the container), AEA-51 (CAP-1). Frozen after wave 0. Must not edit: any consumer's file, DO-4.
- Scope boundary / refusal: masking only; it decides nothing about whether a turn is a code turn (that is
  `parse_intake`, AEA-12) and never sees a stored code (hashed in `identity_codes`, AEA-27); no name pattern beyond
  introductions and no known-values argument until DAT-1 is answered.
- Wave and gates: wave 0; merges before AEA-02 (R-G-18); security review at the wave-0 merge; gates: none beyond DAT-1
  below.
- Lane: build-loop — source and tests that every outbound path loads (`ticket-lanes`).
- Risk: security — a bug here leaks a verification code, a card-like number or a customer's contact details into the
  database, a model provider, Langfuse or Railway logs (R-15, R-36; DO-6 *What leaves the environment*).
- Awaiting Innocent: DAT-1 — built on the recommended option (A: introduction patterns plus a street-address pattern, with
  the limit written into DO-6 by AC-12); if he picks B, a keyword-only `known: Sequence[KnownValue] = ()` is added to
  `redact` and AEA-20 passes the located customer's values (data.md §1), changing AC-2, AC-6 and AEA-20's tests; if he
  picks C, a name-recognition model replaces the introduction patterns and needs an AEA-01 dependency follow-up.
- Entry points added or changed: None.
