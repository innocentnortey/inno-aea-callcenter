import { describe, expect, it } from "vitest";
import * as copy from "./copy";
import { resetSuccessLine, staffingSuccessLine } from "./copy";

describe("staffingSuccessLine", () => {
  it("on", () => expect(staffingSuccessLine("simulated_on_shift", 0)).toBe("Simulated staff on shift (demo). The banner now shows on the chat and the console."));
  it("off with 1", () => expect(staffingSuccessLine("nobody_online", 1)).toBe("Shift ended. 1 waiting customer now has the 1-business-day promise."));
  it("off with 2", () => expect(staffingSuccessLine("nobody_online", 2)).toBe("Shift ended. 2 waiting customers now have the 1-business-day promise."));
  it("off with 0", () => expect(staffingSuccessLine("nobody_online", 0)).toBe("Shift ended. Nobody is online."));
});

describe("resetSuccessLine", () => {
  const base = "Demo reset. Bookings, cases and codes are back to the start, and the date is Fri Oct 16, 2026.";
  it("with chats ended", () => expect(resetSuccessLine(2, false)).toBe(`${base} Open chats have ended.`));
  it("without chats ended", () => expect(resetSuccessLine(0, false)).toBe(base));
  it("with the role reset", () =>
    expect(resetSuccessLine(2, true)).toBe(`${base} Open chats have ended. The demo was reset, so you're back to the customer role. Pick a role again.`));
});

describe("forbidden words", () => {
  const lines = Object.values(copy).flatMap((v) => (typeof v === "string" ? [v] : Array.isArray(v) ? v : []));
  it("never pairs the assistant with simulated", () => {
    for (const l of lines) expect(/assistant/i.test(l) && /simulated/i.test(l), l).toBe(false);
  });
  it("claims nobody is online only as Nobody online / Nobody is online", () => {
    for (const l of lines.filter((x) => /online/i.test(x))) {
      expect(/nobody (is )?online|unless you turn on|every open|online\)/i.test(l) || /Nobody/.test(l), l).toBe(true);
    }
  });
});
