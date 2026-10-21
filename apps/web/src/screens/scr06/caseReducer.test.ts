import { describe, expect, it } from "vitest";
import { caseReducer, initialCaseState, type CaseState } from "./caseReducer";
import { callReachedResponse, claimedResponse, defaultCase, liveJoinedCase, sentResponse } from "./case.fixtures";

const loaded = (d = defaultCase()): CaseState => caseReducer(initialCaseState, { type: "loaded", detail: d });
const iso = "2026-10-16T14:24:00-05:00";

describe("caseReducer", () => {
  it("1. loaded resets everything", () => {
    const s = caseReducer({ ...loaded(), changedElsewhere: true, endedByReset: true, events: [{ id: "x", at: iso, text: "t" }] }, { type: "loaded", detail: defaultCase() });
    expect(s.messages).toHaveLength(3);
    expect(s.events).toEqual([]);
    expect(s.changedElsewhere).toBe(false);
    expect(s.endedByReset).toBe(false);
  });
  it("2. summary replaces the case summary and nothing else", () => {
    const s = caseReducer(loaded(), { type: "summary", summary: claimedResponse().case });
    expect(s.detail!.case.lifecycle).toBe("claimed");
    expect(s.detail!.case.version).toBe(4);
    expect(s.detail!.brief).toEqual(defaultCase().brief);
  });
  it("3. activity is prepended and the summary merged", () => {
    const r = callReachedResponse();
    const s = caseReducer(loaded(), { type: "activity", activity: r.activity, summary: r.case });
    expect(s.detail!.activities[0].activity_id).toBe("act-17");
    expect(s.detail!.case.lifecycle).toBe("claimed");
  });
  it("4. live sets the live state, appends the message and adds an event", () => {
    const r = sentResponse();
    const s = caseReducer(loaded(liveJoinedCase()), { type: "live", live: { state: "handed_back", since: iso, controller: "ai" }, message: r.message, eventText: "Handed back to the assistant at 2:24 pm" });
    expect(s.detail!.live.state).toBe("handed_back");
    expect(s.messages.at(-1)!.message_id).toBe("m-88");
    expect(s.events[0].text).toBe("Handed back to the assistant at 2:24 pm");
  });
  it("5a. stream customer_message appends once", () => {
    const ev = { event_id: 31, type: "customer_message", at: iso, message: { message_id: "m-90", speaker: { kind: "customer", display_name: "You" }, at: iso, text: "Thanks" } } as const;
    let s = caseReducer(loaded(), { type: "stream", event: ev });
    s = caseReducer(s, { type: "stream", event: ev });
    expect(s.messages.filter((m) => m.message_id === "m-90")).toHaveLength(1);
  });
  it("5b. stream controller_changed sets the controller and adds the line", () => {
    const s = caseReducer(loaded(liveJoinedCase()), { type: "stream", event: { event_id: 33, type: "controller_changed", at: iso, controller: { kind: "ai", display_name: null }, line: "Handed back" } });
    expect(s.detail!.live.controller).toBe("ai");
    expect(s.events[0].text).toBe("Handed back");
  });
  it("5c. stream chat_closed closes the chat; shift_ended also marks the case changed", () => {
    const a = caseReducer(loaded(liveJoinedCase()), { type: "stream", event: { event_id: 32, type: "chat_closed", at: iso, reason: "closed_by_staff" } });
    expect(a.detail!.live.state).toBe("closed");
    expect(a.events[0].text).toBe("Chat closed at 2:24 pm");
    expect(a.changedElsewhere).toBe(false);
    const b = caseReducer(loaded(liveJoinedCase()), { type: "stream", event: { event_id: 32, type: "chat_closed", at: iso, reason: "shift_ended" } });
    expect(b.changedElsewhere).toBe(true);
  });
  it("5d. stream demo_reset ends the chat by reset", () => {
    const s = caseReducer(loaded(liveJoinedCase()), { type: "stream", event: { event_id: 34, type: "demo_reset", at: iso, line: "This chat ended because the demo was reset." } });
    expect(s.endedByReset).toBe(true);
    expect(s.detail!.live.state).toBe("closed");
  });
  it("5e. stream case_changed flags only a newer version", () => {
    const older = caseReducer(loaded(), { type: "stream", event: { event_id: 35, type: "case_changed", at: iso, version: 3, lifecycle: "unassigned" } });
    expect(older.changedElsewhere).toBe(false);
    const newer = caseReducer(loaded(), { type: "stream", event: { event_id: 35, type: "case_changed", at: iso, version: 4, lifecycle: "claimed" } });
    expect(newer.changedElsewhere).toBe(true);
  });
  it("5f. own write, response first: the later case_changed for that version shows no banner", () => {
    let s = caseReducer(loaded(), { type: "summary", summary: claimedResponse().case }); // version 4
    s = caseReducer(s, { type: "stream", event: { event_id: 36, type: "case_changed", at: iso, version: 4, lifecycle: "claimed" } });
    expect(s.changedElsewhere).toBe(false);
  });
  it("5g. own write, event first: the banner clears when the response levels the versions", () => {
    let s = caseReducer(loaded(), { type: "stream", event: { event_id: 36, type: "case_changed", at: iso, version: 4, lifecycle: "claimed" } });
    expect(s.changedElsewhere).toBe(true);
    s = caseReducer(s, { type: "summary", summary: claimedResponse().case });
    expect(s.changedElsewhere).toBe(false);
  });
  it("5h. a version beyond the user's own write still shows the banner", () => {
    let s = caseReducer(loaded(), { type: "summary", summary: claimedResponse().case }); // 4
    s = caseReducer(s, { type: "stream", event: { event_id: 37, type: "case_changed", at: iso, version: 5, lifecycle: "in_progress" } });
    expect(s.changedElsewhere).toBe(true);
    s = caseReducer(s, { type: "summary", summary: { ...claimedResponse().case, version: 4 } });
    expect(s.changedElsewhere).toBe(true);
  });
  it("5i. a summary does not clear the shift-ended notice", () => {
    let s = caseReducer(loaded(liveJoinedCase()), { type: "stream", event: { event_id: 32, type: "chat_closed", at: iso, reason: "shift_ended" } });
    s = caseReducer(s, { type: "summary", summary: claimedResponse().case });
    expect(s.changedElsewhere).toBe(true);
  });
  it("6. any action with no detail returns the state unchanged", () => {
    expect(caseReducer(initialCaseState, { type: "summary", summary: claimedResponse().case })).toBe(initialCaseState);
  });
});
