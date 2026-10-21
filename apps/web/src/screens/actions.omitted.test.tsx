// UNIT (fake transport), G-01 for the write responses (CON-13 to 16): the answer to a click comes back with keys OMITTED, not null.
// applyCaseAction, liveChatAction, recordContactActivity, createFlag and reviewFlag are each driven through the real screen
// (SCR-6, SCR-8) by clicking the control that sends them; the fake transport answers with a spec example whose nullable or
// optional keys are deleted. Compared with the null version of the same body. MOCK-ONLY/UNIT evidence only.
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { OperationId } from "@/api/client";
import { omittedExampleVariants, specBody, type Variant } from "@/test/spec";
import { settle } from "@/test/readTargets";
import { defaultCase, liveJoinedCase, ok, renderRoute } from "./scr06/case.fixtures";
import { seededQueue } from "./scr05/queue.fixtures";
import { configure } from "@testing-library/react";
/** Under the full parallel suite the first lazy screen chunk can take longer than the 1 s default. */
configure({ asyncUtilTimeout: 4000 });

/* eslint-disable @typescript-eslint/no-explicit-any -- spec bodies are walked as plain JSON */
let errorLog: string[] = [];
beforeEach(() => {
  errorLog = [];
  vi.spyOn(console, "error").mockImplementation((...a: unknown[]) => { errorLog.push(a.map(String).join(" ").slice(0, 300)); });
});
afterEach(() => cleanup());
const BAD = /\bundefined\b|\bNaN\b|\bnull\b|Unexpected Application Error/;
const buttons = () => [...document.querySelectorAll("button, a[href]")].map((b) => (b.getAttribute("aria-label") ?? b.textContent ?? "").trim());

const claimed = () => {
  const c = defaultCase();
  c.case.lifecycle = "claimed";
  c.case.allowed_actions = ["start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag"];
  return c;
};
const queued = () => {
  const c = defaultCase();
  c.case.lifecycle = "live_queued";
  c.case.allowed_actions = ["claim_and_join", "claim", "flag"];
  c.live = { state: "queued", since: "2026-10-16T14:14:00-05:00", controller: "ai" };
  return c;
};

interface Scenario {
  name: string; op: OperationId; status: number; examples: string[];
  caseBody: () => any;
  drive: () => Promise<void>;
}
const SCENARIOS: Scenario[] = [
  {
    name: "Claim", op: "applyCaseAction", status: 200, examples: ["CLAIMED", "WAITING", "RESOLVED", "ASSIGNED", "PRIORITY_CHANGED"], caseBody: defaultCase,
    drive: async () => { fireEvent.click(await screen.findByRole("button", { name: "Claim" })); },
  },
  {
    name: "Log a call", op: "recordContactActivity", status: 201, examples: ["CALL_REACHED", "EMAIL_LEFT_MESSAGE"], caseBody: claimed,
    drive: async () => {
      fireEvent.click(await screen.findByRole("button", { name: "Log a call" }));
      fireEvent.click(screen.getByLabelText("Reached the customer"));
      fireEvent.click(screen.getByRole("button", { name: "Record" }));
    },
  },
  {
    name: "Send a live message", op: "liveChatAction", status: 200, examples: ["SENT"], caseBody: liveJoinedCase,
    drive: async () => {
      await screen.findByText(/You are replying as Riley/);
      fireEvent.change(screen.getByLabelText("Reply"), { target: { value: "Hello" } });
      fireEvent.click(screen.getByRole("button", { name: "Send" }));
    },
  },
  {
    name: "Hand back", op: "liveChatAction", status: 200, examples: ["HANDED_BACK"], caseBody: liveJoinedCase,
    drive: async () => { await screen.findByText(/You are replying as Riley/); fireEvent.click(screen.getByRole("button", { name: "Hand back to the assistant" })); },
  },
  {
    name: "Close the chat", op: "liveChatAction", status: 200, examples: ["CLOSED"], caseBody: liveJoinedCase,
    drive: async () => { await screen.findByText(/You are replying as Riley/); fireEvent.click(screen.getByRole("button", { name: "Close the chat" })); },
  },
  {
    name: "Claim and join (join answer)", op: "liveChatAction", status: 200, examples: ["JOINED"], caseBody: queued,
    drive: async () => { fireEvent.click(await screen.findByRole("button", { name: "Claim and join" })); },
  },
  {
    name: "Flag a case", op: "createFlag", status: 201, examples: ["ANSWER"], caseBody: claimed,
    drive: async () => {
      await userEvent.click(await screen.findByRole("button", { name: "Flag" }));
      fireEvent.click(screen.getByLabelText("An answer was wrong"));
      fireEvent.change(screen.getByLabelText("Note"), { target: { value: "Quoted $144" } });
      fireEvent.click(screen.getByRole("button", { name: "Add to review list" }));
    },
  },
];

