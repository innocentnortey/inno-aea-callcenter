import type { OpForce, Scenario, ScreenScenarios } from "./types";
import { withLiveQueue } from "./g5-transforms";

const SEEDED: OpForce = { example: "SEEDED" };
const base = { screen: "SCR-7", route: "/staff/oversight", role: "supervisor" } as const;
const s = (x: Omit<Scenario, "screen" | "route" | "role">): Scenario => ({ ...base, ...x });

export const screenScenarios: ScreenScenarios = {
  complete: true,
  scenarios: [
    s({ id: "scr07.default", state: "default", label: "Seeded lanes and the P0 alert", ops: { getOversight: SEEDED }, notes: "FLOW-8/10 seeds carry the Demo seed tag" }),
    s({ id: "scr07.empty", state: "empty", label: "Nothing urgent", ops: { getOversight: { example: "NOTHING_URGENT" } } }),
    s({ id: "scr07.loading", state: "loading", label: "Lane skeletons", ops: { getOversight: { hang: true } } }),
    s({ id: "scr07.error", state: "error", label: "Oversight did not load", ops: { getOversight: { fail: "network" } } }),
    s({ id: "scr07.error-advance", state: "error", label: "The clock did not move", ops: { getOversight: SEEDED, advanceDemoClock: { fail: "network" } }, notes: "Click any advance button" }),
    s({
      id: "scr07.error-reason", state: "error", label: "Server says a reason is missing",
      ops: { getOversight: SEEDED, applyCaseAction: { example: "REASON_REQUIRED", status: 422 } }, notes: "Assign, type a reason, Assign",
    }),
    s({
      id: "scr07.error-version-conflict", state: "error", label: "Case changed under the supervisor",
      ops: { getOversight: SEEDED, applyCaseAction: { example: "VERSION_CONFLICT", status: 409 } }, notes: "Assign, type a reason, Assign",
    }),
    s({
      id: "scr07.stale-lanes-updated", state: "stale", label: "A later read changes the lanes", ops: { getOversight: SEEDED },
      notes: "A reaction swaps the force to AFTER_ADVANCE about 11 s after the first read; the 10 s poll then shows Lanes updated.",
    }),
    s({
      id: "scr07.success-advanced", state: "success", label: "Advance to Monday morning",
      ops: { getOversight: SEEDED, getDemoClock: { example: "START" }, advanceDemoClock: { example: "NEXT_MORNING" } },
      notes: "Click Next business morning; a reaction swaps the oversight and clock reads",
    }),
    s({
      id: "scr07.success-shift-ended", state: "success", label: "End the shift with a customer waiting", staffing: "simulated_on_shift",
      ops: { getOversight: { example: "SEEDED", transform: withLiveQueue(1) }, setStaffing: { example: "TURNED_OFF_WITH_WAITING" } },
      notes: "Turn the switch off; a reaction swaps the oversight read to SHIFT_ENDED_WITH_WAITING",
    }),
    s({
      id: "scr07.success-assigned", state: "success", label: "Assign a case", ops: { getOversight: SEEDED, applyCaseAction: { example: "ASSIGNED" } },
      notes: "Assign, reason, Assign; a reaction removes the case from Unowned",
    }),
    s({
      id: "scr07.success-priority-changed", state: "success", label: "Change a case's priority",
      ops: { getOversight: SEEDED, applyCaseAction: { example: "PRIORITY_CHANGED" } }, notes: "Assign, Change priority, pick one, reason",
    }),
    s({
      id: "scr07.disabled-saving", state: "disabled", label: "Controls disabled while saving",
      ops: { getOversight: SEEDED, advanceDemoClock: { example: "NEXT_MORNING", delayMs: 4000 }, setStaffing: { example: "TURNED_ON", delayMs: 4000 } },
      notes: "Click an advance button and look at the controls for 4 s",
    }),
    s({
      id: "scr07.disabled-no-back", state: "disabled", label: "Demo time is Monday; no back button",
      ops: { getOversight: { example: "AFTER_ADVANCE" }, getDemoClock: { example: "ADVANCED" } }, notes: "The hint line says how to go back",
    }),
    s({
      id: "scr07.staffed-live-queue", state: "default", label: "Staffed, two customers waiting", staffing: "simulated_on_shift",
      ops: { getOversight: { example: "SEEDED", transform: withLiveQueue(2) } }, notes: "R5 live queue line",
    }),
  ],
};
