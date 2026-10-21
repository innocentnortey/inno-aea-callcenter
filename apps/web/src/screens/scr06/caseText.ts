import type { components } from "@/api/types.gen";
import { formatDateTimeShort, formatDayShort, formatStaffTime, formatTimePoint } from "@/lib/time";

export type CaseSummary = components["schemas"]["CaseSummary"];
export type CaseDetail = components["schemas"]["CaseDetail"];

export function dueHeadline(c: CaseSummary): string {
  if (c.due_state === "no_due_time") return "No due time: safety";
  if (c.due_at) {
    const suffix = /,\s*the window start$/.exec(c.due_label ?? "")?.[0] ?? "";
    return "Due " + formatDateTimeShort(c.due_at) + suffix;
  }
  return c.due_label ?? "No due time";
}
export function createdLine(c: CaseSummary): string {
  return `Created ${formatDayShort(c.created_at)}, ${formatTimePoint(c.created_at)}`;
}
export function ownerLine(c: CaseSummary): string {
  return c.owner ? `Owned by ${c.owner}` : "Unassigned, nobody owns it yet";
}
export function headerStatusLine(d: CaseDetail, nowIso: string): string | null {
  if (d.live.state === "joined") return "Live · you are replying · assistant paused";
  if (d.case.lifecycle === "live_queued" && d.live.since) return `The customer is waiting in the chat since ${formatTimePoint(d.live.since)}.`;
  if (d.case.lifecycle === "waiting" && d.case.wake_up_at) {
    const wake = d.case.wake_up_at;
    if (Date.parse(nowIso) >= Date.parse(wake)) return `Wake-up time passed (${formatStaffTime(wake)}). Pick it back up.`;
    return `Wakes ${formatDateTimeShort(wake)}`;
  }
  return null;
}
export const LIFECYCLE_LABEL: Record<CaseSummary["lifecycle"], string> = {
  live_queued: "Live-queued", unassigned: "Unassigned", claimed: "Claimed", in_progress: "In progress",
  waiting: "Waiting", resolved: "Resolved", closed_unresolved: "Closed unresolved",
};
export const PROMISE_STATUS_LABEL = { open: "Open", kept: "Kept", missed: "Missed", changed: "Changed" } as const;
export function bestTimeLabel(window: string | null): string {
  if (window == null) return "No preference";
  if (window === "morning") return "Mornings";
  if (window === "afternoon") return "Afternoons";
  if (window === "any") return "Any time";
  return window;
}
export function channelLabel(ch: "email" | "phone"): string {
  return ch === "email" ? "Email" : "Phone";
}
export function humanizeKey(key: string): string {
  const s = key.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}
export function caseTitle(c: CaseSummary): string {
  return `${c.reason} · ${c.priority.level} ${c.priority.word}`;
}
export const KIND_WORD = { call: "Called", email: "Emailed" } as const;
export const OUTCOME_WORD = { reached: "Reached the customer", no_answer: "No answer", left_message: "Left a message" } as const;
