import { beforeEach, describe, expect, it } from "vitest";
import { allowedFor, getOverride, patchOverride, resetCaseStore } from "./case-store";

beforeEach(resetCaseStore);
const act = { activity_id: "a1", kind: "call", outcome: "reached", note: null, at: "2026-10-16T14:40:00-05:00", by: "Riley (demo)", label: "Demo: recorded, not sent" } as const;
const msg = { message_id: "m-1", speaker: { kind: "representative", display_name: "Riley" }, at: "2026-10-16T14:41:00-05:00", text: "Hi" } as const;

describe("case store", () => {
  it("allowedFor rep/supervisor/owner per lifecycle", () => {
    expect(allowedFor("unassigned", "representative", "not_live")).toEqual(["claim", "flag"]);
    expect(allowedFor("unassigned", "supervisor", "not_live")).toEqual(["claim", "assign", "change_priority", "flag"]);
    expect(allowedFor("live_queued", "representative", "queued")).toEqual(["claim_and_join", "claim", "flag"]);
    expect(allowedFor("claimed", "representative", "not_live")).toEqual(["start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag"]);
    expect(allowedFor("in_progress", "representative", "not_live")).not.toContain("start");
    expect(allowedFor("claimed", "representative", "queued")).toContain("join_chat");
    expect(allowedFor("in_progress", "representative", "joined")).toEqual(["send_live_message", "hand_back", "close_chat", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag"]);
    expect(allowedFor("waiting", "representative", "not_live")).toEqual(["start", "release", "flag"]);
    expect(allowedFor("resolved", "representative", "not_live")).toEqual(["flag"]);
    expect(allowedFor("waiting", "supervisor", "not_live")).toEqual(["start", "release", "assign", "change_priority", "flag"]);
    for (const lc of ["unassigned", "claimed", "waiting", "resolved"] as const) expect(allowedFor(lc, "owner", "not_live")).toEqual([]);
  });
  it("patchOverride appends activities and messages", () => {
    patchOverride("MHC-C-0007", { lifecycle: "claimed", activities: [act] });
    const o = patchOverride("MHC-C-0007", { messages: [msg], activities: [{ ...act, activity_id: "a2" }] });
    expect(o.lifecycle).toBe("claimed");
    expect(o.activities.map((a) => a.activity_id)).toEqual(["a1", "a2"]);
    expect(o.messages).toHaveLength(1);
  });
  it("resetCaseStore clears overrides", () => {
    patchOverride("MHC-C-0007", { lifecycle: "claimed" });
    resetCaseStore();
    expect(getOverride("MHC-C-0007")).toBeUndefined();
  });
});
