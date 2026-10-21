import type { Scenario, ScreenScenarios } from "./types";

const s = (x: Omit<Scenario, "screen" | "route" | "role">): Scenario => ({ screen: "SCR-11", route: "/eval", role: "customer", ...x });

export const screenScenarios: ScreenScenarios = {
  complete: true,
  scenarios: [
    s({ id: "scr11.default", state: "default", label: "Held-out and dev runs", ops: { getLatestEval: { example: "BOTH_SPLITS" } } }),
    s({ id: "scr11.empty", state: "empty", label: "No evaluation run yet", ops: { getLatestEval: { example: "NO_RUN" } } }),
    s({ id: "scr11.loading", state: "loading", label: "Skeletons", ops: { getLatestEval: { hang: true } } }),
    s({ id: "scr11.partial-dev-only", state: "partial", label: "Only a dev run exists", ops: { getLatestEval: { example: "DEV_ONLY" } } }),
    s({ id: "scr11.error", state: "error", label: "The report did not load", ops: { getLatestEval: { fail: "network" } } }),
    s({ id: "scr11.error-resetting", state: "error", label: "The demo is resetting", ops: { getLatestEval: { example: "RESET_IN_PROGRESS", status: 503 } } }),
    s({ id: "scr11.stale-run-version", state: "stale", label: "Run used an earlier agent version", ops: { getLatestEval: { example: "STALE_RUN" } } }),
  ],
};
