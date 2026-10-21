import { describe, expect, it } from "vitest";
import { SseParser } from "./sse";

describe("SseParser", () => {
  it("parses two frames in one chunk", () => {
    const f = new SseParser().push('id: 1\nevent: a\ndata: {"x":1}\n\nid: 2\ndata: {"y":2}\n\n');
    expect(f).toHaveLength(2);
    expect(f[0]).toEqual({ id: 1, event: "a", data: '{"x":1}' });
    expect(f[1]).toEqual({ id: 2, event: "message", data: '{"y":2}' });
  });
  it("parses one frame split over three chunks", () => {
    const p = new SseParser();
    expect(p.push("id: 7\nevent: ai_pa")).toEqual([]);
    expect(p.push('used\ndata: {"a"')).toEqual([]);
    expect(p.push(":1}\n\n")).toEqual([{ id: 7, event: "ai_paused", data: '{"a":1}' }]);
  });
  it("handles CRLF and multi-line data", () => {
    const f = new SseParser().push("id: 3\r\ndata: one\r\ndata: two\r\n\r\n");
    expect(f).toEqual([{ id: 3, event: "message", data: "one\ntwo" }]);
  });
  it("returns a heartbeat comment as a frame with no data", () => {
    const f = new SseParser().push(": heartbeat\n\n");
    expect(f).toHaveLength(1);
    expect(f[0].comment).toBe("heartbeat");
    expect(f[0].data).toBe("");
  });
  it("gives a null id when none is sent", () => {
    expect(new SseParser().push("data: {}\n\n")[0].id).toBeNull();
  });
});
