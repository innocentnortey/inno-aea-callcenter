// UNIT (fake transport), G-14 (class b): arrays INSIDE a body that are empty although the body is not an "empty list" example:
// a case with no conversation, activities or sources, a resumed thread with turns: [], a reply with blocks: [] and so on.
// src/test/spec.ts empties every array the schema allows to be empty (no minItems above 0), one location at a time and all
// together, starting from each named example. Asserts: no throw, one h1, no "undefined"/"NaN"/"null" text.
// Bodies come only from the spec's named examples. MOCK-ONLY/UNIT evidence.
import { act, cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { buttonNames, captureConsoleErrors, errorSpy, expectSensible, shotScreen, TARGETS } from "@/test/readTargets";
import { emptiedExampleVariants, responseExamples } from "@/test/spec";
import { ok, renderRoute } from "./scr06/case.fixtures";
import { startExample } from "./scr01/core/testFixtures";
import { resetCardState } from "./scr01/cards/testing/resets";
import { configure } from "@testing-library/react";
/** Under the full parallel suite the first lazy screen chunk can take longer than the 1 s default. */
configure({ asyncUtilTimeout: 4000 });

/* eslint-disable @typescript-eslint/no-explicit-any -- spec bodies are walked as plain JSON */
beforeEach(() => { captureConsoleErrors(); resetCardState(); });
afterEach(() => { sessionStorage.clear(); cleanup(); });

describe("UNIT (fake transport) G-14: empty arrays inside read bodies", () => {
  for (const t of TARGETS) {
    if (!t.examples.some((ex) => emptiedExampleVariants<any>(t.op, t.status, ex).length > 0)) continue; // e.g. a body with no arrays
    describe(t.name, () => {
      for (const ex of t.examples) {
        const variants = emptiedExampleVariants<any>(t.op, t.status, ex);
        if (variants.length === 0) continue;
        it.each(variants.map((v) => [v.label, v] as [string, { label: string; body: any }]))(`${ex}: %s`, async (_l, v) => {
          const s = await shotScreen(t.route, t.role, t.op, t.status, v.body, t.extra, t.before);
          expectSensible(`${t.name} ${ex} ${v.label}`, s, null);
        }, 20_000);
      }
    });
  }
});

describe("UNIT (fake transport) G-14: a reply with blocks: [] and a thread with turns: [] in SCR-1", () => {
  async function send(body: unknown) {
    const { calls } = renderRoute("/", "customer", (ctx) => (ctx.op === "startChatSession" ? ok(startExample(), 201) : ctx.op === "submitTurn" ? ok(body) : undefined));
    await screen.findByRole("log");
    await userEvent.type(screen.getByRole("textbox"), "hello");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(calls.some((c) => c.op === "submitTurn")).toBe(true));
    await act(async () => { await new Promise((r) => setTimeout(r, 60)); });
    return { text: document.body.textContent ?? "", buttons: buttonNames(), h1: document.querySelectorAll("h1").length, fieldDisabled: (screen.getByRole("textbox") as HTMLTextAreaElement).disabled };
  }
  const names = Object.keys(responseExamples("submitTurn", 200));
  it.each(names)("%s with every array emptied (blocks: [] included)", async (name) => {
    const vs = emptiedExampleVariants<any>("submitTurn", 200, name);
    const all = vs.at(-1)!;
    const s = await send(all.body);
    expect(errorSpy.log).toEqual([]);
    expect(s.h1).toBe(1);
    expect(s.text).not.toMatch(/\bundefined\b|\bNaN\b|\bnull\b|Unexpected Application Error/);
  }, 20_000);
  it("blocks: [] alone: the pending line clears and the field is usable again", async () => {
    const body = { ...(await import("@/test/spec")).specBody<any>("submitTurn", 200, "ANSWER_WITH_SOURCE") };
    body.blocks = [];
    const s = await send(body);
    expect(errorSpy.log).toEqual([]);
    expect(s.h1).toBe(1);
    expect(s.fieldDisabled).toBe(false);
    expect(s.text).not.toMatch(/Meridian assistant is replying|Still working on this/);
  });
});
