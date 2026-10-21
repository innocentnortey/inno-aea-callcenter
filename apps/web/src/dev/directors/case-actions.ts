/* eslint-disable @typescript-eslint/no-explicit-any -- response bodies are reshaped as plain JSON */
// The case director (FR-1): picks the getQueue / getCase / applyCaseAction / liveChatAction / recordContactActivity example
// from the request, so a Resolve click does not come back as "Claimed". Picks are pure; every store write happens inside a
// `transform`, which runs only when the response is actually delivered.
import type { components } from "@/api/types.gen";
import { formatDateTimeShort } from "@/lib/time";
import type { Role } from "@/lib/roles";
import type { CaseCall, CasePick, CasePicker } from "./index";
import { allowedFor, CATALOG, getOverride, patchOverride, type CaseOverride, type CaseSummary } from "./case-store";

type S = components["schemas"];
type Req = S["CaseActionRequest"];
type Live = S["LiveState"];
// The demo clock's start; the case skeleton has no clock of its own.
export const DEMO_NOW = "2026-10-16T14:20:00-05:00";
const WORD: Record<string, string> = { P0: "Safety", P1: "Danger", P2: "Time-sensitive", P3: "Standard", P4: "Routine" };
const NAMED = new Set(["MHC-C-0007", "MHC-C-0008", "MHC-C-0009"]);

const empty = (v: unknown) => typeof v !== "string" || v.trim() === "";
const err = (example: string, status: number, transform?: CasePick["transform"]): CasePick => ({ example, status, transform });

function baseLive(ref: string): Live {
  const row = CATALOG[ref];
  return row?.lifecycle === "live_queued" ? { state: "queued", since: row.queued_at, controller: "ai" } : { state: "not_live", since: null, controller: "ai" };
}
/** The case summary skeleton for `ref`, from the catalog. */
export function catalogBase(ref: string): Omit<CaseSummary, "lifecycle" | "owner" | "version" | "allowed_actions" | "wake_up_at"> {
  const r = CATALOG[ref] ?? CATALOG["MHC-C-0007"];
  return {
    reference: ref, reason: r.reason, priority: r.priority, created_at: r.created_at, due_at: r.due_at, due_label: r.due_label,
    due_state: r.due_state, promise_status: "open", seed: ref !== "MHC-C-0012",
  };
}
/** The case summary after the override `now`, with allowed_actions derived for the role. */
function caseFromOverride(ref: string, now: CaseOverride, role: Role): CaseSummary {
  const lifecycle = now.lifecycle ?? CATALOG[ref]?.lifecycle ?? "unassigned";
  const base = catalogBase(ref);
  return {
    ...base, priority: now.priority ?? base.priority, promise_status: now.promise_status ?? "open", lifecycle,
    owner: now.owner ?? null, version: now.version ?? 3, wake_up_at: now.wake_up_at ?? null,
    allowed_actions: allowedFor(lifecycle, role, (now.live ?? baseLive(ref)).state),
  };
}
function current(ref: string): { lifecycle: CaseSummary["lifecycle"]; live: Live; ov: CaseOverride | undefined } {
  const ov = getOverride(ref);
  return { lifecycle: ov?.lifecycle ?? CATALOG[ref]?.lifecycle ?? "unassigned", live: ov?.live ?? baseLive(ref), ov };
}

/** Rewrites a getCase body for a reference that has no named example (0005, 0006, 0012). */
function reskin(ref: string, b: any): any {
  const r = CATALOG[ref];
  b.case = { ...b.case, ...catalogBase(ref), owner: null, lifecycle: r.lifecycle, wake_up_at: null };
  b.brief.headings = b.brief.headings.map((h: any) => ({ ...h, items: [] }));
  b.sources = [];
  b.conversation = [];
  b.other_cases = [];
  b.promise = { ...b.promise, text: String(b.promise.text).replace("MHC-C-0007", ref), due_at: r.due_at, due_label: r.due_label };
  b.live = baseLive(ref);
  return b;
}
/** Applies what staff did since load, then derives allowed_actions for the role asked as. */
function applyOverride(ref: string, role: Role, b: any): any {
  const ov = getOverride(ref);
  if (ov) {
    const c = b.case;
    if (ov.lifecycle !== undefined) c.lifecycle = ov.lifecycle;
    if (ov.owner !== undefined) c.owner = ov.owner;
    if (ov.version !== undefined) c.version = ov.version;
    if (ov.wake_up_at !== undefined) c.wake_up_at = ov.wake_up_at;
    if (ov.priority !== undefined) c.priority = ov.priority;
    if (ov.promise_status !== undefined) { c.promise_status = ov.promise_status; b.promise.status = ov.promise_status; }
    if (ov.live !== undefined) b.live = ov.live;
    const seen = new Set(b.activities.map((a: any) => a.activity_id));
    b.activities = [...ov.activities.filter((a) => !seen.has(a.activity_id)), ...b.activities];
    const have = new Set(b.conversation.map((m: any) => m.message_id));
    b.conversation = [...b.conversation, ...ov.messages.filter((m) => !have.has(m.message_id))];
  }
  b.case.allowed_actions = allowedFor(b.case.lifecycle, role, b.live.state);
  return b;
}

