_Conventions for every inno-aea-callcenter issue (from the approved breakdown, `docs/plans/slice-plan.md`):_
repository `/home/linuxuser/workspaces/inno-aea-callcenter` (package `src/meridian/`, tests `tests/`, eval `eval/`); GitLab
`innocentnortey/inno-aea-callcenter`. Read first: `CLAUDE.md`, `.claude/README.md`, `.claude/reference/area-map.md`, the
slice plan's row for this issue, `docs/design/code-design.md` (DO-3) and `docs/design/contracts/internal-components.md`
(DO-4: exact types and signatures). Vocabulary: PRD R-n, US-n, WP-n, HP-n, WF-n, CAP-n, E-n, M-n, CON-n as their owner
documents define them. Workflow: `lane::build-loop` issues run plan (`fanout-planner`, plan meets
`to-tickets/templates/implementation-plan.md`) → implement (`fanout-implementer`) → test → `code-review-agent`; affected tests
only (`.claude/rules/build-loop-test-scope.md`); `risk::security` issues get frozen failing tests first and the security
agent at their wave merge. **Every `lane::build-loop` issue carries exactly one `[journey]` criterion**
(`.claude/rules/integrated-journeys.md`; slice plan §0a): it extends or runs the journeys of the §0a map that its code touches, in
`tests/journeys/j<N>/test_aea_<NN>.py` (one file per issue per journey; `support/` is AEA-57's and `browser/` AEA-58's, never
edited by others), states its verification level (`mock-tested`, `integrated with a scripted model`, `verified with live
models`) and names *Blocked by* when the harness or the journey's landing issue has not merged; a bug fix first reproduces the
failure as a journey step and, when it changes a guard, also asserts that the legitimate path still passes. **Route issues**
(AEA-23, AEA-40…AEA-48) add the server cases of the operations they serve to their own `tests/contract/cases/<route>.py`;
AEA-59 owns the runner, and from the wave-3 merge an operationId with no case fails it. **Siblings in the same or a later wave are called through their DO-4 signature by injection
(constructor, `GraphDeps`, or `web/deps.py`) and tested with a double; a plan that needs more than that signature records
`blocked-on AEA-NN` instead of inventing behaviour.** Never: edit the briefing, issued data or `docs/archive/`; edit
`docs/ux/03-structure/ui-contracts.openapi.yaml` or `UI_CONTRACTS.md` (a needed change stops the issue and goes to
Innocent); touch `apps/web/**` or `docs/ux/**`; edit another issue's owned file (collision map, slice plan §3); put a
secret, verification code, card-like number or full phone number in code, logs, traces, fixtures or test names; call a
paid model in a default test (mark `live`); bind ports 4019 or 5184; `git add -A`. Evidence: every criterion names its
test or command and the result a reviewer should see; numbers come from runs, never from targets.
