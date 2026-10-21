// UNIT (fake transport): a 401 on an event stream sends the user to /login?return_to=...&reason=... (G-04).
// The stream here is the real defaultTransport.openStream against a stubbed global fetch; every other call is the fake transport.
// MOCK-ONLY/UNIT evidence. It does not show that a real server answers a stream with 401 (that is a REAL-BACKEND journey).
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createElement } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { defaultTransport, setTransport } from "@/api/transport";
import { buildRoutes } from "@/router";
import { renderApp } from "@/test/render";
import { fakeApi, ok, defaultCase } from "@/screens/scr06/case.fixtures";
import { seededQueue } from "@/screens/scr05/queue.fixtures";
import { specBody, specError } from "@/test/spec";
import type { Role } from "@/lib/roles";
import type { CallContext } from "@/api/transport";
import { configure } from "@testing-library/react";
/** Under the full parallel suite the first lazy screen chunk can take longer than the 1 s default. */
configure({ asyncUtilTimeout: 4000 });

afterEach(() => vi.unstubAllGlobals());

function renderWithRealStream(route: string, role: Role, handler: (ctx: CallContext) => Response | undefined, streamAnswer: Response) {
  const f = vi.fn(async () => streamAnswer.clone());
  vi.stubGlobal("fetch", f);
  const api = fakeApi(role, handler);
  setTransport({ fetch: api.transport.fetch, openStream: defaultTransport.openStream });
  const router = createMemoryRouter(buildRoutes(), { initialEntries: [route] });
  const view = render(createElement(RouterProvider, { router }));
  return { router, f, view };
}
const caseApi = (ctx: CallContext) => (ctx.op === "getCase" ? ok(defaultCase()) : ctx.op === "getQueue" ? ok(seededQueue()) : undefined);
const chatApi = (ctx: CallContext) => (ctx.op === "startChatSession" ? ok(specBody("startChatSession", 201, "STARTED"), 201) : undefined);
const unauth = (name: "UNAUTHENTICATED" | "UNAUTHENTICATED_EXPIRED", op: "streamCaseEvents" | "streamChatEvents") =>
  new Response(JSON.stringify(specError(op, 401, name)), { status: 401 });

describe("UNIT (fake transport): stream 401 -> login with return_to", () => {
  it("the case stream's 401 (expired) lands on /login with the case path as return_to and reason=expired", async () => {
    const { router, f } = renderWithRealStream("/staff/cases/MHC-C-0007", "representative", caseApi, unauth("UNAUTHENTICATED_EXPIRED", "streamCaseEvents"));
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    const q = new URLSearchParams(router.state.location.search);
    expect(q.get("return_to")).toBe("/staff/cases/MHC-C-0007");
    expect(q.get("reason")).toBe("expired");
    expect(f).toHaveBeenCalledTimes(1); // stopped, no reconnect loop
    expect(String((f.mock.calls[0] as unknown[])[0])).toBe("/api/staff/cases/MHC-C-0007/events");
  });

  it("the chat stream's 401 (no session) lands on /login with return_to=/ and reason=none", async () => {
    const { router, f } = renderWithRealStream("/", "customer", chatApi, unauth("UNAUTHENTICATED", "streamChatEvents"));
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    const q = new URLSearchParams(router.state.location.search);
    expect(q.get("return_to")).toBe("/");
    expect(q.get("reason")).toBe("none");
    expect(f).toHaveBeenCalledTimes(1);
  });

  it("a getSession 401 with the expired reason keeps reason=expired through RequireSession (same race as the stream)", async () => {
    const { router } = renderApp({
      route: "/staff/queue", role: null,
      extra: (op) => (op === "getSession" ? new Response(JSON.stringify(specError("getSession", 401, "UNAUTHENTICATED_EXPIRED")), { status: 401 }) : undefined),
    });
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    await new Promise((r) => setTimeout(r, 30));
    const q = new URLSearchParams(router.state.location.search);
    expect(q.get("return_to")).toBe("/staff/queue");
    expect(q.get("reason")).toBe("expired");
  });

  it("logout answered 401 UNAUTHENTICATED (already signed out elsewhere) still ends on /login, with no error shown", async () => {
    const { router } = renderApp({
      route: "/staff/queue", role: "representative",
      extra: (op) => (op === "logout" ? new Response(JSON.stringify(specError("logout", 401, "UNAUTHENTICATED")), { status: 401 }) : op === "getQueue" ? ok(seededQueue()) : undefined),
    });
    fireEvent.click(await screen.findByRole("button", { name: "Sign out" }, { timeout: 4000 }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    await new Promise((r) => setTimeout(r, 40));
    expect(router.state.location.pathname).toBe("/login");
    expect(document.body.textContent).not.toMatch(/UNAUTHENTICATED|undefined/);
  });
});
