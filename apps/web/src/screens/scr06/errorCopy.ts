import type { components } from "@/api/types.gen";
import type { ApiError } from "@/api/errors";
import { ROLE_LABEL, type Role } from "@/lib/roles";
import { formatTimePoint } from "@/lib/time";

export type ActionKey =
  | components["schemas"]["CaseActionRequest"]["action"]
  | "log_call" | "log_email" | "flag" | "join" | "send" | "hand_back" | "close";
export interface ShownError { text: string; offerReload: boolean }

const REASON_TEXT: Partial<Record<ActionKey, string>> = {
  release: "Add a reason to release this case.",
  assign: "Add a reason to assign this case.",
  change_priority: "Add a reason to change the priority.",
  close_unresolved: "Add a reason to close this case.",
};
/** Proposed strings (no wording in SCREEN_SPECS): claim succeeded, join did not. */
export const CLAIMED_NOT_JOINED_CASE = "You claimed this case, but joining the chat didn't go through. Try Join chat.";
export const CLAIMED_NOT_JOINED_QUEUE = "You claimed the case, but joining the chat didn't go through. Open it and try Join chat.";
const str = (v: unknown): string | undefined => (typeof v === "string" && v ? v : undefined);

export function errorText(err: ApiError, action: ActionKey, role: Role): ShownError {
  const d = err.details ?? {};
  switch (err.code) {
    case "REASON_REQUIRED": return { text: REASON_TEXT[action] ?? "Add a reason.", offerReload: false };
    case "WAKE_UP_REQUIRED": return { text: "Waiting needs a wake-up time.", offerReload: false };
    case "OUTCOME_REQUIRED": return { text: "Resolving needs an outcome.", offerReload: false };
    case "NOT_ALLOWED_IN_STATE":
      if (d.needs === "claimed") return { text: "Claim the case first.", offerReload: false };
      return { text: "That isn't possible in the case's current state.", offerReload: true };
    case "NOT_CLAIMED_BY_YOU": return { text: "Claim the case first.", offerReload: false };
    case "VERSION_CONFLICT": {
      const who = str(d.changed_by);
      const at = str(d.changed_at);
      const paren = who && at ? ` (${who} at ${formatTimePoint(at)})` : who ? ` (${who})` : "";
      return { text: `This case changed since you opened it${paren}. Reload to see it.`, offerReload: true };
    }
    case "CASE_ALREADY_CLAIMED": {
      const by = str(d.claimed_by);
      const at = str(d.claimed_at);
      return { text: `Already claimed by ${by ?? "someone else"}${at ? " at " + formatTimePoint(at) : ""}. Reload.`, offerReload: true };
    }
    case "NOT_LIVE":
      return { text: d.reason === "demo_reset" ? "This chat ended because the demo was reset." : "This chat has ended.", offerReload: false };
    case "ROLE_NOT_ALLOWED": return { text: `You can't do that as ${ROLE_LABEL[role].full}.`, offerReload: false };
    case "CASE_NOT_FOUND": {
      const ref = str(d.reference);
      return { text: `${ref ? `No case ${ref}.` : "No such case."} It may have been cleared by a demo reset.`, offerReload: false };
    }
    default: return { text: "That didn't go through. Try again.", offerReload: false };
  }
}
