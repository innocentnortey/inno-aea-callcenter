import { describe, expect, it } from "vitest";
import { bestTimeLabel, caseTitle, createdLine, dueHeadline, headerStatusLine, humanizeKey, ownerLine } from "./caseText";
import { defaultCase, liveJoinedCase, safetyCase, waitingCase } from "./case.fixtures";

const NOW = "2026-10-16T14:20:00-05:00";
describe("caseText", () => {
  it("dueHeadline for safety, normal, window-start and label-only cases", () => {
    expect(dueHeadline(safetyCase().case)).toBe("No due time: safety");
    expect(dueHeadline(defaultCase().case)).toBe("Due Mon Oct 19 · 7:00 pm");
    const fee = { ...defaultCase().case, due_at: "2026-10-17T12:00:00-05:00", due_label: "Sat Oct 17 · 12:00 pm, the window start" };
    expect(dueHeadline(fee)).toBe("Due Sat Oct 17 · 12:00 pm, the window start");
    expect(dueHeadline({ ...defaultCase().case, due_at: null, due_label: "Later" })).toBe("Later");
  });
  it("createdLine", () => expect(createdLine(defaultCase().case)).toBe("Created Fri Oct 16, 2:14 pm"));
  it("ownerLine", () => {
    expect(ownerLine(defaultCase().case)).toBe("Unassigned, nobody owns it yet");
    expect(ownerLine(waitingCase().case)).toBe("Owned by Riley");
  });
  it("headerStatusLine for joined, live-queued, waiting, stuck waiting", () => {
    expect(headerStatusLine(liveJoinedCase(), NOW)).toBe("Live · you are replying · assistant paused");
    const q = defaultCase();
    q.case.lifecycle = "live_queued";
    q.live = { state: "queued", since: "2026-10-16T14:14:00-05:00", controller: "ai" };
    expect(headerStatusLine(q, NOW)).toBe("The customer is waiting in the chat since 2:14 pm.");
    expect(headerStatusLine(waitingCase(), NOW)).toBe("Wakes Mon Oct 19 · 9:00 am");
    expect(headerStatusLine(waitingCase(), "2026-10-19T10:00:00-05:00")).toBe("Wake-up time passed (Mon 9:00 am). Pick it back up.");
    expect(headerStatusLine(defaultCase(), NOW)).toBeNull();
  });
  it("bestTimeLabel", () => {
    expect([bestTimeLabel("morning"), bestTimeLabel("afternoon"), bestTimeLabel("any"), bestTimeLabel(null), bestTimeLabel("evening")]).toEqual(["Mornings", "Afternoons", "Any time", "No preference", "evening"]);
  });
  it("humanizeKey and caseTitle", () => {
    expect(humanizeKey("after_hours_dispatch")).toBe("After hours dispatch");
    expect(caseTitle(defaultCase().case)).toBe("Billing dispute · P3 Standard");
  });
});