function pickQueue(call: CaseCall): CasePick {
  const example = call.world.staffing === "simulated_on_shift" ? "STAFFED_WITH_WAITING" : "SEEDED";
  return {
    example,
    transform: (b: any) => {
      const apply = (r: any) => {
        const ov = getOverride(r.reference);
        if (!ov) return r;
        return { ...r, ...(ov.lifecycle !== undefined && { lifecycle: ov.lifecycle }), ...(ov.owner !== undefined && { owner: ov.owner }),
          ...(ov.wake_up_at !== undefined && { wake_up_at: ov.wake_up_at }), ...(ov.priority !== undefined && { priority: ov.priority }) };
      };
      const alive = (r: any) => r.lifecycle !== "resolved" && r.lifecycle !== "closed_unresolved";
      const live = b.live.map(apply).filter(alive);
      const moved = live.filter((r: any) => r.lifecycle !== "live_queued").map((r: any) => ({ ...r, queued_at: null }));
      return { ...b, live: live.filter((r: any) => r.lifecycle === "live_queued"), needs_my_action: [...b.needs_my_action.map(apply).filter(alive), ...moved] };
    },
  };
}

function pickGetCase(call: CaseCall): CasePick {
  const ref = call.reference ?? "";
  const role = call.world.role;
  if (NAMED.has(ref)) {
    const example = ref === "MHC-C-0008" ? "SAFETY_CASE" : ref === "MHC-C-0009" ? "FEE_BEARING_CHANGE" : "DEFAULT";
    return { example, transform: (b: any) => applyOverride(ref, role, b) };
  }
  if (CATALOG[ref]) return { example: "DEFAULT", transform: (b: any) => applyOverride(ref, role, reskin(ref, b)) };
  return err("CASE_NOT_FOUND", 404, (b: any) => ({ ...b, error: { ...b.error, details: { reference: ref } } }));
}

interface Next extends Partial<CaseOverride> { live: Live; lifecycle: CaseSummary["lifecycle"]; version: number }
function nextState(ref: string, body: Req, role: Role): Next {
  const { lifecycle, live, ov } = current(ref);
  const version = (ov?.version ?? 3) + 1;
  const ownerName = role === "supervisor" ? "Demo supervisor" : "Riley";
  switch (body.action) {
    case "claim": return { lifecycle: "claimed", owner: ownerName, version, live };
    case "start": return { lifecycle: "in_progress", wake_up_at: null, version, live };
    case "wait": return { lifecycle: "waiting", wake_up_at: body.wake_up_at ?? null, version, live };
    case "resolve": return { lifecycle: "resolved", version, live, promise_status: Date.parse(DEMO_NOW) > Date.parse(CATALOG[ref]?.due_at ?? "9999-01-01") ? "missed" : "kept" };
    case "close_unresolved": return { lifecycle: "closed_unresolved", version, live };
    case "release": return { lifecycle: "unassigned", owner: null, version, live };
    case "assign": return { lifecycle: lifecycle === "unassigned" || lifecycle === "live_queued" ? "claimed" : lifecycle, owner: body.assignee === "riley" ? "Riley" : "Demo supervisor", version, live };
    default: {
      const level = body.priority ?? "P3";
      return { lifecycle, priority: { level, word: WORD[level] } as CaseSummary["priority"], version, live };
    }
  }
}
function resultLine(ref: string, body: Req, next: Next): string {
  switch (body.action) {
    case "claim": return `Claimed · ${next.owner}${next.owner === "Riley" ? " (demo)" : ""}`;
    case "start": return "Picked back up."; // dev fixture: no named example
    case "wait": return `Waiting until ${body.wake_up_at ? formatDateTimeShort(body.wake_up_at) : "later"}`;
    case "resolve": return `${ref} resolved.`;
    case "close_unresolved": return "Closed unresolved."; // dev fixture
    case "release": return "Released."; // dev fixture
    case "assign": return `Assigned to ${next.owner}${next.owner === "Riley" ? " (demo)" : ""}.`;
    default: return `Priority is now ${next.priority?.level} · ${next.priority?.word}.`;
  }
}
const EXAMPLE: Record<string, string> = { claim: "CLAIMED", wait: "WAITING", resolve: "RESOLVED", assign: "ASSIGNED", change_priority: "PRIORITY_CHANGED", start: "CLAIMED", release: "CLAIMED", close_unresolved: "CLAIMED" };

