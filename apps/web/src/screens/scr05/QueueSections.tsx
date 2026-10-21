import type { components } from "@/api/types.gen";
import { Tag } from "@/components/ui";
import { QueueRow } from "@/components/shared/QueueRow";
import { LiveRow } from "./LiveRow";

type Row = components["schemas"]["QueueRow"];
type Staffing = components["schemas"]["Staffing"];

export function LiveQueueSection(props: {
  staffing: Staffing; rows: Row[]; cursor: string | null; onOpen(ref: string): void; onClaimAndJoin(ref: string): void; pendingRef: string | null;
}) {
  const { staffing, rows, cursor, onOpen, onClaimAndJoin, pendingRef } = props;
  return (
    <section aria-labelledby="live-queue-h" className="flex flex-col gap-2">
      <h2 id="live-queue-h" className="t-section flex items-center gap-2">
        Waiting in chat
        {staffing.mode === "simulated_on_shift" ? <Tag>{rows.length}</Tag> : null}
      </h2>
      {staffing.mode === "nobody_online" ? (
        <p className="text-ui text-text-muted">Nobody is on shift, so there is no live queue. Turn on the simulation in the demo guide to try it.</p>
      ) : rows.length === 0 ? (
        <p className="text-ui text-text-muted">Nobody is waiting in chat right now.</p>
      ) : (
        <ul className="flex flex-col gap-1">
          {rows.map((r) => (
            <LiveRow key={r.reference} row={r} selected={r.reference === cursor} onOpen={onOpen} onClaimAndJoin={onClaimAndJoin} pending={pendingRef === r.reference} />
          ))}
        </ul>
      )}
    </section>
  );
}

export function NeedsActionSection({ rows, cursor, onOpen }: { rows: Row[]; cursor: string | null; onOpen(ref: string): void }) {
  return (
    <section aria-labelledby="needs-h" className="flex flex-col gap-2">
      <h2 id="needs-h" className="t-section flex items-center gap-2">
        Needs my action
        <Tag>{rows.length}</Tag>
      </h2>
      <p className="text-small text-text-muted">Safety and danger first, then by due time.</p>
      <ul className="flex flex-col gap-1">
        {rows.map((r) => (
          <QueueRow key={r.reference} row={r} selected={r.reference === cursor} showStaffTags onSelect={onOpen} />
        ))}
      </ul>
    </section>
  );
}
