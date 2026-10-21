import type { ReplyBlock } from "../contract";
import type { ChatThread, Entry, NoticeCode, Speaker } from "./model";

export interface ReplyGroup { key: string; speaker: Speaker; at: string; blocks: ReplyBlock[] }
type SafetyBlock = Extract<ReplyBlock, { type: "safety" }>;

const sameSpeaker = (a: Speaker, b: Speaker) => a.kind === b.kind && a.display_name === b.display_name;

/** Consecutive blocks from the same speaker share one name line. */
export function groupBlocks(entryId: string, blocks: ReplyBlock[]): ReplyGroup[] {
  const groups: ReplyGroup[] = [];
  for (const b of blocks) {
    const last = groups[groups.length - 1];
    if (last && sameSpeaker(last.speaker, b.speaker)) last.blocks.push(b);
    else groups.push({ key: `${entryId}:${groups.length}`, speaker: b.speaker, at: b.at, blocks: [b] });
  }
  return groups;
}
/** D1: only `safety` (DANGER) is pinned; `conditional_safety` stays in the thread. First one wins. */
export function findPinnedSafety(entries: Entry[]): SafetyBlock | null {
  for (const e of entries) {
    if (e.kind !== "reply") continue;
    const hit = e.blocks.find((b): b is SafetyBlock => b.type === "safety");
    if (hit) return hit;
  }
  return null;
}
export function withoutPinned(blocks: ReplyBlock[]): ReplyBlock[] {
  return blocks.filter((b) => b.type !== "safety");
}
export function cardIdOf(block: ReplyBlock): string | null {
  return "card_id" in block && typeof block.card_id === "string" ? block.card_id : null;
}
export function isAnswered(block: ReplyBlock, answered: Record<string, string>): boolean {
  if ("answered" in block && block.answered != null) return true;
  const id = cardIdOf(block);
  return id !== null && id in answered;
}
export function optionLabel(entries: Entry[], cardId: string, option: string): string | null {
  for (const e of entries) {
    if (e.kind !== "reply") continue;
    for (const b of e.blocks) {
      if (cardIdOf(b) !== cardId || !("options" in b) || !Array.isArray(b.options)) continue;
      const hit = (b.options as { option: string; label: string }[]).find((o) => o.option === option);
      if (hit) return hit.label;
    }
  }
  return null;
}
export function turnsToEntries(turns: ChatThread["turns"]): Entry[] {
  const out: Entry[] = [];
  for (const t of turns) {
    if (t.speaker.kind === "customer") {
      const text = t.text ?? "Choice sent";
      out.push({ kind: "customer", id: `c:${t.turn_id}`, turnId: t.turn_id, at: t.at, text, payload: { kind: "text", text }, delivery: "sent", failure: null, retryable: false, attempt: 0 });
    } else if (t.blocks.length > 0) {
      out.push({ kind: "reply", id: `${t.turn_id}:reply`, blocks: t.blocks, live: false });
    } else if (t.text) {
      if (t.speaker.kind === "event") out.push({ kind: "event", id: `h:${t.turn_id}`, at: t.at, line: t.text, icon: "staffing" });
      else out.push({ kind: "message", id: `h:${t.turn_id}`, speaker: t.speaker, at: t.at, text: t.text });
    }
  }
  return out;
}
export function lastNoticeOf(blocks: ReplyBlock[]): { code: NoticeCode; text: string } | null {
  for (let i = blocks.length - 1; i >= 0; i--) {
    const b = blocks[i];
    if (b.type === "notice") return { code: b.code, text: b.text };
  }
  return null;
}
