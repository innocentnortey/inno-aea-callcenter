import type { Role } from "@/lib/roles";
import type { CaseDetail, CaseSummary } from "./caseText";

type Allowed = CaseSummary["allowed_actions"][number];
export type BarKey = "log_call" | "log_email" | "join_chat" | "flag" | "assign" | "change_priority";
export type MenuKey = "release" | "wait" | "close_unresolved" | "resolve" | "start";
export interface PlanItem<K extends string> { key: K; label: string; enabled: boolean; reason?: string }
export interface ActionPlan {
  readOnly: boolean;
  primary: { kind: "claim_and_join" | "claim" | "resolve" | "start"; label: string } | null;
  menu: PlanItem<MenuKey>[];
  bar: PlanItem<BarKey>[];
  liveBox: "hidden" | "active" | "disabled";
}

export function disabledReason(lifecycle: CaseSummary["lifecycle"], key: string): string {
  if (key === "join_chat") return "Join chat works only while the customer is waiting in a live chat.";
  if (lifecycle === "unassigned" || lifecycle === "live_queued") return "Claim the case first.";
  if (lifecycle === "waiting") return "Pick the case back up first.";
  if (lifecycle === "resolved" || lifecycle === "closed_unresolved") return "This case is closed.";
  return "Not available right now.";
}

export function planActions(detail: CaseDetail, role: Role): ActionPlan {
  if (role === "owner") return { readOnly: true, primary: null, menu: [], bar: [], liveBox: "hidden" };
  const c = detail.case;
  const allowed = new Set<Allowed>(c.allowed_actions);
  const joined = detail.live.state === "joined";
  const liveBox: ActionPlan["liveBox"] = joined ? "active" : detail.live.state === "handed_back" || detail.live.state === "closed" ? "disabled" : "hidden";

  let primary: ActionPlan["primary"] = null;
  if (!joined) {
    if (allowed.has("claim_and_join")) primary = { kind: "claim_and_join", label: "Claim and join" };
    else if (allowed.has("claim")) primary = { kind: "claim", label: "Claim" };
    else if (allowed.has("resolve")) primary = { kind: "resolve", label: "Resolve" };
    else if (allowed.has("start")) primary = { kind: "start", label: "Pick it back up" };
  }

  const item = <K extends string>(key: K, allowKey: Allowed, label: string): PlanItem<K> => {
    const enabled = allowed.has(allowKey);
    return enabled ? { key, label, enabled } : { key, label, enabled, reason: disabledReason(c.lifecycle, allowKey) };
  };
  const menu: PlanItem<MenuKey>[] = [
    item("release", "release", "Release"),
    item("wait", "wait", "Set waiting"),
    item("close_unresolved", "close_unresolved", "Close unresolved"),
  ];
  if (primary?.kind !== "resolve") menu.push(item("resolve", "resolve", "Resolve"));
  if (primary?.kind !== "start" && allowed.has("start")) menu.push(item("start", "start", "Pick it back up"));

  const bar: PlanItem<BarKey>[] = [
    item("log_call", "log_call", "Log a call"),
    item("log_email", "log_email", "Log an email"),
  ];
  if (role === "representative") bar.push(item("join_chat", "join_chat", "Join chat"));
  bar.push(item("flag", "flag", "Flag"));
  if (role === "supervisor") {
    bar.push(item("assign", "assign", c.owner !== null ? "Reassign" : "Assign"));
    bar.push(item("change_priority", "change_priority", "Change priority"));
  }
  return { readOnly: false, primary, menu, bar, liveBox };
}
