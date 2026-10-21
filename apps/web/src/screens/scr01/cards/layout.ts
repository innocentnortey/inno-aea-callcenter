import type { ReplyBlock } from "../contract";

export type BlockLayout = "bubble" | "card" | "pinned" | "event";
/** Where each block belongs: bubble = inside the grey assistant turn; card = standalone hairline card; pinned = the safety card; event = centred quiet line. */
export function blockLayout(block: ReplyBlock): BlockLayout {
  switch (block.type) {
    case "safety": return "pinned";
    case "session_ended": return "event";
    case "text":
    case "source_chip":
    case "no_info":
    case "failure_offer": return "bubble";
    case "notice": return block.code === "BUSY" || block.code === "AI_PAUSED" ? "bubble" : "card";
    default: return "card";
  }
}
