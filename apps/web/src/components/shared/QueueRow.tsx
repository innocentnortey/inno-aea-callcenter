import { cn } from "@/lib/cx";
import type { components } from "@/api/types.gen";
import { Tag } from "@/components/ui/Tag";
import { IconClock } from "@/components/ui/icons";
import { formatStaffTime } from "@/lib/time";
import { PriorityTag } from "./PriorityTag";
import { RefChip } from "./RefChip";
import { Time } from "./Time";

type Row = components["schemas"]["QueueRow"];
export interface QueueRowProps {
  row: Row;
  selected?: boolean;
  showStaffTags?: boolean;
  onSelect?(reference: string): void;
  href?: string;
}

/** The accessible name is the visible text itself (WCAG 2.5.3), so there is no aria-label. */
export function QueueRow({ row, selected, showStaffTags = true, onSelect, href }: QueueRowProps) {
  const cls = cn(
    "motion-control grid min-h-[var(--target-min)] w-full grid-cols-[1fr_auto] gap-x-2 rounded-control border px-[9px] py-2 text-left text-ui",
    selected ? "border-[color:var(--qrow-selected-edge)] bg-[var(--qrow-selected-bg)]" : "border-transparent [--hover-base:var(--color-surface-rail)] hover-mix",
  );
  const body = (
    <>
      <span className="font-semibold">{row.reason}</span>
      <span><PriorityTag priority={row.priority} /></span>
      <span className="col-span-2 flex flex-wrap items-center gap-x-1 text-time-meta text-text-muted">
        <span>{row.customer_display_name}</span>
        <span>{"·"}</span>
        <RefChip reference={row.reference} />
        <span>{"·"}</span>
        {row.due_state === "no_due_time" ? <span>No due time: safety</span>
          : row.due_at ? <span>Due <Time iso={row.due_at} format="short" variant="meta" /></span>
          : <span>{row.due_label}</span>}
        {row.due_state === "overdue" ? (
          <Tag tone="strong" icon={<IconClock size={14} strokeWidth={1.8} aria-hidden="true" />}>Overdue</Tag>
        ) : null}
      </span>
      {showStaffTags ? (
        <span className="col-span-2 flex flex-wrap items-center gap-x-1 gap-y-1 text-time-meta text-text-muted">
          <span>{row.owner ?? "Unowned"}</span>
          {row.follow_up_short ? <><span>{"·"}</span><span>{row.follow_up_short}</span></> : null}
          {row.seed ? <Tag>Demo seed</Tag> : null}
          {row.brief_status === "being_written" ? <Tag>Brief being written</Tag> : null}
          {row.lifecycle === "waiting" && row.wake_up_at ? <Tag>Waiting {"·"} wakes {formatStaffTime(row.wake_up_at)}</Tag> : null}
        </span>
      ) : null}
    </>
  );
  return (
    <li>
      {href ? (
        <a href={href} className={cls} aria-current={selected ? "true" : undefined}>{body}</a>
      ) : (
        <button type="button" className={cls} aria-current={selected ? "true" : undefined} onClick={() => onSelect?.(row.reference)}>{body}</button>
      )}
    </li>
  );
}
