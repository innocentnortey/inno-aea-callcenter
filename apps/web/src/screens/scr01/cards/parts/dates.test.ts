import { describe, expect, it } from "vitest";
import { formatDayLong, formatDayShort } from "@/lib/time";
import { chicagoIso, dayIso, formatMonthDayYear, parseWindowLabel, spokenWindow, windowIsos } from "./dates";

describe("dates", () => {
  it("builds Chicago ISO with the right offset", () => {
    expect(chicagoIso("2026-10-21", "08:00")).toBe("2026-10-21T08:00:00-05:00");
    expect(chicagoIso("2026-11-02", "08:00")).toBe("2026-11-02T08:00:00-06:00");
    expect(windowIsos("2026-10-21", "12:00-16:00")).toEqual({ startIso: "2026-10-21T12:00:00-05:00", endIso: "2026-10-21T16:00:00-05:00" });
  });
  it("formats date-only values on the right day", () => {
    expect(formatDayShort(dayIso("2026-10-21"))).toBe("Wed Oct 21");
    expect(formatDayLong(dayIso("2026-10-21"))).toBe("Wednesday, October 21, 2026");
    expect(formatMonthDayYear("2026-11-01")).toBe("Nov 1, 2026");
  });
  it("spells a window and parses a label", () => {
    expect(spokenWindow("8:00 am – 12:00 pm")).toBe("8:00 am to 12:00 pm");
    expect(parseWindowLabel("8:00 am – 12:00 pm")).toEqual({ start: "08:00", end: "12:00" });
    expect(parseWindowLabel("12:00 pm – 4:00 pm")).toEqual({ start: "12:00", end: "16:00" });
    expect(parseWindowLabel("soon")).toBeNull();
  });
});
