import { afterEach, describe, expect, it, vi } from "vitest";
import { onAuthLost } from "./refetch";
import { defaultTransport, type StreamStatus } from "./transport";

const enc = new TextEncoder();
function sseResponse(chunks: Promise<string>[]): Response {
  let i = 0;
  const stream = new ReadableStream<Uint8Array>({
    async pull(c) {
      if (i >= chunks.length) return c.close();
      c.enqueue(enc.encode(await chunks[i++]));
    },
  });
  return new Response(stream, { status: 200, headers: { "Content-Type": "text/event-stream" } });
}
const flush = () => new Promise((r) => setTimeout(r, 10));
const spec = { op: "streamCaseEvents" as const, path: { reference: "MHC-C-0007" } };

afterEach(() => vi.unstubAllGlobals());

describe("defaultTransport.openStream", () => {
  it("after close() no frame reaches onEvent and no status is emitted", async () => {
    let release!: (s: string) => void;
    const late = new Promise<string>((r) => { release = r; });
    vi.stubGlobal("fetch", vi.fn(async () => sseResponse([Promise.resolve('id: 1\ndata: {"a":1}\n\n'), late])));
    const events: unknown[] = [];
    const statuses: StreamStatus[] = [];
    const h = defaultTransport.openStream({ ...spec, onEvent: (d) => events.push(d), onStatus: (s) => statuses.push(s) });
    await flush();
    expect(events).toEqual([{ a: 1 }]);
    const before = statuses.length;
    h.close();
    release('id: 2\ndata: {"b":2}\n\n');
    await flush();
    expect(events).toEqual([{ a: 1 }]);
    expect(statuses).toHaveLength(before);
    expect(statuses).not.toContain("closed");
  });

  it("a 401 raises the shared auth-lost signal and stops; 403 stops silently", async () => {
    const lost = vi.fn();
    const off = onAuthLost(lost);
    const f = vi.fn(async () => new Response(JSON.stringify({ error: { code: "UNAUTHENTICATED", details: { reason: "expired" } } }), { status: 401 }));
    vi.stubGlobal("fetch", f);
    const statuses: StreamStatus[] = [];
    defaultTransport.openStream({ ...spec, onEvent: () => undefined, onStatus: (s) => statuses.push(s) });
    await flush();
    expect(lost).toHaveBeenCalledWith("expired");
    expect(f).toHaveBeenCalledTimes(1);
    expect(statuses.at(-1)).toBe("closed");

    lost.mockClear();
    vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 403 })));
    defaultTransport.openStream({ ...spec, onEvent: () => undefined, onStatus: () => undefined });
    await flush();
    expect(lost).not.toHaveBeenCalled();
    off();
  });
});
