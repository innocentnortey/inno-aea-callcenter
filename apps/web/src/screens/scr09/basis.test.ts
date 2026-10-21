import { describe, expect, it } from "vitest";
import { specExample } from "../reads/test/specExample";
import { basisLine, isEmptyOwner, isStale } from "./basis";

describe("basis", () => {
  it("names the seeds and says not targets", () => {
    expect(basisLine(specExample("getOwnerMetrics", "SEEDED"))).toBe(
      "From stored conversations and cases, as of Fri Oct 16 · 2:20 pm (demo time). Includes 4 demo seed cases. These are not targets.",
    );
  });
  it("uses the singular for one seed", () => {
    expect(basisLine({ as_of: "2026-10-16T14:20:00-05:00", seeds_included: true, seed_count: 1 })).toContain("Includes 1 demo seed case.");
  });
  it("says so when seeds are not included", () => {
    expect(basisLine({ as_of: "2026-10-16T14:20:00-05:00", seeds_included: false, seed_count: 4 })).toContain("Does not include the 4 demo seed cases.");
  });
  it("isEmptyOwner is true for EMPTY and false for SEEDED", () => {
    expect(isEmptyOwner(specExample("getOwnerMetrics", "EMPTY"))).toBe(true);
    expect(isEmptyOwner(specExample("getOwnerMetrics", "SEEDED"))).toBe(false);
  });
  it("isStale compares the demo clock with as_of", () => {
    expect(isStale("2026-10-16T14:20:00-05:00", "2026-10-19T07:00:00-05:00")).toBe(true);
    expect(isStale("2026-10-16T14:20:00-05:00", "2026-10-16T14:20:00-05:00")).toBe(false);
    expect(isStale("2026-10-16T14:20:00-05:00", null)).toBe(false);
  });
});
