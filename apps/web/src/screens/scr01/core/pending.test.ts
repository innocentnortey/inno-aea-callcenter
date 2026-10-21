import { describe, expect, it } from "vitest";
import { DEFAULT_LIMITS, pendingPhase } from "./pending";

describe("pendingPhase", () => {
  it.each([[0, "hidden"], [299, "hidden"], [300, "replying"], [9999, "replying"], [10000, "still"], [64999, "still"], [65000, "gave-up"]] as const)("%i ms is %s", (ms, phase) => {
    expect(pendingPhase(ms, DEFAULT_LIMITS)).toBe(phase);
  });
});
