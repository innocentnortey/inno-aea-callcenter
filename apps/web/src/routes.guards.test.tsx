// UNIT (fake transport), class (d): navigation guards for EVERY screen and EVERY role, derived from the route table (src/routes.ts).
// - a role the screen does not allow sees the role panel, its data call is never made, and the role switch is there;
// - an allowed role sees no panel and its data call is made;
// - a signed-out visit to any guarded route lands on /login?return_to=<path>&reason=none (the public login stays put);
// - an unknown path shows the not-found page with one h1;
// - SCR-6 for the supervisor and the owner: the owner is read-only, the supervisor's refused live/contact writes read as role errors.
// MOCK-ONLY/UNIT: the cookie and the real 401/403 are the server's; here the fake transport decides. Not REAL-BACKEND.
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { OperationId } from "@/api/client";
import type { CallContext } from "@/api/transport";
import { ROLES, type Role } from "@/lib/roles";
import { SCREENS } from "@/routes";
import { renderApp } from "@/test/render";
import { specBody, specError } from "@/test/spec";
import { defaultCase, liveJoinedCase, ok, renderRoute } from "@/screens/scr06/case.fixtures";
import { seededQueue } from "@/screens/scr05/queue.fixtures";
import { configure } from "@testing-library/react";
/** Under the full parallel suite the first lazy screen chunk can take longer than the 1 s default. */
configure({ asyncUtilTimeout: 4000 });

beforeEach(() => { vi.spyOn(console, "error").mockImplementation(() => undefined); });
afterEach(() => cleanup());

const DATA_OP: Partial<Record<string, OperationId>> = { "SCR-5": "getQueue", "SCR-6": "getCase", "SCR-7": "getOversight", "SCR-8": "listFlags", "SCR-9": "getOwnerMetrics", "SCR-10": "getMonitoring", "SCR-11": "getLatestEval", "SCR-2": "listDemoInbox" };
const pathOf = (p: string) => p.replace(":reference", "MHC-C-0007");
const guarded = SCREENS.filter((s) => !s.public);
const GATE = /You're acting as/;

describe("UNIT (fake transport) (d): the role gate on every screen, for every role", () => {
  const cases = guarded.flatMap((s) => ROLES.map((r) => [`${s.id} ${s.title} as ${r}`, s, r] as const));
  it("covers all 11 guarded screens and 4 roles", () => expect(cases).toHaveLength(11 * 4));
  it.each(cases)("%s", async (_l, s, role) => {
    const seen: string[] = [];
    renderApp({ route: pathOf(s.path), role: role as Role, seen });
    await waitFor(() => expect(document.querySelectorAll("h1").length).toBeGreaterThan(0), { timeout: 4000 });
    await new Promise((r) => setTimeout(r, 30));
    const op = DATA_OP[s.id];
    const allowed = s.roles.includes(role as Role);
    if (allowed) {
      expect(document.body.textContent).not.toMatch(GATE);
      if (op) await waitFor(() => expect(seen).toContain(op));
    } else {
      expect(document.body.textContent).toMatch(GATE);
      expect(screen.getAllByRole("radiogroup", { name: "Acting as" }).length).toBeGreaterThan(0); // the way out is on the page
      if (op) expect(seen).not.toContain(op);
    }
    expect(document.querySelectorAll("h1").length).toBe(1);
  }, 15_000);
});

describe("UNIT (fake transport) (d): signed out", () => {
  it.each(guarded.map((s) => [`${s.id} ${pathOf(s.path)}`, s] as const))("%s goes to /login with return_to and reason=none", async (_l, s) => {
    const { router } = renderApp({ route: pathOf(s.path), role: null });
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    await new Promise((r) => setTimeout(r, 30));
    const q = new URLSearchParams(router.state.location.search);
    expect(q.get("return_to")).toBe(pathOf(s.path));
    expect(q.get("reason")).toBe("none");
  });
  it("the login page itself is not redirected", async () => {
    const { router } = renderApp({ route: "/login", role: null });
    await screen.findByLabelText("Username", undefined, { timeout: 4000 });
    expect(router.state.location.pathname).toBe("/login");
  });
  it("an unknown path shows the not-found page with one h1 and a way back", async () => {
    renderApp({ route: "/no/such/page", role: "customer" });
    await screen.findByRole("heading", { level: 1, name: "Page not found" });
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("link", { name: "Back to the start" }).getAttribute("href")).toBe("/");
  });
});

describe("UNIT (fake transport) (d): SCR-6 for the supervisor and the owner", () => {
  const bg = (c: ReturnType<typeof defaultCase>) => (ctx: CallContext): Response | undefined => (ctx.op === "getCase" ? ok(c) : ctx.op === "getQueue" ? ok(seededQueue()) : undefined);
  it("owner on a joined live chat: read-only line, no Send, no hand back, no menu, no queue call", async () => {
    const { calls } = renderRoute("/staff/cases/MHC-C-0007", "owner", bg(liveJoinedCase()));
    await screen.findByText("Read-only for the business owner role");
    expect(screen.queryByRole("button", { name: "Send" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Hand back to the assistant" })).toBeNull();
    expect(screen.queryByRole("button", { name: "More actions" })).toBeNull();
    expect(calls.some((c) => c.op === "getQueue")).toBe(false);
  });
  it("supervisor on a joined live chat: sending is refused with the spec's 403, shown as a role sentence, never as a code", async () => {
    const { calls } = renderRoute("/staff/cases/MHC-C-0007", "supervisor", (ctx) => (ctx.op === "liveChatAction" ? ok(specError("liveChatAction", 403, "NOT_CLAIMED_BY_YOU"), 403) : bg(liveJoinedCase())(ctx)));
    await screen.findByText(/You are replying as/);
    fireEvent.change(screen.getByLabelText("Reply"), { target: { value: "Hi" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(calls.some((c) => c.op === "liveChatAction")).toBe(true));
    await screen.findByText("Claim the case first.");
    expect(document.body.textContent).not.toMatch(/NOT_CLAIMED_BY_YOU|ROLE_NOT_ALLOWED/);
  });
  it("supervisor logging a call that the server refuses (ROLE_NOT_ALLOWED) reads as a role sentence", async () => {
    const c = defaultCase();
    c.case.lifecycle = "claimed";
    c.case.allowed_actions = ["start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag", "assign", "change_priority"];
    renderRoute("/staff/cases/MHC-C-0007", "supervisor", (ctx) => (ctx.op === "recordContactActivity" ? ok(specError("recordContactActivity", 403, "ROLE_NOT_ALLOWED"), 403) : bg(c)(ctx)));
    await userEvent.click(await screen.findByRole("button", { name: "Log a call" }));
    fireEvent.click(screen.getByLabelText("Reached the customer"));
    fireEvent.click(screen.getByRole("button", { name: "Record" }));
    await screen.findByText(/You can't do that as/);
    expect(document.body.textContent).not.toMatch(/ROLE_NOT_ALLOWED/);
  });
  it("sanity: the spec examples used above exist", () => {
    expect(specBody("getCase", 200, "LIVE_JOINED")).toBeTruthy();
  });
});
