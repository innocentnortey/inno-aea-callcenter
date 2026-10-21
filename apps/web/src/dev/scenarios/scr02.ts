import type { ScreenScenarios } from "./types";

const ONE = { example: "ONE_ACTIVE" };
const EMPTY = { example: "EMPTY" };
const USED = { example: "USED_AND_EXPIRED" };

export const screenScenarios: ScreenScenarios = {
  complete: true,
  scenarios: [
    { id: "scr02.default", screen: "SCR-2", state: "default", flowState: "code arrives (FLOW-3)", label: "One active code", route: "/demo/inbox", ops: { listDemoInbox: ONE } },
    { id: "scr02.empty", screen: "SCR-2", state: "empty", label: "No codes yet", route: "/demo/inbox", ops: { listDemoInbox: EMPTY } },
    {
      id: "scr02.empty-after-reset", screen: "SCR-2", state: "empty", flowState: "reset (FLOW-12)", label: "Empty after a demo reset", route: "/demo/inbox", ops: { listDemoInbox: ONE },
      notes: "Reached by: open this, go to /demo, reset the demo, come back: the reaction empties the inbox.",
    },
    { id: "scr02.loading", screen: "SCR-2", state: "loading", label: "Loading (skeleton stays)", route: "/demo/inbox", ops: { listDemoInbox: { hang: true } }, notes: "The skeleton stays until you leave." },
    { id: "scr02.error", screen: "SCR-2", state: "error", label: "Inbox did not load (reset in progress)", route: "/demo/inbox", ops: { listDemoInbox: { example: "RESET_IN_PROGRESS" } }, notes: "CON-6 503." },
    { id: "scr02.error-rate-limited", screen: "SCR-2", state: "error", label: "Inbox did not load (rate limited)", route: "/demo/inbox", ops: { listDemoInbox: { example: "REQUEST_RATE_LIMITED" } }, notes: "429." },
    { id: "scr02.error-network", screen: "SCR-2", state: "error", label: "Inbox did not load (network)", route: "/demo/inbox", ops: { listDemoInbox: { fail: "network" } } },
    {
      id: "scr02.stale-new-code", screen: "SCR-2", state: "stale", flowState: "code arrives (FLOW-3)", label: "A new code arrives", route: "/demo/inbox",
      ops: { listDemoInbox: { sequence: [EMPTY, EMPTY, ONE] } },
      notes: "Starts empty; within about 10 s a code appears and 'New code received' is announced. The first two calls are consumed by StrictMode's double mount.",
    },
    { id: "scr02.stale-used-and-expired", screen: "SCR-2", state: "stale", flowState: "code used", label: "Used and expired codes", route: "/demo/inbox", ops: { listDemoInbox: USED }, notes: "Used and Expired rows." },
    {
      id: "scr02.stale-expires-on-refresh", screen: "SCR-2", state: "stale", label: "Active code expires on refresh", route: "/demo/inbox",
      ops: { listDemoInbox: { sequence: [ONE, ONE, USED] } },
      notes: "Active at first; after a refresh the first code is Expired and a Used one is announced as new.",
    },
    { id: "scr02.success-copied", screen: "SCR-2", state: "success", label: "Copy a code", route: "/demo/inbox", ops: { listDemoInbox: ONE }, notes: "Press Copy code: 'Copied' shows for 2 s." },
    { id: "scr02.disabled-used-expired", screen: "SCR-2", state: "disabled", label: "Copy disabled (used, expired)", route: "/demo/inbox", ops: { listDemoInbox: USED }, notes: "Copy is disabled with the status word as the reason." },
  ],
};
