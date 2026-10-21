import { ApiError } from "@/api/errors";
import type { EndedReason } from "./model";

export type Ctx = "start" | "turn" | "person" | "followup";
export interface Described { message: string; retryable: boolean; ended: EndedReason | null }

export const MSG = {
  ended: "This chat has ended.",
  reset: "The demo is resetting. Try again in a few seconds.",
  rate: "Try again in a moment.",
  startFailed: "The chat didn't start. Try again.", // [P]
  sendFailed: "That didn't send. Your message is still here.",
  personFailed: "We couldn't reach a person just now. Tap Talk to a person to try again.", // [P]
  followUpNotAllowed: "There's no open request to attach this to.",
  followUpFailed: "Your choice didn't save. Try again.", // [P]
};

export function describe(err: unknown, ctx: Ctx): Described {
  const e = err instanceof ApiError ? err : null;
  const status = e?.status ?? 0;
  const code = e?.code ?? "";
  if ((status === 404 && code === "SESSION_NOT_FOUND") || status === 410) return { message: MSG.ended, retryable: false, ended: "gone" };
  if (ctx === "start" || ctx === "turn") {
    if (status === 503 && code === "RESET_IN_PROGRESS") return { message: MSG.reset, retryable: true, ended: null };
    if (status === 429) return { message: MSG.rate, retryable: true, ended: null };
    return { message: ctx === "start" ? MSG.startFailed : MSG.sendFailed, retryable: true, ended: null };
  }
  if (ctx === "person") return { message: MSG.personFailed, retryable: true, ended: null };
  if (status === 409 && code === "NOT_ALLOWED_IN_STATE") return { message: MSG.followUpNotAllowed, retryable: false, ended: null };
  return { message: MSG.followUpFailed, retryable: true, ended: null };
}
