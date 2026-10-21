import { describe, expect, it, vi } from "vitest";
import type { DevCtx } from "../scenarios/types";
import { reactions } from "./scr01-core";

describe("scr01-core reactions", () => {
  it("a demo reset makes the stored thread read as ended; a new chat clears that", () => {
    const setForce = vi.fn();
    const ctx = { setForce } as unknown as DevCtx;
    reactions.find((r) => r.when.op === "resetDemo")!.then(ctx);
    expect(setForce).toHaveBeenCalledWith("getChatThread", { example: "SESSION_ENDED", status: 410 });
    reactions.find((r) => r.when.op === "startChatSession")!.then(ctx);
    expect(setForce).toHaveBeenLastCalledWith("getChatThread", null);
  });
});
