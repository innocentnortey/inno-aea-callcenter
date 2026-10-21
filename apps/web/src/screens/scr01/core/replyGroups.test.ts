import { describe, expect, it } from "vitest";
import type { ReplyBlock } from "../contract";
import type { Entry } from "./model";
import { cardIdOf, findPinnedSafety, groupBlocks, isAnswered, lastNoticeOf, optionLabel, turnsToEntries, withoutPinned } from "./replyGroups";
import { threadExample, turnExample } from "./testFixtures";

const blk = (type: string, extra: object = {}, kind = "assistant"): ReplyBlock =>
  ({ block_id: `${type}-${Math.random()}`, type, speaker: { kind, display_name: null }, at: "2026-10-16T14:20:00-05:00", ...extra }) as unknown as ReplyBlock;
const reply = (blocks: ReplyBlock[], id = "r"): Entry => ({ kind: "reply", id, blocks, live: true });

describe("replyGroups", () => {
  it("groups consecutive blocks by speaker", () => {
    const g = groupBlocks("e", [blk("text"), blk("source_chip"), blk("text", {}, "representative"), blk("text")]);
    expect(g.map((x) => x.blocks.length)).toEqual([2, 1, 1]);
  });
  it("pins the first safety block only; conditional safety is not pinned", () => {
    const first = blk("safety");
    expect(findPinnedSafety([reply([blk("conditional_safety")])])).toBeNull();
    expect(findPinnedSafety([reply([blk("text"), first]), reply([blk("safety")], "r2")])).toBe(first);
    expect(withoutPinned([blk("text"), blk("safety"), blk("conditional_safety")]).map((b) => b.type)).toEqual(["text", "conditional_safety"]);
  });
  it("answers: server flag or local choice", () => {
    expect(isAnswered(blk("quick_checks", { card_id: "qc-1", answered: "skip" }), {})).toBe(true);
    expect(isAnswered(blk("quick_checks", { card_id: "qc-1", answered: null }), {})).toBe(false);
    expect(isAnswered(blk("quick_checks", { card_id: "qc-1", answered: null }), { "qc-1": "x" })).toBe(true);
    expect(cardIdOf(blk("text"))).toBeNull();
  });
  it("optionLabel found and not found", () => {
    const e = [reply([blk("quick_checks", { card_id: "qc-1", options: [{ option: "a", label: "Alpha" }] })])];
    expect(optionLabel(e, "qc-1", "a")).toBe("Alpha");
    expect(optionLabel(e, "qc-1", "b")).toBeNull();
    expect(optionLabel(e, "nope", "a")).toBeNull();
  });
  it("turnsToEntries for the OPEN thread: customer turn then assistant blocks", () => {
    const entries = turnsToEntries(threadExample("OPEN").turns);
    expect(entries[0]).toMatchObject({ kind: "customer", delivery: "sent" });
    expect(entries.some((e) => e.kind === "reply" && e.blocks.some((b) => b.type === "locate_prompt") && !e.live)).toBe(true);
  });
  it("lastNoticeOf reads the notice block", () => {
    expect(lastNoticeOf(turnExample("RATE_LIMITED").blocks)?.code).toBe("RATE_LIMITED");
    expect(lastNoticeOf(turnExample("ANSWER_WITH_SOURCE").blocks)).toBeNull();
  });
});
