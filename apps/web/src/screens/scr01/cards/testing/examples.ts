// Test helpers: read named examples from the OpenAPI file. Imported by *.test.* files only.
import fs from "node:fs";
import path from "node:path";
import YAML from "yaml";
import type { components } from "@/api/types.gen";
import type { BlockOf, BlockType } from "../../contract";

export type TurnResponse = components["schemas"]["TurnResponse"];
type Json = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any -- raw YAML

let cached: Json | null = null;
function doc(): Json {
  if (!cached) cached = YAML.parse(fs.readFileSync(path.resolve(process.cwd(), "../../docs/ux/03-structure/ui-contracts.openapi.yaml"), "utf8")) as Json;
  return cached;
}
function deref(node: Json): Json {
  let cur = node;
  let guard = 0;
  while (cur && typeof cur.$ref === "string" && guard++ < 20) {
    cur = cur.$ref.slice(2).split("/").reduce<Json>((acc, k) => acc?.[k], doc());
  }
  return cur;
}
function examplesOf(p: string, method: string, status: string): Json {
  const r = deref(doc().paths[p][method].responses[status]);
  return deref(r.content["application/json"]).examples as Json;
}
const clone = <T>(v: T): T => JSON.parse(JSON.stringify(v)) as T;
const TURNS = "/api/chat/sessions/{thread_id}/turns";

export function turnExample(name: string): TurnResponse {
  return clone(deref(examplesOf(TURNS, "post", "200")[name]).value as TurnResponse);
}
export function turnExampleNames(): string[] { return Object.keys(examplesOf(TURNS, "post", "200")); }
export function chatThreadExample(name: "OPEN" | "ENDED_BLOCK"): components["schemas"]["ChatThread"] {
  return clone(deref(examplesOf("/api/chat/sessions/{thread_id}", "get", "200")[name]).value);
}
export function handoffExample(name: "CASE_CREATED" | "LIVE_QUEUED" | "ALREADY_OPEN"): components["schemas"]["HandoffResponse"] {
  return clone(deref(examplesOf("/api/chat/sessions/{thread_id}/handoff", "post", "200")[name]).value);
}
export function followUpExample(name: string): components["schemas"]["FollowUpResponse"] {
  return clone(deref(examplesOf("/api/chat/sessions/{thread_id}/follow-up", "put", "200")[name]).value);
}
/** The 24 ReplyBlock discriminator values. */
export function schemaBlockTypes(): string[] {
  return Object.keys(doc().components.schemas.ReplyBlock.discriminator.mapping as Json);
}
export function blockOf<T extends BlockType>(res: TurnResponse, type: T, index = 0): BlockOf<T> {
  const found = res.blocks.filter((b) => b.type === type);
  if (!found[index]) throw new Error(`no ${type} block #${index}`);
  return found[index] as BlockOf<T>;
}
