import type { ReplyBlock } from "../contract";
import type { ChatEvent, ChatState, ChatThread, CustomerEntry, Entry, EndedReason, FollowUpResponse, HandoffResponse, Limits, StartSessionResponse, TurnResponse } from "./model";
import { initialState } from "./model";
import { lastNoticeOf, turnsToEntries } from "./replyGroups";

export type Action =
  | { type: "START_BEGIN" }
  | { type: "START_OK"; res: StartSessionResponse }
  | { type: "START_FAIL"; message: string }
  | { type: "RESUME_OK"; thread: ChatThread; limits: Limits }
  | { type: "RESYNC_OK"; thread: ChatThread } // replace server-owned entries, keep local pending/failed customer entries
  | { type: "RESUME_GONE"; limits: Limits } // the stored thread reads 410: show an ended chat
  | { type: "ENDED"; reason: EndedReason }
  | { type: "SEND_BEGIN"; entry: CustomerEntry; startedAtMs: number }
  | { type: "RETRY_BEGIN"; turnId: string; startedAtMs: number }
  | { type: "TURN_OK"; turnId: string; res: TurnResponse }
  | { type: "TURN_FAIL"; turnId: string; message: string; retryable: boolean }
  | { type: "PERSON_OK"; turnId: string; res: HandoffResponse; entry: CustomerEntry | null }
  | { type: "LINE"; id: string; text: string }
  | { type: "FOLLOWUP_OK"; res: FollowUpResponse }
  | { type: "ANSWERED"; cardId: string; option: string }
  | { type: "EVENT"; key: string; event: ChatEvent }
  | { type: "RATE_HOLD_END" };

const hasEnded = (blocks: ReplyBlock[]) => blocks.some((b) => b.type === "session_ended");
const withEntry = (entries: Entry[], e: Entry): Entry[] => (entries.some((x) => x.id === e.id) ? entries : [...entries, e]);
const mapCustomer = (entries: Entry[], turnId: string, f: (e: CustomerEntry) => CustomerEntry): Entry[] =>
  entries.map((e) => (e.kind === "customer" && e.turnId === turnId ? f(e) : e));

function fromThread(thread: ChatThread): Pick<ChatState, "entries" | "settled" | "replying" | "ended"> {
  const entries = turnsToEntries(thread.turns);
  let ended: EndedReason | null = thread.state === "closed" ? "closed" : thread.state === "ended_by_reset" ? "reset" : null;
  if (!ended && entries.some((e) => e.kind === "reply" && hasEnded(e.blocks))) ended = "gone";
  return { entries, settled: thread.settled, replying: thread.settled.replying, ended };
}

