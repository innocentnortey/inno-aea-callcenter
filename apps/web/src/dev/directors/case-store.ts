// In-memory case store for the mock: what staff did to a case since the page loaded, plus a replica of the server's rules.
// Resets with the demo (reactions/scr06.ts). Values are copied from the OpenAPI named examples.
import type { components } from "@/api/types.gen";
import type { Role } from "@/lib/roles";

type S = components["schemas"];
export type CaseSummary = S["CaseSummary"];
type LiveState = S["LiveState"];
type Priority = S["Priority"];
type QueueRow = S["QueueRow"];

export interface CaseOverride {
  lifecycle?: CaseSummary["lifecycle"]; owner?: string | null; version?: number; wake_up_at?: string | null;
  promise_status?: CaseSummary["promise_status"]; priority?: CaseSummary["priority"];
  live?: LiveState; activities: S["Activity"][]; messages: S["ChatLine"][]; resolvedSummary?: string;
}
const store = new Map<string, CaseOverride>();

export function getOverride(ref: string): CaseOverride | undefined { return store.get(ref); }
export function patchOverride(ref: string, patch: Partial<CaseOverride>): CaseOverride {
  const cur = store.get(ref) ?? { activities: [], messages: [] };
  const next: CaseOverride = {
    ...cur, ...patch,
    activities: [...cur.activities, ...(patch.activities ?? [])],
    messages: [...cur.messages, ...(patch.messages ?? [])],
  };
  store.set(ref, next);
  return next;
}
export function resetCaseStore(): void { store.clear(); }

export interface CatalogRow {
  reference: string; reason: string; priority: Priority; customer: string; created_at: string; due_at: string | null; due_label: string | null;
  due_state: QueueRow["due_state"]; follow_up_short: string | null; lifecycle: QueueRow["lifecycle"]; queued_at: string | null;
}
// getQueue SEEDED / STAFFED_WITH_WAITING examples (0005, 0006, 0007, 0008, 0012); getCase FEE_BEARING_CHANGE example (0009).
export const CATALOG: Record<string, CatalogRow> = {
  "MHC-C-0005": { reference: "MHC-C-0005", reason: "Refund request", priority: { level: "P3", word: "Standard" }, customer: "Dana Whitaker", created_at: "2026-10-16T14:14:00-05:00", due_at: "2026-10-16T09:00:00-05:00", due_label: "Fri Oct 16 · 9:00 am", due_state: "overdue", follow_up_short: "Email", lifecycle: "unassigned", queued_at: null },
  "MHC-C-0006": { reference: "MHC-C-0006", reason: "Conduct complaint", priority: { level: "P3", word: "Standard" }, customer: "Marcus Hill", created_at: "2026-10-16T14:14:00-05:00", due_at: "2026-10-19T19:00:00-05:00", due_label: "Mon Oct 19 · 7:00 pm", due_state: "on_time", follow_up_short: "Phone · afternoons", lifecycle: "unassigned", queued_at: null },
  "MHC-C-0007": { reference: "MHC-C-0007", reason: "Billing dispute", priority: { level: "P3", word: "Standard" }, customer: "Omar Patel", created_at: "2026-10-16T14:14:00-05:00", due_at: "2026-10-19T19:00:00-05:00", due_label: "Mon Oct 19 · 7:00 pm", due_state: "on_time", follow_up_short: "Phone · mornings", lifecycle: "unassigned", queued_at: null },
  "MHC-C-0008": { reference: "MHC-C-0008", reason: "Gas smell reported in chat", priority: { level: "P0", word: "Safety" }, customer: "No name given", created_at: "2026-10-16T14:16:00-05:00", due_at: null, due_label: null, due_state: "no_due_time", follow_up_short: null, lifecycle: "unassigned", queued_at: null },
  "MHC-C-0009": { reference: "MHC-C-0009", reason: "Fee-bearing change request", priority: { level: "P2", word: "Time-sensitive" }, customer: "Omar Patel", created_at: "2026-10-16T14:14:00-05:00", due_at: "2026-10-17T12:00:00-05:00", due_label: "Sat Oct 17 · 12:00 pm, the window start", due_state: "on_time", follow_up_short: null, lifecycle: "unassigned", queued_at: null },
  "MHC-C-0012": { reference: "MHC-C-0012", reason: "Asked for a person", priority: { level: "P3", word: "Standard" }, customer: "Omar Patel", created_at: "2026-10-16T14:14:00-05:00", due_at: null, due_label: null, due_state: "no_due_time", follow_up_short: null, lifecycle: "live_queued", queued_at: "2026-10-16T14:14:00-05:00" },
};

type Allowed = CaseSummary["allowed_actions"];
// dev replica of the server rules, derived from the CLAIMED / LIVE_JOINED / WAITING / ASSIGNED / DEFAULT examples
export function allowedFor(lifecycle: CaseSummary["lifecycle"], role: Role, liveState: LiveState["state"]): Allowed {
  if (role === "owner" || role === "customer") return [];
  const sup = role === "supervisor";
  let base: Allowed;
  switch (lifecycle) {
    case "unassigned": base = sup ? ["claim", "assign", "change_priority", "flag"] : ["claim", "flag"]; return base;
    case "live_queued": return sup ? ["claim", "assign", "change_priority", "flag"] : ["claim_and_join", "claim", "flag"];
    case "claimed":
    case "in_progress":
      if (liveState === "joined") base = ["send_live_message", "hand_back", "close_chat", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag"];
      else {
        base = ["start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag"];
        if (lifecycle === "in_progress") base = base.filter((a) => a !== "start");
        if (liveState === "queued") base.splice(base.indexOf("log_email") + 1, 0, "join_chat");
      }
      break;
    case "waiting": base = ["start", "release", "flag"]; break;
    default: return ["flag"];
  }
  return sup ? [...base.slice(0, -1), "assign", "change_priority", "flag"] : base;
}
