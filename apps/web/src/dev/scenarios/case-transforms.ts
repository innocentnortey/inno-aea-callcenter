/* eslint-disable @typescript-eslint/no-explicit-any -- these reshape example bodies as plain JSON */
// Pure body transforms shared by the SCR-5 and SCR-6 scenario files. Each takes an example body and returns a new one.
import type { components } from "@/api/types.gen";

type QueueRow = components["schemas"]["QueueRow"];

// applyCaseAction CLAIMED example: lifecycle, owner, version and allowed_actions
export const CLAIMED_ALLOWED = ["start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag"] as const;

/** getCase DEFAULT as it reads once Riley has claimed it. */
export function claimedByMe(body: any): any {
  return { ...body, case: { ...body.case, lifecycle: "claimed", owner: "Riley", version: 4, allowed_actions: [...CLAIMED_ALLOWED] } };
}
/** getCase DEFAULT after the demo supervisor claimed it (the VERSION_CONFLICT example: changed_by, current_version 4). */
export function claimedByDemoSupervisor(body: any): any {
  return { ...body, case: { ...body.case, lifecycle: "claimed", owner: "Demo supervisor", version: 4, allowed_actions: ["flag"] } };
}
/** Empties the listed brief headings so they read "Nothing recorded.". */
export function emptyHeadings(numbers: number[]) {
  return (body: any): any => ({
    ...body,
    brief: { ...body.brief, headings: body.brief.headings.map((h: any) => (numbers.includes(h.number) ? { ...h, items: [] } : h)) },
  });
}
/** Overwrites fields of queue rows by reference. */
export function queueChange(refs: Record<string, Partial<QueueRow>>) {
  return (body: any): any => {
    const patch = (r: QueueRow): QueueRow => (refs[r.reference] ? { ...r, ...refs[r.reference] } : r);
    return { ...body, live: body.live.map(patch), needs_my_action: body.needs_my_action.map(patch) };
  };
}
/** The shift ends: waiting chats become unassigned handoffs, keeping created_at. */
export function moveLiveToNeeds() {
  return (body: any): any => ({
    ...body,
    staffing: { mode: "nobody_online", label: "Nobody online", banner: null },
    live: [],
    needs_my_action: [...body.needs_my_action, ...body.live.map((r: QueueRow) => ({ ...r, lifecycle: "unassigned", queued_at: null, age_label: null }))],
  });
}
export function addNeedsRow(row: QueueRow) {
  return (body: any): any => ({ ...body, needs_my_action: [...body.needs_my_action, row] });
}
/** getCase WAITING with a wake-up time that has already passed. */
export function stuckWaiting(isoWake: string) {
  return (body: any): any => ({ ...body, case: { ...body.case, wake_up_at: isoWake } });
}
// dev fixture: no named example in the OpenAPI (foundation plan 8.2). Wording from the SCREEN_SPECS flow state.
export function shiftEndedPromise() {
  return (body: any): any => ({
    ...body,
    promise: {
      ...body.promise,
      status: "changed",
      history: [{ at: "2026-10-16T14:26:00-05:00", text: "The chat handoff went unclaimed, so the follow-up promise replaced the live one.", reason: "Shift ended before a claim" }],
    },
  });
}
