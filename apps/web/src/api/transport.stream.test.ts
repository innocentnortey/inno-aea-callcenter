// UNIT (fake transport): the real defaultTransport.openStream loop run against a stubbed global fetch (G-04).
// Frames are the spec's own FRAMES examples (CON-3 ids 12..14, CON-21 ids 5..6). Backoff runs on fake timers.
// None of this talks to a server: MOCK-ONLY/UNIT evidence about the client loop, never REAL-BACKEND.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { onAuthLost } from "./refetch";
import { SseParser } from "./sse";
import { defaultTransport, type StreamSpec, type StreamStatus } from "./transport";
import { specError, streamFrames, violationsLoose } from "@/test/spec";

const enc = new TextEncoder();
const frames = (op: "streamChatEvents" | "streamCaseEvents") => streamFrames(op).text;
function body(text: string, then: "close" | "hang" = "close"): Response {
  const s = new ReadableStream<Uint8Array>({
    start(c) {
      c.enqueue(enc.encode(text));
      if (then === "close") c.close();
    },
  });
  return new Response(s, { status: 200, headers: { "Content-Type": "text/event-stream" } });
}
const err = (status: number, b?: unknown) => new Response(b === undefined ? "{}" : JSON.stringify(b), { status });
const chat = { op: "streamChatEvents" as const, path: { thread_id: "thr_9d41" } };
const caseSpec = { op: "streamCaseEvents" as const, path: { reference: "MHC-C-0007" } };

type Call = { url: string; lastEventId: string | null };
function stubFetch(answers: (Response | Error)[]) {
  const calls: Call[] = [];
  const f = vi.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, lastEventId: (init.headers as Record<string, string>)["Last-Event-ID"] ?? null });
    const a = answers[Math.min(calls.length - 1, answers.length - 1)];
    if (a instanceof Error) throw a;
    return a.clone();
  });
  vi.stubGlobal("fetch", f);
  return { calls, f };
}
function open(spec: Omit<StreamSpec, "onEvent" | "onStatus">) {
  const events: { data: unknown; id: number | null; type: string }[] = [];
  const statuses: StreamStatus[] = [];
  const handle = defaultTransport.openStream({ ...spec, onEvent: (data, id, type) => events.push({ data, id, type }), onStatus: (s) => statuses.push(s) });
  return { events, statuses, handle };
}
const tick = (ms = 0) => vi.advanceTimersByTimeAsync(ms);

beforeEach(() => vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] }));
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

describe("UNIT (fake transport): the spec's FRAMES examples", () => {
  it.each(["streamChatEvents", "streamCaseEvents"] as const)("%s: every frame's data line is a valid event of the spec's event schema", (op) => {
    const { eventSchema } = streamFrames(op);
    const parsed = new SseParser().push(frames(op));
    expect(parsed.length).toBeGreaterThanOrEqual(2);
    for (const f of parsed.filter((x) => x.data)) expect(violationsLoose(eventSchema, JSON.parse(f.data)), `id ${f.id}`).toEqual([]);
  });
});

