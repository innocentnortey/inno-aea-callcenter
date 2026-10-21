import type { ReactNode } from "react";
import { cn } from "@/lib/cx";
import { EventLine, SpeakerLine } from "@/components/shared/messages";
import { renderBlock } from "../../blocks";
import { blockLayout } from "../../cards";
import type { BlockProps, ReplyBlock } from "../../contract";
import { groupBlocks, isAnswered, withoutPinned } from "../replyGroups";

type Shared = Pick<BlockProps<"text">, "settled" | "dispatch" | "announce" | "landed">;
export interface AssistantGroupProps extends Shared {
  entryId: string;
  blocks: ReplyBlock[];
  live: boolean; // false while hydrating history: cards get no-op landed/announce so a reload stays quiet (G1-b)
  answered: Record<string, string>;
  disabled: boolean;
}
const noop = () => undefined;
const BUBBLE: Record<string, string> = {
  assistant: "bg-[var(--turn-assistant-bg)]",
  representative: "bg-[var(--turn-rep-bg)] border border-[color:var(--turn-rep-edge)]",
};

/** One reply: consecutive blocks per speaker, laid out by blockLayout (bubble, card, event). The pinned safety block is not here. */
export function AssistantGroup({ entryId, blocks, live, settled, answered, disabled, dispatch, announce, landed }: AssistantGroupProps) {
  const render = (block: ReplyBlock) =>
    renderBlock({ block, settled, answered: isAnswered(block, answered), disabled, dispatch, announce: live ? announce : noop, landed: live ? landed : noop });
  return (
    <>
      {groupBlocks(entryId, withoutPinned(blocks)).map((g) => {
        const parts: ReactNode[] = [];
        let run: ReplyBlock[] = [];
        const flush = () => {
          if (!run.length) return;
          parts.push(
            <div key={`b:${run[0].block_id}`} className={cn("max-w-[62ch] rounded-card rounded-tl-tip px-3 py-2 text-body", BUBBLE[g.speaker.kind] ?? BUBBLE.assistant)}>
              {run.map((b) => <div key={b.block_id}>{render(b)}</div>)}
            </div>,
          );
          run = [];
        };
        let sawVisible = false;
        for (const b of g.blocks) {
          const layout = blockLayout(b);
          if (layout === "bubble") { run.push(b); sawVisible = true; continue; }
          flush();
          if (layout === "event") parts.push(<EventLine key={b.block_id} at={b.at}>{render(b)}</EventLine>);
          else { parts.push(<div key={b.block_id} className="max-w-[62ch]">{render(b)}</div>); sawVisible = true; }
        }
        flush();
        return (
          <div key={g.key} className="flex flex-col gap-1">
            {sawVisible ? <SpeakerLine speaker={g.speaker} at={g.at} /> : null}
            {parts}
          </div>
        );
      })}
    </>
  );
}
