// Cross-screen scenarios, available on any screen. Ids start with `shared.`.
import type { ScreenScenarios } from "./types";

export const screenScenarios: ScreenScenarios = {
  complete: true,
  scenarios: [
    {
      id: "shared.session-ended", screen: "*", state: "error", label: "Session ended (expired)", route: "/",
      ops: { getSession: { example: "UNAUTHENTICATED_EXPIRED", status: 401 } },
    },
    {
      id: "shared.role-reset", screen: "*", state: "error", label: "Role reset by a demo reset", route: "/staff/queue", role: "representative",
      ops: { getQueue: { example: "ROLE_NOT_ALLOWED_ROLE_RESET", status: 403 }, getOversight: { example: "ROLE_NOT_ALLOWED_ROLE_RESET", status: 403 }, getCase: { example: "ROLE_NOT_ALLOWED_ROLE_RESET", status: 403 } },
    },
    { id: "shared.staffing-on", screen: "*", state: "default", label: "Simulated staffing on", route: "/", staffing: "simulated_on_shift" },
    { id: "shared.staffing-off", screen: "*", state: "default", label: "Nobody online", route: "/", staffing: "nobody_online" },
    {
      id: "shared.offline", screen: "*", state: "error", label: "Offline (network failure)", route: "/",
      ops: { getSession: { fail: "network" }, getStaffing: { fail: "network" }, getDemoClock: { fail: "network" } },
    },
    {
      id: "shared.slow", screen: "*", state: "loading", label: "Slow (4 s on every shared read)", route: "/",
      ops: { getSession: { example: "CUSTOMER", delayMs: 4000 }, getStaffing: { example: "OFF", delayMs: 4000 }, getDemoClock: { example: "START", delayMs: 4000 } },
    },
  ],
};
