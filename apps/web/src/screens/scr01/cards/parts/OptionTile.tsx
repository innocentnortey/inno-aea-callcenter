import type { ReactNode } from "react";
import { cn } from "@/lib/cx";
import { IconCheck } from "@/components/ui";

export interface OptionTileProps {
  label: ReactNode;
  accessibleName?: string;
  selected?: boolean;
  disabled?: boolean;
  taken?: boolean;
  tag?: ReactNode;
  onClick(): void;
  className?: string;
}
/** A choice tile. Selected = mint + 2 px emerald edge + check (mint is only ever the customer's own choice). */
export function OptionTile({ label, accessibleName, selected, disabled, taken, tag, onClick, className }: OptionTileProps) {
  const off = disabled || taken;
  return (
    <button
      type="button"
      aria-pressed={selected ?? false}
      aria-label={accessibleName}
      aria-disabled={off || undefined}
      disabled={off}
      onClick={onClick}
      className={cn(
        "motion-control inline-flex min-h-[var(--target-min)] items-center justify-center gap-2 rounded-control border border-[color:var(--tile-edge)] bg-[var(--tile-bg)] px-3 text-ui",
        selected && "border-2 border-[color:var(--tile-selected-edge)] bg-[var(--tile-selected-bg)] font-semibold",
        taken && "bg-[var(--tile-taken-bg)] text-[color:var(--tile-taken-text)]",
        className,
      )}
    >
      {selected ? <IconCheck size={16} strokeWidth={1.8} aria-hidden="true" /> : null}
      <span className={cn(taken && "line-through")}>{label}</span>
      {taken ? <span className="text-caption font-semibold">Taken</span> : null}
      {tag}
    </button>
  );
}
