import { type ReactNode } from "react";
import { cn } from "@/lib/cx";
import { IconChevron } from "./icons";

export interface DisclosureProps {
  summary: ReactNode;
  children: ReactNode;
  open?: boolean;
  onOpenChange?(open: boolean): void;
  className?: string;
}
/** Native <details>; the chevron turns 180 degrees in --dur-check (only with motion allowed). */
export function Disclosure({ summary, children, open, onOpenChange, className }: DisclosureProps) {
  return (
    <details
      className={cn("group", className)}
      open={open}
      onToggle={(e) => onOpenChange?.((e.currentTarget as HTMLDetailsElement).open)}
    >
      <summary className="flex min-h-[var(--target-min)] cursor-pointer list-none items-center gap-2 [&::-webkit-details-marker]:hidden">
        <span className="flex-1">{summary}</span>
        <IconChevron className="motion-chevron" size={16} strokeWidth={1.8} aria-hidden="true" />
      </summary>
      <div>{children}</div>
    </details>
  );
}
