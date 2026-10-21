## [AEA-08] docs: reconcile DO-3, DO-4 and the area map with this plan

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

Make the code map every build agent reads agree with the approved slice plan and the final Stage 7 contracts, so no
wave-1 or wave-2 planner reads a file owner, path, name or code the tickets have changed. **The OpenAPI wins on wire
names and codes; the slice plan wins on files and owners; an addendum (DO-4 §16) wins over earlier DO-4 text.** This
ticket records those decisions in the design documents; it makes none.

**Already applied before this ticket (2026-10-21, uncommitted; check, do not redo):** DO-3 §3 marks `templates/ ·
static/` NOT PLANNED and §8's collision map has the `web/templates/`, `web/static/` and route/schema-split rows citing
AEA-08 and AEA-49; the area map's *Screens* line says screens are `apps/web`; DO-4 carries `> Superseded at Stage 7`
notes for `domain/base.py`/`domain/ids.py`, `retrieval/build_index.py`, `TurnContext`'s home, `STAFF_AUTH_REQUIRED`, the
repository shells, `ProviderCall`, `export_status` and `ResetService.reset`.

**The remainder, file by file.**

1. **`docs/design/code-design.md` (DO-3)** — header: "revision 3, 2026-10-21: reconciled with the slice plan and the
   Stage 7 addenda (AEA-08)".
   - **Deviation 1 (slice plan §0): AEA-10 writes every DDL file and owns `repos_cases.py`.** §3 tree: `repos_cases.py`
     and `schema/60_cases.sql` change area to A0 (AEA-10); split `60_cases` out of the `{20_spend,…}` DDL line; every
     `schema/*.sql` line says "written by A0 (AEA-10) from the owning area's field list" (still one file per area, applied
     by number). §8: the A0 row gains `repos_cases.py` and every `schema/*.sql`; the A2, A4, A5, A9, A10a rows keep their
     repository bodies and lose authorship of their DDL; the A6 row loses both and its *Depends on* names A0's
     `repos_cases`. One line under §8's rule: "Deviation (slice plan §0, 2026-10-21): the cases tables are written by
     cases/handoff, demo/scheduler, reset, live chat and seed, so by this section's own rule they live in A0; the other
     DDL files land with them so no wave-2 ticket waits for a sibling's schema." Collision-map rows: repository stubs
     `repos_{spend,identity,booking,staff,ops}.py` (five; `repos_cases` is A0's); `schema/*.sql` owner AEA-10 only, "a
     missing column is a small follow-up on AEA-10, merged first".
   - **Deviation 2 (slice plan §0): cross-ticket reads and reset clearing land in `repos_core`.** §4.3 (or the module row
     for `repos_core.py`) names `reads.invoice`, `reads.appointment`, `reads.identity_state`,
     `reset.clear_demo_tables(tx)` and `settled_for(thread_id, read_at)` with a pointer to stage7/cases.md §1.2–§1.3 for
     their signatures (do not copy them).
   - **Deviation 3 (slice plan §0): one route file and one schema file per ticket.** §3 `web/` subtree lists exactly:
     `container.py` (A0), `app.py`, `middleware.py`, `deps.py` (every service provider incl. `require_staff(*roles)`),
     `errors.py` (one `ApiProblem` and handler, stage7/web.md §1), `logging.py` (LOG-profile allow-list formatter, web.md
     §10) — all AEA-23; `frontend.py` (static mount, SPA fallback, public paths; AEA-49, web.md §12); and ten route/schema
     pairs: `auth` (CON-22; AEA-23), `chat` (CON-1, CON-2; AEA-40), `events` (CON-3; AEA-41), `handoff` (CON-4, CON-5;
     AEA-42), `demo` (CON-6, CON-7, CON-8 read, CON-9; AEA-43), `staff_session` (CON-10; AEA-44), `staff_cases`
     (CON-11…13, CON-15…17; AEA-45), `staff_live` (CON-14, CON-21; AEA-46), `staff_clock` (CON-8 advance; AEA-47), `reads`
     (CON-18…20; AEA-48). Remove `schemas/customer.py`, `schemas/staff.py`, `routes/staff.py` and every "+ page(s)" note.
   - **Modules the addenda added**, each as one tree line with area, ticket and the addendum section: `domain/staff.py`
     (AEA-02; staff.md §1, MC-2; the §4.1 table gains its row and the domain count goes from 9 to 10 files);
     `services/reset_gate.py` (AEA-23; web.md §7); `services/person_request.py` (AEA-42; web.md §8);
     `retrieval/settings.py` (AEA-16; data.md §3, DAT-11); `agent/signals.py` (AEA-21; graph-core §4, graph-nodes §4);
     `scripts/agent_version.py`, `scripts/reset.py` (AEA-50; data.md §7); `tests/fixtures/sqlite.py` (AEA-10; DAT-10,
     cases.md §1.5) and `tests/fakes/clock.py` (AEA-11; data.md §8a) in §9. Recount the tree and correct the **Count**
     line (the criterion is the recount, not a number written here).
   - §1 step 1: `web/schemas/customer.py` → `web/schemas/chat.py`. §7: R-2 and R-27 point at `web/routes/handoff.py`
     (CON-4, CON-5); R-32 at `web/routes/staff_cases.py`; R-48 adds `web/routes/auth.py` (login) and
     `web/routes/staff_session.py` (role switch). Any other row naming an old file is corrected the same way.
   - §4.4 `services/staff.py` interface: `sign_in`, `current`, `sign_out` → the staff.md §2 names (`StaffSessionStore`:
     start, resolve, end, actor_for, switch_role, session_info; `FlagService`) (STF-26). AEA-44 later flips the row to
     built; it does not rename.
   - §8 A8, A9, A10b rows: owned files as in the split; A10b says `routes/reads.py` is built in ticket wave 2 (AEA-48,
     because `require_staff` is declared in `web/deps.py` by AEA-23) and `services/metrics_reader.py` in ticket wave 3
     (AEA-53). Add a collision row for `web/deps.py` (owner AEA-23; a new provider is a follow-up on 23).
   - §8 closing line: build order and ticket waves are the slice plan's (§1–§2); DO-3's area waves stay as the dependency
     rule. Do not copy the ticket table into DO-3.
   - §11 and the *UX-3 reconciliation* paragraph are history: leave their text, append "(file split per ticket since
     2026-10-21, §8)" where they name `routes/staff.py` or `repos_cases` under A6.
