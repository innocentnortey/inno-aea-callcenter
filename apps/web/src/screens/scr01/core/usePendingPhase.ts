import { useEffect, useState } from "react";
import type { ChatState, Limits } from "./model";
import { DEFAULT_LIMITS, pendingPhase, SHOW_AFTER_MS, type PendingPhase } from "./pending";

/** Fires at the three boundaries (300 ms, still-working, give-up) with setTimeout; never an interval. */
export function usePendingPhase(pending: ChatState["pending"], limits: Limits | null): PendingPhase {
  const [phase, setPhase] = useState<PendingPhase>("hidden");
  const turnId = pending?.turnId ?? null;
  const startedAt = pending?.startedAtMs ?? 0;
  const still = (limits ?? DEFAULT_LIMITS).still_working_after_ms;
  const giveUp = (limits ?? DEFAULT_LIMITS).browser_give_up_after_ms;
  useEffect(() => {
    if (turnId === null) { setPhase("hidden"); return; }
    const lim = { still_working_after_ms: still, browser_give_up_after_ms: giveUp };
    const timers: ReturnType<typeof setTimeout>[] = [];
    const elapsed = Date.now() - startedAt;
    setPhase(pendingPhase(elapsed, lim));
    for (const at of [SHOW_AFTER_MS, still, giveUp]) {
      if (at > elapsed) timers.push(setTimeout(() => setPhase(pendingPhase(at, lim)), at - elapsed));
    }
    return () => timers.forEach(clearTimeout);
  }, [turnId, startedAt, still, giveUp]);
  return turnId === null ? "hidden" : phase;
}
