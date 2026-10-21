import { describe, expect, it } from "vitest";
import { dataAgeMinutes, staleLine } from "./dataAge";

const asOf = "2026-10-16T14:20:00-05:00";
const at = (iso: string) => Date.parse(iso);
describe("dataAge", () => {
  it("fresh data has no line", () => expect(staleLine(asOf, at("2026-10-16T14:20:30-05:00"))).toBeNull());
  it("exactly 2 minutes old has no line", () => expect(staleLine(asOf, at("2026-10-16T14:22:00-05:00"))).toBeNull());
  it("5 minutes gives This data is 5 minutes old.", () => expect(staleLine(asOf, at("2026-10-16T14:25:00-05:00"))).toBe("This data is 5 minutes old."));
  it("a future as_of is 0 minutes and no line", () => {
    expect(dataAgeMinutes(asOf, at("2026-10-16T14:00:00-05:00"))).toBe(0);
    expect(staleLine(asOf, at("2026-10-16T14:00:00-05:00"))).toBeNull();
  });
});
