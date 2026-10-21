# Component contracts (DO-4)

**Date:** 2026-10-21. **Status:** DRAFT, revision 3 (reconciled with UX-3); revision 2 came after the `metz-code-design-agent` review
([`../reviews/2026-10-21-code-design-review.md`](../reviews/2026-10-21-code-design-review.md); response in code-design §11). Nothing is built; every type and endpoint here is planned.
**Stage:** zero-to-hero §6, System track. 

## What is here

| File | What it holds | Who reads it |
|---|---|---|
| [`internal-components.md`](internal-components.md) | The typed hand-offs inside the backend, as Pydantic sketches and `Protocol` signatures: code gates → planner, planner output, specialist results, escalation decision, handoff (case, promise, eight-heading brief), turn facts, responder input and output, R-46 checks, the error and halt types, the model ports and the role-typed gateway, the retrieval, clock and trace ports, the unit of work (concrete repositories, no repository Protocols) and the concrete `CaseService` | Builders of areas A0–A12 (see [code-design.md](../code-design.md) §8): each area builds against these types, fakes only the external-system ports, and uses a temp SQLite file for storage |
| [`api-con-mapping.md`](api-con-mapping.md) | For each UI contract CON-1…CON-21: the component that serves it, whether the backend agrees with the UX-3 OpenAPI field by field, the requests UXR-21…UXR-26 to the UX session, recommendations on UX-3's [A] items, and the monitoring-clock answer | The UX session (UX-3 contracts), builders of A8–A10, the eval harness (A11) |
| [`stage7/`](stage7/) | The Stage 7 addenda (2026-10-21): eight files, [`models`](stage7/models.md), [`data`](stage7/data.md), [`cases`](stage7/cases.md), [`web`](stage7/web.md), [`staff`](stage7/staff.md), [`graph-core`](stage7/graph-core.md), [`graph-tools`](stage7/graph-tools.md), [`graph-nodes`](stage7/graph-nodes.md), each the single definition of the shapes it owns; where one disagrees with `internal-components.md`, the addendum wins. Ownership table: `internal-components.md` §16; clashes between addenda: [`merge-clashes.md`](../../plans/7b-decisions/merge-clashes.md) | Builders of every AEA ticket (each addendum lists its tickets) |

## How this relates to the UX contracts

- **The UX session owns CON-1…CON-21.** Their UX-3 specification is
  [`UI_CONTRACTS.md`](../../ux/03-structure/UI_CONTRACTS.md) with
  [`ui-contracts.openapi.yaml`](../../ux/03-structure/ui-contracts.openapi.yaml) (OpenAPI 3.1, 29 operations), written
  2026-10-21 as **proposals, not yet signed by Innocent**. The OpenAPI is the authority for every request and response
  field; DO-4 does not restate them.
- **These files implement the CONs; they do not redefine them.** Where the backend needs a change, `api-con-mapping.md`
  §2 asks for it as a numbered request (UXR-n). Nothing under `docs/ux/` is edited from the System track.
- **When UX-3 is signed,** this table is re-checked against the signed set; the §6 gate needs "DO-4 agrees with the
  signed contracts" (`PROJECT-CHECKLIST.md`).

### Reconciliation with UX-3 (2026-10-21)

UXR-1…UXR-20 are closed (17 adopted, 3 adapted and accepted). **15 of 21 contracts agree field by field; 6 differ, each
by a new request; 0 gaps.**

| CON | Status | Request |
|---|---|---|
| CON-1 Start / resume a chat | agrees | — |
| CON-2 One turn | agrees | UXR-21, UXR-24, UXR-25, UXR-26 adopted by the UX track, 2026-10-21 (`version_label`, `due_label`, alert names checked in the OpenAPI) |
| CON-3 Chat events | agrees | UXR-25 adopted by the UX track, 2026-10-21 (`version_label`, `due_label`, alert names checked in the OpenAPI) |
| CON-4 Talk to a person | agrees | UXR-25 adopted by the UX track, 2026-10-21 (`version_label`, `due_label`, alert names checked in the OpenAPI) |
| CON-5 Follow-up choice | agrees | — |
| CON-6 Demo inbox | agrees | — |
| CON-7 Staffing | agrees | UXR-27 adopted by the UX track, 2026-10-21 (`mhcSession` on the operation; checked in the OpenAPI) |
| CON-8 Demo clock | agrees | — |
| CON-9 Reset | agrees | UXR-27 adopted by the UX track, 2026-10-21 (`mhcSession` on the operation; checked in the OpenAPI) |
| CON-10 Role switch (was staff sign-in) | agrees | UXR-27 adopted by the UX track, 2026-10-21 (`mhcSession` on the operation; checked in the OpenAPI) |
| CON-11 Queue | agrees | — |
| CON-12 Case view | agrees | UXR-24 adopted by the UX track, 2026-10-21 (`version_label`, `due_label`, alert names checked in the OpenAPI) |
| CON-13 Case actions | agrees | — |
| CON-14 Live chat | agrees | — |
| CON-15 Contact activity | agrees | — |
| CON-16 Flags | agrees | UXR-22 adopted by the UX track, 2026-10-21 (`version_label`, `due_label`, alert names checked in the OpenAPI) |
| CON-17 Oversight | agrees | — |
| CON-18 Owner metrics | agrees | — |
| CON-19 Monitoring | agrees | UXR-23 adopted by the UX track, 2026-10-21 (`version_label`, `due_label`, alert names checked in the OpenAPI) |
| CON-20 Latest eval | agrees | — |
| CON-21 Staff case stream (new) | agrees | — |
| CON-22 Demo login (new, R-48) | agrees | `login` / `logout`, cookie `mhc_session`; served by `web/routes/auth.py` and `web/middleware.py` (A8) |

**Result 2026-10-21:** all **22** CONs (30 operations) agree with the UX-3 specified set, after UXR-27 (app-wide demo login and role switch, PRD R-48) was adopted. OpenAPI lint 0 errors; Prism smoke test passed with the cookie scheme. **Innocent signed UX-3 on 2026-10-21**, so DO-4 agrees with the signed set (22/22 CONs, 30 operations); the CONs become "agreed" at the §6 gate. The §6 gate re-checks this table against the set Innocent signs at UX-3.

## Decisions these files apply

SDQ-1…SDQ-10 from [system-design.md](../system-design.md) were decided by Innocent on 2026-10-21: **SDQ-1 a 60 s
per-turn deadline** (then `TURN_TIMEOUT` with *Try again* or a person; the p95 ≤ 12.5 s line is unchanged), and
SDQ-2…SDQ-10 as recommended (whole replies, ingestion-only TLS proxy to the VPS Langfuse, eval and load runs on the same
image on the VPS, CON-3 as async SSE with replay, Sonnet planner fallback, SP-1's call shape plus prompt caching, the
R-46 completion check against every completed action in the conversation, 30 turns in flight then `BUSY`, checkpoints
pruned daily to the last 2). Every other choice that no requirement settles is marked **proposal**.
