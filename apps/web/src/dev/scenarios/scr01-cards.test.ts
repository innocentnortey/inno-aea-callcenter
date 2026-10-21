import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { OPS } from "@/api/client";
import { cardRenderers } from "@/screens/scr01/cards";
import { turnExample } from "@/screens/scr01/cards/testing/examples";
import { screenScenarios } from "./scr01-cards";
import * as fx from "./scr01-cards.fixtures";
import { FIXTURE_IDS } from "./scr01-cards.fixtures";

const SLUG = "scr01-cards";
const { scenarios } = screenScenarios;
const spec = fs.readFileSync(path.resolve(process.cwd(), "../../docs/ux/03-structure/SCREEN_SPECS.md"), "utf8");
const scr1 = spec.slice(spec.indexOf("### SCR-1 ·"), spec.indexOf("### SCR-2 ·"));
const flowTable = scr1.slice(scr1.indexOf("- Flow states"), scr1.indexOf("- Interactions"));
const flowStates = new Set(flowTable.split("\n").filter((l) => /^\s*\|/.test(l)).map((l) => l.split("|")[1].trim()));

describe("scr01-cards scenarios", () => {
  it("ids are unique and prefixed", () => {
    expect(new Set(scenarios.map((s) => s.id)).size).toBe(scenarios.length);
    for (const s of scenarios) expect(s.id.startsWith(`${SLUG}.`)).toBe(true);
  });
  it("every flowState is a first-column cell of the SCR-1 table", () => {
    expect(flowStates.size).toBeGreaterThan(30);
    for (const s of scenarios) if (s.flowState) expect(flowStates.has(s.flowState), s.flowState).toBe(true);
  });
  it("every forced example exists for its operation", () => {
    const walk = (f: import("./types").OpForce): import("./types").OpForce[] => ("sequence" in f ? f.sequence.flatMap(walk) : [f]);
    for (const s of scenarios) {
      for (const [op, force] of Object.entries(s.ops ?? {})) {
        for (const f of walk(force!)) {
          if ("example" in f) expect(OPS[op as keyof typeof OPS].responses.flatMap((r) => r.examples), s.id).toContain(f.example);
        }
      }
    }
  });
  it("every submitTurn scenario renders every block through the registry", () => {
    for (const s of scenarios) {
      const force = s.ops?.submitTurn;
      if (!force || !("example" in force)) continue;
      const body = (force.transform ? force.transform(turnExample(force.example)) : turnExample(force.example)) as ReturnType<typeof turnExample>;
      for (const b of body.blocks) expect(cardRenderers[b.type], `${s.id}/${b.type}`).toBeTypeOf("function");
    }
  });
  it("ten dev fixtures are exported", () => {
    expect(Object.keys(FIXTURE_IDS)).toHaveLength(10);
  });
});

describe("scr01-cards fixtures change only what they say", () => {
  const body = (n: string) => turnExample(n);
  it("slotCardUrgent", () => {
    const a = body("SLOT_CARD"); const b = fx.slotCardUrgent(body("SLOT_CARD"));
    expect(b.blocks[0]).toEqual({ ...a.blocks[0], urgent: true });
  });
  it("emergencyLineStaffed", () => {
    const a = body("EMERGENCY_LINE"); const b = fx.emergencyLineStaffed(body("EMERGENCY_LINE"));
    expect(b.blocks[0]).toEqual({ ...a.blocks[0], separate_line: null });
  });
  it("quickChecksShown", () => {
    const b = fx.quickChecksShown(body("QUICK_CHECKS")).blocks[0] as { checks: unknown[] };
    expect(b.checks).toHaveLength(2);
  });
  it("noWindowFits", () => {
    const a = body("NO_INFO"); const b = fx.noWindowFits(body("NO_INFO"));
    expect(b.blocks[0]).toEqual({ ...a.blocks[0], text: "That's the earliest I can book. I can't add you to a waitlist from here.", person_key: true });
  });
  it("partialReply appends the NO_INFO block verbatim", () => {
    const base = body("ANSWER_WITH_SOURCE"); const b = fx.partialReply(body("ANSWER_WITH_SOURCE"));
    expect(b.blocks.slice(0, base.blocks.length)).toEqual(base.blocks);
    expect(b.blocks.at(-1)).toEqual(body("NO_INFO").blocks[0]);
  });
  it("handoffRefund", () => {
    const a = body("HANDOFF"); const b = fx.handoffRefund(body("HANDOFF"));
    expect(b.blocks[0]).toEqual({ ...a.blocks[0], variant: "refund", promise_text: "A representative will get to your refund request within 2 business days.", due_at: null, due_label: null, extra_lines: ["I can't promise an outcome.", "Your reference is MHC-C-0007."] });
  });
  it("handoffGeneralOnly", () => {
    const a = body("HANDOFF").blocks[0] as { followup_chooser: { channels: Array<{ on_record: boolean }> } };
    const b = fx.handoffGeneralOnly(body("HANDOFF")).blocks[0] as typeof a & { followup_chooser: { general_only: boolean } };
    expect(b.followup_chooser.general_only).toBe(true);
    expect(b.followup_chooser.channels.every((c) => !c.on_record)).toBe(true);
    expect(a.followup_chooser.channels.length).toBe(b.followup_chooser.channels.length);
  });
  it("changeRequestCancel and changeRequestStaffed", () => {
    const a = body("CHANGE_REQUEST").blocks[0];
    expect(fx.changeRequestCancel(body("CHANGE_REQUEST")).blocks[0]).toEqual({ ...a, change: "cancel", wanted_text: "Cancel the visit on Wednesday, October 21, 8:00 am – 12:00 pm" });
    const s = fx.changeRequestStaffed(body("CHANGE_REQUEST")).blocks[0] as { due_at: null; cant_guarantee_line: null; phone_support_line: string };
    expect(s.due_at).toBeNull();
    expect(s.cant_guarantee_line).toBeNull();
    expect(s.phone_support_line).toContain("Phone support is open until 7:00 pm");
  });
  it("cancelledWithWrite adds exactly one cancelled action", () => {
    const a = body("CANCELLED"); const b = fx.cancelledWithWrite(body("CANCELLED"));
    expect(b.settled.actions).toHaveLength(a.settled.actions.length + 1);
    expect(b.settled.actions.at(-1)?.kind).toBe("cancelled");
    expect(b.blocks).toEqual(a.blocks);
  });
});
