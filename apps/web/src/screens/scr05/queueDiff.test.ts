import { describe, expect, it } from "vitest";
import { countChangedRows } from "./queueDiff";
import { seededQueue } from "./queue.fixtures";

describe("countChangedRows", () => {
  it("counts an added row once", () => {
    const shown = seededQueue();
    const fresh = seededQueue();
    fresh.needs_my_action.push({ ...fresh.needs_my_action[0], reference: "MHC-C-0099" });
    expect(countChangedRows(shown, fresh)).toBe(1);
  });
  it("counts a removed row once", () => {
    const fresh = seededQueue();
    fresh.needs_my_action.pop();
    expect(countChangedRows(seededQueue(), fresh)).toBe(1);
  });
  it("counts a changed owner once", () => {
    const fresh = seededQueue();
    fresh.needs_my_action[1].owner = "Demo supervisor";
    expect(countChangedRows(seededQueue(), fresh)).toBe(1);
  });
  it("ignores as_of and age_label", () => {
    const fresh = seededQueue();
    fresh.as_of = "2026-10-16T14:30:00-05:00";
    fresh.needs_my_action.forEach((r) => { r.age_label = "Open 99 min"; });
    expect(countChangedRows(seededQueue(), fresh)).toBe(0);
  });
  it("returns 0 for identical payloads", () => {
    expect(countChangedRows(seededQueue(), seededQueue())).toBe(0);
  });
});
