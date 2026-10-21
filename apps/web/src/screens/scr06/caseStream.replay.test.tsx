// UNIT (fake transport), G-04 (3) and (2) for the case stream (CON-21) and the chat stream (CON-3), through the real screens.
// The stream is the real defaultTransport.openStream against a stubbed global fetch; every other call is the fake transport.
// Frames are the spec's own FRAMES examples. Fake timers drive the backoff. MOCK-ONLY/UNIT evidence only.
import { act, cleanup, render, screen, waitFor, within } from "@testing-library/react";
import { createElement } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defaultTransport, setTransport } from "@/api/transport";
import { buildRoutes } from "@/router";
import { streamFrames } from "@/test/spec";
import { startExample } from "../scr01/core/testFixtures";
import { seededQueue } from "../scr05/queue.fixtures";
import { fakeApi, liveJoinedCase, ok } from "./case.fixtures";
import { configure } from "@testing-library/react";
/** Under the full parallel suite the first lazy screen chunk can take longer than the 1 s default. */
configure({ asyncUtilTimeout: 4000 });

const enc = new TextEncoder();
const body = (text: string, hang = false) => new Response(new ReadableStream<Uint8Array>({ start(c) { c.enqueue(enc.encode(text)); if (!hang) c.close(); } }), { status: 200 });
beforeEach(() => vi.useFakeTimers({ shouldAdvanceTime: true }));
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); cleanup(); });

function open(route: string, role: "representative" | "customer", answers: (() => Response)[], handler: Parameters<typeof fakeApi>[1]) {
  const calls: { url: string; lastEventId: string | null }[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, lastEventId: (init.headers as Record<string, string>)["Last-Event-ID"] ?? null });
    return answers[Math.min(calls.length - 1, answers.length - 1)]();
  }));
  const api = fakeApi(role, handler);
  setTransport({ fetch: api.transport.fetch, openStream: defaultTransport.openStream });
  const router = createMemoryRouter(buildRoutes(), { initialEntries: [route] });
  render(createElement(RouterProvider, { router }));
  return { calls, router };
}
const tick = (ms: number) => act(async () => { await vi.advanceTimersByTimeAsync(ms); });
const caseHandler: Parameters<typeof fakeApi>[1] = (ctx) => (ctx.op === "getCase" ? ok(liveJoinedCase()) : ctx.op === "getQueue" ? ok(seededQueue()) : undefined);

describe("UNIT (fake transport) G-04: the case stream through SCR-6", () => {
  it("a reconnect resends the highest id, and a replayed frame is shown once", async () => {
    const frames = streamFrames("streamCaseEvents").text; // ids 5 (customer_message) and 6 (chat_closed)
    const { calls } = open("/staff/cases/MHC-C-0007", "representative", [() => body(frames), () => body(frames), () => body("", true)], caseHandler);
    await screen.findByText(/You are replying as Riley/);
    await waitFor(() => expect(calls.length).toBeGreaterThanOrEqual(1));
    await tick(50);
    await tick(1100); // backoff 1 s: second connection replays 5 and 6
    await tick(50);
    expect(calls[0].lastEventId).toBeNull();
    expect(calls[1].lastEventId).toBe("6");
    expect(calls[1].url).toBe("/api/staff/cases/MHC-C-0007/events");
    await waitFor(() => expect(screen.getAllByText("Thanks, that helps.")).toHaveLength(1));
    expect(screen.getAllByText(/^Chat closed at/)).toHaveLength(1);
  });

  it("the case stream is NOT closed by the consumer after chat_closed (case_changed can still arrive): a server that ends it each time is re-asked every 1 s with Last-Event-ID", async () => {
    const frames = streamFrames("streamCaseEvents").text;
    const { calls } = open("/staff/cases/MHC-C-0007", "representative", [() => body(frames), () => body(frames), () => body(frames), () => body("", true)], caseHandler);
    await screen.findByText(/You are replying as Riley/);
    await tick(100);
    expect(calls).toHaveLength(1);
    await tick(1000); expect(calls).toHaveLength(2);
    await tick(1000); expect(calls).toHaveLength(3); // a connection that succeeded resets the backoff to 1 s
    expect(calls.map((c) => c.lastEventId)).toEqual([null, "6", "6"]);
    // Residual (INTEGRATION_HANDOFF G-04): if the real server ends the case stream after chat_closed, this is a request per second
    // for as long as the case page stays open. Nothing here can tell whether it does.
  });
});

describe("UNIT (fake transport) G-04: the chat stream through SCR-1", () => {
  const closed = (id: number) => `id: ${id}\nevent: chat_closed\ndata: ${JSON.stringify({ event_id: id, type: "chat_closed", at: "2026-10-16T14:24:00-05:00", speaker: { kind: "event", display_name: null }, line: "This chat has ended.", composer_disabled: true })}\n\n`;
  async function startChat(answers: (() => Response)[]) {
    const r = open("/", "customer", answers, (ctx) => (ctx.op === "startChatSession" ? ok(startExample(), 201) : undefined));
    await screen.findByRole("log");
    return r;
  }
  it("a replayed frame after reconnect is delivered once", async () => {
    const frames = streamFrames("streamChatEvents").text; // ids 12, 13, 14
    const { calls } = await startChat([() => body(frames), () => body(frames), () => body("", true)]);
    await tick(100);
    await tick(1100);
    await tick(100);
    expect(calls[1].lastEventId).toBe("14");
    const log = within(screen.getByRole("log")); // the polite live region repeats the text, so count inside the thread only
    await waitFor(() => expect(log.getAllByText(/Hi Omar, I can look at the after-hours charge with you\./)).toHaveLength(1));
    expect(log.getAllByText("The assistant is paused while Riley is here.")).toHaveLength(1);
  });

  it("after chat_closed the stream is not reopened: the consumer drops its spec", async () => {
    const { calls } = await startChat([() => body(closed(40)), () => body("", true)]);
    await tick(100);
    await screen.findByRole("button", { name: "Start a new chat" });
    const n = calls.length;
    await tick(30_000);
    expect(calls).toHaveLength(n);
    expect(n).toBe(1);
  });
});
