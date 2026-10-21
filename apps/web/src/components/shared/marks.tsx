import { cn } from "@/lib/cx";
import { IconTicket } from "@/components/ui/icons";

/** Grey well, hairline, emerald glyph. Never a face. */
export function AssistantMark({ size = 24, className }: { size?: 18 | 24 | 30; className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn("inline-flex shrink-0 items-center justify-center rounded-tag border border-[color:var(--mark-edge)] bg-[var(--mark-bg)] text-[color:var(--mark-glyph)]", className)}
      style={{ width: size, height: size }}
    >
      <IconTicket size={Math.round(size * 0.6)} strokeWidth={1.8} />
    </span>
  );
}

export function PersonDisc({ initial, size = 32, className }: { initial: string; size?: 18 | 32; className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn("inline-flex shrink-0 items-center justify-center rounded-round bg-[var(--disc-person-bg)] font-semibold text-[color:var(--disc-person-text)]", size === 18 ? "text-caption" : "text-ui", className)}
      style={{ width: size, height: size }}
    >
      {initial.slice(0, 1)}
    </span>
  );
}
