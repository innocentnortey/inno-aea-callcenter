import { describe, expect, it } from "vitest";
import { specExample } from "../reads/test/specExample";
import { buildEvalRows, formatRange, hasTargets, mixSummary } from "./evalRows";

describe("evalRows", () => {
  const both = () => specExample("getLatestEval", "BOTH_SPLITS");
  it("rows start with the held-out measures in order, then dev-only ids", () => {
    const b = both();
    b.splits.dev!.measures.push({ ...b.splits.dev!.measures[0]!, id: "E-99", label: "Dev only measure" });
    const rows = buildEvalRows(b.splits);
    expect(rows.slice(0, 6).map((r) => r.id)).toEqual(b.splits.held_out!.measures.map((m) => m.id));
    expect(rows[rows.length - 1]).toMatchObject({ id: "E-99", heldOut: null });
  });
  it("E-1 appears once with both columns", () => {
    const rows = buildEvalRows(both().splits).filter((r) => r.id === "E-1");
    expect(rows).toHaveLength(1);
    expect(rows[0]!.heldOut).not.toBeNull();
    expect(rows[0]!.dev).not.toBeNull();
  });
  it("dev-only run gives rows with heldOut null", () => {
    const rows = buildEvalRows(specExample("getLatestEval", "DEV_ONLY").splits);
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.every((r) => r.heldOut === null && r.dev !== null)).toBe(true);
  });
  it("NO_RUN gives no rows", () => {
    expect(buildEvalRows(specExample("getLatestEval", "NO_RUN").splits)).toEqual([]);
  });
  it("hasTargets is false for the example and true when one target is set", () => {
    const b = both();
    expect(hasTargets(buildEvalRows(b.splits))).toBe(false);
    b.splits.held_out!.measures[0]!.target = "Target text";
    expect(hasTargets(buildEvalRows(b.splits))).toBe(true);
  });
  it("formatRange for the headline", () => {
    expect(formatRange(both().headline!)).toBe("Range over repeats: 60% – 68%");
    expect(formatRange(both().splits.held_out!.measures[1]!)).toBeNull();
  });
  it("mixSummary counts by origin", () => {
    expect(mixSummary(both().splits.held_out!)).toBe("8 transcript-derived and 4 labelled synthetic cases in the mix");
  });
});
