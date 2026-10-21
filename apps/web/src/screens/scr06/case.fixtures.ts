// Test-only: case bodies and a fake API for the SCR-5 / SCR-6 tests, quoted from the OpenAPI examples.
import { createElement } from "react";
import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import type { CallContext } from "@/api/transport";
import { setTransport } from "@/api/transport";
import type { components } from "@/api/types.gen";
import type { Role } from "@/lib/roles";
import { buildRoutes } from "@/router";
import { jsonResponse, makeFakeTransport } from "@/test/fakeTransport";
import { shellTransport } from "@/test/render";
import { specExample } from "./specExample";

type S = components["schemas"];
const getCase = (n: string) => specExample<S["CaseDetail"]>("/api/staff/cases/{reference}", "get", "200", n);
export const defaultCase = () => getCase("DEFAULT");
export const liveJoinedCase = () => getCase("LIVE_JOINED");
export const waitingCase = () => getCase("WAITING");
export const safetyCase = () => getCase("SAFETY_CASE");
export const briefPendingCase = () => getCase("BRIEF_BEING_WRITTEN");
export const trimmedCase = () => getCase("TRIMMED_STOP");
const act = (n: string) => specExample<S["CaseActionResponse"]>("/api/staff/cases/{reference}/actions", "post", "200", n);
export const claimedResponse = () => act("CLAIMED");
export const waitingResponse = () => act("WAITING");
export const resolvedResponse = () => act("RESOLVED");
const live = (n: string) => specExample<S["LiveActionResponse"]>("/api/staff/cases/{reference}/live", "post", "200", n);
export const joinedResponse = () => live("JOINED");
export const sentResponse = () => live("SENT");
export const handedBackResponse = () => live("HANDED_BACK");
export const callReachedResponse = () => specExample<S["ActivityResponse"]>("/api/staff/cases/{reference}/activities", "post", "201", "CALL_REACHED");
export const flagResponse = () => specExample<S["Flag"]>("/api/staff/flags", "post", "201", "ANSWER");
export function apiErrorBody(op: "applyCaseAction" | "liveChatAction" | "getCase", status: string, name: string) {
  const p = op === "getCase" ? "/api/staff/cases/{reference}" : op === "applyCaseAction" ? "/api/staff/cases/{reference}/actions" : "/api/staff/cases/{reference}/live";
  return specExample<unknown>(p, op === "getCase" ? "get" : "post", status, name);
}

export interface Call { op: string; body: unknown; path: string }
/** Fake API: `handler` answers the screen's ops (return undefined to fall through to the shell); every call is recorded in `calls`. */
export function fakeApi(role: Role, handler: (ctx: CallContext) => Response | undefined) {
  const calls: Call[] = [];
  const streams: { onEvent(data: unknown, id: number | null, type: string): void }[] = [];
  const shell = shellTransport(role);
  const transport = makeFakeTransport(
    (ctx, url, init) => {
      if (!["getSession", "switchRole", "getStaffing", "getDemoClock", "logout"].includes(ctx.op)) calls.push({ op: ctx.op, body: ctx.body, path: ctx.path });
      return handler(ctx) ?? shell.fetch(ctx, url, init);
    },
    (spec) => streams.push(spec),
  );
  return { transport, calls, streams };
}
export function renderRoute(route: string, role: Role, handler: (ctx: CallContext) => Response | undefined) {
  const api = fakeApi(role, handler);
  setTransport(api.transport);
  const router = createMemoryRouter(buildRoutes(), { initialEntries: [route] });
  return { ...api, router, ...render(createElement(RouterProvider, { router })) };
}
export const ok = (body: unknown, status = 200) => jsonResponse(status, body);
