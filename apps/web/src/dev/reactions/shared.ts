import type { components } from "@/api/types.gen";
import { setSessionCookie } from "../session-fake";
import { setWorld } from "../world";
import type { Reaction } from "../scenarios/types";

type SessionInfo = components["schemas"]["SessionInfo"];

export const reactions: Reaction[] = [
  {
    when: { op: "login", status: 200 },
    then: ({ response }) => {
      const session = (response?.body as { session?: SessionInfo } | undefined)?.session;
      setWorld({ signedIn: true, role: "customer", sessionBody: session ?? null });
      setSessionCookie();
    },
  },
  {
    // The fake cookie stays set: Prism's own 401 has no named error body, so the dev layer emulates "signed out" itself.
    when: { op: "logout" },
    then: () => setWorld({ signedIn: false, sessionBody: null }),
  },
  {
    when: { op: "switchRole", status: 200 },
    then: ({ response }) => {
      const s = response?.body as SessionInfo | undefined;
      if (s) setWorld({ role: s.role, sessionBody: s.role === "customer" ? null : s });
    },
  },
  {
    when: { op: "setStaffing", status: 200 },
    then: ({ request }) => {
      const mode = (request as { mode?: string } | undefined)?.mode;
      setWorld({ staffing: mode === "simulated_on_shift" ? "simulated_on_shift" : "nobody_online" });
    },
  },
  {
    when: { op: "resetDemo", status: 200 },
    then: (ctx) => {
      setWorld({ role: "customer", sessionBody: null, roleResetPending: true, staffing: "nobody_online" });
      ctx.refetch();
    },
  },
];
