import type { Role } from "@/api/client";
import type { Scenario, ScreenScenarios } from "./types";

const THREE = { example: "THREE" } as const;
const s = (x: Omit<Scenario, "screen" | "route" | "role"> & { role?: Role }): Scenario => ({ screen: "SCR-8", route: "/staff/flags", role: "supervisor", ...x });

export const screenScenarios: ScreenScenarios = {
  complete: true,
  scenarios: [
    s({ id: "scr08.default", state: "default", label: "One new flag", ops: { listFlags: THREE } }),
    s({ id: "scr08.empty", state: "empty", label: "No flags yet", ops: { listFlags: { example: "EMPTY" } }, notes: "FLOW-12: also what a reset leaves" }),
    s({ id: "scr08.loading", state: "loading", label: "Row skeletons", ops: { listFlags: { hang: true } } }),
    s({ id: "scr08.error", state: "error", label: "The review list did not load", ops: { listFlags: { fail: "network" } } }),
    s({
      id: "scr08.error-review-forbidden", state: "error", label: "Review refused: supervisors only",
      ops: { listFlags: THREE, reviewFlag: { example: "ROLE_NOT_ALLOWED", status: 403 } }, notes: "Mark reviewed, confirm",
    }),
    s({
      id: "scr08.error-flag-gone", state: "error", label: "Flag gone after a reset",
      ops: { listFlags: THREE, reviewFlag: { example: "FLAG_NOT_FOUND", status: 404 } }, notes: "Mark reviewed, confirm",
    }),
    s({
      id: "scr08.stale-new-flag", state: "stale", label: "A new flag arrives while the page is open", ops: { listFlags: THREE },
      notes: "A reaction adds a flag about 3 s after the first read; the 15 s poll shows the line",
    }),
    s({ id: "scr08.success-reviewed", state: "success", label: "Mark a flag reviewed", ops: { listFlags: THREE, reviewFlag: { example: "REVIEWED" } }, notes: "Mark reviewed, optional note, confirm" }),
    s({ id: "scr08.disabled-rep", state: "disabled", label: "Representative: review disabled", role: "representative", ops: { listFlags: THREE } }),
  ],
};
