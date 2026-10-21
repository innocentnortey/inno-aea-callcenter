// UNIT (fake transport), G-08 (class c): a 429 or 503 on a POLLED read, after the first read succeeded.
// SCR-2 (5 s), SCR-5 (10 s), SCR-6 queue rail (10 s), SCR-7 (10 s), SCR-8 (15 s), SCR-10 (30 s) keep polling. The poll's answer
// is the spec's own REQUEST_RATE_LIMITED / RESET_IN_PROGRESS example. Asserted: the list already on screen stays, no raw code
// appears, nothing throws, and the next good answer is shown. Fake timers; no real clock. MOCK-ONLY/UNIT evidence.
import { act, cleanup, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { OperationId } from "@/api/client";
import type { CallContext } from "@/api/transport";
import type { Role } from "@/lib/roles";
import { allErrorCodes, specBody, specError } from "@/test/spec";
import { captureConsoleErrors, errorSpy } from "@/test/readTargets";
import { ok, renderRoute } from "./scr06/case.fixtures";
import { configure } from "@testing-library/react";
/** Under the full parallel suite the first lazy screen chunk can take longer than the 1 s default. */
configure({ asyncUtilTimeout: 4000 });

interface Poll { name: string; route: string; role: Role; op: OperationId; example: string; pollMs: number; marker: RegExp; bg?: (ctx: CallContext) => Response | undefined }
const inboxLine = (specBody<{ messages: { body: string }[] }>("listDemoInbox", 200, "ONE_ACTIVE").messages[0].body).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
// Only the polled reads whose operation lists a 429 or 503 in the spec: listDemoInbox (5 s), getMonitoring (30 s), getStaffing (10 s, 429 only).
const POLLS: [Poll, [number, string][]][] = [
  [{ name: "SCR-2 inbox", route: "/demo/inbox", role: "customer", op: "listDemoInbox", example: "ONE_ACTIVE", pollMs: 5000, marker: new RegExp(inboxLine) }, [[429, "REQUEST_RATE_LIMITED"], [503, "RESET_IN_PROGRESS"]]],
  [{ name: "SCR-10 monitoring", route: "/monitoring", role: "customer", op: "getMonitoring", example: "DEFAULT", pollMs: 30_000, marker: /Spend today/ }, [[429, "REQUEST_RATE_LIMITED"], [503, "RESET_IN_PROGRESS"]]],
  [{ name: "SCR-3 staffing switch", route: "/demo", role: "customer", op: "getStaffing", example: "OFF", pollMs: 10_000, marker: /Nobody online/ }, [[429, "REQUEST_RATE_LIMITED"]]],
];
const ELIGIBLE: [Poll, number, string][] = POLLS.flatMap(([p, sts]) => sts.map(([s, n]) => [p, s, n] as [Poll, number, string]));

beforeEach(() => { vi.useFakeTimers({ shouldAdvanceTime: true }); captureConsoleErrors(); });
afterEach(() => { vi.useRealTimers(); cleanup(); });

describe("UNIT (fake transport) G-08: a rate-limit or reset answer on a polled read keeps what is on screen", () => {
  it("lists which polled reads the spec gives a 429/503 for", () => {
    expect(ELIGIBLE.map(([p, s]) => `${p.op}:${s}`)).toEqual(["listDemoInbox:429", "listDemoInbox:503", "getMonitoring:429", "getMonitoring:503", "getStaffing:429"]);
  });
  it.each(ELIGIBLE.map(([p, s, n]) => [`${p.name}: ${s} ${n}`, p, s, n] as [string, Poll, number, string]))("%s", async (_l, p, status, name) => {
    let mode: "good" | "limited" = "good";
    let polls = 0;
    renderRoute(p.route, p.role, (ctx) => {
      if (ctx.op !== p.op) return p.bg?.(ctx);
      polls++;
      return mode === "good" ? ok(specBody(p.op, 200, p.example)) : ok(specError(p.op, status, name), status);
    });
    await screen.findAllByText(p.marker, undefined, { timeout: 4000 });
    const before = polls;
    mode = "limited";
    await act(async () => { await vi.advanceTimersByTimeAsync(p.pollMs + 200); });
    expect(polls).toBeGreaterThan(before);
    expect(screen.getAllByText(p.marker).length).toBeGreaterThan(0); // the list is still there
    for (const c of allErrorCodes()) expect(document.body.textContent, c).not.toContain(c);
    expect(document.body.textContent).not.toMatch(/\bundefined\b|\bNaN\b/);
    expect(document.querySelectorAll("h1").length).toBe(1);
    mode = "good";
    const mid = polls;
    await act(async () => { await vi.advanceTimersByTimeAsync(p.pollMs + 200); });
    expect(polls).toBeGreaterThan(mid);
    expect(screen.getAllByText(p.marker).length).toBeGreaterThan(0);
    expect(errorSpy.log).toEqual([]);
  }, 30_000);
});
