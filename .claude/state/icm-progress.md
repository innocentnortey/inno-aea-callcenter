# ICM progress checklist
Tracks context-system maturity only; product stage lives in [`PROJECT-CHECKLIST.md`](../../PROJECT-CHECKLIST.md).
Set up by `icm-project` **1.5.0**, invoked from zero-to-hero **1.9.0** Stage 0 (retrofit), 2026-10-20.
Update the affected row in the same task as the change, with an evidence link.
Status: pending (names its unblocking event) · provisional · established · verified · n/a (reason).

| Milestone | Status | Evidence / owner | Next check — enabled by |
|---|---|---|---|
| Work home, sources and owners located | established | [setup profile](../reference/setup-profile.md); [source register](../../docs/source/source-register.md) | Re-check when the GitLab remote or a VPS copy is created |
| Purpose, audience and domain meaning (representative task) | provisional | [briefing](../../docs/source/aea-call-center-briefing.md); [brief audit](../../docs/analysis/2026-10-20-brief-audit.md); task: invoice INV-204411 dispute → explain, escalate with brief | Stage 1 gate sign-off by Innocent |
| Environment, tools and collaboration | established | [setup profile § Locations](../reference/setup-profile.md#locations-and-environment) | Re-check at first deploy (Railway) or VPS move |
| Blueprint and first delivery step | established | 2026-10-21: PRD 0.4 approved (Stage 4); [system design](../../docs/design/system-design.md) DO-1/DO-2 | Stage 6 gate, then §7 tickets |
| Entry → router → maintenance instruction | established | 2026-10-21: entry rebuilt to the entry template against the [area map](../reference/area-map.md) (70 lines, 6.4 KB); check_context no FAIL | Re-run check_context at every gate |
| Fresh-context route walkthrough | verified | 2026-10-21: 56 links in entry, router and area map resolve; traced "build the fee-bearing change request" (entry → router → area map A5 → DO-3 `request_change` → DO-4 `ChangeRequestDraft` → escalation P2) and "what is the per-turn deadline" (→ system design §8.1) | Re-walk after §7 tickets and the first built slice |
| Code design: planned locations | established | 2026-10-21: [area map](../reference/area-map.md) from [DO-3](../../docs/design/code-design.md) revision 3; reconciled with the slice plan in commit `c0621de` (AEA-08) | Each build ticket changes its own row; verify when §8 builds the first slice |
| Physical scaffold | established | Backend spine: `pyproject.toml`, `src/meridian/` package skeleton, `policy/limits.py`, `web/container.py`, `tests/` and `tests/journeys/` skeleton (AEA-01); frontend [`apps/web/`](../../apps/web/) (UX-4, gate unsigned) | Area map rows turn actual as wave-0/1 tickets land |
| Routes verified against code and tests | provisional | 2026-10-21: A0 types AEA-02 `5c367ad`: `tests/unit/domain`, `tests/unit/ports`, `tests/unit/adapters`, `tests/unit/test_config.py`, `test_import_direction.py::test_domain_ports_config_imports` pass (370 passed) | Each later slice adds its tests; verified at the wave-0 seam audit |
| Routes verified against code and tests | provisional | 2026-10-21: area map A0 → `policy/texts.py` (AEA-03, `2689582`; 14 pass) and A1 → `gates/rules.py` (AEA-05, `0d443ab`; 111 pass); A8 `web/` shell vs `tests/api/`, `tests/unit/web/` (AEA-23; 63 pass) | Each slice adds its route; verified when every area-map row is actual |
| Integrated-journey protection (real path, evidence levels) | provisional | 2026-10-21: [integrated-journeys rule](../rules/integrated-journeys.md) (inventory §1); routed from entry and router; nothing executable yet | First journey record in `docs/testing/journeys/` from the harness ticket (wave 2) |

Last reconciled: 2026-10-21 — AEA-01 scaffold (scaffold row); earlier, DO-3 revision 3 and the area map reconciled with the slice plan (AEA-08, `c0621de`); earlier, integrated-journeys rule routed (journey row); earlier, UX-4 frontend `apps/web/` recorded (scaffold row); earlier, Stage 6: area map, router rows per area, entry rebuilt, walkthrough verified.
