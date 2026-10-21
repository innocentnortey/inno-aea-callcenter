---
paths:
  - "src/**"
  - "tests/**"
  - "eval/**"
  - "scripts/**"
---

# Integrated Journeys → Prove the Real Path Runs, Not Only That the Parts Pass

Project rule for `inno-aea-callcenter`, recorded 2026-10-21 at Innocent's instruction, from the Riverside
Onboarding build. Binding on every `lane::build-loop` ticket, reviewer, seam audit, merge gate and walkthrough in §8
and later. Project-local: it extends the workspace build loop for this repo only; making it a workspace rule needs
Innocent's say-so.

**The lesson, in Innocent's words.** Riverside's tests passed while real journeys failed: prompt outputs disagreed with
schemas, frontend state disagreed with backend state, security guards broke navigation outside mock mode, and real API
responses lacked fields the UI expected. These surfaced late because components were tested against fakes and
integration reviews read code without executing the journeys.

**What this means here.** Every check in DO-3 §9 can be green while a reviewer still can't sign in, book a visit and
see it remembered. This rule adds one thing the plan didn't have: a small suite that drives the real product path
(browser → real server → a writable copy of the database), runs at every merge, and grows with every feature. It also
says what a "verified" claim must record.

## 1. Inventory: what already protects us, and what runs today

Checked 2026-10-21. `tests/` and `eval/` are empty, and the parked `src/meridian/` has no tests. **Nothing on the
backend is executable today.** The only runnable checks are the UX track's, in `apps/web/`, and they run against the
Prism mock.

| Protection | Written down in | Runs today? | This rule |
|---|---|---|---|
| WP-1…WP-8, WP-4F, DANGER, NODANGER through the compiled graph with fake models and a temp DB | DO-3 §9 `tests/graph/` | No | Kept. Journeys add the browser, the real server and checks on stored rows (§3 rule 1) |
| The same cases through the HTTP API with fake models; seams S-1…S-24 across tickets | slice plan AEA-51, AEA-52 (wave 3) | No | Kept. Journeys reuse those scripts at the browser level, and seam audits must run them (rule 5) |
| Route responses validated against `ui-contracts.openapi.yaml` (`tests/api/openapi_check.py`) | contracts `stage7/web.md` §13, AEA-23 | No | Extended to real-server responses and to fixtures (rule 3, AEA-59). Not rewritten |
| Frontend types generated from the OpenAPI; stale-file check | `apps/web` `gen:types`, `check:gen` | Yes (UX-owned; not run for this rule) | Referenced, not duplicated. AEA-59 adds it to the merge gate without editing `apps/web` |
| Request drift flagged by Prism (`[contract drift]`) | `apps/web/src/dev/transport.ts` | Yes, mock mode only | Counts as `mock-tested` only |
| Playwright smoke and sweep with axe, 12 screens, 1280/390 | `apps/web/tests/e2e/` | Yes, on Prism; signs in with dev-only `?signedin=1&role=…` | Counts as `mock-tested` only: it skips the real login gate, the exact Riverside failure |
| UX-5 suite rerun against the real backend in Prism proxy mode | slice plan AEA-55 (wave 4, after UX-5) | No | Kept. It arrives too late to be the first integrated check; AEA-58 comes a wave earlier |
| CAP-1…CAP-11: seeded values absent from body, log and trace | DO-6; `tests/capture/` | No | Kept as is. Journeys don't repeat them |
| Model-port contract tests on recorded fixtures; `tests/live/` marker | DO-3 §9 `tests/contract/`, `tests/live/` | No | Extended. Rendered prompts are checked against their consumers, and the live smoke set is defined (rule 4, AEA-60) |
| Turn-2+ prompt test through the real path | workspace rule `context-management-multi-turn` rule 3 | No | Kept. The booking journey adds the browser-level follow-up turn |
| E-1…E-8 eval runs through the HTTP API | DO-5 `evaluation-plan.md` | No (`eval/` empty) | Untouched. A live smoke is not an E-run and produces no reported number |
| Affected tests at each merge; full suite before deploy | `rules/build-loop-test-scope.md` | Process only | Gains the journey gate (its *AEA addition*) |
| Seam audit per wave | checklist §8; `seam-audit-agent` | Process only | It must run the journeys, not only read code (rule 5) |
| Deploy smoke with the demo login | AEA-56 (`lane::human`) | No | Kept; only runs once the pre-deploy journey run is green |

