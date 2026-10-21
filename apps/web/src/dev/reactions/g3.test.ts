import { describe, expect, it, vi } from "vitest";
import type { DevCtx, Reaction } from "../scenarios/types";
import { reactions as r02 } from "./scr02";
import { reactions as r03 } from "./scr03";

const all: Reaction[] = [...r02, ...r03];
function fire(when: Reaction["when"]) {
  const setForce = vi.fn();
  const ctx = { setForce } as unknown as DevCtx;
  for (const r of all) {
    const same = r.when.op === when.op && (r.when.status === undefined || r.when.status === when.status) && (r.when.example === undefined || r.when.example === when.example);
    if (same) r.then(ctx);
  }
  return setForce;
}

describe("G3 reactions", () => {
  it("resetDemo 200 forces the inbox to EMPTY", () => {
    expect(fire({ op: "resetDemo", status: 200 })).toHaveBeenCalledWith("listDemoInbox", { example: "EMPTY" });
  });
  it("submitTurn CODE_SENT forces the inbox to ONE_ACTIVE", () => {
    expect(fire({ op: "submitTurn", example: "CODE_SENT" })).toHaveBeenCalledWith("listDemoInbox", { example: "ONE_ACTIVE" });
  });
  it("setStaffing TURNED_ON forces the next write to TURNED_OFF_WITH_WAITING and the reverse", () => {
    expect(fire({ op: "setStaffing", example: "TURNED_ON" })).toHaveBeenCalledWith("setStaffing", { example: "TURNED_OFF_WITH_WAITING" });
    expect(fire({ op: "setStaffing", example: "TURNED_OFF_WITH_WAITING" })).toHaveBeenCalledWith("setStaffing", { example: "TURNED_ON" });
  });
  it("reactions ignore other ops", () => {
    expect(fire({ op: "getStaffing", status: 200, example: "ON" })).not.toHaveBeenCalled();
    expect(fire({ op: "submitTurn", example: "BOOKED" })).not.toHaveBeenCalled();
    expect(fire({ op: "resetDemo", status: 500 })).not.toHaveBeenCalled();
  });
});
