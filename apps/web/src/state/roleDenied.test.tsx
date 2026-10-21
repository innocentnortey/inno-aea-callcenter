// UNIT (fake transport), G-06 and G-13: a 403 ROLE_NOT_ALLOWED as a RESPONSE (the demo was reset, or the role changed on the
// server) while the session in the browser still says the old role. Bodies are the spec's own 403 examples.
// Asserted: the screen shows the role panel (not a raw error), getSession is read again, and the role switch shows the new
// role. G-13: the same when it is a case STREAM that answers 403 (it used to stop silently with the live box still "live").
// MOCK-ONLY/UNIT: the sequence a real demo reset produces has not been run against a real server.
import { render, screen, waitFor } from "@testing-library/react";
import { createElement } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { OperationId } from "@/api/client";
import { defaultTransport, setTransport, type CallContext } from "@/api/transport";
import { buildRoutes } from "@/router";
import type { Role } from "@/lib/roles";
import { SESSION_BY_ROLE } from "@/test/fixtures";
import { specError } from "@/test/spec";
import { fakeApi, liveJoinedCase, ok, renderRoute } from "@/screens/scr06/case.fixtures";
import { seededQueue } from "@/screens/scr05/queue.fixtures";
import { configure } from "@testing-library/react";
/** Under the full parallel suite the first lazy screen chunk can take longer than the 1 s default. */
configure({ asyncUtilTimeout: 4000 });

afterEach(() => vi.unstubAllGlobals());

interface Screen { name: string; route: string; role: Role; op: OperationId; background?: (ctx: CallContext) => Response | undefined }
const SCREENS: Screen[] = [
  { name: "SCR-5 queue", route: "/staff/queue", role: "representative", op: "getQueue" },
  { name: "SCR-6 case", route: "/staff/cases/MHC-C-0007", role: "representative", op: "getCase", background: (c) => (c.op === "getQueue" ? ok(seededQueue()) : undefined) },
  { name: "SCR-7 oversight", route: "/staff/oversight", role: "supervisor", op: "getOversight" },
  { name: "SCR-8 flags", route: "/staff/flags", role: "supervisor", op: "listFlags" },
  { name: "SCR-9 owner outcomes", route: "/staff/owner", role: "owner", op: "getOwnerMetrics" },
];

describe("UNIT (fake transport) G-06: a 403 response on a staff read", () => {
  describe.each(SCREENS)("$name", (s) => {
    it("ROLE_NOT_ALLOWED_ROLE_RESET: role panel, session re-read, switch shows Customer", async () => {
      let reset = false;
      let sessions = 0;
      renderRoute(s.route, s.role, (ctx) => {
        if (ctx.op === "getSession") { sessions++; return ok(reset ? SESSION_BY_ROLE.customer : SESSION_BY_ROLE[s.role]); }
        if (ctx.op === s.op) { reset = true; return ok(specError(s.op, 403, "ROLE_NOT_ALLOWED_ROLE_RESET"), 403); }
        return s.background?.(ctx);
      });
      await screen.findByText(/back to the customer role|You're acting as the customer\./, undefined, { timeout: 4000 });
      await waitFor(() => expect(sessions).toBeGreaterThanOrEqual(2));
      await waitFor(() => expect(screen.getAllByRole("radio").some((r) => /^Customer \(demo\), current$/.test(r.getAttribute("aria-label") ?? ""))).toBe(true));
      expect(screen.queryAllByRole("radio").some((r) => /Riley.*current/.test(r.getAttribute("aria-label") ?? ""))).toBe(false);
      expect(document.body.textContent).not.toMatch(/ROLE_NOT_ALLOWED|undefined/);
      expect(document.querySelectorAll("h1").length).toBe(1);
    });

    it("ROLE_NOT_ALLOWED (wrong role, session unchanged): a panel or the ordinary load error, session re-read, no raw error", async () => {
      let sessions = 0;
      renderRoute(s.route, s.role, (ctx) => {
        if (ctx.op === "getSession") { sessions++; return ok(SESSION_BY_ROLE[s.role]); }
        if (ctx.op === s.op) return ok(specError(s.op, 403, "ROLE_NOT_ALLOWED"), 403);
        return s.background?.(ctx);
      });
      await waitFor(() => expect(sessions).toBeGreaterThanOrEqual(2));
      // SCR-5 and SCR-6 have no wrong-role panel (their roles can only be refused after a reset): they show their ordinary load error.
      await waitFor(() => expect(document.body.textContent).toMatch(/You're acting as|back to the customer role|didn't load|Try again/));
      expect(document.body.textContent).not.toMatch(/ROLE_NOT_ALLOWED|undefined/);
      expect(screen.getAllByRole("radio").some((r) => new RegExp(`${SESSION_BY_ROLE[s.role].display_name}.*current`).test(r.getAttribute("aria-label") ?? ""))).toBe(true);
    });
  });
});

describe("UNIT (fake transport) G-13: the case stream answers 403 while the live box is open", () => {
  it("the session is read again, the role gate replaces the live box, and the stream is not retried", async () => {
    let reset = false;
    let sessions = 0;
    const f = vi.fn(async () => { reset = true; return new Response(JSON.stringify(specError("streamCaseEvents", 403, "ROLE_NOT_ALLOWED_ROLE_RESET")), { status: 403 }); });
    vi.stubGlobal("fetch", f);
    const api = fakeApi("representative", (ctx) => {
      if (ctx.op === "getSession") { sessions++; return ok(reset ? SESSION_BY_ROLE.customer : SESSION_BY_ROLE.representative); }
      if (ctx.op === "getCase") return ok(liveJoinedCase());
      if (ctx.op === "getQueue") return ok(seededQueue());
      return undefined;
    });
    setTransport({ fetch: api.transport.fetch, openStream: defaultTransport.openStream });
    const router = createMemoryRouter(buildRoutes(), { initialEntries: ["/staff/cases/MHC-C-0007"] });
    render(createElement(RouterProvider, { router }));
    await screen.findByText(/You're acting as the customer\./, undefined, { timeout: 4000 });
    expect(sessions).toBeGreaterThanOrEqual(2);
    expect(screen.queryByText(/You are replying as Riley/)).toBeNull();
    expect(f).toHaveBeenCalledTimes(1);
    expect(String((f.mock.calls[0] as unknown[])[0])).toBe("/api/staff/cases/MHC-C-0007/events");
  });
});