**Nothing duplicates:** the browser-to-real-server journey with guards on, the stored-effect assertions, fixture
validation (including variants), rendered-prompt ↔ consumer checks, a live smoke through the app, the evidence record,
and the three verification levels.

## 2. What it looks like in practice

**Input.** Journey `J-BOOK`, built on WP-4F and run after AEA-58 lands. The server is the real FastAPI app, serving the
production `apps/web/dist` (AEA-49), on a temporary data directory holding a copy of the issued scheduling DB. Models are
the scripted adapter. Playwright opens `/`, is redirected to SCR-12, and signs in with the demo login from the
environment. There are no `?signedin`, `?role` or `?scenario` parameters. It then opens the chat as MHC-57204, whose
tune-up is more than 24 hours away, and types "Can I move my tune-up?". It reads the code from SCR-2, enters it, picks
the second slot offered, reloads the page, and asks "so when is the tech coming now?".

**Process.** The real middleware runs: login gate, request IDs, rate limits. So do the gates, the identity service, the
scheduling service, the SQLite working copy and the graph. The scripted adapter replaces only the provider call. It
returns the raw planner, classifier and responder output fixed in the journey script, so the production parsers and
schemas run on it. Every API response in the run is checked by `openapi_check.assert_response_matches`.

**Output.** The journey checks what the user sees:
- the confirmation card shows the new window in 12-hour time and no fee sentence;
- after the reload, the same conversation resumes with that confirmation;
- the follow-up answer names the new window, not the old one.

It also checks what was stored:
- the appointment row in the working copy holds the new window;
- one `actions` row records the move with this `turn_id`;
- no case was opened;
- the issued DB file's hash is unchanged.

**A `200` from CON-2 with an unchanged row fails the journey.** The fee-bearing twin `J-FEE` (WP-4) checks the
opposite: the row is untouched, a P2 case exists, and it shows in SCR-5. Opening it in SCR-6 shows the wanted time in
the handoff brief.

## 3. The rules

1. **The smallest runnable journey exists from the first slice that has a server path, and grows with every feature.**
   - It runs browser → real application server → an isolated writable database. It uses the production frontend build
     and the normal application paths, with authentication, guards, validation and persistence all **on**.
   - A deterministic scripted model adapter is allowed in this suite. It sits at the provider boundary, so parsers run,
     and a deployed configuration can't select it. API, retrieval, scheduling and the database use their real
     implementations as soon as each lands.
   - Data is issued or synthetic only (`source-authority` rule 8), on a disposable copy of the DB built per run (AEA-10's
     `temp_sqlite()` pattern). The issued files are never written.
   - Order of arrival:
     - Waves 0–1 have no server path to drive, so their evidence is labelled below the integrated level.
     - AEA-57 (wave 2) lands the harness and the first journey at the API level: log in → open a chat → one turn → its
       rows in the DB copy.
     - AEA-58 (wave 3) moves it into the browser once AEA-49 serves the build.
     - Every later ticket that adds a capability extends a journey.

2. **These journeys are covered as their capabilities land.** Each journey checks what the user sees **and** what was
   stored. A 2xx response alone proves nothing.

   | Journey | Covers |
   |---|---|
   | `J-DRIVERS` | The top three call drivers, through retrieval to a grounded answer that cites the current KB document |
   | `J-BOOK` | Booking through confirmation, the stored state, and a follow-up turn that remembers the completed action (R-45) |
   | `J-ESC` | Escalation through case creation, the staff list (SCR-5), and opening the case with its handoff context (SCR-6) |
   | `J-SAFE` | The approved safety handling (WP-3/WP-5 words, R-8 danger path) |
   | `J-FEE` | The fee-bearing change restriction (WP-4, R-21/R-22) |
   | `J-AUTH` | Login and role switching (R-48, CON-22, SCR-4), refresh and resume of a conversation and a staff view |
   | `J-STATES` | The relevant empty, missing-data, timeout (TURN_TIMEOUT/BUSY) and error states, reached through the real server, not dev scenarios |

