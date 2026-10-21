import { callOp } from "@/api/client";
import type { ChatThread, FollowUpRequest, FollowUpResponse, HandoffResponse, StartSessionResponse, TurnRequest, TurnResponse } from "./model";

/** The one seam: callOp is the external system, so the hook takes a gateway and tests inject a fake. */
export interface ChatGateway {
  start(): Promise<StartSessionResponse>;
  resume(threadId: string): Promise<ChatThread>;
  submit(threadId: string, body: TurnRequest, signal?: AbortSignal): Promise<TurnResponse>;
  requestPerson(threadId: string, turnId: string): Promise<HandoffResponse>;
  saveFollowUp(threadId: string, body: FollowUpRequest): Promise<FollowUpResponse>;
}
export const apiGateway: ChatGateway = {
  start: () => callOp("startChatSession"),
  resume: (thread_id) => callOp("getChatThread", { path: { thread_id } }),
  submit: (thread_id, body, signal) => callOp("submitTurn", { path: { thread_id }, body, signal }),
  requestPerson: (thread_id, turn_id) => callOp("requestPerson", { path: { thread_id }, body: { turn_id } }),
  saveFollowUp: (thread_id, body) => callOp("saveFollowUp", { path: { thread_id }, body }),
};
