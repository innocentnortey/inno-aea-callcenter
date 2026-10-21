// FROZEN by the foundation slice: the seam between G1 (chat core) and G2 (chat cards).
import type { ReactNode } from "react";
import type { components } from "@/api/types.gen";

export type ReplyBlock = components["schemas"]["ReplyBlock"];
export type Settled = components["schemas"]["Settled"];
export type BlockType = ReplyBlock["type"];
export type BlockOf<T extends BlockType> = Extract<ReplyBlock, { type: T }>;
export type ChatAction =
  | { kind: "text"; text: string }
  | { kind: "choice"; cardId: string; option: string }
  | { kind: "code"; cardId: string; code: string }
  | { kind: "form"; cardId: string; values: Record<string, string> }
  | { kind: "person" } // CON-4 requestPerson
  | { kind: "followUp"; channel: "email" | "phone"; destination: "on_record" | "general"; window: "morning" | "afternoon" | "any" } // CON-5
  | { kind: "retry"; turnId: string } // "Try again" reuses the same turn_id
  | { kind: "newChat" };
export interface BlockProps<T extends BlockType> {
  block: BlockOf<T>;
  settled: Settled | null;
  answered: boolean; // this card already received its answer (buttons disabled, choice kept)
  disabled: boolean; // chat ended / pending
  dispatch(action: ChatAction): Promise<void>;
  announce(message: string): void; // polite region
  landed(target: "visit" | "request" | "identity"): void; // mint wash on the matching panel block (not under reduced motion)
}
export type BlockRenderer<T extends BlockType> = (props: BlockProps<T>) => ReactNode;
export type RendererMap = { [T in BlockType]?: BlockRenderer<T> };
