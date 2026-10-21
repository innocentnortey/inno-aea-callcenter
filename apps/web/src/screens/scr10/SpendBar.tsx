import { IconWarning, Tag } from "@/components/ui";
import { formatCents } from "../reads/format";

export function SpendBar({ todayCents, capCents }: { todayCents: number; capCents: number }) {
  const pct = capCents > 0 ? Math.min(100, Math.round((todayCents / capCents) * 100)) : 0;
  return (
    <div className="flex flex-col items-end gap-1">
      <p>{formatCents(todayCents)} of {formatCents(capCents)} daily cap</p>
      <div aria-hidden="true" className="h-2 w-40 rounded-tag border border-border-hair bg-surface-well">
        <div data-testid="spend-fill" className="h-full rounded-tag bg-text" style={{ width: `${pct}%` }} />
      </div>
      <span className="sr-only">Spend today {formatCents(todayCents)} of the {formatCents(capCents)} daily cap, {pct} percent.</span>
      {todayCents >= capCents ? <Tag tone="strong" icon={<IconWarning size={14} strokeWidth={1.8} aria-hidden="true" />}>Cap reached</Tag> : null}
    </div>
  );
}
