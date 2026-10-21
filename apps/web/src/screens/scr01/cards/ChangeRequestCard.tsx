import { Card, CardHeader, CardRow, IconTicket } from "@/components/ui";
import { RefChip } from "@/components/shared/RefChip";
import { Time, TimeWindow } from "@/components/shared/Time";
import type { BlockProps } from "../contract";
import { HintLine } from "./parts/CardParts";
import { dayIso, windowIsos } from "./parts/dates";
import { useLandedOnce } from "./parts/landed";
import { joinPromise } from "./parts/promise";

export function ChangeRequestCard(props: BlockProps<"change_request">) {
  const { block, settled } = props;
  const visit = settled?.visit ?? null;
  useLandedOnce(block.block_id, "request", `Your request: ${block.reference}`, props);
  return (
    <Card>
      <CardHeader icon={<IconTicket size={16} strokeWidth={1.8} aria-hidden="true" />} title="Change request" hint="Waiting for a representative to confirm" meta={<RefChip reference={block.reference} copyable />} />
      <div className="space-y-3 p-3">
        <div>
          {visit ? (
            <CardRow label="Your visit stays">
              <span className="block"><TimeWindow variant="due" {...windowIsos(visit.date, visit.window)} /></span>
              <Time iso={dayIso(visit.date)} format="day" variant="meta" />
            </CardRow>
          ) : null}
          <CardRow label="Requested"><span className="font-normal">{block.wanted_text}</span></CardRow>
          <CardRow label="Fee">{block.fee_line}</CardRow>
        </div>
        <p className="text-ui">{block.original_stays_line}</p>
        {block.windows_shown.length ? (
          <div>
            <HintLine>Windows are shown, not held.</HintLine>
            <ul className="mt-1 space-y-1 text-ui">
              {block.windows_shown.map((w) => (
                <li key={w.slot_id}>
                  {w.window_label} <Time iso={dayIso(w.date)} format="day" variant="meta" />
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        <p className="t-lead">{joinPromise(block, [block.cant_guarantee_line, block.phone_support_line])}</p>
        {block.due_at ? <CardRow label="Due" hint="The latest we've promised to get back to you"><Time iso={block.due_at} format="short" variant="row" /></CardRow> : null}
        {block.cant_guarantee_line ? <p className="text-ui">{block.cant_guarantee_line}</p> : null}
        {block.phone_support_line ? <p className="text-ui">{block.phone_support_line}</p> : null}
      </div>
    </Card>
  );
}
