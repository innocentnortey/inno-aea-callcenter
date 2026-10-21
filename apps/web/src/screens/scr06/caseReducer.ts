import type { components } from "@/api/types.gen";
import { formatTimePoint } from "@/lib/time";
import type { CaseDetail, CaseSummary } from "./caseText";

type ChatLine = components["schemas"]["ChatLine"];
type Activity = components["schemas"]["Activity"];
type LiveState = components["schemas"]["LiveState"];
type CaseEvent = components["schemas"]["CaseEvent"];

export interface LocalEvent { id: string; at: string; text: string }
export interface CaseState {
  detail: CaseDetail | null;
  messages: ChatLine[];
  events: LocalEvent[];
  /** Derived: a newer version than this user's own writes explain, or the shift ended under the chat. */
  changedElsewhere: boolean;
  endedByReset: boolean;
  /** Highest version carried by a case_changed event. */
  seenVersion: number;
  /** Highest version this user's own responses (summary/activity) have confirmed. */
  actedVersion: number;
  shiftEnded: boolean;
}
export type CaseAction =
  | { type: "loaded"; detail: CaseDetail }
  | { type: "summary"; summary: CaseSummary }
  | { type: "activity"; activity: Activity; summary: CaseSummary }
  | { type: "live"; live: LiveState; message: ChatLine | null; eventText?: string; eventAt?: string }
  | { type: "stream"; event: CaseEvent };

export const initialCaseState: CaseState = { detail: null, messages: [], events: [], changedElsewhere: false, endedByReset: false, seenVersion: 0, actedVersion: 0, shiftEnded: false };

const withMessage = (msgs: ChatLine[], m: ChatLine | null): ChatLine[] =>
  m && !msgs.some((x) => x.message_id === m.message_id) ? [...msgs, m] : msgs;

/** A stream event replayed after a reconnect (same event_id) is shown once. */
const withEvent = (events: LocalEvent[], e: LocalEvent): LocalEvent[] => (events.some((x) => x.id === e.id) ? events : [...events, e]);

/** The banner shows only for a version neither the loaded case nor this user's own responses account for. */
const settle = (s: CaseState): CaseState => {
  const changed = s.shiftEnded || (s.detail !== null && s.seenVersion > Math.max(s.detail.case.version, s.actedVersion));
  return changed === s.changedElsewhere ? s : { ...s, changedElsewhere: changed };
};

export function caseReducer(s: CaseState, a: CaseAction): CaseState {
  if (a.type === "loaded") return { ...initialCaseState, detail: a.detail, messages: a.detail.conversation };
  const d = s.detail;
  if (!d) return s;
  switch (a.type) {
    // A summary or activity is the answer to this user's own write: its version is theirs, not someone else's.
    case "summary": return settle({ ...s, detail: { ...d, case: a.summary }, actedVersion: Math.max(s.actedVersion, a.summary.version) });
    case "activity": return settle({ ...s, detail: { ...d, case: a.summary, activities: [a.activity, ...d.activities] }, actedVersion: Math.max(s.actedVersion, a.summary.version) });
    case "live": {
      const next: CaseState = { ...s, detail: { ...d, live: a.live }, messages: withMessage(s.messages, a.message) };
      if (a.eventText) {
        const at = a.eventAt ?? a.live.since ?? d.as_of;
        next.events = [...s.events, { id: `local-${s.events.length + 1}`, at, text: a.eventText }];
      }
      return next;
    }
    case "stream": {
      const ev = a.event;
      switch (ev.type) {
        case "customer_message": return { ...s, messages: withMessage(s.messages, ev.message) };
        case "controller_changed":
          return {
            ...s,
            detail: { ...d, live: { ...d.live, controller: ev.controller.kind } },
            events: withEvent(s.events, { id: `ev-${ev.event_id}`, at: ev.at, text: ev.line }),
          };
        case "chat_closed":
          return {
            ...s,
            detail: { ...d, live: { state: "closed", since: ev.at, controller: "ai" } },
            events: withEvent(s.events, { id: `ev-${ev.event_id}`, at: ev.at, text: "Chat closed at " + formatTimePoint(ev.at) }),
            ...(ev.reason === "shift_ended" ? { shiftEnded: true, changedElsewhere: true } : {}),
          };
        case "demo_reset":
          return {
            ...s,
            detail: { ...d, live: { state: "closed", since: ev.at, controller: "ai" } },
            endedByReset: true,
            events: withEvent(s.events, { id: `ev-${ev.event_id}`, at: ev.at, text: ev.line }),
          };
        case "case_changed":
          return settle({ ...s, seenVersion: Math.max(s.seenVersion, ev.version) });
        default: return s;
      }
    }
  }
}
