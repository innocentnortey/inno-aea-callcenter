# Final cross-reference pass, slice A (graph-core.md, web.md)

2026-10-21. One line per fix: file, what, why. Items 1–3 of the pass brief (`GraphOutcome.turn_trace` / `TurnTrace`,
`LoginSessionId` in `domain/staff.py`, STF-4 and the single `get_staff_access()` declaration) were already in both files
when this agent started; checked, nothing undone.

| File | What | Why |
|---|---|---|
| `stage7/graph-core.md` §12 (new) | Added AEA-02's consolidated `Settings` sketch: provider keys, `models: ModelSettings`, the four optional Langfuse values incl. `langfuse_project_id` (`LANGFUSE_PROJECT_ID`) with `langfuse_complete()` / `langfuse_export()`, demo login pair, `session_secret`, optional `eval_key`, the four web flags, `data_dir`, `index_dir`, `issued_db_path`, `agent_version`, `role_model_map()`; what is not in `Settings` (limits, the parked `.env.example` names) | Pass item 5: the field list was spread over five files (data §9.1, web GRA row, models §4/§7, two closing-table rows), so no one place proved `LANGFUSE_PROJECT_ID` is in it. The previous agent's sketch had not landed |
| `stage7/graph-core.md` intro, closing table (models 3 / data 1; web settings) | Point to §12; ledger range GRC-1…GRC-22 | One owner for the list; the rows keep their history |
| `stage7/graph-core.md` §2 `TurnTrace.specialists_run` | "each SpecialistResult's specialist" → its `kind` | `SpecialistResult` is discriminated on `kind` (DO-4 §5); it has no `specialist` field |
| `stage7/graph-core.md` §7 | `SpendLimits` / `WebLimits` cite their defining files (models.md §6, web.md §5) | Pass item 5/6: one definition, cited by the user |
| `plans/7b-decisions/graph-core.md` | GRC-22 row; counts line | Records §12 |
| `stage7/web.md` §8 step 2 | `HandoffRequest` now carries `thread_id` and `rule_id="CON4.person"`; identity from `core.reads.identity_state(thread_id)` | DO-4 §7 makes `thread_id` and `rule_id` required and no CON-4 rule id existed; cases.md §1.2's `identity_state` is the one identity read (graph-core X-4) |
| `stage7/web.md` §8 and GRA cross-topic row | `HandoffBlockView \| LiveQueuedBlockView` → `HandoffBlock \| LiveQueuedBlock` | The `…View` names were defined nowhere; `domain/blocks.py`'s `ReplyBlock` members follow the OpenAPI schema names (`QuickChecksBlock`, `EmergencyLineBlock`) |
| `stage7/web.md` GRA Settings row | Points to graph-core §12 (GRC-22) | One field list |
| `plans/7b-decisions/web.md` | WEB-22 row notes the change; new *Final cross-reference pass* section (also marks MC-3's `domain/common.py` note superseded) | Decision row changed |

## For the coordinator (owners' files, not edited)

- `docs/plans/tickets/AEA-01.md` (§3, handoff) and `AEA-02.md:58` still give `config.py` / `ModelSettings` to AEA-01;
  the slice plan (row AEA-02, line 156) and MC-21 give it to AEA-02. Ticket files are out of this pass's scope.
- The sweep found no other mismatch between web.md / graph-core.md and the owners (staff §1–§2, cases §1.2, §3.3, §5,
  §7, §9, models §4, §6, graph-nodes §1, §4, graph-tools §2, §5, DO-4 §3, §5, §7, §9, §13, §14).
