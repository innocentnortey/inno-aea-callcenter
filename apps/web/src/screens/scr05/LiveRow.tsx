import type { components } from "@/api/types.gen";
import { Button } from "@/components/ui";
import { PriorityTag } from "@/components/shared/PriorityTag";
import { RefChip } from "@/components/shared/RefChip";
import { Time } from "@/components/shared/Time";
import { cn } from "@/lib/cx";

type Row = components["schemas"]["QueueRow"];
export interface LiveRowProps {
  row: Row;
  onOpen(reference: string): void;
  onClaimAndJoin?(reference: string): void;
  pending?: boolean;
  compact?: boolean;
  selected?: boolean;
}

/** A customer waiting in the chat. The shared QueueRow would print "No due time: safety" here, so this row is its own. */
export function LiveRow({ row, onOpen, onClaimAndJoin, pending, compact, selected }: LiveRowProps) {
  return (
    <li className="flex flex-wrap items-stretch gap-2">
      <button
        type="button"
        aria-current={selected ? "true" : undefined}
        onClick={() => onOpen(row.reference)}
        className={cn(
          "motion-control flex min-h-[var(--target-min)] min-w-0 flex-1 flex-col gap-1 rounded-control border px-[9px] py-2 text-left text-ui",
          selected ? "border-[color:var(--qrow-selected-edge)] bg-[var(--qrow-selected-bg)]" : "border-transparent [--hover-base:var(--color-surface-rail)] hover-mix",
        )}
      >
        <span className="flex items-center gap-2">
          <span className="font-semibold">{row.reason}</span>
          <PriorityTag priority={row.priority} />
        </span>
        <span className="flex flex-wrap items-center gap-x-1 text-time-meta text-text-muted">
          <span>{row.customer_display_name}</span>
          <span>{"·"}</span>
          <RefChip reference={row.reference} />
          <span>{"·"}</span>
          <span>Waiting since <Time iso={row.queued_at} format="point" variant="meta" fallback={(row.age_label ?? "").replace(/^Waiting since /, "")} /></span>
        </span>
      </button>
      {!compact ? (
        <Button
          variant="secondary"
          density="console"
          aria-label={`Claim and join ${row.reference}`}
          loading={pending}
          onClick={() => onClaimAndJoin?.(row.reference)}
        >
          Claim and join
        </Button>
      ) : null}
    </li>
  );
}
