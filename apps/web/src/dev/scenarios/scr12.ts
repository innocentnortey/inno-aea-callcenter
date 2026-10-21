import type { ScreenScenarios } from "./types";

export const screenScenarios: ScreenScenarios = {
  complete: true,
  scenarios: [
    { id: "scr12.default", screen: "SCR-12", state: "default", flowState: "first visit (FLOW-12)", label: "First visit", route: "/login", notes: "Signed-out world (the SCR-12 default)." },
    { id: "scr12.loading", screen: "SCR-12", state: "loading", label: "Signing in", route: "/login", ops: { login: { hang: true } }, notes: "Type anything, press Sign in." },
    { id: "scr12.error-refused", screen: "SCR-12", state: "error", flowState: "wrong login (FLOW-12)", label: "Login refused", route: "/login", ops: { login: { example: "LOGIN_FAILED" } } },
    { id: "scr12.error-rate-limited", screen: "SCR-12", state: "error", label: "Too many attempts", route: "/login", ops: { login: { example: "LOGIN_RATE_LIMITED" } }, notes: "Same sentence as refused (decision G-2)." },
    { id: "scr12.error-unreachable", screen: "SCR-12", state: "error", label: "Demo unreachable", route: "/login", ops: { login: { fail: "network" } } },
    {
      // Route is the login page itself: the integrity test ties a SCR-12 scenario to /login.
      id: "scr12.stale-session-ended", screen: "SCR-12", state: "stale", flowState: "session expired on any screen", label: "Sent back after the session ended",
      route: "/login?return_to=%2Fstaff%2Fqueue&reason=expired", notes: "This is the page the foundation redirects to from /staff/queue when a call answers UNAUTHENTICATED_EXPIRED.",
    },
    { id: "scr12.stale-already-signed-in", screen: "SCR-12", state: "stale", flowState: "signed in already", label: "Already signed in", route: "/login", signedIn: true },
    { id: "scr12.success-chat", screen: "SCR-12", state: "success", label: "Sign in lands on the chat", route: "/login", notes: "Sign in with anything: you land on the chat as the customer." },
    {
      id: "scr12.success-asked-page", screen: "SCR-12", state: "success", label: "Sign in lands on the page asked for", route: "/login?return_to=%2Fstaff%2Fqueue&reason=none",
      notes: "Sign in: you land on /staff/queue (as the customer, so the role-gate panel shows).",
    },
    { id: "scr12.disabled-empty-fields", screen: "SCR-12", state: "disabled", label: "Sign in disabled until both fields are filled", route: "/login" },
    { id: "scr12.disabled-in-flight", screen: "SCR-12", state: "disabled", label: "Fields read-only while signing in", route: "/login", ops: { login: { hang: true } } },
  ],
};
