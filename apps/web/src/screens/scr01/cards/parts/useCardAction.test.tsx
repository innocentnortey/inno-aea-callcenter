import { describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useCardAction } from "./useCardAction";

describe("useCardAction", () => {
  it("ignores a second call while one is in flight", async () => {
    let release: () => void = () => {};
    let calls = 0;
    const dispatch = () => { calls++; return new Promise<void>((r) => { release = r; }); };
    const { result } = renderHook(() => useCardAction(dispatch));
    let first: Promise<boolean> = Promise.resolve(false);
    act(() => { first = result.current.run({ kind: "person" }); });
    let second = true;
    await act(async () => { second = await result.current.run({ kind: "person" }); });
    expect(second).toBe(false);
    expect(calls).toBe(1);
    await act(async () => { release(); await first; });
    expect(await first).toBe(true);
    expect(result.current.pending).toBe(false);
  });
  it("returns false when dispatch rejects", async () => {
    const { result } = renderHook(() => useCardAction(() => Promise.reject(new Error("x"))));
    let ok = true;
    await act(async () => { ok = await result.current.run({ kind: "person" }); });
    expect(ok).toBe(false);
    expect(result.current.pending).toBe(false);
  });
});
