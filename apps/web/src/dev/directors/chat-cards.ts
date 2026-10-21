// G2 director rules: pick the submitTurn example from what the customer typed or tapped.
// Typed words are never echoed; the reply is the example's. Keyword sets here are G2's (G1's chat-core must not reuse them).
import { OPS } from "@/api/client";
import type { DirectorRule } from "../scenarios/types";

const isTurnExample = (name: string): boolean =>
  OPS.submitTurn.responses.some((r) => r.status === 200 && r.examples.includes(name));
const valid = (name: string | undefined): string | undefined => (name && isTurnExample(name) ? name : undefined);

let takenShown = false; // slot 57 is "taken" the first time only
export function resetChatCardsDirector(): void { takenShown = false; }

const textOf = (req: Parameters<DirectorRule>[0]): string | null => (req.payload.kind === "text" ? req.payload.text : null);

const explicit: DirectorRule = (req) => {
  const m = /^demo:\s*([a-z_ ]+)$/i.exec(textOf(req)?.trim() ?? "");
  return m ? valid(m[1].trim().replace(/\s+/g, "_").toUpperCase()) : undefined;
};
const byCard: DirectorRule = (req) => {
  const p = req.payload;
  if (p.kind === "choice") {
    switch (p.card_id) {
      case "burn-1": return ({ yes: "SAFETY", no: "SLOT_CARD", not_sure: "CONDITIONAL_SAFETY" } as Record<string, string>)[p.option];
      case "qc-1": return ({ skip_and_book: "WHERE_PROMPT", show_checks: "QUICK_CHECKS" } as Record<string, string>)[p.option];
      case "uq-1": return "SLOT_CARD";
      case "slots-7":
        if (p.option === "57") {
          if (takenShown) return "LOCATE_PROMPT";
          takenShown = true;
          return "SLOT_TAKEN";
        }
        return p.option === "58" ? "BOOKED" : "LOCATE_PROMPT";
      case "code-1": return p.option === "resend" ? "CODE_SENT" : undefined;
      default: return undefined;
    }
  }
  if (p.kind === "form") {
    if (p.card_id === "where-1") return /^(00000|99999)$|outside/i.test(p.values?.zip_or_city ?? "") ? "OUT_OF_AREA" : "SLOT_CARD";
    if (p.card_id === "loc-1") return "CODE_SENT";
  }
  if (p.kind === "code" && p.card_id === "code-1") {
    return ({ "111111": "CODE_WRONG", "222222": "CODE_EXPIRED", "333333": "CODE_LOCKED", "444444": "NOT_VERIFIED" } as Record<string, string>)[p.code] ?? "VERIFIED_ACCOUNT_INVOICE";
  }
  return undefined;
};

const KEYWORDS: Array<[RegExp, string]> = [
  [/\bgas\b|carbon monoxide|\bco alarm\b/i, "SAFETY"],
  [/burning|smells? like (smoke|burn)/i, "BURNING_CHECK"],
  [/no heat|no (a\/c|ac|cooling)|\bleak/i, "EMERGENCY_LINE"],
  [/\bcancel/i, "CANCELLED"],
  [/reschedul|\bmove (my|the)\b/i, "CHANGE_REQUEST"],
  [/confirm (my )?(appointment|visit)/i, "APPOINTMENT"],
  [/\bbook|schedule|appointment|\bvisit\b|technician/i, "QUICK_CHECKS"],
  [/\bbill\b|invoice|charge/i, "LOCATE_PROMPT"],
  [/membership|\bplan\b/i, "ACCOUNT_MEMBERSHIP"],
  [/warranty/i, "ACCOUNT_WARRANTY"],
  [/weather|joke|recipe/i, "NO_INFO"],
  [/not getting this|useless/i, "FAILURE_OFFER"],
];
const keywords: DirectorRule = (req) => {
  const t = textOf(req);
  if (t === null) return undefined;
  return KEYWORDS.find(([re]) => re.test(t))?.[1];
};

export const rules: DirectorRule[] = [
  (req, ctx) => valid(explicit(req, ctx)),
  (req, ctx) => valid(byCard(req, ctx)),
  (req, ctx) => valid(keywords(req, ctx)),
];
