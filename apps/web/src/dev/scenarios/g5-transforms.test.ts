import { describe, expect, it } from "vitest";
import { specExample } from "@/screens/reads/test/specExample";
import { rebaseMonitoring, withExtraFlag, withLiveQueue, withNullPromises, withReviewed, withoutRow } from "./g5-transforms";

describe("g5-transforms", () => {
  it("withoutRow removes MHC-C-0007 from Unowned and decrements the count", () => {
    const out = withoutRow("MHC-C-0007")(specExample("getOversight", "SEEDED"));
    expect(out.lanes.unowned.count).toBe(1);
    expect(out.lanes.unowned.rows.map((r) => r.reference)).toEqual(["MHC-C-0006"]);
    expect(out.lanes.p0_p1.count).toBe(1);
  });
  it("withLiveQueue sets the queue length", () => {
    expect(withLiveQueue(2)(specExample("getOversight", "SEEDED")).live_queue_length).toBe(2);
  });
  it("withExtraFlag adds exactly one new flag with a new id", () => {
    const base = specExample("listFlags", "THREE");
    const out = withExtraFlag(base);
    expect(out.flags).toHaveLength(base.flags.length + 1);
    expect(out.flags[out.flags.length - 1]).toMatchObject({ flag_id: "flg-4", status: "new" });
    expect(withExtraFlag(specExample("listFlags", "EMPTY")).flags).toHaveLength(0);
  });
  it("withReviewed marks only the named flag", () => {
    const base = withExtraFlag(specExample("listFlags", "THREE"));
    const out = withReviewed("flg-3", { by: "Demo supervisor", note: "ok" })(base);
    expect(out.flags.map((f) => f.status)).toEqual(["reviewed", "new"]);
    expect(out.flags[0]).toMatchObject({ reviewed_by: "Demo supervisor", reviewed_note: "ok" });
  });
  it("rebaseMonitoring(0) puts as_of within a second of now; rebaseMonitoring(300000) is five minutes old", () => {
    const base = specExample("getMonitoring", "DEFAULT");
    expect(Math.abs(Date.now() - Date.parse(rebaseMonitoring(0)(base).as_of))).toBeLessThan(1000);
    const age = Date.now() - Date.parse(rebaseMonitoring(300_000)(base).as_of);
    expect(age).toBeGreaterThanOrEqual(300_000);
    expect(age).toBeLessThan(301_000);
  });
  it("withNullPromises keeps the other measures", () => {
    const base = specExample("getOwnerMetrics", "SEEDED");
    const out = withNullPromises(base);
    expect(out.promises_kept_on_time).toMatchObject({ value: null, null_reason: "No promises are due yet.", case_refs: [] });
    expect(out.handoffs).toEqual(base.handoffs);
    expect(out.missed_promises).toEqual([]);
  });
  it("inputs are not mutated", () => {
    const o = specExample("getOversight", "SEEDED");
    const f = specExample("listFlags", "THREE");
    const m = specExample("getOwnerMetrics", "SEEDED");
    const mon = specExample("getMonitoring", "DEFAULT");
    const snaps = [structuredClone(o), structuredClone(f), structuredClone(m), structuredClone(mon)];
    withoutRow("MHC-C-0007")(o); withLiveQueue(3)(o); withExtraFlag(f); withReviewed("flg-3", { by: null, note: null })(f); withNullPromises(m); rebaseMonitoring(1)(mon);
    expect([o, f, m, mon]).toEqual(snaps);
  });
});
