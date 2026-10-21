import { type ReactElement } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { render } from "@testing-library/react";
import { AnnounceProvider } from "@/components/ui/LiveRegion";
import { SessionProvider } from "@/state/session";
import { DemoStatusProvider } from "@/state/demoStatus";
import { defaultTransport, setTransport, type ApiTransport } from "@/api/transport";
import type { Role } from "@/lib/roles";
import { jsonResponse, makeFakeTransport } from "./fakeTransport";
import { CLOCK_START, SESSION_BY_ROLE, STAFFING_OFF } from "./fixtures";
import { afterEach } from "vitest";
import { buildRoutes } from "@/router";

afterEach(() => setTransport(defaultTransport));

/** A fake transport that answers the shell's own reads (session, staffing, clock) and 404s the rest. */
export function shellTransport(role: Role | null, extra?: (op: string) => Response | undefined, seen?: string[]): ApiTransport {
  return makeFakeTransport((ctx) => {
    seen?.push(ctx.op);
    const e = extra?.(ctx.op);
    if (e) return e;
    switch (ctx.op) {
      case "getSession":
        return role ? jsonResponse(200, SESSION_BY_ROLE[role]) : jsonResponse(401, { error: { code: "UNAUTHENTICATED", details: { reason: "none" } } });
      case "switchRole": {
        const next = JSON.parse(String(ctx.body ? JSON.stringify(ctx.body) : "{}")).role as Role;
        return jsonResponse(200, SESSION_BY_ROLE[next]);
      }
      case "getStaffing": return jsonResponse(200, STAFFING_OFF);
      case "getDemoClock": return jsonResponse(200, CLOCK_START);
      case "logout": return jsonResponse(204);
      default: return jsonResponse(404, { error: { code: "NOT_FOUND" } });
    }
  });
}

export function renderWithProviders(ui: ReactElement, opts: { route?: string; transport?: ApiTransport; role?: Role } = {}) {
  setTransport(opts.transport ?? shellTransport(opts.role ?? "customer"));
  const router = createMemoryRouter(
    [{ path: "*", element: (
      <AnnounceProvider><SessionProvider><DemoStatusProvider>{ui}</DemoStatusProvider></SessionProvider></AnnounceProvider>
    ) }],
    { initialEntries: [opts.route ?? "/"] },
  );
  return { router, ...render(<RouterProvider router={router} />) };
}

/** Renders the real app routes in a memory router, so route tests exercise RequireSession and the stubs. */
export function renderApp(opts: { route: string; role: Role | null; seen?: string[]; extra?: (op: string) => Response | undefined }) {
  setTransport(shellTransport(opts.role, opts.extra, opts.seen));
  const router = createMemoryRouter(buildRoutes(), { initialEntries: [opts.route] });
  return { router, ...render(<RouterProvider router={router} />) };
}