3. **Contracts are verified at their boundaries.**
   - Frontend types are generated from the signed OpenAPI (`apps/web` already does this).
   - Every actual server response a journey receives is validated against that OpenAPI, using the one check AEA-23
     owns.
   - Mock fixtures are validated too. That covers `apps/web`'s dev scenarios and contract index (read only, never
     edited from this track) and every API-shaped fake under `tests/fakes/`. Validation includes the variants: optionals
     omitted, nulls, empty lists, and every documented error response.
   - **The signed contract stays authoritative.** When a response and the contract disagree, find out why. Never
     regenerate the contract around an accidental implementation. A needed contract change stops the ticket and goes to
     Innocent (checklist *Skips* row for §7).

4. **Prompt outputs are tested against the code that consumes them.**
   - Render the **actual** prompts through the real prompt builder with real state.
   - Check that every identifier, enum value, tool name, argument and output shape they mention matches the parser,
     `ToolDef` registry or schema that consumes it. Feed malformed and unsupported outputs (unknown tool, missing field,
     out-of-range enum) and check the documented fallback.
   - **Live smoke.** A small live-model smoke set runs through the real app:
     - when the integrated path first exists;
     - again whenever a relevant prompt, schema, model, tool or the orchestration changes.
   - It stays within the approved spend (PRD SD-1.6, $30/day) and uses development cases only (worked pairs, WP-4F,
     DANGER, NODANGER, dev split). The sealed held-out split is never used.
   - Record failures, model IDs and versions, Langfuse trace IDs and cost from the spend ledger.
   - A smoke run proves limited compatibility only. It is never cited as containment or quality: those come from E-runs
     (`verification-evals-observability`).

5. **Evidence is executed during the build, not read.**
   - Each ticket extends or runs the journey it affects.
   - Every bug fix first reproduces the failure, then adds a test that protects the intended success. This matters most
     when changing a guard: the fix must show the guard still blocks the bad case **and** the legitimate navigation
     still passes.
   - The deterministic journey suite is part of the merge gate, as `build-loop-test-scope.md`'s *AEA addition* says.
   - Reviewers and wave seam audits **execute** the relevant journeys. A review that only reads code doesn't count as a
     check.
   - A focused browser walkthrough of the journeys a wave touched runs after each wave reaches the integrated branch.

6. **Every verification claim records its basis** in the format in §4, at one of the three levels. If a dependency
   blocks a check, the record says so explicitly. It is never silently downgraded or left out.

7. **Authorization boundaries are unchanged.** Commits, pushes, deployment (AEA-56 is `lane::human`) and changes to
   shared rules under the workspace `.claude/` or `~/.claude/` still need Innocent's yes. Paid live-model calls stay
   inside the approved cap. Live smoke spends from the cap and is recorded; nothing here raises it.

## 4. Verification levels and the evidence record

| Level | Means | Example |
|---|---|---|
| `mock-tested` | Ran against fakes, doubles or Prism; guards may be bypassed | Today's `apps/web` Playwright sweep |
| `integrated with a scripted model` | Real server, real DB copy, guards on, production build; the model is the scripted adapter | `J-BOOK` above |
| `verified with live models` | The same path with the real providers, inside the cap | A live smoke run; it proves compatibility, not quality |

A claim without its level is read as `mock-tested`. Records go in `docs/testing/journeys/YYYY-MM-DD-<scope>.md`
(planned; scope is `AEA-NN`, `wave-N-walkthrough` or `live-smoke-N`). Screenshots go beside the record. No secrets, the
demo password or real personal data appear in either.

