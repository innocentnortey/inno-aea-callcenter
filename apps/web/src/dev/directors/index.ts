import type { OperationId } from "@/api/client";
import type { components } from "@/api/types.gen";
import type { World } from "../world";
import type { ChatDirectorCtx } from "../scenarios/types";
import { rules as coreRules } from "./chat-core";
import { rules as cardRules } from "./chat-cards";

const RULES = [...coreRules, ...cardRules];
/** The submitTurn example to answer with; typed words are never echoed, the reply is the example's. */
export function pickTurnExample(req: components["schemas"]["TurnRequest"], ctx: ChatDirectorCtx): string {
  for (const rule of RULES) {
    const name = rule(req, ctx);
    if (name) return name;
  }
  return "ANSWER_WITH_SOURCE";
}

// FR-1 (G4): case-aware picking. The picker lives in G4's ./case-actions (`export const casePicker`); it is loaded with
// import.meta.glob so this file compiles and works before that module exists (no match -> no pick).
export interface CaseCall { op: OperationId; reference: string | null; body: unknown; world: World }
export interface CasePick { example: string; status?: number; transform?: (body: any) => any } // eslint-disable-line @typescript-eslint/no-explicit-any
export type CasePicker = (call: CaseCall) => CasePick | undefined;
export const CASE_OPS: readonly OperationId[] = ["getQueue", "getCase", "applyCaseAction", "liveChatAction", "recordContactActivity"];

const caseModules = import.meta.glob<{ casePicker?: CasePicker }>("./case-actions.ts", { eager: true });
/** The first defined pick from G4's `casePicker`, or undefined (no such module, or no opinion). */
export function pickCaseCall(call: CaseCall): CasePick | undefined {
  for (const m of Object.values(caseModules)) {
    const pick = m.casePicker?.(call);
    if (pick) return pick;
  }
  return undefined;
}
