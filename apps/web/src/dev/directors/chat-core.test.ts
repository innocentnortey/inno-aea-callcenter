import { describe, expect, it } from "vitest";
import { OPS } from "@/api/client";
import type { components } from "@/api/types.gen";
import { rules } from "./chat-core";
import type { World } from "../world";

type Req = components["schemas"]["TurnRequest"];
const ctx = { world: {} as World };
const text = (t: string): Req => ({ turn_id: "t", payload: { kind: "text", text: t } });
const pick = (req: Req) => rules.map((r) => r(req, ctx)).find(Boolean);
const NAMES = OPS.submitTurn.responses.find((r) => r.status === 200)!.examples;

describe("chat-core director", () => {
  it.each([
    ["test: rate limit", "RATE_LIMITED"], ["Test: booking cap", "BOOKING_CAP"], ["test: spend cap", "SPEND_CAP_REACHED"],
    ["test: timeout", "TURN_TIMEOUT"], ["test: busy", "BUSY"], ["test:paused", "AI_PAUSED"],
  ])("%s -> %s", (input, expected) => {
    expect(pick(text(input))).toBe(expected);
    expect(NAMES).toContain(expected);
  });
  it("leaves ordinary text, choices and the other group's words alone", () => {
    expect(pick(text("hello"))).toBeUndefined();
    expect(pick(text("I smell gas"))).toBeUndefined(); // G2's keyword rules own this
    expect(pick(text("demo: slot taken"))).toBeUndefined();
    expect(pick({ turn_id: "t", payload: { kind: "choice", card_id: "burn-1", option: "yes" } })).toBeUndefined();
    expect(pick({ turn_id: "t", payload: { kind: "code", card_id: "code-1", code: "111111" } })).toBeUndefined();
  });
});