| Field | Value |
|---|---|
| Claim | What is said to work (journey IDs, ticket) |
| Level | `mock-tested` / `integrated with a scripted model` / `verified with live models` |
| Tested revision | Commit SHA (and `agent_version`); "uncommitted" if so |
| Environment | Host, server command, DB copy source, frontend build, model adapter and model IDs |
| Command | The exact command or walkthrough steps |
| Result | Pass/fail per journey, with the failing assertion quoted |
| Evidence location | Report, screenshots, trace IDs, spend-ledger total |
| Remaining limitations | What this did not cover |
| Blocked by | The dependency that prevents a higher level (e.g. "browser level waits on AEA-49 / UX-4 sign-off"), or "none" |

## 5. Who runs what, when

| Who | When | Runs | Level it can claim |
|---|---|---|---|
| Ticket implementer | Before the final commit | The journeys the change affects, extended for the new capability; the bug's reproduction first when fixing one | `integrated with a scripted model` once AEA-57 exists |
| Code reviewer (`code-review-agent`) | Per ticket | Re-runs the affected journeys itself; reading the diff is not a check | Same |
| Merge gate | Ticket merge / wave merge / before deploy | Affected journeys / all journeys and the contract boundary checks / all journeys plus the full suite | Same |
| Wave seam audit (`seam-audit-agent`) | After each wave merges | All journeys on the integrated branch; names which seams each journey exercised and which none did | Same |
| Wave walkthrough | After each wave reaches the integrated branch | A focused browser walk (chrome-devtools MCP or headed Playwright) of the journeys the wave touched, with screenshots | Same |
| Live smoke | First integrated path (AEA-61), then on any prompt, schema, model, tool or orchestration change | The development smoke set through the real app with real providers | `verified with live models` (compatibility only) |

## 6. Where this extends existing mechanisms

- **`build-loop-test-scope.md`** keeps its role table. Its *AEA addition* adds the journey gate. "Affected" now includes
  the journeys that touch a changed module.
- **`verification-evals-observability.md`** still owns evals, judges and traces. Live smoke borrows its trace and cost
  recording and stays out of its numbers.
- **DO-3 §9** keeps its folders. Journeys get their own folder; AEA-57's plan names it, outside `apps/web/**` while the
  UX track owns that tree.
- **CAP-n capture tests** (DO-6) are unchanged; journeys don't re-check redaction.
- **AEA-23's OpenAPI check** is the only response validator; AEA-59 calls it from more places.
- **AEA-51/52** keep their API-level integration scope. Their scripts become the journey inputs.
- **The UX-5 suite and AEA-55** keep the visual and accessibility checks. They are not journey evidence where they sign
  in through dev-only parameters.

**The tickets that carry it.** The rows, blockers and lanes are owned by the plan amendment in
`docs/plans/slice-plan.md`. This rule owns what they must prove.

| Ticket | Wave | Proves |
|---|---|---|
| AEA-57 | 2 | Journey harness: real app on a disposable DB copy, scripted adapter at the provider boundary (a deployed config can't select it), the first API-level journey, the merge-gate command, the evidence template |
| AEA-58 | 3 | Browser journeys on the production build through the normal login (§3 rule 2 as capabilities land); the walkthrough recipe |
| AEA-59 | 2 | Contract boundary checks: real responses during journeys, fixtures and fakes with their variants, and the generated-types freshness check in the gate (read only on `apps/web`) |
| AEA-60 | 3 | Rendered-prompt ↔ consumer checks |
| AEA-61 | 4 | The live smoke set and its record (`gate::paid`) |
| AEA-62 | 4 | Browser legs of J-2, J-3, J-6, J-8 against the production build |

## 7. What this rule does not change

- Nothing merges on red affected tests or red journeys, and nothing deploys on a red full suite.
- Frozen tests for `risk::security` tickets, the held-out custody rules, and every rule about secrets, values and live
  calls.
- Ticket lanes and acceptance criteria. Lanes decide who builds a ticket; this rule decides what its evidence must
  show.