describe("UNIT (fake transport): G-04 Last-Event-ID, reconnect, server close", () => {
  it("the first request carries no Last-Event-ID unless the caller has one; the caller's id is sent as is", async () => {
    const a = stubFetch([err(404)]);
    open(chat);
    await tick();
    expect(a.calls[0].lastEventId).toBeNull();
    const b = stubFetch([err(404)]);
    open({ ...chat, lastEventId: 11 });
    await tick();
    expect(b.calls[0].lastEventId).toBe("11");
  });

  it("when the server closes the body, the next request resends the highest id seen (14) after the first backoff", async () => {
    const { calls } = stubFetch([body(frames("streamChatEvents")), body("", "hang")]);
    const { events, statuses } = open(chat);
    await tick();
    expect(events.map((e) => e.id)).toEqual([12, 13, 14]);
    expect(events.map((e) => e.type)).toEqual(["representative_joined", "ai_paused", "staff_message"]);
    expect(calls).toHaveLength(1);
    expect(statuses).toContain("reconnecting");
    await tick(999);
    expect(calls).toHaveLength(1); // still inside the 1 s backoff
    await tick(1);
    expect(calls).toHaveLength(2);
    expect(calls[1]).toEqual({ url: "/api/chat/sessions/thr_9d41/events", lastEventId: "14" });
  });

  it("the case stream resends its own highest id (6) on the case URL", async () => {
    const { calls } = stubFetch([body(frames("streamCaseEvents")), body("", "hang")]);
    open(caseSpec);
    await tick(1000);
    expect(calls[1]).toEqual({ url: "/api/staff/cases/MHC-C-0007/events", lastEventId: "6" });
  });

  it("a replay that starts below the highest id never lowers Last-Event-ID", async () => {
    const two = 'id: 13\nevent: ai_paused\ndata: {"event_id":13}\n\n';
    const { calls } = stubFetch([body(frames("streamChatEvents")), body(two), body("", "hang")]);
    open(chat);
    await tick(1000); // second connection replays 13 only
    await tick(2000); // third connection after the 2 s backoff
    expect(calls.map((c) => c.lastEventId)).toEqual([null, "14", "14"]);
  });

  it("a 5xx and a network error reconnect with backoff 1 s, 2 s, 4 s, then hold at 5 s", async () => {
    const { calls } = stubFetch([err(502), new Error("offline"), err(503), err(500), err(500), body("", "hang")]);
    const { statuses } = open(chat);
    await tick();
    expect(calls).toHaveLength(1);
    await tick(1000); expect(calls).toHaveLength(2);
    await tick(2000); expect(calls).toHaveLength(3);
    await tick(4000); expect(calls).toHaveLength(4);
    await tick(5000); expect(calls).toHaveLength(5);
    await tick(5000); expect(calls).toHaveLength(6);
    await tick(); expect(statuses.at(-1)).toBe("open");
    expect(statuses.filter((s) => s === "reconnecting").length).toBe(5);
  });

  it("a successful connection resets the backoff to 1 s", async () => {
    const { calls } = stubFetch([err(502), err(502), body(frames("streamChatEvents")), body("", "hang")]);
    open(chat);
    await tick(); await tick(1000); await tick(2000);
    expect(calls).toHaveLength(3); // third connection succeeded and closed
    await tick(1000);
    expect(calls).toHaveLength(4); // 1 s again, not 4 s
  });

  it("close() after a server close stops the loop: no further request, no 'closed' status", async () => {
    const { calls } = stubFetch([body(frames("streamChatEvents")), body("", "hang")]);
    const { handle, statuses } = open(chat);
    await tick();
    handle.close();
    await tick(10_000);
    expect(calls).toHaveLength(1);
    expect(statuses).not.toContain("closed");
  });

  it("heartbeat comments and malformed frames are skipped without stopping the stream", async () => {
    const text = ": heartbeat\n\nid: 20\nevent: x\ndata: {not json\n\nid: 21\nevent: ai_paused\ndata: {\"event_id\":21}\n\n";
    const { calls } = stubFetch([body(text), body("", "hang")]);
    const { events } = open(chat);
    await tick(1000);
    expect(events.map((e) => e.id)).toEqual([21]);
    expect(calls[1].lastEventId).toBe("21"); // the malformed frame still advanced the id (20), 21 is the highest
  });

  it.each([404, 410])("a %i stops the stream for good: one request, status closed, no auth-lost signal", async (status) => {
    const lost = vi.fn();
    const off = onAuthLost(lost);
    const { calls } = stubFetch([status === 404 ? err(404, specError("streamChatEvents", 404, "SESSION_NOT_FOUND")) : err(410, specError("submitTurn", 410, "SESSION_ENDED"))]);
    const { statuses } = open(chat);
    await tick(20_000);
    expect(calls).toHaveLength(1);
    expect(statuses.at(-1)).toBe("closed");
    expect(statuses).not.toContain("reconnecting");
    expect(lost).not.toHaveBeenCalled();
    off();
  });

  it("a case stream 403 (role changed) and 404 stop with no auth-lost signal", async () => {
    const lost = vi.fn();
    const off = onAuthLost(lost);
    for (const [status, b] of [[403, specError("streamCaseEvents", 403, "ROLE_NOT_ALLOWED_ROLE_RESET")], [404, specError("streamCaseEvents", 404, "CASE_NOT_FOUND")]] as const) {
      const { calls } = stubFetch([err(status, b)]);
      const { statuses } = open(caseSpec);
      await tick(10_000);
      expect(calls, String(status)).toHaveLength(1);
      expect(statuses.at(-1)).toBe("closed");
    }
    expect(lost).not.toHaveBeenCalled();
    off();
  });

  it("a 401 carries the body's reason (expired or none) into the auth-lost signal and stops; a body that is not JSON means none", async () => {
    const lost = vi.fn();
    const off = onAuthLost(lost);
    for (const [name, reason] of [["UNAUTHENTICATED_EXPIRED", "expired"], ["UNAUTHENTICATED", "none"]] as const) {
      lost.mockClear();
      const { calls } = stubFetch([err(401, specError("streamChatEvents", 401, name))]);
      open(chat);
      await tick(10_000);
      expect(lost).toHaveBeenCalledTimes(1);
      expect(lost).toHaveBeenCalledWith(reason);
      expect(calls).toHaveLength(1);
    }
    lost.mockClear();
    stubFetch([new Response("<html>nope</html>", { status: 401 })]);
    open(chat);
    await tick(10_000);
    expect(lost).toHaveBeenCalledWith("none");
    off();
  });
});
