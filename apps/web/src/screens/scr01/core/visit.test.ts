import { describe, expect, it } from "vitest";
import { formatDateOnlyLong, formatDateOnlyShort, formatWindow, hhmmTo12h, visitSentence } from "./visit";

describe("visit formatting", () => {
  it("converts 24-hour strings to 12-hour", () => {
    expect(hhmmTo12h("00:00")).toBe("12:00 am");
    expect(hhmmTo12h("08:00")).toBe("8:00 am");
    expect(hhmmTo12h("12:00")).toBe("12:00 pm");
    expect(hhmmTo12h("12:30")).toBe("12:30 pm");
    expect(hhmmTo12h("16:00")).toBe("4:00 pm");
  });
  it("formats a window with an en dash and falls back when it does not parse", () => {
    expect(formatWindow("08:00-12:00", "x")).toBe("8:00 am – 12:00 pm");
    expect(formatWindow("soon", "8:00 am – 12:00 pm")).toBe("8:00 am – 12:00 pm");
  });
  it("does not shift the date across the timezone", () => {
    expect(formatDateOnlyShort("2026-10-21")).toBe("Wed Oct 21");
    expect(formatDateOnlyLong("2026-10-21")).toBe("Wednesday, October 21");
  });
  it("builds the landing sentence", () => {
    expect(visitSentence("2026-10-21", "08:00-12:00", "")).toBe("Wednesday, October 21, 8:00 am to 12:00 pm");
  });
  it("never emits 24-hour clocks, capital AM/PM or narrow spaces", () => {
    for (const out of [formatWindow("08:00-12:00", ""), visitSentence("2026-10-21", "13:00-17:00", "")]) {
      expect(out).not.toMatch(/\u202f|[AP]M/);
    }
  });
});
