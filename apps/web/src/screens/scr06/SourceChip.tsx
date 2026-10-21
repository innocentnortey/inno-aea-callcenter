import type { components } from "@/api/types.gen";
import { IconDoc, Tag } from "@/components/ui";

type Source = components["schemas"]["CaseSource"];

export function SourceChip({ source, changed, onJump }: { source: Source | undefined; changed: boolean; onJump(id: string): void }) {
  if (!source) return null;
  const isChanged = changed || source.changed_since;
  return (
    <button
      type="button"
      onClick={() => onJump(source.source_id)}
      className="motion-control inline-flex min-h-7 items-center gap-1 rounded-control border border-border-hair bg-surface-well px-2 text-small [--hover-base:var(--color-surface-well)] hover-mix"
    >
      <IconDoc size={14} strokeWidth={1.8} aria-hidden="true" />
      {source.title}
      {isChanged ? <Tag tone="strong" className="py-0">changed</Tag> : null}
    </button>
  );
}
