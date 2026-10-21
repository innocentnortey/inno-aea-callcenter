## [AEA-25] docs: README (how to run)

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

Rewrite the root `README.md` into the reviewer's front door: what this is, how to try it, how to run it, where the eval
set is, and (once Stage 9 runs) what the containment numbers were. The current README says "Stage 1" and "No code yet";
both go. Its opening summary and *History* section stay.

**Sections, in this order:**

1. **What this is** (keep the current opening; lead with the business problem, rule `hiring-partner-framing`): one
   paragraph on Meridian's call center and the agent, then the two competencies and escalation.
2. **Try it.** Deployed URL: `pending: AEA-56`. The demo login (R-48): one username and password gate every page except
   the login screen and `/healthz`; after signing in, a visible control switches between the customer view and the staff
   roles (representative, supervisor, owner) with no second password; reset sits behind the same login. **Where the
   reviewer gets the login (DAT-3, open):** until Innocent answers, the line reads "The demo login is provided with the
   submission." and holds no value. What to try: a membership, billing or warranty question; booking a repair; "talk to
   a person"; a safety phrase; then the staff console and the monitoring page.
3. **Results.** One line per headline measure, each in the form "n of N on <split>, run <id>, <date>": in-scope correct
   resolution on the sealed held-out split (M-1, the README number), containment (M-5, shown as coverage × resolution),
   accuracy on handled drivers, escalation rate on out-of-scope cases (M-19), retrieval hit rate @3 (M-6). **Every value
   reads `pending: Stage 9`** in this ticket; the brief's 60–75% appears only as "the brief's target". Link to the test
   results (D-6, `pending: Stage 9` as plain text) and to `docs/technical-documentation.md` (AEA-07).
4. **How to run it locally.** Prerequisites: Python 3.12 (`pyproject.toml` `requires-python = ">=3.12,<3.13"`), `uv`.
   Steps: `uv sync`; copy `.env.example` to `.env` and fill the names it lists (AEA-02 owns `.env.example` beside
   `config.py`; the names are stage7/graph-core.md §12's: the two provider keys, the demo login pair,
   `MERIDIAN_SESSION_SECRET`, optional `MERIDIAN_EVAL_KEY` and the four optional `LANGFUSE_*` values; without all four
   Langfuse values trace export is off); values are never committed. Start the app with the command AEA-23 lands for
   `create_app` in `src/meridian/web/app.py` (`pending: AEA-23` until then; one worker, never port 4019 or 5184, which
   the UX prototype holds); the first boot copies the issued scheduling DB into a working copy under `MERIDIAN_DATA_DIR`
   (default `var/`) and never writes the issued file (R-19); the local knowledge index is built with
   `python -m meridian.retrieval.ingest --kb-dir PATH --transcriptions-dir PATH --out-dir PATH` into `MERIDIAN_INDEX_DIR`
   (default `var/index`; stage7/data.md §3; `pending: AEA-16`). Tests: the default `pytest` run excludes the `live` marker,
   so it makes no paid call; lint and type check as AEA-01 configures them. Eval (stage7/data.md §6, `pending: AEA-24`):
   `python -m eval.harness run --suite worked-pairs|e2e|load --split dev --base-url URL` and
   `python -m eval.run_retrieval --index-dir PATH`; the held-out split is sealed and scored only at Stage 9. The React
   screens (`apps/web`): `pending: AEA-49/AEA-55`. Docker: `pending: AEA-50`.
