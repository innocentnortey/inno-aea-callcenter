import { describe, expect, it } from "vitest";
import { chatScripts } from "./chat-scripts";

const TYPES = ["representative_joined", "staff_message", "ai_paused", "ai_resumed", "chat_closed", "staffing_changed", "shift_ended", "clock_changed", "demo_reset"];
describe("chatScripts", () => {
  const entries = Object.entries(chatScripts);
  it("has the nine planned scripts", () => {
    expect(Object.keys(chatScripts).sort()).toEqual(["clock-moves", "demo-reset", "drop-and-late", "rep-closes", "rep-hands-back", "rep-joins", "shift-ends", "staffing-off", "staffing-on"].sort());
  });
  it.each(entries)("%s: steps are sorted and every event is a valid chat event", (_name, script) => {
    const times = script.steps.map((s) => s.afterMs);
    expect(times).toEqual([...times].sort((a, b) => a - b));
    let last = 39;
    for (const step of script.steps) {
      const ev = step.event as { type: string; event_id: number; at: string; speaker: unknown };
      expect(TYPES).toContain(ev.type);
      expect(typeof ev.at).toBe("string");
      expect(ev.speaker).toBeTruthy();
      expect(ev.event_id).toBeGreaterThan(last);
      last = ev.event_id;
    }
  });
  it("shift-ends carries the HANDOFF card with the same reference", () => {
    const ev = chatScripts["shift-ends"].steps[0].event as { type: string; line: string; handoff: { type: string; reference: string } };
    expect(ev.handoff.type).toBe("handoff");
    expect(ev.handoff.reference).toBe("MHC-C-0007");
    expect(ev.line).toBe("The simulated shift ended before a representative joined.");
  });
  it("staffing-off turns the simulation off; drop-and-late drops the connection", () => {
    expect((chatScripts["staffing-off"].steps[0].event as { staffing: { mode: string } }).staffing.mode).toBe("nobody_online");
    expect(chatScripts["drop-and-late"].dropAfterMs).toBe(1500);
  });
  it("lines match the spec copy", () => {
    const line = (k: string, i: number) => (chatScripts[k].steps[i].event as { line: string }).line;
    expect(line("rep-joins", 0)).toBe("Riley (demo representative) has joined.");
    expect(line("rep-joins", 1)).toBe("The assistant is paused while Riley is here.");
    expect(line("rep-hands-back", 3)).toBe("Riley handed the chat back to the automated assistant.");
    expect(line("rep-closes", 3)).toBe("Riley closed this chat.");
    expect(line("demo-reset", 0)).toBe("The demo was reset, so this chat has ended. Nothing from it was kept.");
  });
});
