// UNIT (fake transport), G-05 / G-06 / G-08 / G-15: every named error example in the spec, as an answer to the call that
// can produce it, rendered through the real screen. The bodies are the spec's own error examples (src/test/spec.ts
// specError), never hand-written. For each (operation, status, example) the screen must not throw, keep one h1, and never
// print a machine code ("VERSION_CONFLICT", "HTTP_500") or a placeholder ("undefined"). Where the copy is pinned by the UX
// contract it is asserted by text. MOCK-ONLY/UNIT evidence; the real server's error bodies are untested here.
import { act, cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { OPS, type OperationId } from "@/api/client";
import type { CallContext } from "@/api/transport";
import type { Role } from "@/lib/roles";
import { allErrorCodes, responseExamples, specBody, specError } from "@/test/spec";
import { defaultCase, liveJoinedCase, ok, renderRoute } from "./scr06/case.fixtures";
import { seededQueue } from "./scr05/queue.fixtures";
import { THREAD_KEY } from "./scr01/core/storage";
import { startExample } from "./scr01/core/testFixtures";
import { configure } from "@testing-library/react";
/** Under the full parallel suite the first lazy screen chunk can take longer than the 1 s default. */
configure({ asyncUtilTimeout: 4000 });

/* eslint-disable @typescript-eslint/no-explicit-any -- spec bodies are walked as plain JSON */
let errorLog: string[] = [];
beforeEach(() => {
  errorLog = [];
  sessionStorage.clear();
  vi.spyOn(console, "error").mockImplementation((...a: unknown[]) => { errorLog.push(a.map(String).join(" ").slice(0, 300)); });
});
afterEach(() => cleanup());
const settle = (ms = 60) => act(async () => { await new Promise((r) => setTimeout(r, ms)); });
const CODES = [...allErrorCodes()];

const claimed = () => {
  const c = defaultCase();
  c.case.lifecycle = "claimed";
  c.case.allowed_actions = ["start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag", "assign", "change_priority"];
  return c;
};

interface Target {
  name: string; route: string; role: Role; op: OperationId;
  /** answers for the surrounding calls (the screen's other reads) */
  background?: (ctx: CallContext) => Response | undefined;
  drive?: () => Promise<void>;
  before?: () => void;
  /** exact visible sentences, by example name */
  says?: Record<string, string | RegExp>;
  skip?: number[];
}
const bgCase = (c: () => any) => (ctx: CallContext) => (ctx.op === "getCase" ? ok(c()) : ctx.op === "getQueue" ? ok(seededQueue()) : undefined);
const bgChat = (turn?: string) => (ctx: CallContext) => {
  if (ctx.op === "startChatSession") return ok(startExample(), 201);
  if (ctx.op === "submitTurn" && turn) return ok(specBody("submitTurn", 200, turn));
  if (ctx.op === "requestPerson" && turn) return ok(specBody("requestPerson", 200, "CASE_CREATED"));
  return undefined;
};
const typeAndSend = async () => {
  await screen.findByRole("log");
  await userEvent.type(screen.getByRole("textbox"), "hello");
  await userEvent.click(screen.getByRole("button", { name: "Send" }));
};

const TARGETS: Target[] = [
  // ---- reads
  { name: "SCR-2 inbox", route: "/demo/inbox", role: "customer", op: "listDemoInbox", says: { REQUEST_RATE_LIMITED: /The inbox didn't load\. Try again\./, RESET_IN_PROGRESS: /The inbox didn't load\. Try again\./ } },
  { name: "SCR-5 queue", route: "/staff/queue", role: "representative", op: "getQueue" },
  { name: "SCR-6 case", route: "/staff/cases/MHC-C-0007", role: "representative", op: "getCase", background: (c) => (c.op === "getQueue" ? ok(seededQueue()) : undefined),
    says: { CASE_NOT_FOUND: "No case MHC-C-0007. It may have been cleared by a demo reset." } },
  { name: "SCR-7 oversight", route: "/staff/oversight", role: "supervisor", op: "getOversight" },
  { name: "SCR-8 flags", route: "/staff/flags", role: "supervisor", op: "listFlags" },
  { name: "SCR-9 owner", route: "/staff/owner", role: "owner", op: "getOwnerMetrics" },
  { name: "SCR-10 monitoring", route: "/monitoring", role: "customer", op: "getMonitoring", says: { REQUEST_RATE_LIMITED: /Try again in a moment\./, RESET_IN_PROGRESS: /The demo is resetting\. Try again in a few seconds\./ } },
  { name: "SCR-11 evaluation", route: "/eval", role: "customer", op: "getLatestEval", says: { REQUEST_RATE_LIMITED: /Try again in a moment\./, RESET_IN_PROGRESS: /The demo is resetting\. Try again in a few seconds\./ } },
  { name: "SCR-1 start", route: "/", role: "customer", op: "startChatSession", says: { REQUEST_RATE_LIMITED: "Try again in a moment.", RESET_IN_PROGRESS: "The demo is resetting. Try again in a few seconds." } },
  { name: "SCR-1 resume", route: "/", role: "customer", op: "getChatThread", background: bgChat(),
    before: () => sessionStorage.setItem(THREAD_KEY, JSON.stringify({ threadId: "thr_9d41", limits: startExample().limits })) },
  { name: "SCR-3 demo bar: getStaffing", route: "/demo", role: "customer", op: "getStaffing" },
  { name: "SCR-3 demo bar: getDemoClock", route: "/demo", role: "customer", op: "getDemoClock" },
  // ---- writes
  { name: "SCR-1 submitTurn", route: "/", role: "customer", op: "submitTurn", background: bgChat(), drive: typeAndSend },
  { name: "SCR-1 requestPerson", route: "/", role: "customer", op: "requestPerson", background: bgChat(),
    drive: async () => { await screen.findByRole("log"); await userEvent.click(screen.getByRole("button", { name: "Talk to a person" })); } },
  { name: "SCR-1 saveFollowUp", route: "/", role: "customer", op: "saveFollowUp", background: bgChat("HANDOFF"),
    drive: async () => { await typeAndSend(); await userEvent.click(await screen.findByRole("button", { name: "Save my choice" })); } },
  { name: "SCR-3 setStaffing", route: "/demo", role: "customer", op: "setStaffing",
    drive: async () => { const sw = await screen.findByRole("switch", { name: "Demo: simulate staff on shift" }); await waitFor(() => expect((sw as HTMLInputElement).disabled).toBe(false)); fireEvent.click(sw); },
    says: { RESET_IN_PROGRESS: /./ } },
  { name: "SCR-3 resetDemo", route: "/demo", role: "customer", op: "resetDemo",
    drive: async () => {
      await userEvent.click(await screen.findByRole("button", { name: "Reset the demo" }));
      const dlg = await screen.findByRole("dialog", { name: "Reset the demo?" });
      await userEvent.click([...dlg.querySelectorAll("button")].find((b) => b.textContent === "Reset the demo")!);
    },
    says: { RESET_FAILED: "The reset didn't finish. Nothing was half-reset; try again." } },
  { name: "SCR-7 advanceDemoClock", route: "/staff/oversight", role: "supervisor", op: "advanceDemoClock", background: (c) => (c.op === "getOversight" ? ok(specBody("getOversight", 200, "SEEDED")) : undefined),
    drive: async () => { await screen.findByRole("switch"); fireEvent.click(screen.getByRole("button", { name: "+1 hour" })); } },
  { name: "SCR-6 applyCaseAction (Claim)", route: "/staff/cases/MHC-C-0007", role: "representative", op: "applyCaseAction", background: bgCase(defaultCase),
    drive: async () => { fireEvent.click(await screen.findByRole("button", { name: "Claim" })); },
    says: {
      VALIDATION_ERROR: "That didn't go through. Try again.",
      ROLE_NOT_ALLOWED: "You can't do that as Riley, demo representative.",
      ROLE_NOT_ALLOWED_ROLE_RESET: "You can't do that as Riley, demo representative.",
      CASE_NOT_FOUND: "No case MHC-C-0099. It may have been cleared by a demo reset.",
      CASE_ALREADY_CLAIMED: "Already claimed by Demo supervisor at 2:31 pm. Reload.",
      VERSION_CONFLICT: "This case changed since you opened it (Demo supervisor at 2:31 pm). Reload to see it.",
      NOT_ALLOWED_IN_STATE: "Claim the case first.",
      REASON_REQUIRED: "Add a reason.", WAKE_UP_REQUIRED: "Waiting needs a wake-up time.", OUTCOME_REQUIRED: "Resolving needs an outcome.",
    } },
  { name: "SCR-6 applyCaseAction (Release)", route: "/staff/cases/MHC-C-0007", role: "representative", op: "applyCaseAction", background: bgCase(claimed),
    drive: async () => {
      await userEvent.click(await screen.findByRole("button", { name: "More actions" }));
      await userEvent.click(await screen.findByRole("menuitem", { name: "Release" }));
      fireEvent.change(await screen.findByLabelText("Reason"), { target: { value: "Not mine" } });
      fireEvent.click(screen.getAllByRole("button", { name: "Release" }).at(-1)!);
    },
    says: { REASON_REQUIRED: /./ } },
  { name: "SCR-6 liveChatAction (Send)", route: "/staff/cases/MHC-C-0007", role: "representative", op: "liveChatAction", background: bgCase(liveJoinedCase),
    drive: async () => { await screen.findByText(/You are replying as Riley/); fireEvent.change(screen.getByLabelText("Reply"), { target: { value: "Hi" } }); fireEvent.click(screen.getByRole("button", { name: "Send" })); } },
  { name: "SCR-6 recordContactActivity", route: "/staff/cases/MHC-C-0007", role: "representative", op: "recordContactActivity", background: bgCase(claimed),
    drive: async () => { fireEvent.click(await screen.findByRole("button", { name: "Log a call" })); fireEvent.click(screen.getByLabelText("Reached the customer")); fireEvent.click(screen.getByRole("button", { name: "Record" })); } },
  { name: "SCR-6 createFlag", route: "/staff/cases/MHC-C-0007", role: "representative", op: "createFlag", background: bgCase(claimed),
    drive: async () => {
      await userEvent.click(await screen.findByRole("button", { name: "Flag" }));
      fireEvent.click(screen.getByLabelText("An answer was wrong"));
      fireEvent.change(screen.getByLabelText("Note"), { target: { value: "Quoted $144" } });
      fireEvent.click(screen.getByRole("button", { name: "Add to review list" }));
    } },
  { name: "SCR-8 reviewFlag", route: "/staff/flags", role: "supervisor", op: "reviewFlag", background: (c) => (c.op === "listFlags" ? ok(specBody("listFlags", 200, "THREE")) : undefined),
    drive: async () => {
      const mark = () => screen.findByRole("button", { name: "Mark reviewed, flag on MHC-C-0007" });
      fireEvent.click(await mark());
      fireEvent.click(await mark());
    } },
  { name: "SCR-12 login", route: "/login", role: "customer", op: "login",
    background: (c) => (c.op === "getSession" ? new Response(JSON.stringify(specError("getSession", 401, "UNAUTHENTICATED")), { status: 401 }) : undefined),
    drive: async () => {
      await userEvent.type(await screen.findByLabelText("Username"), "<demo-username>");
      await userEvent.type(screen.getByLabelText("Password"), "<demo-password>");
      await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    },
    says: { LOGIN_FAILED: "That username or password didn't work. Check the README and try again.", LOGIN_RATE_LIMITED: "That username or password didn't work. Check the README and try again." } },
  { name: "SCR-4 switchRole", route: "/role", role: "customer", op: "switchRole", background: (c) => (c.op === "listDemoRoles" ? ok(specBody("listDemoRoles", 200, "ROLES")) : undefined),
    drive: async () => { await userEvent.click(await screen.findByRole("button", { name: "Demo supervisor" })); },
    says: { RESET_IN_PROGRESS: "Couldn't switch role. Try again." } },
];

const CASE_PINS: Record<string, string | RegExp> = {
  VALIDATION_ERROR: "That didn't go through. Try again.",
  ROLE_NOT_ALLOWED: "You can't do that as Riley, demo representative.",
  ROLE_NOT_ALLOWED_ROLE_RESET: "You can't do that as Riley, demo representative.",
  CASE_NOT_FOUND: "No case MHC-C-0099. It may have been cleared by a demo reset.",
  CASE_ALREADY_CLAIMED: "Already claimed by Demo supervisor at 2:31 pm. Reload.",
  VERSION_CONFLICT: "This case changed since you opened it (Demo supervisor at 2:31 pm). Reload to see it.",
  NOT_ALLOWED_IN_STATE: "Claim the case first.",
};
/** Visible sentences pinned for the names the UX contract gives copy for; the rest only meet the invariants below. */
const PINS: Record<string, Record<string, string | RegExp>> = {
  "SCR-6 applyCaseAction (Release)": { ...CASE_PINS, REASON_REQUIRED: "Add a reason to release this case." },
  "SCR-6 liveChatAction (Send)": { ...CASE_PINS, CASE_ALREADY_CLAIMED: /Already claimed by .*\. Reload\./, NOT_CLAIMED_BY_YOU: "Claim the case first.", NOT_LIVE: /This chat has ended\.|ended because the demo was reset\./ },
  "SCR-6 recordContactActivity": CASE_PINS,
  "SCR-6 createFlag": { VALIDATION_ERROR: CASE_PINS.VALIDATION_ERROR, ROLE_NOT_ALLOWED: CASE_PINS.ROLE_NOT_ALLOWED, ROLE_NOT_ALLOWED_ROLE_RESET: CASE_PINS.ROLE_NOT_ALLOWED_ROLE_RESET, CASE_NOT_FOUND: CASE_PINS.CASE_NOT_FOUND },
  "SCR-8 reviewFlag": { ROLE_NOT_ALLOWED: "Supervisors mark flags reviewed.", ROLE_NOT_ALLOWED_ROLE_RESET: "Supervisors mark flags reviewed.", FLAG_NOT_FOUND: "That flag is gone. It may have been cleared by a demo reset.", VALIDATION_ERROR: "Couldn't mark it reviewed. Try again." },
  "SCR-1 submitTurn": { VALIDATION_ERROR: "That didn't send. Your message is still here.", SESSION_NOT_FOUND: "This chat has ended.", SESSION_ENDED: "This chat has ended.", RESET_IN_PROGRESS: "The demo is resetting. Try again in a few seconds." },
  "SCR-1 requestPerson": { VALIDATION_ERROR: "We couldn't reach a person just now. Tap Talk to a person to try again.", HANDOFF_FAILED: "We couldn't reach a person just now. Tap Talk to a person to try again.", SESSION_NOT_FOUND: "This chat has ended.", SESSION_ENDED: "This chat has ended." },
  "SCR-1 saveFollowUp": { VALIDATION_ERROR: "Your choice didn't save. Try again.", NOT_ALLOWED_IN_STATE: "There's no open request to attach this to.", SESSION_NOT_FOUND: "This chat has ended.", SESSION_ENDED: "This chat has ended." },
  "SCR-1 resume": { SESSION_ENDED: "This chat has ended." },
  "SCR-3 setStaffing": { VALIDATION_ERROR: "Staffing didn't change. Try again.", RESET_IN_PROGRESS: "Staffing didn't change. Try again." },
  "SCR-3 resetDemo": { VALIDATION_ERROR: "The reset didn't finish. Nothing was half-reset; try again.", RESET_IN_PROGRESS: "The demo is resetting. Try again in a few seconds." },
  "SCR-7 advanceDemoClock": { VALIDATION_ERROR: "The clock didn't move. Try again.", ROLE_NOT_ALLOWED: "The clock didn't move. Try again.", ROLE_NOT_ALLOWED_ROLE_RESET: "The clock didn't move. Try again.", RESET_IN_PROGRESS: "The clock didn't move. Try again." },
  "SCR-12 login": { VALIDATION_ERROR: "That username or password didn't work. Check the README and try again." },
};

function errorExamples(op: OperationId): [number, string][] {
  const out: [number, string][] = [];
  for (const r of OPS[op].responses) {
    if (r.status < 400 || (r.status === 401 && op !== "login")) continue; // the shared 401 is the session tests; login's 401 is its own LOGIN_FAILED
    for (const name of Object.keys(responseExamples(op, r.status))) out.push([r.status, name]);
  }
  return out;
}

describe("UNIT (fake transport) G-05/G-08/G-15: every spec error example, as the answer to the call that can raise it", () => {
  for (const t of TARGETS) {
    const cases = errorExamples(t.op).filter(([s]) => !(t.skip ?? []).includes(s));
    describe(t.name, () => {
      it("the spec lists errors for this operation", () => expect(cases.length).toBeGreaterThan(0));
      it.each(cases.map(([s, n]) => [`${s} ${n}`, s, n] as [string, number, string]))("%s", async (_l, status, name) => {
        t.before?.();
        let hit = false;
        renderRoute(t.route, t.role, (ctx) => {
          if (ctx.op === t.op) { hit = true; return ok(specError(t.op, status, name), status); }
          return t.background?.(ctx);
        });
        await t.drive?.();
        await waitFor(() => expect(hit).toBe(true));
        await waitFor(() => expect(document.querySelectorAll("h1").length).toBeGreaterThan(0)); // the screen chunk is lazy
        await settle(t.op === "submitTurn" || t.op === "requestPerson" ? 80 : 60);
        const text = document.body.textContent ?? "";
        expect(errorLog, "console.error").toEqual([]);
        expect(document.querySelectorAll("h1").length, "h1 count").toBe(1);
        for (const c of CODES) expect(text, `raw code ${c}`).not.toContain(c);
        expect(text).not.toMatch(/\bundefined\b|\bNaN\b|\bnull\b|HTTP_\d|\[object|Unexpected Application Error/);
        const says = (PINS[t.name] ?? {})[name] ?? t.says?.[name];
        if (says instanceof RegExp) expect(text).toMatch(says);
        else if (says) expect(text).toContain(says);
        if (process.env.DUMP_ERR) console.log(`[${t.name}] ${status} ${name}: ${[...document.querySelectorAll('[role="status"],[role="alert"],[aria-live]')].map((e) => e.textContent).filter(Boolean).join(" | ").slice(0, 200)}`);
      }, 20_000);
    });
  }
});