async function run(sc: Scenario, body: unknown) {
  const calls: string[] = [];
  renderRoute("/staff/cases/MHC-C-0007", "representative", (ctx) => {
    calls.push(ctx.op);
    if (ctx.op === "getCase") return ok(sc.caseBody());
    if (ctx.op === "getQueue") return ok(seededQueue());
    if (ctx.op === sc.op) return ok(body, sc.status);
    if (sc.name.startsWith("Claim and join") && ctx.op === "applyCaseAction") return ok(specBody("applyCaseAction", 200, "CLAIMED"));
    return undefined;
  });
  await screen.findByRole("heading", { level: 1, name: /Billing dispute/ });
  await sc.drive();
  await waitFor(() => expect(calls).toContain(sc.op));
  await settle();
  const out = { text: document.body.textContent ?? "", buttons: buttons(), h1: document.querySelectorAll("h1").length, errors: [...errorLog] };
  cleanup();
  return out;
}

describe("UNIT (fake transport) G-01: write responses with keys omitted instead of null", () => {
  for (const sc of SCENARIOS) {
    describe(sc.name, () => {
      for (const ex of sc.examples) {
        const variants = omittedExampleVariants<any>(sc.op, sc.status, ex);
        it(`${ex}: has keys to omit`, () => expect(variants.length).toBeGreaterThan(0));
        it.each(variants.map((v) => [v.label, v] as [string, Variant<any>]))(`${ex}: %s`, async (_l, v) => {
          const nulled = v.nulled ? await run(sc, v.nulled) : null;
          const s = await run(sc, v.body);
          expect(s.errors).toEqual([]);
          expect(s.h1).toBe(1);
          expect(s.text).not.toMatch(BAD);
          if (nulled) { expect(s.buttons).toEqual(nulled.buttons); expect(s.text).toBe(nulled.text); }
        }, 20_000);
      }
    });
  }
});

describe("UNIT (fake transport) G-01: reviewFlag response with keys omitted instead of null (SCR-8)", () => {
  const variants = omittedExampleVariants<any>("reviewFlag", 200, "REVIEWED");
  const shoot = async (body: unknown) => {
    let hit = false;
    renderRoute("/staff/flags", "supervisor", (ctx) => {
      if (ctx.op === "listFlags") return ok(specBody("listFlags", 200, "THREE"));
      if (ctx.op === "reviewFlag") { hit = true; return ok(body); }
      return undefined;
    });
    const mark = () => screen.findByRole("button", { name: "Mark reviewed, flag on MHC-C-0007" });
    fireEvent.click(await mark());
    fireEvent.click(await mark());
    await waitFor(() => expect(hit).toBe(true));
    await settle();
    const out = { text: document.body.textContent ?? "", buttons: buttons(), h1: document.querySelectorAll("h1").length, errors: [...errorLog] };
    cleanup();
    return out;
  };
  it("has keys to omit", () => expect(variants.length).toBeGreaterThan(0));
  it.each(variants.map((v) => [v.label, v] as [string, Variant<any>]))("%s", async (_l, v) => {
    const nulled = v.nulled ? await shoot(v.nulled) : null;
    const s = await shoot(v.body);
    expect(s.errors).toEqual([]);
    expect(s.h1).toBe(1);
    expect(s.text).not.toMatch(BAD);
    if (nulled) { expect(s.buttons).toEqual(nulled.buttons); expect(s.text).toBe(nulled.text); }
  }, 20_000);
});
