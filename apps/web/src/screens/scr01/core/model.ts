import type { components } from "@/api/types.gen";
import type { ReplyBlock, Settled } from "../contract";

type S = components["schemas"];
export type StartSessionResponse = S["StartSessionResponse"];
export type ChatThread = S["ChatThread"];
export type TurnRequest = S["TurnRequest"];
export type TurnPayload = S["TurnPayload"];
export type TurnResponse = S["TurnResponse"];
export type HandoffResponse = S["HandoffResponse"];
export type FollowUpRequest = S["FollowUpRequest"];
export type FollowUpResponse = S["FollowUpResponse"];
export type ChatEvent = S["ChatEvent"];
export type Speaker = S["Speaker"];
export type Limits = S["Limits"];
export type Staffing = S["Staffing"];
export type DemoClock = S["DemoClock"];
export type Write = S["Write"];

export type EndedReason = "closed" | "reset" | "gone"; // gone = 404/410/session_ended block
export type EventIcon = "joined" | "paused" | "resumed" | "closed" | "shift" | "reset" | "staffing";
export type CustomerPayload = TurnPayload | { kind: "person" };
export type NoticeCode = "RATE_LIMITED" | "BOOKING_CAP" | "SPEND_CAP_REACHED" | "TURN_TIMEOUT" | "BUSY" | "AI_PAUSED";
export type CustomerEntry = {
  kind: "customer"; id: string; turnId: string; at: string | null; text: string; payload: CustomerPayload;
  delivery: "pending" | "sent" | "failed"; failure: string | null; retryable: boolean;
  attempt: number; // bumped by each Try again so every attempt's reply gets its own entry id
};
export type Entry =
  | CustomerEntry
  // live=false: rebuilt from history (getChatThread / greeting); its cards get no-op landed/announce (G1-b)
  | { kind: "reply"; id: string; blocks: ReplyBlock[]; live: boolean }
  | { kind: "message"; id: string; speaker: Speaker; at: string; text: string }
  | { kind: "event"; id: string; at: string | null; line: string; icon: EventIcon }
  | { kind: "line"; id: string; text: string };

export interface ChatState {
  phase: "starting" | "ready" | "start-failed";
  startFailure: string | null;
  threadId: string | null;
  limits: Limits | null;
  entries: Entry[];
  settled: Settled | null;
  replying: { kind: "ai" | "human"; display_name: string | null };
  pending: { turnId: string; startedAtMs: number } | null;
  ended: EndedReason | null;
  lastNotice: { code: NoticeCode; text: string } | null;
  rateHeld: boolean;
  answered: Record<string, string>;
  seenEvents: string[];
}
export const initialState: ChatState = {
  phase: "starting", startFailure: null, threadId: null, limits: null, entries: [], settled: null,
  replying: { kind: "ai", display_name: null }, pending: null, ended: null, lastNotice: null, rateHeld: false,
  answered: {}, seenEvents: [],
};
