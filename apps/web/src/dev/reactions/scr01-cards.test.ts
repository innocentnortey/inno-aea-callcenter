import { describe, expect, it, vi } from "vitest";
import type { OperationId } from "@/api/client";
import type { DevCtx, OpForce, Reaction } from "../scenarios/types";
import type { World } from "../world";
import { reactions } from "./scr01-cards";

function ctxWith(forces: World["forces"], scenarioId: string | null) {
  const setForce = vi.fn<(op: OperationId, f: OpForce | null) => void>();
  return { ctx: { world: { forces, scenarioId } as World, setForce } as unknown as DevCtx, setForce };
}
const find = (op: OperationId, example?: string): Reaction => reactions.find((r) => r.when.op === op && r.when.example === example)!;

describe("scr01-cards reactions", () => {
  it("clears a one-shot example force for its own scenarios", () => {
    const { ctx, setForce } = ctxWith({ submitTurn: { example: "SAFETY" } }, "scr01-cards.safety-takeover");
    find("submitTurn").then(ctx);
    expect(setForce).toHaveBeenCalledWith("submitTurn", null);
  });
  it("leaves a sequence force and other scenarios alone", () => {
    const a = ctxWith({ submitTurn: { sequence: [{ example: "TURN_TIMEOUT" }] } }, "scr01-cards.turn-timeout");
    find("submitTurn").then(a.ctx);
    expect(a.setForce).not.toHaveBeenCalled();
    const b = ctxWith({ submitTurn: { example: "SAFETY" } }, "scr01-core.other");
    find("submitTurn").then(b.ctx);
    expect(b.setForce).not.toHaveBeenCalled();
  });
  it("a second Talk to a person answers ALREADY_OPEN", () => {
    for (const ex of ["CASE_CREATED", "LIVE_QUEUED"]) {
      const { ctx, setForce } = ctxWith({}, null);
      find("requestPerson", ex).then(ctx);
      expect(setForce).toHaveBeenCalledWith("requestPerson", { example: "ALREADY_OPEN" });
    }
  });
  it("reset and a new session clear the person force", () => {
    const r = ctxWith({}, null);
    find("resetDemo").then(r.ctx);
    expect(r.setForce).toHaveBeenCalledWith("requestPerson", null);
    expect(r.setForce).toHaveBeenCalledWith("submitTurn", null);
    const s = ctxWith({}, null);
    find("startChatSession").then(s.ctx);
    expect(s.setForce).toHaveBeenCalledWith("requestPerson", null);
  });
});
