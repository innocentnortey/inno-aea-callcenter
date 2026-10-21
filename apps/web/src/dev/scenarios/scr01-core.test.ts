import { describe, expect, it } from "vitest";
import { STANDARD_STATES } from "./matrix";
import { chatScripts } from "../stream/chat-scripts";
import { screenScenarios } from "./scr01-core";

// First column of the SCREEN_SPECS SCR-1 flow-state table (the ones G1 uses).
const FLOW_STATES = [
  "No current source", "Limit reached (rate, booking cap)", "Spend cap reached", "Session ended while the chat is open",
  "Simulation switched on or off while open", "Booked", "Handoff, nobody online", "Verified", "Fee-bearing change request",
  "Live-queued (simulated staff on shift)", "Representative joined, AI paused", "Handed back", "Shift ended before a claim",
  "Safety takeover", "Burning smell, risk unclear", "Chat closed by Riley", "Reset during a live chat",
];
const IDS = [
  "default", "default-resumed", "empty", "loading-starting", "loading-replying", "loading-timeout", "loading-busy", "partial-part-answered",
  "partial-handoff-unsaved", "flow-no-info", "error-send-failed", "error-giveup-fast", "error-session-gone", "error-start-reset", "error-start-offline",
  "flow-limit-rate", "flow-limit-booking", "flow-spend-cap", "flow-session-ended", "stale-reconnecting", "stale-staffing-on", "stale-staffing-off",
  "stale-clock-moves", "success-booked", "success-handoff", "success-person-again", "success-followup-saved", "success-verified",
  "success-change-request", "success-live-queued", "success-rep-joined", "success-handed-back", "success-shift-ended", "flow-safety-takeover",
  "flow-safety-midbooking", "flow-conditional-safety", "disabled-empty-field", "disabled-pending", "disabled-chat-closed", "flow-reset-live-chat",
  "disabled-ended-on-resume",
].map((s) => `scr01-core.${s}`);

describe("scr01-core scenarios", () => {
  const list = screenScenarios.scenarios;
  it("is complete and has exactly the planned ids", () => {
    expect(screenScenarios.complete).toBe(true);
    expect(list.map((s) => s.id)).toEqual(IDS);
    expect(new Set(list.map((s) => s.id)).size).toBe(list.length);
  });
  it("covers all eight standard states", () => {
    for (const st of STANDARD_STATES) expect(list.some((s) => s.state === st), st).toBe(true);
  });
  it("every flow state is a spec'd first-column text", () => {
    for (const s of list) if (s.flowState) expect(FLOW_STATES, s.id).toContain(s.flowState);
  });
  it("every stream is one of the chat scripts; every scenario has a recipe note", () => {
    const scripts = Object.values(chatScripts);
    for (const s of list) {
      if (s.stream) expect(scripts, s.id).toContain(s.stream);
      expect(s.notes, s.id).toBeTruthy();
      expect(s.screen).toBe("SCR-1");
      expect(s.route).toBe("/");
    }
  });
  it("the shortened-limits scenario cuts the 65 s and 10 s limits and nothing else", () => {
    const f = list.find((s) => s.id === "scr01-core.error-giveup-fast")!.ops!.startChatSession as { transform: (b: unknown) => { limits: Record<string, number> } };
    const out = f.transform({ limits: { turn_deadline_ms: 60000, still_working_after_ms: 10000, browser_give_up_after_ms: 65000, max_message_chars: 2000 }, x: 1 });
    expect(out).toMatchObject({ x: 1, limits: { turn_deadline_ms: 60000, still_working_after_ms: 2000, browser_give_up_after_ms: 5000, max_message_chars: 2000 } });
  });
});
