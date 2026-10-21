import { describe, expect, it } from "vitest";
import { specExample } from "../reads/test/specExample";
import { oversightSignature } from "./signature";

describe("oversightSignature", () => {
  it("same read twice gives equal signatures", () => {
    expect(oversightSignature(specExample("getOversight", "SEEDED"))).toBe(oversightSignature(specExample("getOversight", "SEEDED")));
  });
  it("SEEDED vs AFTER_ADVANCE differ", () => {
    expect(oversightSignature(specExample("getOversight", "SEEDED"))).not.toBe(oversightSignature(specExample("getOversight", "AFTER_ADVANCE")));
  });
  it("only as_of and age_label differing gives equal signatures", () => {
    const a = specExample("getOversight", "SEEDED");
    const b = specExample("getOversight", "SEEDED");
    b.as_of = "2026-10-16T14:21:00-05:00";
    b.demo_now = "2026-10-16T14:21:00-05:00";
    b.lanes.unowned.rows.forEach((r) => { r.age_label = "Open 99 min"; });
    expect(oversightSignature(a)).toBe(oversightSignature(b));
  });
});
