import type { Limits } from "./model";

export const SHOW_AFTER_MS = 300; // design --delay-pending
export type PendingPhase = "hidden" | "replying" | "still" | "gave-up";
export function pendingPhase(elapsedMs: number, limits: Pick<Limits, "still_working_after_ms" | "browser_give_up_after_ms">): PendingPhase {
  if (elapsedMs < SHOW_AFTER_MS) return "hidden";
  if (elapsedMs < limits.still_working_after_ms) return "replying";
  if (elapsedMs < limits.browser_give_up_after_ms) return "still";
  return "gave-up";
}
// CON-1 values; only a fallback for a missing or malformed stored value
export const DEFAULT_LIMITS: Limits = { turn_deadline_ms: 60000, still_working_after_ms: 10000, browser_give_up_after_ms: 65000, max_message_chars: 2000 };
// [A] no source gives how long a rate-limit hold lasts
export const RATE_HOLD_MS = 60_000;
