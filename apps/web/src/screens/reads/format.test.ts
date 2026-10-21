import { describe, expect, it } from "vitest";
import { ApiError } from "@/api/errors";
import {
  dateOnlyToIso, formatCents, formatCount, formatSeconds, formatShare, formatTileValue, nOfN, pluralize, readErrorText,
} from "./format";

describe("format", () => {
  it("pluralize picks by count", () => {
    expect(pluralize(1, "case", "cases")).toBe("case");
    expect(pluralize(0, "case", "cases")).toBe("cases");
  });
  it("formatShare rounds and dashes null", () => {
    expect(formatShare(0.75)).toBe("75%");
    expect(formatShare(0.667)).toBe("67%");
    expect(formatShare(0.294)).toBe("29%");
    expect(formatShare(0)).toBe("0%");
    expect(formatShare(null)).toBe("—");
  });
  it("formatCount and nOfN", () => {
    expect(formatCount(null)).toBe("—");
    expect(formatCount(18)).toBe("18");
    expect(nOfN(9, 12, "in-scope conversations")).toBe("9 of 12 in-scope conversations");
    expect(nOfN(0, 0, "promises due")).toBe("0 promises due");
    expect(nOfN(null, null, "x")).toBe("—");
  });
  it("formatSeconds, formatCents, formatTileValue", () => {
    expect(formatSeconds(4200)).toBe("4.2 s");
    expect(formatSeconds(10200)).toBe("10.2 s");
    expect(formatSeconds(13800)).toBe("13.8 s");
    expect(formatCents(612)).toBe("$6.12");
    expect(formatCents(3000)).toBe("$30.00");
    expect(formatCents(3012)).toBe("$30.12");
    expect(formatTileValue({ value: 4200, unit: "ms" })).toBe("4.2 s");
    expect(formatTileValue({ value: 0.05, unit: "share" })).toBe("5%");
    expect(formatTileValue({ value: 18, unit: "count" })).toBe("18");
  });
  it("dateOnlyToIso keeps the Chicago date", () => {
    expect(dateOnlyToIso("2026-10-20")).toBe("2026-10-20T12:00:00-05:00");
  });
  it("readErrorText maps the named errors", () => {
    expect(readErrorText(new ApiError(503, "RESET_IN_PROGRESS", {}), "x")).toBe("The demo is resetting. Try again in a few seconds.");
    expect(readErrorText(new ApiError(429, "REQUEST_RATE_LIMITED", {}), "x")).toBe("Try again in a moment.");
    expect(readErrorText(new ApiError(0, "NETWORK", null), "Didn't load.")).toBe("Didn't load.");
    expect(readErrorText(undefined, "Didn't load.")).toBe("Didn't load.");
  });
});
