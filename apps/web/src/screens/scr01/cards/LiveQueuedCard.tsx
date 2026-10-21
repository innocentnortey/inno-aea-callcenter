import { Card, CardHeader, IconClock } from "@/components/ui";
import { RefChip } from "@/components/shared/RefChip";
import type { BlockProps } from "../contract";
import { StepList } from "./parts/CardParts";
import { useLandedOnce } from "./parts/landed";

export function LiveQueuedCard(props: BlockProps<"live_queued">) {
  const { block, settled } = props;
  const human = settled?.replying.kind === "human";
  useLandedOnce(block.block_id, "request", `Your request: ${block.reference}`, props);
  return (
    <Card>
      <CardHeader icon={<IconClock size={16} strokeWidth={1.8} aria-hidden="true" />} title="Your request" meta={<RefChip reference={block.reference} copyable />} />
      <div className="space-y-3 p-3">
        <p className="text-body">{block.promise_text}</p>
        <StepList
          steps={[
            { text: "You asked for a person", state: "done" },
            { text: "A representative joins this chat", state: human ? "done" : "current" },
            { text: "Back to the assistant, or the chat closes", state: human ? "current" : "todo" },
          ]}
        />
      </div>
    </Card>
  );
}
