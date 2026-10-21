import { afterEach, describe, expect, it, vi } from "vitest";
import type { StreamSpec, StreamStatus } from "@/api/transport";
import { createDevStreamOpener, dropStreams, emitToStream, resumeStreams, setActiveStreamScript } from "./stream/dev-stream";
import { chatEvents } from "./stream/events";
import { jsonResponse } from "@/test/fakeTransport";

function open(thread = "thr_9d41") {
  const events: { id: number | null; type: string }[] = [];
  const statuses: StreamStatus[] = [];
  const opener = createDevStreamOpener(async () => jsonResponse(200, {}));
  const spec: StreamSpec = {
    op: "streamChatEvents", path: { thread_id: thread },
    onEvent: (_d, id, type) => events.push({ id, type }), onStatus: (s) => statuses.push(s),
  };
  return { handle: opener(spec), events, statuses };
}
const tick = () => new Promise((r) => setTimeout(r, 0));
afterEach(() => { setActiveStreamScript(null); vi.useRealTimers(); });

describe("dev stream", () => {
  it("delivers events in order with increasing ids", async () => {
    const { handle, events, statuses } = open();
    await tick(); await tick();
    expect(statuses).toContain("open");
    emitToStream("thr_9d41", chatEvents.representative_joined());
    emitToStream("thr_9d41", chatEvents.ai_paused());
    emitToStream("thr_9d41", chatEvents.staff_message());
    expect(events.map((e) => e.type)).toEqual(["representative_joined", "ai_paused", "staff_message"]);
    expect(events.map((e) => e.id)).toEqual([1, 2, 3]);
    handle.close();
  });
  it("buffers while dropped and replays in order on resume", async () => {
    const { handle, events, statuses } = open("thr_a");
    await tick(); await tick();
    dropStreams();
    expect(statuses.at(-1)).toBe("reconnecting");
    emitToStream("thr_a", chatEvents.staff_message());
    emitToStream("thr_a", chatEvents.ai_resumed());
    expect(events).toHaveLength(0);
    resumeStreams();
    expect(statuses.at(-1)).toBe("open");
    expect(events.map((e) => e.type)).toEqual(["staff_message", "ai_resumed"]);
    handle.close();
  });
  it("closes after chat_closed", async () => {
    const { events, statuses } = open("thr_b");
    await tick(); await tick();
    emitToStream("thr_b", chatEvents.chat_closed());
    expect(statuses.at(-1)).toBe("closed");
    emitToStream("thr_b", chatEvents.ai_resumed());
    expect(events.map((e) => e.type)).toEqual(["chat_closed"]);
  });
  it("plays a scenario script on a timer", async () => {
    vi.useFakeTimers();
    setActiveStreamScript({ thread: "thr_c", steps: [{ afterMs: 100, event: chatEvents.representative_joined() }] });
    const { handle, events } = open("thr_c");
    await vi.advanceTimersByTimeAsync(10);
    expect(events).toHaveLength(0);
    await vi.advanceTimersByTimeAsync(200);
    expect(events.map((e) => e.type)).toEqual(["representative_joined"]);
    handle.close();
  });
});
