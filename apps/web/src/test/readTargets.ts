// Test-only: the screens the read-side gap tests render (G-01 keys omitted, G-14 empty arrays) and how they are measured.
// Bodies come from the spec through src/test/spec.ts; nothing here is a hand-written API body.
import { act, cleanup, waitFor } from "@testing-library/react";
import { expect, vi } from "vitest";
import type { OperationId } from "@/api/client";
import type { CallContext } from "@/api/transport";
import type { Role } from "@/lib/roles";
import { ok, renderRoute } from "@/screens/scr06/case.fixtures";
import { seededQueue } from "@/screens/scr05/queue.fixtures";
import { THREAD_KEY } from "@/screens/scr01/core/storage";
import { startExample } from "@/screens/scr01/core/testFixtures";

export interface Shot { text: string; buttons: string[]; h1: number; errors: string[] }

export const errorSpy = { log: [] as string[] };
/** Call in beforeEach: records console.error instead of printing it. */
export function captureConsoleErrors(): void {
  errorSpy.log = [];
  vi.spyOn(console, "error").mockImplementation((...a: unknown[]) => { errorSpy.log.push(a.map(String).join(" ").slice(0, 300)); });
}

export const buttonNames = () =>
  [...document.querySelectorAll("button, a[href]")].map((b) => (b.getAttribute("aria-label") ?? b.textContent ?? "").trim());
/** Waits until the page text has stopped changing (two reads 40 ms apart agree), so a slow machine cannot make a snapshot early. */
export const settle = async () => {
  let prev = "";
  for (let i = 0; i < 50; i++) {
    await act(async () => { await new Promise((r) => setTimeout(r, 40)); });
    const now = document.body.textContent ?? "";
    if (now === prev) return;
    prev = now;
  }
};
export const busy = () => document.querySelector('[aria-busy="true"], [data-skeleton]') !== null;

export async function shotScreen(
  route: string, role: Role, op: OperationId, status: number, body: unknown,
  extra?: (ctx: CallContext) => Response | undefined, before?: () => void,
): Promise<Shot> {
  before?.();
  let hit = false; // renderRoute's call log leaves out the shell's own reads (getStaffing), so note the hit here
  renderRoute(route, role, (ctx) => { if (ctx.op === op) { hit = true; return ok(body, status); } return extra?.(ctx); });
  await waitFor(() => expect(hit).toBe(true));
  await waitFor(() => expect(busy()).toBe(false));
  await settle();
  const shot: Shot = { text: document.body.textContent ?? "", buttons: buttonNames(), h1: document.querySelectorAll("h1").length, errors: [...errorSpy.log] };
  cleanup();
  return shot;
}

export function expectSensible(label: string, shot: Shot, nulled: Shot | null) {
  expect(shot.errors, `${label}: console.error`).toEqual([]);
  expect(shot.h1, `${label}: h1 count`).toBe(1);
  expect(shot.text, `${label}: placeholder text`).not.toMatch(/\bundefined\b|\bNaN\b|\bnull\b|Unexpected Application Error|Something went wrong/);
  if (nulled) {
    expect(shot.buttons, `${label}: buttons vs the null version`).toEqual(nulled.buttons);
    expect(shot.text, `${label}: text vs the null version`).toBe(nulled.text);
  }
}

export interface Target {
  name: string; route: string; role: Role; op: OperationId; status: number; examples: string[];
  extra?: (ctx: CallContext) => Response | undefined; before?: () => void;
}
const rep: Role = "representative";
export const TARGETS: Target[] = [
  { name: "SCR-5 queue", route: "/staff/queue", role: rep, op: "getQueue", status: 200, examples: ["SEEDED", "STAFFED_WITH_WAITING", "ALL_CAUGHT_UP", "BRIEF_BEING_WRITTEN"] },
  { name: "SCR-6 case", route: "/staff/cases/MHC-C-0007", role: rep, op: "getCase", status: 200, examples: ["DEFAULT", "LIVE_JOINED", "WAITING", "SAFETY_CASE", "BRIEF_BEING_WRITTEN", "TRIMMED_STOP", "FEE_BEARING_CHANGE"], extra: (c) => (c.op === "getQueue" ? ok(seededQueue()) : undefined) },
  { name: "SCR-7 oversight", route: "/staff/oversight", role: "supervisor", op: "getOversight", status: 200, examples: ["SEEDED", "AFTER_ADVANCE", "SHIFT_ENDED_WITH_WAITING", "NOTHING_URGENT"] },
  { name: "SCR-8 flags", route: "/staff/flags", role: "supervisor", op: "listFlags", status: 200, examples: ["THREE"] },
  { name: "SCR-9 owner outcomes", route: "/staff/owner", role: "owner", op: "getOwnerMetrics", status: 200, examples: ["SEEDED", "EMPTY"] },
  { name: "SCR-10 monitoring", route: "/monitoring", role: "customer", op: "getMonitoring", status: 200, examples: ["DEFAULT", "FIRING", "TOO_FEW_TURNS", "EMPTY", "ZERO_TRAFFIC_FIRING", "FAILURE_AND_TRACE_FIRING"] },
  { name: "SCR-11 evaluation", route: "/eval", role: "customer", op: "getLatestEval", status: 200, examples: ["BOTH_SPLITS", "DEV_ONLY", "STALE_RUN", "NO_RUN"] },
  { name: "SCR-1 resumed thread", route: "/", role: "customer", op: "getChatThread", status: 200, examples: ["OPEN", "ENDED_BLOCK"],
    before: () => sessionStorage.setItem(THREAD_KEY, JSON.stringify({ threadId: "thr_9d41", limits: startExample().limits })) },
  { name: "SCR-1 new chat", route: "/", role: "customer", op: "startChatSession", status: 201, examples: ["STARTED", "SIMULATION_ON"] },
  { name: "SCR-3 demo bar (staffing)", route: "/demo", role: "customer", op: "getStaffing", status: 200, examples: ["OFF", "ON"] },
];

