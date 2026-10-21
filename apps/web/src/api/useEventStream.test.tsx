import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { getTransport, setTransport, defaultTransport, type StreamSpec } from "./transport";
import { useEventStream } from "./useEventStream";

afterEach(() => setTransport(defaultTransport));

describe("useEventStream", () => {
  it("ignores frames and statuses from a handle that was replaced", () => {
    const specs: StreamSpec[] = [];
    setTransport({ ...getTransport(), openStream(s) { specs.push(s); return { close() {} }; } });
    const got: unknown[] = [];
    const { result, rerender } = renderHook(({ ref }) => useEventStream({ op: "streamCaseEvents", path: { reference: ref } }, (d) => got.push(d)), { initialProps: { ref: "A" } });
    rerender({ ref: "B" });
    expect(specs).toHaveLength(2);
    act(() => specs[1].onStatus("open"));
    act(() => { specs[0].onEvent({ stale: true }, 5, "x"); specs[0].onStatus("closed"); });
    expect(got).toEqual([]);
    expect(result.current.status).toBe("open");
    expect(result.current.lastEventId).toBeNull();
    act(() => specs[1].onEvent({ ok: 1 }, 6, "x"));
    expect(got).toEqual([{ ok: 1 }]);
  });
});
