import type { components } from "@/api/types.gen";
import type { Scenario, ScreenScenarios } from "./types";
import { addNeedsRow, claimedByMe, moveLiveToNeeds, queueChange } from "./case-transforms";

type QueueRow = components["schemas"]["QueueRow"];
// The MHC-C-0012 row of the getQueue STAFFED_WITH_WAITING example, unassigned (a handoff nobody has claimed).
const HANDOFF_ROW: QueueRow = {
  reference: "MHC-C-0012", priority: { level: "P3", word: "Standard" }, reason: "Asked for a person", customer_display_name: "Omar Patel", owner: null,
  created_at: "2026-10-16T14:14:00-05:00", due_at: null, due_label: null, due_state: "no_due_time", wake_up_at: null, lifecycle: "unassigned",
  follow_up_short: null, seed: false, brief_status: "ready", queued_at: null, age_label: "Open 6 min",
};
const ROUTE = "/staff/queue";
const base = { screen: "SCR-5", route: ROUTE } as const;
const SEEDED = { example: "SEEDED" };

const scenarios: Scenario[] = [
  { ...base, id: "scr05.default", state: "default", label: "Seeded queue, nobody on shift", ops: { getQueue: SEEDED }, notes: "Four rows in server order (0008 first); Overdue on 0005." },
  { ...base, id: "scr05.empty", state: "empty", label: "All caught up", ops: { getQueue: { example: "ALL_CAUGHT_UP" } } },
  { ...base, id: "scr05.loading", state: "loading", label: "Queue loading", ops: { getQueue: { hang: true } } },
  { ...base, id: "scr05.partial-brief-pending", state: "partial", label: "A brief is still being written", ops: { getQueue: { example: "BRIEF_BEING_WRITTEN" } } },
  { ...base, id: "scr05.error", state: "error", label: "Queue fails, then loads", ops: { getQueue: { sequence: [{ fail: "network" }, SEEDED] } }, notes: "Try again loads the seeded queue." },
  {
    ...base, id: "scr05.stale-cases-changed", state: "stale", label: "Two cases changed", ops: { getQueue: { sequence: [SEEDED, { example: "SEEDED", transform: queueChange({
      "MHC-C-0006": { owner: "Demo supervisor", lifecycle: "claimed" }, "MHC-C-0005": { owner: "Demo supervisor", lifecycle: "claimed" },
    }) }] } }, notes: "Wait 10 s or refocus the tab: '2 cases changed. Show them.'; the selected row does not move.",
  },
  {
    ...base, id: "scr05.success-resolved-return", state: "success", label: "Return from a resolved case", route: "/staff/cases/MHC-C-0007", screen: "*", role: "representative",
    ops: { getCase: { example: "DEFAULT", transform: claimedByMe } },
    notes: "Resolve with any outcome to land on /staff/queue with 'MHC-C-0007 resolved.' for 4 s; the case director also removes the row.",
  },
  { ...base, id: "scr05.success-claimed-row", state: "success", label: "A claimed row shows its owner", ops: { getQueue: { example: "SEEDED", transform: queueChange({ "MHC-C-0007": { owner: "Riley", lifecycle: "claimed" } }) } } },
  { ...base, id: "scr05.disabled-no-live-queue", state: "disabled", label: "Nobody on shift: no live queue", ops: { getQueue: SEEDED }, notes: "The Waiting in chat region explains how to turn the simulation on." },
  { ...base, id: "scr05.live-queued", state: "default", flowState: "live-queued customer (FLOW-8)", label: "A customer waiting in chat", staffing: "simulated_on_shift", ops: { getQueue: { example: "STAFFED_WITH_WAITING" } }, notes: "Row MHC-C-0012 'Waiting since 2:14 pm' with Claim and join." },
  { ...base, id: "scr05.new-handoff", state: "stale", flowState: "new handoff from the chat (FLOW-7)", label: "A new handoff arrives", ops: { getQueue: { sequence: [SEEDED, { example: "SEEDED", transform: addNeedsRow(HANDOFF_ROW) }] } }, notes: "After 10 s: '1 case changed. Show them.'" },
  {
    ...base, id: "scr05.shift-ended", state: "stale", flowState: "shift ended before claim (FLOW-8)", label: "The shift ends with a customer waiting", staffing: "simulated_on_shift",
    ops: { getQueue: { sequence: [{ example: "STAFFED_WITH_WAITING" }, { example: "STAFFED_WITH_WAITING", transform: moveLiveToNeeds() }] } },
    notes: "After 10 s staffing flips to nobody online and the row moves to Needs my action with its original creation time.",
  },
  {
    ...base, id: "scr05.overdue-after-advance", state: "stale", flowState: "overdue after the clock advances (FLOW-10)", label: "The clock moves: 0006 turns overdue",
    ops: { getQueue: { sequence: [SEEDED, { example: "SEEDED", transform: queueChange({ "MHC-C-0006": { due_state: "overdue" } }) }] } }, notes: "After 10 s: '1 case changed. Show them.', then the Overdue tag on 0006.",
  },
];
export const screenScenarios: ScreenScenarios = { complete: true, scenarios };
