import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DEFAULT_LIMITS } from "./pending";
import { usePendingPhase } from "./usePendingPhase";

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("usePendingPhase", () => {
  it("is hidden with no pending turn", () => {
    expect(renderHook(() => usePendingPhase(null, DEFAULT_LIMITS)).result.current).toBe("hidden");
  });
  it("walks hidden, replying, still, gave-up at the boundaries", () => {
    const pending = { turnId: "t", startedAtMs: Date.now() };
    const { result } = renderHook(() => usePendingPhase(pending, DEFAULT_LIMITS));
    expect(result.current).toBe("hidden");
    act(() => { vi.advanceTimersByTime(299); });
    expect(result.current).toBe("hidden");
    act(() => { vi.advanceTimersByTime(1); });
    expect(result.current).toBe("replying");
    act(() => { vi.advanceTimersByTime(9700); });
    expect(result.current).toBe("still");
    act(() => { vi.advanceTimersByTime(55000); });
    expect(result.current).toBe("gave-up");
  });
  it("clears its timers on unmount", () => {
    const pending = { turnId: "t", startedAtMs: Date.now() };
    const { unmount } = renderHook(() => usePendingPhase(pending, DEFAULT_LIMITS));
    unmount();
    expect(vi.getTimerCount()).toBe(0);
  });
});
