import type { Scenario, ScreenScenarios } from "./types";
import { withNullPromises } from "./g5-transforms";

const SEEDED = { example: "SEEDED" } as const;
const s = (x: Omit<Scenario, "screen" | "route" | "role">): Scenario => ({ screen: "SCR-9", route: "/staff/owner", role: "owner", ...x });

export const screenScenarios: ScreenScenarios = {
  complete: true,
  scenarios: [
    s({ id: "scr09.default", state: "default", label: "Seeded outcomes", ops: { getOwnerMetrics: SEEDED, getDemoClock: { example: "START" } } }),
    s({ id: "scr09.empty", state: "empty", label: "No outcomes yet", ops: { getOwnerMetrics: { example: "EMPTY" } }, notes: "FLOW-12: also what a reset leaves" }),
    s({ id: "scr09.loading", state: "loading", label: "Tile and table skeletons", ops: { getOwnerMetrics: { hang: true } } }),
    s({
      id: "scr09.partial", state: "partial", label: "Promises tile has no denominator",
      ops: { getOwnerMetrics: { example: "SEEDED", transform: withNullPromises } }, notes: "The promises tile shows a dash and its reason",
    }),
    s({ id: "scr09.error", state: "error", label: "Outcomes did not load", ops: { getOwnerMetrics: { fail: "network" } } }),
    s({
      id: "scr09.stale-clock-moved", state: "stale", label: "Demo clock moved since the numbers",
      ops: { getOwnerMetrics: SEEDED, getDemoClock: { example: "ADVANCED" } }, notes: "Numbers are as of Friday 2:20 pm; the demo clock reads Monday 7:00 am",
    }),
    s({
      id: "scr09.disabled-zero-denominator", state: "disabled", label: "Zero denominator is not a link",
      ops: { getOwnerMetrics: { example: "SEEDED", transform: withNullPromises } }, notes: "No cases to open. on the promises and estimate tiles",
    }),
  ],
};