function pickAction(call: CaseCall): CasePick | undefined {
  const ref = call.reference ?? "";
  const body = call.body as Req | undefined;
  if (!body) return undefined;
  const role = call.world.role;
  if (["release", "assign", "change_priority", "close_unresolved"].includes(body.action) && empty(body.reason)) return err("REASON_REQUIRED", 422);
  if (body.action === "wait" && empty(body.wake_up_at)) return err("WAKE_UP_REQUIRED", 422);
  if (body.action === "resolve" && empty(body.outcome)) return err("OUTCOME_REQUIRED", 422);
  const { lifecycle, live, ov } = current(ref);
  if (ov) {
    const key = body.action;
    if (!(allowedFor(lifecycle, role, live.state) as string[]).includes(key)) {
      return key === "claim" ? err("CASE_ALREADY_CLAIMED", 409) : err("NOT_ALLOWED_IN_STATE", 409);
    }
  }
  return {
    example: EXAMPLE[body.action] ?? "CLAIMED",
    transform: (b: any) => {
      const next = nextState(ref, body, role);
      const now = patchOverride(ref, next);
      b.case = caseFromOverride(ref, now, role);
      b.result_line = resultLine(ref, body, next);
      return b;
    },
  };
}

function pickLive(call: CaseCall): CasePick | undefined {
  const ref = call.reference ?? "";
  const body = call.body as S["LiveActionRequest"] | undefined;
  if (!body) return undefined;
  const { lifecycle, live, ov } = current(ref);
  if (body.action === "join") {
    if (ov && (lifecycle === "unassigned" || lifecycle === "live_queued")) return err("NOT_CLAIMED_BY_YOU", 403);
    return { example: "JOINED", transform: (b: any) => { patchOverride(ref, { lifecycle: "in_progress", live: b.live }); return b; } };
  }
  const ended = !!ov?.live && live.state !== "joined";
  if (body.action === "send") {
    if (empty(body.text)) return err("VALIDATION_ERROR", 400);
    if (ended) return err("NOT_LIVE", 409, (b: any) => ({ ...b, error: { ...b.error, details: { reason: "closed" } } }));
    return {
      example: "SENT",
      transform: (b: any) => {
        const n = ov?.messages.length ?? 0;
        b.message = { ...b.message, message_id: `m-${88 + n}`, text: body.text };
        patchOverride(ref, { messages: [b.message] });
        return b;
      },
    };
  }
  if (ended) return err("NOT_LIVE", 409);
  return { example: body.action === "hand_back" ? "HANDED_BACK" : "CLOSED", transform: (b: any) => { patchOverride(ref, { live: b.live }); return b; } };
}

function pickContact(call: CaseCall): CasePick | undefined {
  const ref = call.reference ?? "";
  const body = call.body as S["ActivityRequest"] | undefined;
  if (!body) return undefined;
  const { lifecycle, live, ov } = current(ref);
  if (ov && lifecycle !== "claimed" && lifecycle !== "in_progress") return err("NOT_ALLOWED_IN_STATE", 409);
  return {
    example: body.kind === "email" ? "EMAIL_LEFT_MESSAGE" : "CALL_REACHED",
    transform: (b: any) => {
      const n = ov?.activities.length ?? 0;
      b.activity = { ...b.activity, kind: body.kind, outcome: body.outcome, note: body.note ?? null, activity_id: `act-${n + 17}` };
      const now = patchOverride(ref, { activities: [b.activity], version: ov?.version ?? 4, owner: ov?.owner ?? "Riley", lifecycle, live });
      b.case = caseFromOverride(ref, now, call.world.role);
      return b;
    },
  };
}

export const casePicker: CasePicker = (call) => {
  switch (call.op) {
    case "getQueue": return pickQueue(call);
    case "getCase": return pickGetCase(call);
    case "applyCaseAction": return pickAction(call);
    case "liveChatAction": return pickLive(call);
    case "recordContactActivity": return pickContact(call);
    default: return undefined;
  }
};