2. **`.claude/reference/area-map.md`** (mirror of DO-3; DO-3 wins): A0, A2, A4, A5, A6, A8, A9, A10a, A10b rows and the
   *Repo stubs* line match the DO-3 changes; *Screens* line lists the ten route files and says AEA-49 serves
   `apps/web/dist`. Add a **Tickets** column with each area's AEA numbers from slice plan §1 (A0 → 01, 02, 03, 04, 10,
   11; A1 → 05, 12; A2 → 17, 18, 20, 26; A3 → 16, 33; A4 → 27; A5 → 13, 28; A6 → 14, 29, 30, 31; A7a → 21, 34; A7b → 14
   (`policy/escalation.py`), 22, 35, 39; A7c → 15, 38; A7d → 36, 37; A8 → 23, 40, 41, 42, 43, 49; A9 → 44, 45, 46, 47;
   A10a → 19, 32; A10b → 48, 53; A11 → 06, 24; A12 → 50; integration and journeys → 51, 52, 55, 57, 58, 59, 60, 61).
   Check every number against slice plan §1 before writing it. *As of* line: 2026-10-21, reconciled with the slice plan
   (AEA-08).
3. **`docs/design/contracts/api-con-mapping.md`** (DO-4's endpoint table): the *served by* cell of CON-1…CON-22 and the
   UXR-9 row name the split route files; CON-10's operationIds become the OpenAPI's `listDemoRoles`, `switchRole`; a
   CON-22 row (if absent) names `login`, `logout`, `getSession` and `web/routes/auth.py`; the *Cookies* row says one
   cookie, `mhc_session`, with `mhc_demo` and `mhc_staff` retired (OpenAPI `info.description`); the CON-18 note reads
   "route in ticket wave 2 (AEA-48), reader in wave 3 (AEA-53)". **No field, type, status or signature changes.**
4. **`docs/design/contracts/internal-components.md` (DO-4)**: the `cases: CaseRepos` comment in `SqliteUnitOfWork` reads
   A0 (AEA-10); §14's `NotVerified` comment drops "and cap reached" (GRT-3; graph-tools §5, C-12); §5's SONNET-profile
   comments (`customer_text`, `wanted_text`) gain "emails, street addresses; phones to their last two digits" (DAT-5;
   data.md §1). Each edit carries a `> Superseded at Stage 7` note citing its addendum, as the existing notes do.
5. **`docs/design/system-design.md` (DO-1/DO-2)**: §10 *No account fishing* drops "and failed code" from the
   `NOT_VERIFIED` grouping (GRT-3, C-12); `CONFLICT_STALE` → `VERSION_CONFLICT` in the CON-13 rows (UI_CONTRACTS renamed
   list; STF-26); the CON-10 row reads "role switch for the signed-in session (R-48, CON-22)" instead of "Staff sign-in".
   Wording only; no decision changes.
6. **UX-owned stale lines (never edited here):** post on the issue, for the UX session, the lines STF-26 lists in
   `UI_CONTRACTS.md` and the OpenAPI (N-15 "Roles, GET, DELETE; no passcode"; CON-8 *Access* "read by any browser";
   `getCase`'s "[open: …]" owner note; CON-21's error list without `ROLE_NOT_ALLOWED`; `liveChatAction`'s 403 example).
   The tickets already follow the settled behaviour (AEA-45, 46, 47 contract notes).
7. **`.claude/state/icm-progress.md`** row *Code design: planned locations*: replace its evidence with this ticket's
   commit.
8. **UX-join reconcile record (AEA-08-1; `docs/plans/ux-join/backend-amendments.md` §2; staff audit A5, A7; customer
   audit A-1; join decisions 5 and 6):** post on the issue, beside AC-10's hand-over, four entries, each citing its audit
   row, without editing the OpenAPI, `UI_CONTRACTS.md` or SCREEN_SPECS: (1) the `applyCaseAction` 409 examples' `changed_at`
   written with a space where the server emits ISO 8601 with `T`; (2) staff.md §8 `ClockAdvanced.date_label` vs the
   OpenAPI `ClockAdvanceResponse` keys (`now`, `label`, `became_overdue`; the route returns the OpenAPI keys, AEA-47-1);
   (3) web.md §14's `thread()` comment replaced by AEA-40-1's full-history rule (**already present in web.md §14 since
   R-W-6, 2026-10-21: check, do not redo**); (4) SCREEN_SPECS N-28 vs UI_CONTRACTS CON-22 on the login-throttle copy, and
   SCR-1's "the chat resumes" after a new sign-in vs `owned_thread`'s 404, both open with Innocent
   (`docs/plans/ux-join/decisions-for-innocent.md` §5, §6; R-W-12).

### Source
- Slice plan §0 (the three deviations), §1 rows 08, 10, 23, 40…49, 53, §3 collision map.
- DO-3 §1, §3, §4.1, §4.3, §4.4, §7, §8, §9, §11; area map; DO-4 §5, §13 `SqliteUnitOfWork`, §14, §16;
  `api-con-mapping.md` CON-1…CON-22, UXR-9; DO-1 `system-design.md` §10 and the CON table.
- Addenda: stage7/web.md §1, §6, §7, §8, §10, §12; stage7/staff.md §1–§2; stage7/cases.md §1.1–§1.5; stage7/data.md §1,
  §3, §7, §8a; stage7/graph-core.md §4; stage7/graph-tools.md §5 and C-12.
- Ledgers: `docs/plans/7b-decisions/staff.md` STF-26; `graph-tools.md` GRT-3; `data.md` DAT-5 (contradiction 1), DAT-10;
  `merge-clashes.md` MC-2.
- OpenAPI `docs/ux/03-structure/ui-contracts.openapi.yaml` (read only): operationIds, `info.description` cookies.
- UX join: `docs/plans/ux-join/backend-amendments.md` §2 AEA-08-1; `audit-staff.md` A5, A7; `audit-customer.md` A-1;
  `decisions-for-innocent.md` §5, §6; `docs/plans/7b-decisions/residuals-web.md` R-W-6 (web.md §14 history), R-W-12.
- Rule `context-maintenance` (fix the owner, then the routes; planned is not built); workspace rule
  `new-project-zero-to-hero` hard stop "No ticket cut while `.claude/reference/area-map.md` is missing or disagrees with
  the code design".
- User story / worked pair / hard problem: none; a context-maintenance ticket.
- **Brief check:** serves no brief sentence directly; it keeps the build's map true so every deliverable is built where
  the design says; touches nothing out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] Cases storage and every DDL file are A0 / AEA-10 everywhere current — verify: `grep -n -E 'repos_cases|60_cases|schema/' docs/design/code-design.md .claude/reference/area-map.md docs/design/contracts/internal-components.md` — evidence: every hit outside DO-3 §11 says A0 / AEA-10; no current row or tree line assigns DDL authorship to another area.
- [ ] AC-2 [invariant] The old route and schema files are gone from current text — verify: `grep -n -E 'routes/staff\.py|schemas/(customer|staff)\.py|\+ pages?\b' docs/design/code-design.md .claude/reference/area-map.md docs/design/contracts/api-con-mapping.md` — evidence: hits only in DO-3 §11 and the UX-3 reconciliation paragraph, each followed by the "split per ticket" pointer.
- [ ] AC-3 [invariant] DO-3 §3, DO-3 §8, the area map and `api-con-mapping.md` name the same ten route files and ten schema files, each with the owning ticket of slice plan §1/§3 — verify: list the `routes/` and `schemas/` names from each of the four places and compare with slice plan §3's route/schema row — evidence: the four lists and the slice plan list are identical (posted on the issue).
- [ ] AC-4 [invariant] Every module an addendum or a slice-plan *Owns* cell names under `src/meridian/`, `scripts/` or `tests/{fixtures,fakes}/` has a DO-3 line — verify: extract the `.py` paths with `grep -ohE '\b(web|services|domain|agent|adapters|retrieval|policy|privacy|gates|ports|scripts)/[A-Za-z_/]*\.py\b' docs/design/contracts/stage7/*.md docs/plans/slice-plan.md | sort -u` and grep each basename in DO-3 §3 and §9 — evidence: no path missing except the superseded `domain/base.py`, which appears only in a Superseded note.
- [ ] AC-5 [invariant] DO-3's module **Count** line equals a recount of its §3 tree — verify: count the `.py` lines under `src/meridian/` in the tree block — evidence: the recount and the stated count agree (number posted on the issue).
- [ ] AC-6 [negative] Stale names are gone from current text in the documents this ticket may edit — verify: `grep -n -E 'listStaffRoles|createStaffSession|getStaffSession|endStaffSession|mhc_demo|mhc_staff|CONFLICT_STALE|and cap reached|and failed code|sign_in|sign_out|AEA-06|AEA-51 serves' docs/design/code-design.md .claude/reference/area-map.md docs/design/contracts/api-con-mapping.md docs/design/contracts/internal-components.md docs/design/system-design.md` — evidence: each remaining hit is inside a `> Superseded` note, DO-3 §11 history, or a sentence saying the name is retired.
- [ ] AC-7 [invariant] Every area-map *Tickets* entry matches slice plan §1 — verify: for each area, compare its numbers with the slice plan rows whose *Owns* cell names that area's files — evidence: no ticket in two areas' lists unless its *Owns* cell spans both (AEA-14 spans A6 and A7b); every ticket 01–61 except the direct/human ones (07, 08, 09, 25, 54, 56) appears at least once.
- [ ] AC-8 [negative] No contract changed: no field, type, status code, error name, signature or decision differs — verify: `git diff -U0 docs/design/contracts/ docs/design/system-design.md` (or a word diff against the pre-ticket copy while the files are untracked) — evidence: only *served by* / owner-label / comment wording and `Superseded` notes changed, each citing its addendum or ledger id.
- [ ] AC-9 [negative] Nothing code or tests read is touched, and nothing UX-owned — verify: `git diff --name-only <base>..HEAD` — evidence: only the six documents in *What to build* (DO-3, area map, `api-con-mapping.md`, `internal-components.md`, `system-design.md`, `icm-progress.md`) plus the dev log and resume note; no path under `docs/ux/`, `apps/`, `src/`, `tests/`.
- [ ] AC-10 [invariant] The UX-owned stale lines are handed over, not edited — verify: the issue comment listing the five STF-26 lines with file and line — evidence: the comment exists; `git diff --name-only` shows no `docs/ux/**` path.
- [ ] AC-11 [invariant] The context system still checks clean — verify: `python3 ~/.claude/skills/icm-project/scripts/check_context.py .` — evidence: no FAIL; every link in the area map resolves.
- [ ] AC-12 [regression/context] The reconcile record lists, without editing the OpenAPI, `UI_CONTRACTS.md` or SCREEN_SPECS: (1) the `applyCaseAction` 409 examples write `changed_at` with a space (`2026-10-16 14:31:00-05:00`) where the server emits ISO 8601 with `T`; (2) staff.md §8 lists `date_label` in `ClockAdvanced` while the OpenAPI `ClockAdvanceResponse` has only `now`, `label`, `became_overdue`, and the route returns the OpenAPI keys (AEA-47-1); (3) web.md §14's `thread()` comment ("customer messages and each completed turn's stored response blocks") is replaced by AEA-40-1's full-history rule; (4) SCREEN_SPECS N-28 vs UI_CONTRACTS CON-22 on the login-throttle copy, and SCREEN_SPECS SCR-1's "the chat resumes" after a new sign-in vs `owned_thread`'s 404, are open with Innocent (join decisions 5 and 6) (AEA-08-1; staff audit A5, A7; customer audit A-1) — verify: `git diff --name-only` and a read of the record (the issue comment of *What to build* item 8) — evidence: four entries, each citing its audit row; web.md §14 updated (already carries the full-history rule since R-W-6; the record says so); no path under `docs/ux/` in the diff.
- [ ] AC-13 [regression/context] Same commit: `.claude/state/icm-progress.md` row *Code design: planned locations* carries this commit as evidence; DO-3 status line reads revision 3; the area map's *As of* line updated; every area-map row stays *planned* (nothing is built); one dev-log entry; the resume note says DO-3 is at revision 3 — verify: `git diff` — evidence: the changes in the same commit.

### Observability
N/A — design and context documents only; no code path runs and no entry point is added or changed (the WF-n registry in
DO-6 is not touched; a workflow a ticket adds is registered by that ticket).

### Evaluation
N/A — design and context documents only; no suite, case or expected answer is added or changed.

### Metrics
N/A — design and context documents only; no metric's formula, source record or target changes.

### Blocked by
None. **Should merge before any wave-1 planner reads DO-3** (AEA-10, AEA-23 and the wave-2 route tickets are the readers
that care); it is wave 0 so it lands first.

### Agent handoff
- Area / owner: context system and DO-3 (`rules/context-maintenance`); after this ticket each build ticket changes only its
  own area-map row (planned → actual + commit), per slice plan §3.
- Contracts and shared surfaces: produces the file-ownership map AEA-10, AEA-23 and AEA-40…49 plan against. Must not
  change any DO-4 type or signature, any addendum or ledger, the OpenAPI, `UI_CONTRACTS.md`, `docs/ux/**`, the PRD, or the
  slice plan itself (if the slice plan looks wrong, stop and report on the issue; do not "fix" it here).
- Scope boundary / refusal: records the plan's and the addenda's decisions; makes none. A disagreement found between DO-3,
  DO-4 and the slice plan beyond those listed goes on the issue for Innocent. PRD §6.2's "server-rendered pages" is a known
  PRD discrepancy (slice plan §5 Q-5) and is not edited.
- Wave and gates: wave 0; no gate. Labels: `slice::docs`, `wave::0`, `lane::direct`.
- Lane: direct — design and `.claude/` context files no code or test reads (rule `ticket-lanes`).
- Risk: None.
- Entry points added or changed: None.