export function chatReducer(state: ChatState, action: Action): ChatState {
  switch (action.type) {
    case "START_BEGIN": return { ...initialState };
    case "START_OK": {
      const r = action.res;
      return {
        ...initialState, phase: "ready", threadId: r.thread_id, limits: r.limits, settled: r.settled, replying: r.controller,
        entries: [{ kind: "reply", id: "greeting", blocks: [r.greeting], live: false }],
      };
    }
    case "START_FAIL": return { ...state, phase: "start-failed", startFailure: action.message };
    case "RESUME_OK": {
      return { ...initialState, phase: "ready", threadId: action.thread.thread_id, limits: action.limits, ...fromThread(action.thread) };
    }
    case "RESUME_GONE": return { ...initialState, phase: "ready", limits: action.limits, ended: "gone" };
    case "RESYNC_OK": {
      const t = fromThread(action.thread);
      const local = state.entries.filter((e): e is CustomerEntry => e.kind === "customer" && e.delivery !== "sent");
      return { ...state, ...t, entries: [...t.entries, ...local], ended: t.ended ?? state.ended };
    }
    case "ENDED": return { ...state, ended: action.reason, pending: null };
    case "SEND_BEGIN":
      return { ...state, entries: [...state.entries, action.entry], pending: { turnId: action.entry.turnId, startedAtMs: action.startedAtMs } };
    case "RETRY_BEGIN":
      return {
        ...state,
        entries: mapCustomer(state.entries, action.turnId, (e) => ({ ...e, delivery: "pending", failure: null, attempt: e.attempt + 1 })),
        pending: { turnId: action.turnId, startedAtMs: action.startedAtMs },
      };
    case "TURN_OK": {
      const { res, turnId } = action;
      const mine = state.entries.find((e): e is CustomerEntry => e.kind === "customer" && e.turnId === turnId);
      // A late success for an entry already marked failed is the real answer: accept it.
      let entries = mapCustomer(state.entries, turnId, (e) => ({ ...e, delivery: "sent", failure: null, at: res.blocks[0]?.at ?? e.at }));
      if (res.blocks.length) {
        const id = mine && mine.attempt > 0 ? `${turnId}:reply:${mine.attempt}` : `${turnId}:reply`;
        entries = withEntry(entries, { kind: "reply", id, blocks: res.blocks, live: true });
      }
      const notice = lastNoticeOf(res.blocks);
      return {
        ...state, entries, settled: res.settled, replying: res.controller,
        pending: state.pending?.turnId === turnId ? null : state.pending,
        lastNotice: res.notice ? notice : null, rateHeld: res.notice?.code === "RATE_LIMITED",
        ended: hasEnded(res.blocks) ? "gone" : state.ended,
      };
    }
    case "TURN_FAIL":
      return {
        ...state,
        entries: mapCustomer(state.entries, action.turnId, (e) => ({ ...e, delivery: "failed", failure: action.message, retryable: action.retryable })),
        pending: state.pending?.turnId === action.turnId ? null : state.pending,
      };
    case "PERSON_OK": {
      if (action.res.result === "already_open") return { ...state, settled: action.res.settled };
      let entries = state.entries;
      if (action.entry) entries = withEntry(entries, action.entry);
      entries = withEntry(entries, { kind: "reply", id: `person:${action.turnId}`, blocks: [action.res.block], live: true });
      return { ...state, entries, settled: action.res.settled };
    }
    case "FOLLOWUP_OK": return { ...state, settled: action.res.settled };
    case "LINE": return { ...state, entries: withEntry(state.entries, { kind: "line", id: action.id, text: action.text }) };
    case "ANSWERED": return action.cardId in state.answered ? state : { ...state, answered: { ...state.answered, [action.cardId]: action.option } };
    case "RATE_HOLD_END": return { ...state, rateHeld: false };
    case "EVENT": {
      if (state.seenEvents.includes(action.key)) return state;
      const ev = action.event;
      const base: ChatState = { ...state, seenEvents: [...state.seenEvents, action.key] };
      const line = (icon: Extract<Entry, { kind: "event" }>["icon"], l: string): Entry[] =>
        withEntry(base.entries, { kind: "event", id: `ev:${action.key}`, at: ev.at, line: l, icon });
      switch (ev.type) {
        case "representative_joined": return { ...base, entries: line("joined", ev.line), replying: { kind: "human", display_name: ev.display_name } };
        case "ai_paused": return { ...base, entries: line("paused", ev.line) };
        case "staff_message": return { ...base, entries: withEntry(base.entries, { kind: "message", id: `msg:${ev.message_id}`, speaker: ev.speaker, at: ev.at, text: ev.text }) };
        case "ai_resumed": return { ...base, entries: line("resumed", ev.line), replying: { kind: "ai", display_name: null } };
        case "chat_closed": return { ...base, entries: line("closed", ev.line), ended: ev.composer_disabled ? "closed" : base.ended };
        case "staffing_changed": return { ...base, entries: line("staffing", ev.line) };
        case "shift_ended": {
          const entries = withEntry(line("shift", ev.line), { kind: "reply", id: `shift:${action.key}`, blocks: [ev.handoff], live: true });
          return { ...base, entries, settled: ev.settled };
        }
        case "clock_changed": return base;
        case "demo_reset": return { ...base, entries: line("reset", ev.line), ended: "reset" };
        default: return base;
      }
    }
    default: return state;
  }
}
