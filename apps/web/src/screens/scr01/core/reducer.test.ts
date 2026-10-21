import { describe, expect, it } from "vitest";
import { chatEvents } from "@/dev/stream/events";
import type { ChatEvent, ChatState, CustomerEntry } from "./model";
import { initialState } from "./model";
import { chatReducer, type Action } from "./reducer";
import { followUpExample, handoffExample, startExample, threadExample, turnExample } from "./testFixtures";

const run = (actions: Action[], from: ChatState = initialState) => actions.reduce(chatReducer, from);
const customer = (turnId = "t1", text = "hi"): CustomerEntry => ({
  kind: "customer", id: `c:${turnId}`, turnId, at: null, text, payload: { kind: "text", text }, delivery: "pending", failure: null, retryable: false, attempt: 0,
});
const started = () => run([{ type: "START_OK", res: startExample() }]);
const ev = (e: ChatEvent, key = String(e.event_id)): Action => ({ type: "EVENT", key, event: e });
const withId = (e: ChatEvent, n: number) => ({ ...e, event_id: n }) as ChatEvent;

describe("chatReducer", () => {
  it("START_OK shows the greeting and the settled state", () => {
    const s = started();
    expect(s.phase).toBe("ready");
    expect(s.entries).toHaveLength(1);
    expect(s.entries[0]).toMatchObject({ kind: "reply", id: "greeting", live: false });
    expect(s.settled).toEqual(startExample().settled);
  });
  it("SEND_BEGIN then TURN_OK marks sent and appends the reply once", () => {
    const res = turnExample("ANSWER_WITH_SOURCE");
    const s = run([{ type: "SEND_BEGIN", entry: customer(), startedAtMs: 1 }, { type: "TURN_OK", turnId: "t1", res }, { type: "TURN_OK", turnId: "t1", res }], started());
    expect(s.pending).toBeNull();
    expect(s.entries.filter((e) => e.kind === "reply")).toHaveLength(2); // greeting + one reply
    expect(s.entries.find((e) => e.kind === "customer")).toMatchObject({ delivery: "sent" });
  });
  it("TURN_FAIL then RETRY_BEGIN reuses the turn id and gives the next reply its own entry", () => {
    const res = turnExample("ANSWER_WITH_SOURCE");
    let s = run([{ type: "SEND_BEGIN", entry: customer(), startedAtMs: 1 }, { type: "TURN_FAIL", turnId: "t1", message: "no", retryable: true }], started());
    expect(s.entries.find((e) => e.kind === "customer")).toMatchObject({ delivery: "failed", failure: "no", retryable: true });
    s = run([{ type: "RETRY_BEGIN", turnId: "t1", startedAtMs: 2 }], s);
    expect(s.pending?.turnId).toBe("t1");
    expect(s.entries.filter((e) => e.kind === "customer")).toHaveLength(1);
    s = run([{ type: "TURN_OK", turnId: "t1", res }], s);
    expect(s.entries.map((e) => e.id)).toContain("t1:reply:1");
  });
  it("a late success for a failed entry still applies", () => {
    const s = run([
      { type: "SEND_BEGIN", entry: customer(), startedAtMs: 1 },
      { type: "TURN_FAIL", turnId: "t1", message: "gave up", retryable: true },
      { type: "TURN_OK", turnId: "t1", res: turnExample("ANSWER_WITH_SOURCE") },
    ], started());
    expect(s.entries.find((e) => e.kind === "customer")).toMatchObject({ delivery: "sent", failure: null });
  });
  it("settled is replaced, not merged (the visit disappears when the server sends null)", () => {
    const booked = turnExample("BOOKED");
    expect(booked.settled.visit).not.toBeNull();
    let s = run([{ type: "SEND_BEGIN", entry: customer(), startedAtMs: 1 }, { type: "TURN_OK", turnId: "t1", res: booked }], started());
    expect(s.settled?.visit).not.toBeNull();
    const none = { ...turnExample("ANSWER_WITH_SOURCE"), settled: { ...booked.settled, visit: null } };
    s = run([{ type: "SEND_BEGIN", entry: customer("t2"), startedAtMs: 1 }, { type: "TURN_OK", turnId: "t2", res: none }], s);
    expect(s.settled?.visit).toBeNull();
  });
  it("a notice records the code and rate hold; BOOKING_CAP is recorded without a hold", () => {
    let s = run([{ type: "SEND_BEGIN", entry: customer(), startedAtMs: 1 }, { type: "TURN_OK", turnId: "t1", res: turnExample("RATE_LIMITED") }], started());
    expect(s.lastNotice?.code).toBe("RATE_LIMITED");
    expect(s.rateHeld).toBe(true);
    expect(chatReducer(s, { type: "RATE_HOLD_END" }).rateHeld).toBe(false);
    s = run([{ type: "SEND_BEGIN", entry: customer("t2"), startedAtMs: 1 }, { type: "TURN_OK", turnId: "t2", res: turnExample("BOOKING_CAP") }], started());
    expect(s.lastNotice?.code).toBe("BOOKING_CAP");
    expect(s.rateHeld).toBe(false);
  });
  it("PERSON_OK: case_created adds a row and the card; already_open adds nothing", () => {
    const entry = { ...customer("p1", "Talk to a person"), delivery: "sent" as const, payload: { kind: "person" as const } };
    const created = run([{ type: "PERSON_OK", turnId: "p1", res: handoffExample("CASE_CREATED"), entry }], started());
    expect(created.entries).toHaveLength(3);
    expect(created.settled?.request).not.toBeNull();
    const again = run([{ type: "PERSON_OK", turnId: "p2", res: handoffExample("ALREADY_OPEN"), entry }], created);
    expect(again.entries).toHaveLength(3);
  });
  it("FOLLOWUP_OK replaces settled; LINE is added once; ANSWERED keeps the first answer", () => {
    const fu = followUpExample();
    let s = run([{ type: "FOLLOWUP_OK", res: fu }, { type: "LINE", id: "x", text: "a" }, { type: "LINE", id: "x", text: "a" }, { type: "ANSWERED", cardId: "c", option: "1" }, { type: "ANSWERED", cardId: "c", option: "2" }], started());
    expect(s.settled).toEqual(fu.settled);
    expect(s.entries.filter((e) => e.kind === "line")).toHaveLength(1);
    expect(s.answered).toEqual({ c: "1" });
    s = chatReducer(s, { type: "ENDED", reason: "gone" });
    expect(s.ended).toBe("gone");
  });
  it("events: joined sets human, handed back sets ai, closed ends, reset ends", () => {
    const E = chatEvents;
    let s = run([ev(withId(E.representative_joined(), 1)), ev(withId(E.ai_paused(), 2))], started());
    expect(s.replying).toEqual({ kind: "human", display_name: "Riley" });
    expect(s.entries.filter((e) => e.kind === "event")).toHaveLength(2);
    s = run([ev(withId(E.staff_message(), 3))], s);
    expect(s.entries.at(-1)).toMatchObject({ kind: "message", id: "msg:m-88" });
    s = run([ev(withId(E.ai_resumed(), 4))], s);
    expect(s.replying.kind).toBe("ai");
    expect(run([ev(withId(E.chat_closed(), 5))], s).ended).toBe("closed");
    expect(run([ev(withId(E.demo_reset(), 6))], s).ended).toBe("reset");
  });
  it("events: shift_ended appends the line, the handoff card and the new settled; clock adds no entry; staffing adds one", () => {
    const s0 = started();
    const s = run([ev(withId(chatEvents.shift_ended(), 7))], s0);
    expect(s.entries).toHaveLength(s0.entries.length + 2);
    expect(s.settled?.request?.reference).toBe("MHC-C-0007");
    expect(run([ev(withId(chatEvents.clock_changed(), 8))], s0).entries).toHaveLength(s0.entries.length);
    expect(run([ev(withId(chatEvents.staffing_changed(), 9))], s0).entries).toHaveLength(s0.entries.length + 1);
  });
  it("a duplicate event key is ignored", () => {
    const e = withId(chatEvents.representative_joined(), 1);
    const once = run([ev(e)], started());
    expect(run([ev(e)], once)).toBe(once);
  });
  it("RESUME_OK maps turns; closed and reset states end the chat", () => {
    const thread = threadExample("OPEN");
    const s = run([{ type: "RESUME_OK", thread, limits: startExample().limits }]);
    expect(s.phase).toBe("ready");
    expect(s.ended).toBeNull();
    expect(run([{ type: "RESUME_OK", thread: { ...thread, state: "closed" }, limits: startExample().limits }]).ended).toBe("closed");
    expect(run([{ type: "RESUME_OK", thread: { ...thread, state: "ended_by_reset" }, limits: startExample().limits }]).ended).toBe("reset");
  });
  it("RESYNC_OK keeps failed and pending customer entries", () => {
    const base = run([{ type: "RESUME_OK", thread: threadExample("OPEN"), limits: startExample().limits }, { type: "SEND_BEGIN", entry: customer("t9", "unsent"), startedAtMs: 1 }, { type: "TURN_FAIL", turnId: "t9", message: "x", retryable: true }]);
    const s = chatReducer(base, { type: "RESYNC_OK", thread: threadExample("OPEN") });
    expect(s.entries.at(-1)).toMatchObject({ kind: "customer", turnId: "t9", delivery: "failed" });
  });
  it("a session_ended block ends the chat", () => {
    const thread = threadExample("ENDED_BLOCK");
    expect(run([{ type: "RESUME_OK", thread, limits: startExample().limits }]).ended).not.toBeNull();
    const res = { ...turnExample("ANSWER_WITH_SOURCE"), blocks: [...threadExample("ENDED_BLOCK").turns.flatMap((t) => t.blocks).filter((b) => b.type === "session_ended")] };
    const s = run([{ type: "SEND_BEGIN", entry: customer(), startedAtMs: 1 }, { type: "TURN_OK", turnId: "t1", res }], started());
    expect(s.ended).toBe("gone");
  });
});
