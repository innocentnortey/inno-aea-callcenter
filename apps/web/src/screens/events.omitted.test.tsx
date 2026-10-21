// UNIT (fake transport), G-01 for stream events (CON-3, CON-21): event bodies with keys OMITTED instead of null.
// Events come from the spec's FRAMES examples plus the typed dev fixtures (src/dev/stream/events.ts, typed against
// types.gen.ts) for the types the spec has no example for. Each is delivered to the real SCR-1 / SCR-6 through the fake
// stream, and the screen text is compared with the null version. MOCK-ONLY/UNIT evidence; no server sent these frames.
import { act, cleanup, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { chatEvents, caseEvents } from "@/dev/stream/events";
import { SseParser } from "@/api/sse";
import { captureConsoleErrors, errorSpy, settle } from "@/test/readTargets";
import { omittedVariants, spec, streamFrames, violationsLoose, type Variant } from "@/test/spec";
import { ok, renderRoute, liveJoinedCase } from "./scr06/case.fixtures";
import { seededQueue } from "./scr05/queue.fixtures";
import { startExample } from "./scr01/core/testFixtures";
import { configure } from "@testing-library/react";
/** Under the full parallel suite the first lazy screen chunk can take longer than the 1 s default. */
configure({ asyncUtilTimeout: 4000 });

/* eslint-disable @typescript-eslint/no-explicit-any -- spec bodies are walked as plain JSON */
beforeEach(() => captureConsoleErrors());
afterEach(() => cleanup());

/** Page text without the polite live regions: their announcement is timing-dependent (a later announcement replaces an earlier one). */
const visibleText = () => { const c = document.body.cloneNode(true) as HTMLElement; c.querySelectorAll("[aria-live]").forEach((n) => n.remove()); return c.textContent ?? ""; };
const frames = (op: "streamChatEvents" | "streamCaseEvents") => new SseParser().push(streamFrames(op).text).filter((f) => f.data).map((f) => JSON.parse(f.data));
const withIds = (list: any[]) => list.map((e, i) => ({ ...e, event_id: 100 + i }));
const CHAT = withIds([...frames("streamChatEvents"), ...Object.values(chatEvents).filter((_, i) => i > 2).map((f) => f())]);
const CASE = withIds([...frames("streamCaseEvents"), ...Object.values(caseEvents).filter((_, i) => i > 1).map((f) => f())]);
const schemas = () => spec().components.schemas;

describe("UNIT (fake transport) G-01: stream events, shape", () => {
  it("every event used here is valid against the spec's event union (spec examples and dev fixtures)", () => {
    for (const e of CHAT) expect(violationsLoose(schemas().ChatEvent, e), `chat ${e.type}`).toEqual([]);
    for (const e of CASE) expect(violationsLoose(schemas().CaseEvent, e), `case ${e.type}`).toEqual([]);
    expect(CHAT.map((e) => e.type).sort()).toEqual(["ai_paused", "ai_resumed", "chat_closed", "clock_changed", "demo_reset", "representative_joined", "shift_ended", "staff_message", "staffing_changed"]);
    expect(CASE.map((e) => e.type).sort()).toEqual(["case_changed", "chat_closed", "controller_changed", "customer_message", "demo_reset"]);
  });
});

async function chatShot(event: any) {
  const { streams } = renderRoute("/", "customer", (ctx) => (ctx.op === "startChatSession" ? ok(startExample(), 201) : undefined));
  await screen.findByRole("log", undefined, { timeout: 4000 });
  await waitFor(() => expect(streams.length).toBeGreaterThan(0));
  await act(async () => { streams[0].onEvent(event, event.event_id, event.type); await new Promise((r) => setTimeout(r, 20)); });
  await settle();
  const out = { text: visibleText(), h1: document.querySelectorAll("h1").length, errors: [...errorSpy.log] };
  cleanup();
  return out;
}
async function caseShot(event: any) {
  const { streams } = renderRoute("/staff/cases/MHC-C-0007", "representative", (ctx) => (ctx.op === "getCase" ? ok(liveJoinedCase()) : ctx.op === "getQueue" ? ok(seededQueue()) : undefined));
  await screen.findByText(/You are replying as Riley/, undefined, { timeout: 4000 });
  await waitFor(() => expect(streams.length).toBeGreaterThan(0));
  await act(async () => { streams[0].onEvent(event, event.event_id, event.type); await new Promise((r) => setTimeout(r, 20)); });
  await settle();
  const out = { text: visibleText(), h1: document.querySelectorAll("h1").length, errors: [...errorSpy.log] };
  cleanup();
  return out;
}
const BAD = /\bundefined\b|\bNaN\b|\bnull\b|Unexpected Application Error/;

describe("UNIT (fake transport) G-01: chat events with keys omitted (SCR-1)", () => {
  for (const ev of CHAT) {
    const variants = omittedVariants<any>(schemas().ChatEvent, ev);
    describe(ev.type, () => {
      it.each(variants.map((v) => [v.label, v] as [string, Variant<any>]))("%s", async (_l, v) => {
        const nulled = v.nulled ? await chatShot(v.nulled) : null;
        const s = await chatShot(v.body);
        expect(s.errors).toEqual([]);
        expect(s.h1).toBe(1);
        expect(s.text).not.toMatch(BAD);
        if (nulled) expect(s.text).toBe(nulled.text);
      }, 20_000);
      if (variants.length === 0) it("has no omissible key (nothing to omit)", () => expect(variants).toEqual([]));
    });
  }
});

describe("UNIT (fake transport) G-01: case events with keys omitted (SCR-6)", () => {
  for (const ev of CASE) {
    const variants = omittedVariants<any>(schemas().CaseEvent, ev);
    describe(ev.type, () => {
      it.each(variants.map((v) => [v.label, v] as [string, Variant<any>]))("%s", async (_l, v) => {
        const nulled = v.nulled ? await caseShot(v.nulled) : null;
        const s = await caseShot(v.body);
        expect(s.errors).toEqual([]);
        expect(s.h1).toBe(1);
        expect(s.text).not.toMatch(BAD);
        if (nulled) expect(s.text).toBe(nulled.text);
      }, 20_000);
      if (variants.length === 0) it("has no omissible key (nothing to omit)", () => expect(variants).toEqual([]));
    });
  }
});
