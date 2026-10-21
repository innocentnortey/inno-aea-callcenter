import { beforeEach, describe, expect, it } from "vitest";
import { OPS } from "@/api/client";
import type { components } from "@/api/types.gen";
import type { ChatDirectorCtx } from "../scenarios/types";
import { resetChatCardsDirector, rules } from "./chat-cards";

type Req = components["schemas"]["TurnRequest"];
const ctx = {} as ChatDirectorCtx;
const t = (payload: Req["payload"]): Req => ({ turn_id: "t-1", payload });
const text = (s: string) => t({ kind: "text", text: s });
const pick = (req: Req) => { for (const r of rules) { const n = r(req, ctx); if (n) return n; } return undefined; };
const turnNames = new Set(OPS.submitTurn.responses.filter((r) => r.status === 200).flatMap((r) => r.examples));

beforeEach(resetChatCardsDirector);

describe("chat-cards director", () => {
  const choice = (card_id: string, option: string) => t({ kind: "choice", card_id, option });
  const table: Array<[string, Req, string]> = [
    ["explicit demo prefix", text("demo:slot taken"), "SLOT_TAKEN"],
    ["burn yes", choice("burn-1", "yes"), "SAFETY"],
    ["burn no", choice("burn-1", "no"), "SLOT_CARD"],
    ["burn not sure", choice("burn-1", "not_sure"), "CONDITIONAL_SAFETY"],
    ["qc skip", choice("qc-1", "skip_and_book"), "WHERE_PROMPT"],
    ["qc show", choice("qc-1", "show_checks"), "QUICK_CHECKS"],
    ["uq any", choice("uq-1", "temp:yes;water:no;risk:skip"), "SLOT_CARD"],
    ["where ok", t({ kind: "form", card_id: "where-1", values: { zip_or_city: "78701" } }), "SLOT_CARD"],
    ["where out", t({ kind: "form", card_id: "where-1", values: { zip_or_city: "99999" } }), "OUT_OF_AREA"],
    ["slot 56", choice("slots-7", "56"), "LOCATE_PROMPT"],
    ["slot 58", choice("slots-7", "58"), "BOOKED"],
    ["locate form", t({ kind: "form", card_id: "loc-1", values: { name: "x", phone: "y" } }), "CODE_SENT"],
    ["code wrong", t({ kind: "code", card_id: "code-1", code: "111111" }), "CODE_WRONG"],
    ["code expired", t({ kind: "code", card_id: "code-1", code: "222222" }), "CODE_EXPIRED"],
    ["code locked", t({ kind: "code", card_id: "code-1", code: "333333" }), "CODE_LOCKED"],
    ["code no match", t({ kind: "code", card_id: "code-1", code: "444444" }), "NOT_VERIFIED"],
    ["code ok", t({ kind: "code", card_id: "code-1", code: "123456" }), "VERIFIED_ACCOUNT_INVOICE"],
    ["resend", choice("code-1", "resend"), "CODE_SENT"],
    ["gas", text("I smell gas"), "SAFETY"],
    ["burning", text("there is a burning smell"), "BURNING_CHECK"],
    ["no heat", text("we have no heat"), "EMERGENCY_LINE"],
    ["cancel", text("please cancel"), "CANCELLED"],
    ["reschedule", text("I need to reschedule"), "CHANGE_REQUEST"],
    ["confirm", text("confirm my appointment"), "APPOINTMENT"],
    ["book", text("I want to book a visit"), "QUICK_CHECKS"],
    ["invoice", text("question about my invoice"), "LOCATE_PROMPT"],
    ["membership", text("my membership"), "ACCOUNT_MEMBERSHIP"],
    ["warranty", text("is it under warranty"), "ACCOUNT_WARRANTY"],
    ["off topic", text("tell me a joke"), "NO_INFO"],
    ["frustrated", text("you are useless"), "FAILURE_OFFER"],
  ];
  for (const [name, req, expected] of table) {
    it(`${name} -> ${expected}`, () => {
      const got = pick(req);
      expect(got).toBe(expected);
      expect(turnNames.has(got!)).toBe(true);
    });
  }
  it("slot 57 is taken the first time only", () => {
    expect(pick(choice("slots-7", "57"))).toBe("SLOT_TAKEN");
    expect(pick(choice("slots-7", "57"))).toBe("LOCATE_PROMPT");
  });
  it("unknown text and a form with missing values never throw", () => {
    expect(pick(text("hello there"))).toBeUndefined();
    expect(() => pick(t({ kind: "form", card_id: "where-1", values: {} }))).not.toThrow();
    expect(pick(t({ kind: "form", card_id: "where-1", values: {} }))).toBe("SLOT_CARD");
  });
  it("an unknown demo: name is ignored", () => {
    expect(pick(text("demo:nonsense"))).toBeUndefined();
  });
});
