import { describe, expect, it } from "vitest";
import { TIME_OPTIONS, toDemoIso } from "./wakeUp";

describe("wakeUp", () => {
  it("builds a CDT time", () => expect(toDemoIso("2026-10-19", "09:00")).toBe("2026-10-19T09:00:00-05:00"));
  it("builds a CST time after the change", () => expect(toDemoIso("2026-11-02", "08:00")).toBe("2026-11-02T08:00:00-06:00"));
  it("returns undefined when either part is empty", () => {
    expect(toDemoIso("", "09:00")).toBeUndefined();
    expect(toDemoIso("2026-10-19", "")).toBeUndefined();
  });
  it("TIME_OPTIONS runs 6:00 am to 8:00 pm in 12-hour labels", () => {
    expect(TIME_OPTIONS).toHaveLength(29);
    expect(TIME_OPTIONS[0]).toEqual({ value: "06:00", label: "6:00 am" });
    expect(TIME_OPTIONS.at(-1)!.label).toBe("8:00 pm");
    for (const o of TIME_OPTIONS) expect(o.label).not.toMatch(/\u202f|[AP]M/);
  });
});
