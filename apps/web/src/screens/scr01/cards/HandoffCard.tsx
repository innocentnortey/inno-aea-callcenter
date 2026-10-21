import { Card, CardHeader, CardRow, IconClock, IconTicket, Tag } from "@/components/ui";
import { RefChip } from "@/components/shared/RefChip";
import { Time } from "@/components/shared/Time";
import type { BlockProps } from "../contract";
import { FollowUpChooser } from "./FollowUpChooser";
import { useLandedOnce } from "./parts/landed";
import { joinPromise } from "./parts/promise";

export function HandoffCard(props: BlockProps<"handoff">) {
  const { block } = props;
  useLandedOnce(block.block_id, "request", `Your request: ${block.reference}`, props);
  return (
    <Card>
      <CardHeader icon={<IconTicket size={16} strokeWidth={1.8} aria-hidden="true" />} title="Your request" hint="Your reference number" meta={<RefChip reference={block.reference} copyable />} />
      <div className="space-y-3 p-3">
        <p className="t-lead">{joinPromise(block)}</p>
        <div>
          {block.due_at ? <CardRow label="Due" hint="The latest we've promised to get back to you"><Time iso={block.due_at} format="short" variant="row" /></CardRow> : null}
          <CardRow label="Status"><Tag icon={<IconClock size={14} strokeWidth={1.8} aria-hidden="true" />}>Waiting for a representative</Tag></CardRow>
        </div>
        <FollowUpChooser block={block} settled={props.settled} dispatch={props.dispatch} announce={props.announce} landed={props.landed} disabled={props.disabled} />
      </div>
    </Card>
  );
}
