import type { ScreenScenarios } from "./types";

export const screenScenarios: ScreenScenarios = {
  complete: true,
  scenarios: [
    { id: "scr04.default", screen: "SCR-4", state: "default", label: "Four roles, Customer current", route: "/role", ops: { listDemoRoles: { example: "ROLES" } } },
    { id: "scr04.loading", screen: "SCR-4", state: "loading", label: "Switching (4 s)", route: "/role", ops: { switchRole: { example: "TO_REPRESENTATIVE", delayMs: 4000 } }, notes: "Click Representative: 'Switching...' for 4 s." },
    { id: "scr04.error-network", screen: "SCR-4", state: "error", label: "Switch fails (network)", route: "/role", ops: { switchRole: { fail: "network" } }, notes: "Couldn't switch role. Try again." },
    { id: "scr04.error-reset-in-progress", screen: "SCR-4", state: "error", label: "Switch fails (reset in progress)", route: "/role", ops: { switchRole: { example: "RESET_IN_PROGRESS" } }, notes: "503." },
    { id: "scr04.stale-session-ended", screen: "SCR-4", state: "stale", label: "Session ended", route: "/role", ops: { listDemoRoles: { example: "UNAUTHENTICATED_EXPIRED" } }, notes: "Goes to the login screen with the ended line." },
    {
      // Route is a staff path, so the screen is "*" (the integrity test ties a SCR-4 scenario to /role).
      id: "scr04.stale-staff-as-customer", screen: "*", state: "stale", label: "Staff screen opened as Customer", route: "/staff/queue", role: "customer",
      notes: "No forced op: the foundation's role emulation answers 403 and the role-gate panel shows. SCR-4 stale (b).",
    },
    {
      id: "scr04.stale-role-reset", screen: "*", state: "stale", label: "Role reset by a demo reset", route: "/staff/queue", role: "customer",
      ops: { getQueue: { example: "ROLE_NOT_ALLOWED_ROLE_RESET" } }, notes: "'The demo was reset, so you're back to the customer role. Pick a role again.' SCR-4 stale (b).",
    },
    { id: "scr04.success-lands-on-home", screen: "SCR-4", state: "success", label: "Pick a role, land on its home", route: "/role", notes: "Click a role: you land on its home." },
    { id: "scr04.success-stays", screen: "*", state: "success", label: "Role switch on the demo guide stays", route: "/demo", notes: "Use the role switch in the header on /demo: the page stays." },
    { id: "scr04.disabled-during-switch", screen: "SCR-4", state: "disabled", label: "All four disabled while switching", route: "/role", ops: { switchRole: { hang: true } }, notes: "Click a role: all four are disabled." },
  ],
};
