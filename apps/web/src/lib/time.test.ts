import { describe, expect, it } from "vitest";
import {
  formatClockLabel, formatDateTimeShort, formatDayLong, formatDayShort, formatDemoDate, formatSentence, formatStaffTime,
  formatTimePoint, formatTimeRange, formatTimeRangeArrow,
} from "./time";

describe("time formatting", () => {
  it("formats points", () => {
    expect(formatTimePoint("2026-10-19T19:00:00-05:00")).toBe("7:00 pm");
    expect(formatTimePoint("2026-10-16T12:00:00-05:00")).toBe("12:00 pm");
    expect(formatTimePoint("2026-10-17T00:00:00-05:00")).toBe("12:00 am");
  });
  it("formats ranges with an en dash and an arrow", () => {
    expect(formatTimeRange("2026-10-21T08:00:00-05:00", "2026-10-21T12:00:00-05:00")).toBe("8:00 am – 12:00 pm");
    expect(formatTimeRangeArrow("2026-10-21T08:00:00-05:00", "2026-10-21T12:00:00-05:00")).toBe("8:00 am → 12:00 pm");
  });
  it("formats the composite styles", () => {
    const t = "2026-10-19T19:00:00-05:00";
    expect(formatDateTimeShort(t)).toBe("Mon Oct 19 · 7:00 pm");
    expect(formatStaffTime(t)).toBe("Mon 7:00 pm");
    expect(formatSentence(t)).toBe("Monday, October 19, 7:00 pm");
    expect(formatDemoDate("2026-10-16T14:20:00-05:00")).toBe("Fri Oct 16, 2026 (demo date)");
    expect(formatClockLabel("2026-10-16T14:20:00-05:00")).toBe("Fri Oct 16 · 2:20 pm");
    expect(formatDayShort("2026-10-21T08:00:00-05:00")).toBe("Wed Oct 21");
    expect(formatDayLong("2026-10-21T08:00:00-05:00")).toBe("Wednesday, October 21, 2026");
  });
  it("handles daylight saving and other offsets", () => {
    expect(formatTimePoint("2026-11-02T08:00:00-06:00")).toBe("8:00 am");
    expect(formatTimePoint("2026-10-19T20:00:00-04:00")).toBe("7:00 pm");
  });
  it("never emits a narrow no-break space or capital AM/PM", () => {
    const out = [
      formatTimePoint("2026-10-19T19:00:00-05:00"), formatTimeRange("2026-10-21T08:00:00-05:00", "2026-10-21T12:00:00-05:00"),
      formatDateTimeShort("2026-10-19T07:00:00-05:00"),
    ];
    for (const s of out) expect(s).not.toMatch(new RegExp(String.fromCharCode(0x202f) + "|[AP]M"));
  });
});
