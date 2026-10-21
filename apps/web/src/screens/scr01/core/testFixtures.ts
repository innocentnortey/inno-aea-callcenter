// Test fixtures read from the OpenAPI named examples (Omar Patel, MHC-C-0007, thread thr_9d41, demo clock 2026-10-16T14:20:00-05:00).
// Imported by *.test.* files only.
import fs from "node:fs";
import path from "node:path";
import YAML from "yaml";
import type { ChatThread, FollowUpResponse, HandoffResponse, StartSessionResponse, TurnResponse } from "./model";

/* eslint-disable @typescript-eslint/no-explicit-any -- raw YAML */
let cached: any = null;
const doc = (): any => (cached ??= YAML.parse(fs.readFileSync(path.resolve(process.cwd(), "../../docs/ux/03-structure/ui-contracts.openapi.yaml"), "utf8")));
function deref(node: any): any {
  let cur = node;
  for (let i = 0; cur && typeof cur.$ref === "string" && i < 20; i++) cur = cur.$ref.slice(2).split("/").reduce((a: any, k: string) => a?.[k], doc());
  return cur;
}
function example(p: string, method: string, status: string, name: string): any {
  const r = deref(doc().paths[p][method].responses[status]);
  return JSON.parse(JSON.stringify(deref(deref(r.content["application/json"]).examples[name]).value));
}
/* eslint-enable @typescript-eslint/no-explicit-any */

const SESSIONS = "/api/chat/sessions";
/** startChatSession 201 STARTED */
export const startExample = (name: "STARTED" | "SIMULATION_ON" = "STARTED"): StartSessionResponse => example(SESSIONS, "post", "201", name);
/** getChatThread 200 OPEN | ENDED_BLOCK */
export const threadExample = (name: "OPEN" | "ENDED_BLOCK" = "OPEN"): ChatThread => example(`${SESSIONS}/{thread_id}`, "get", "200", name);
/** submitTurn 200 <name> */
export const turnExample = (name: string): TurnResponse => example(`${SESSIONS}/{thread_id}/turns`, "post", "200", name);
/** requestPerson 200 CASE_CREATED | LIVE_QUEUED | ALREADY_OPEN */
export const handoffExample = (name: "CASE_CREATED" | "LIVE_QUEUED" | "ALREADY_OPEN"): HandoffResponse => example(`${SESSIONS}/{thread_id}/handoff`, "post", "200", name);
/** saveFollowUp 200 PHONE_MORNINGS */
export const followUpExample = (): FollowUpResponse => example(`${SESSIONS}/{thread_id}/follow-up`, "put", "200", "PHONE_MORNINGS");
