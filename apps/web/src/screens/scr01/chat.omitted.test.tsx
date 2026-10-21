// UNIT (fake transport), G-01 for the customer chat (CON-1, 2, 4, 5): reply bodies with keys OMITTED instead of null.
// Variants are derived from the spec's named examples by src/test/spec.ts. Each one is rendered through the real card
// registry, or through the real SCR-1 with a fake transport (submitTurn, requestPerson), and compared with the null version
// of the same body. MOCK-ONLY/UNIT evidence only; no real server produced any of these bodies.
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AnnounceProvider } from "@/components/ui/LiveRegion";
import { omittedExampleVariants, responseExamples, type Variant } from "@/test/spec";
import { settle } from "@/test/readTargets";
import { ok, renderRoute } from "../scr06/case.fixtures";
import { cardRenderers } from "./cards";
import { makeProps, renderCard } from "./cards/testing/props";
import { resetCardState } from "./cards/testing/resets";
import { SettledAside } from "./core/components/SettledAside";
import { startExample } from "./core/testFixtures";
import { expectNo24HourTimes } from "@/test/no24h";
import { configure } from "@testing-library/react";
/** Under the full parallel suite the first lazy screen chunk can take longer than the 1 s default. */
configure({ asyncUtilTimeout: 4000 });

/* eslint-disable @typescript-eslint/no-explicit-any -- spec bodies are walked as plain JSON */
let errorLog: string[] = [];
beforeEach(() => {
  resetCardState();
  sessionStorage.clear();
  errorLog = [];
  vi.spyOn(console, "error").mockImplementation((...a: unknown[]) => { errorLog.push(a.map(String).join(" ").slice(0, 300)); });
});
afterEach(() => cleanup());
const BAD = /\bundefined\b|\bNaN\b|\bnull\b|Unexpected Application Error|Unsupported block/;
const names = () => Object.keys(responseExamples("submitTurn", 200));
const buttons = () => [...document.querySelectorAll("button, a[href]")].map((b) => (b.getAttribute("aria-label") ?? b.textContent ?? "").trim());

describe("UNIT (fake transport) G-01: every reply card with keys omitted (submitTurn blocks)", () => {
  it("covers all 37 named turn examples and every one has something to omit", () => {
    expect(names()).toHaveLength(37);
    for (const n of names()) expect(omittedExampleVariants("submitTurn", 200, n).length, n).toBeGreaterThan(0);
  });
  for (const name of names()) {
    const variants = omittedExampleVariants<any>("submitTurn", 200, name);
    it.each(variants.map((v) => [v.label, v] as [string, Variant<any>]))(`${name}: %s renders every block like the null version`, (_l, v) => {
      const shoot = (res: any) => {
        const out: { text: string; buttons: string[] }[] = [];
        for (const block of res.blocks) {
          const render = cardRenderers[block.type as keyof typeof cardRenderers] as (p: unknown) => React.ReactNode;
          const { container, unmount } = renderCard(<>{render(makeProps(block, { settled: res.settled ?? null }))}</>);
          out.push({ text: container.textContent ?? "", buttons: buttons() });
          expectNo24HourTimes(container);
          unmount();
          resetCardState();
        }
        return out;
      };
      const shot = shoot(v.body);
      expect(errorLog).toEqual([]);
      shot.forEach((s, i) => expect(s.text, `block ${i} (${v.body.blocks[i].type})`).not.toMatch(BAD));
      if (v.nulled) {
        const ref = shoot(v.nulled);
        expect(shot).toEqual(ref);
      }
    });
  }
});

describe("UNIT (fake transport) G-01: SCR-1 end to end with a reply whose keys are omitted", () => {
  const FULL = new Set(["ANSWER_WITH_SOURCE", "HANDOFF", "BOOKED", "CHANGE_REQUEST", "CODE_SENT", "SLOT_CARD", "SLOT_TAKEN", "VERIFIED_ACCOUNT_INVOICE", "RATE_LIMITED"]);
  async function shot(body: unknown, op: "submitTurn" | "requestPerson") {
    const { calls } = renderRoute("/", "customer", (ctx) => {
      if (ctx.op === "startChatSession") return ok(startExample(), 201);
      if (ctx.op === op) return ok(body);
      return undefined;
    });
    await screen.findByRole("log");
    if (op === "submitTurn") {
      await userEvent.type(screen.getByRole("textbox"), "hello");
      await userEvent.click(screen.getByRole("button", { name: "Send" }));
    } else {
      await userEvent.click(screen.getByRole("button", { name: "Talk to a person" }));
    }
    await waitFor(() => expect(calls.some((c) => c.op === op)).toBe(true));
    await settle();
    const out = { text: document.body.textContent ?? "", buttons: buttons(), h1: document.querySelectorAll("h1").length, errors: [...errorLog] };
    cleanup();
    resetCardState();
    sessionStorage.clear();
    return out;
  }
  const cases: [string, Variant<any>][] = [];
  for (const name of names()) {
    const vs = omittedExampleVariants<any>("submitTurn", 200, name);
    for (const v of vs) if (FULL.has(name) || v.label === "omit all") cases.push([`${name}: ${v.label}`, v]);
  }
  it.each(cases)("submitTurn %s", async (_l, v) => {
    const nulled = v.nulled ? await shot(v.nulled, "submitTurn") : null;
    const s = await shot(v.body, "submitTurn");
    expect(s.errors).toEqual([]);
    expect(s.h1).toBe(1);
    expect(s.text).not.toMatch(BAD);
    if (nulled) { expect(s.buttons).toEqual(nulled.buttons); expect(s.text).toBe(nulled.text); }
  }, 20_000);

  for (const name of Object.keys(responseExamples("requestPerson", 200))) {
    const vs = omittedExampleVariants<any>("requestPerson", 200, name);
    it.each(vs.map((v) => [v.label, v] as [string, Variant<any>]))(`requestPerson ${name}: %s`, async (_l, v) => {
      const nulled = v.nulled ? await shot(v.nulled, "requestPerson") : null;
      const s = await shot(v.body, "requestPerson");
      expect(s.errors).toEqual([]);
      expect(s.h1).toBe(1);
      expect(s.text).not.toMatch(BAD);
      if (nulled) { expect(s.buttons).toEqual(nulled.buttons); expect(s.text).toBe(nulled.text); }
    }, 20_000);
  }
});

describe("UNIT (fake transport) G-01: the settled panel after saveFollowUp with keys omitted", () => {
  const vs = omittedExampleVariants<any>("saveFollowUp", 200, "PHONE_MORNINGS");
  it("has variants", () => expect(vs.length).toBeGreaterThan(0));
  it.each(vs.map((v) => [v.label, v] as [string, Variant<any>]))("%s", (_l, v) => {
    window.matchMedia = ((q: string) => ({ matches: q.includes("900"), media: q, addEventListener: () => {}, removeEventListener: () => {} })) as unknown as typeof window.matchMedia;
    const text = (res: any) => {
      const { container, unmount } = render(<AnnounceProvider><SettledAside settled={res.settled} danger={false} replying={{ kind: "ai", display_name: null }} staffingOn={false} landing={null} /></AnnounceProvider>);
      const t = container.textContent ?? "";
      unmount();
      return t;
    };
    const t = text(v.body);
    expect(errorLog).toEqual([]);
    expect(t).not.toMatch(BAD);
    if (v.nulled) expect(t).toBe(text(v.nulled));
  });
});
