import type { OpForce, Scenario, ScreenScenarios } from "./types";
import { rebaseMonitoring } from "./g5-transforms";

// The examples' as_of is a fixed Oct 16 timestamp; the screen follows CON-19 (wall-clock), so every read is rebased to now.
const live = (example: string, ageMs = 0): OpForce => ({ example, transform: rebaseMonitoring(ageMs) });
const s = (x: Omit<Scenario, "screen" | "route" | "role">): Scenario => ({ screen: "SCR-10", route: "/monitoring", role: "customer", ...x });

export const screenScenarios: ScreenScenarios = {
  complete: true,
  scenarios: [
    s({ id: "scr10.default", state: "default", label: "Healthy, all alerts quiet", ops: { getMonitoring: live("DEFAULT") } }),
    s({ id: "scr10.alerts-cap-and-latency", state: "default", label: "Spend cap and latency firing", ops: { getMonitoring: live("FIRING") } }),
    s({ id: "scr10.alert-zero-traffic", state: "default", label: "Zero traffic firing", ops: { getMonitoring: live("ZERO_TRAFFIC_FIRING") } }),
    s({ id: "scr10.alert-failure-and-trace", state: "default", label: "Failure rate and trace export firing", ops: { getMonitoring: live("FAILURE_AND_TRACE_FIRING") } }),
    s({ id: "scr10.empty", state: "empty", label: "No conversations since the reset", ops: { getMonitoring: live("EMPTY") } }),
    s({ id: "scr10.loading", state: "loading", label: "Tile skeletons", ops: { getMonitoring: { hang: true } } }),
    s({ id: "scr10.partial-too-few-turns", state: "partial", label: "Latency needs 20 turns", ops: { getMonitoring: live("TOO_FEW_TURNS") } }),
    s({ id: "scr10.error", state: "error", label: "Monitoring did not load", ops: { getMonitoring: { fail: "network" } } }),
    s({ id: "scr10.error-resetting", state: "error", label: "The demo is resetting", ops: { getMonitoring: { example: "RESET_IN_PROGRESS", status: 503 } } }),
    s({ id: "scr10.stale-data-age", state: "stale", label: "Data is five minutes old", ops: { getMonitoring: live("DEFAULT", 5 * 60_000) }, notes: "The line appears at the next 15 s tick" }),
  ],
};