5. **What is in the repository.** A short tree from the area map's top level: `src/meridian/` (layers in one line),
   `eval/cases/{dev,heldout,retrieval}/`, `eval/harness/`, `eval/reports/`, `tests/` (incl. `tests/journeys/`),
   `apps/web/`, `docs/` (brief, data, PRD, design, delivery), the issued dataset at `docs/data/issued/meridian_dataset/`
   included under R-42 (public repo; licence risk accepted, audit L-8), `Dockerfile`/`railway.json`/`scripts/`. The
   held-out line says where the held-out answer keys live until scoring (DAT-2, open: built on option B, "kept outside
   the repository until the held-out run, then committed with their hash").
6. **Monitoring and the feedback loop** (R-37: "the loop is described in the README"). What the monitoring page shows;
   staff flag a wrong answer, brief or escalation → a review list; nothing changes the knowledge base, prompts or eval set
   automatically; how a reviewed flag becomes a fix (a new dev case, a KB or prompt change, re-scored). Link to
   `docs/technical-documentation.md` section 9 for the full loop.
7. **Documents.** Technical documentation (AEA-07), deployment guide (`docs/deployment-guide.md`, AEA-54; plain text
   until it exists), test results (Stage 9), `SUBMISSION.md`, the brief.
8. **History** (keep as is).

**One line per ticket after this one.** Commands that do not exist yet are written as `pending: AEA-NN`; the ticket that
lands the command replaces its own line in its `[regression/context]` change, and nothing else in the README (slice plan
§3: `README.md` owner AEA-25, others one line per ticket).

### Source
- Brief Part B *Deliverables* 3: "a README that explains how to run it and what the containment numbers were"; Part A
  *Required Deliverables* "Source Code".
- PRD R-43, R-37, R-42, R-48, R-19, R-38, R-39; `SUBMISSION.md` D-3; DO-7 M-1, M-5, M-6, M-19; DO-5 *Scoring* (the R-39
  report); area map; DO-3 §3, §9.
- Final contracts: stage7/graph-core.md §12 (env names, defaults); stage7/data.md §3 (ingest CLI), §5–§6 (case files,
  harness commands), §8 (document paths). Ledgers: `docs/plans/7b-decisions/data.md` DAT-2, DAT-3, DAT-7, DAT-8.
- Slice plan §1 wave 1 row AEA-25; §3 collision row (`README.md` owner 25, others one line per ticket); §5 Q-4.
- User story / worked pair / hard problem: none; the README points at the flows US-1…US-28 build.
- **Brief check:** serves "a README that explains how to run it and what the containment numbers were"; touches nothing
  out of scope; weakens nothing → proceed.

### Acceptance criteria
- [ ] AC-1 [invariant] The eight sections exist in order — verify: `grep -n '^## ' README.md` — evidence: eight headings matching *What to build*.
- [ ] AC-2 [invariant] Every command in *How to run* either runs on the merged tree or is marked `pending: AEA-NN` — verify: in a clean checkout of `main`, run each non-pending command (`uv sync`, the test command, the lint and type-check commands, `--help` of the start, ingest and eval commands where landed) — evidence: each command and its exit status on the issue; every pending line names the ticket that will land it.
- [ ] AC-3 [invariant] Every environment name the README lists equals a name in graph-core §12 (and, once AEA-02 merges, in `.env.example`) — verify: `grep -o -E '\b(MERIDIAN|LANGFUSE|ANTHROPIC|OPENROUTER)_[A-Z_]+' README.md | sort -u` compared with the §12 list — evidence: no README name missing from the list; none of the retired names (`MERIDIAN_DAILY_SPEND_CAP_USD`, `MERIDIAN_LLM_MODEL`, `MERIDIAN_FAST_MODEL`, `MERIDIAN_TODAY`).
- [ ] AC-4 [negative] No result is claimed before a run — verify: `grep -n -E '[0-9]+(\.[0-9]+)?%|[0-9]+ of [0-9]+' README.md` — evidence: the only percentages are the brief's target (labelled as the target) and PRD §3 coverage figures labelled as measured on the 420 issued calls; every result line reads `pending: Stage 9`.
- [ ] AC-5 [negative] No secret or credential value in the README, and no demo-login value while DAT-3 is open — verify: `grep -n -i -E 'password|api[_ -]?key|secret|token' README.md` — evidence: only variable names and descriptions; the login line reads "The demo login is provided with the submission."
- [ ] AC-6 [invariant] Every relative link resolves — verify: `grep -o '](\([^)#]*\)' README.md | sed 's/^](//' | grep -v '^http' | while read p; do [ -e "$p" ] || echo "MISSING $p"; done` — evidence: no `MISSING` lines (files not yet written are plain text marked `pending`, not links).
- [ ] AC-7 [negative] Nothing code or tests read is touched — verify: `git diff --name-only <base>..HEAD` — evidence: only `README.md`, the `SUBMISSION.md` D-3 row and the dev-log/resume files.
- [ ] AC-8 [regression/context] Same commit: `SUBMISSION.md` D-3 Evidence cell names `README.md` with Status `run instructions written; containment pending Stage 9`; no area-map, ICM or DO-3 row changes (documentation only; say so on the issue); one dev-log entry; the resume note — verify: `git diff` — evidence: the changes in the same commit.

### Observability
N/A — documentation only; no code path runs and no entry point is added or changed, so no record is emitted or captured.

### Evaluation
N/A — documentation only; it names DO-5's suites and the stage7/data.md §6 commands, and adds or runs none.

### Metrics
N/A — documentation only; M-1, M-5, M-6 and M-19 are named as DO-7 defines them and filled from the Stage 9 run.

### Blocked by
AEA-01 (`pyproject.toml`, lint/type configuration and the package skeleton the run steps describe; slice plan row AEA-25).

### Agent handoff
- Area / owner: `README.md` (owner AEA-25; slice plan §3).
- Contracts and shared surfaces: reads AEA-01's `pyproject.toml`, AEA-02's `.env.example` (wave 0; if it is not merged
  when this ticket runs, the env line names the graph-core §12 list and reads `pending: AEA-02` for the file), graph-core
  §12 and stage7/data.md §3, §6; links to AEA-07's and AEA-54's files. Later lines are filled by AEA-16 (ingest), AEA-23
  (start command), AEA-24 (eval commands), AEA-49/55 (frontend), AEA-50 (Docker), AEA-56 (URL) and Stage 9 (results),
  one line each. Must not edit `SUBMISSION.md` rows other than D-3, or any doc another ticket owns.
- Scope boundary / refusal: no numbers before a run; no command that does not exist written as if it did; no login value.
- Awaiting Innocent: DAT-3 — built on the recommended option B (the README says the login is provided with the
  submission and holds no value); if he picks A or C, the *Try it* line carries the username and password, written by
  Innocent himself (the value never passes through an agent), and AC-5's grep then expects that one line.
- Awaiting Innocent: DAT-2 — built on the recommended option B (held-out keys outside the repo until the held-out run);
  if he picks A or C, the repository section's held-out line says the keys are in `eval/cases/heldout/` behind a deny
  rule, or were written by Innocent.
- Wave and gates: wave 1; no gate. Labels: `slice::docs`, `wave::1`, `lane::direct`.
- Lane: direct — a Markdown file no code or test reads (rule `ticket-lanes`).
- Risk: None (no value is written; AC-5).
- Entry points added or changed: None.
