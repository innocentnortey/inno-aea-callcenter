import { useState } from "react";
import { cn } from "@/lib/cx";
import { useAnnounce } from "@/components/ui/LiveRegion";
import { IconCopy } from "@/components/ui/icons";

export interface RefChipProps { reference: string; copyable?: boolean; className?: string }
export function RefChip({ reference, copyable, className }: RefChipProps) {
  const announce = useAnnounce();
  const [copied, setCopied] = useState(false);
  if (!copyable) return <span className={cn("t-ref", className)}>{reference}</span>;
  return (
    <button
      type="button"
      className={cn("t-ref motion-control inline-flex min-h-[var(--target-min)] items-center gap-1 rounded-control px-1", className)}
      aria-label={`Copy reference ${reference}`}
      onClick={async () => {
        try { await navigator.clipboard?.writeText(reference); } catch { /* clipboard unavailable */ }
        setCopied(true);
        announce("Copied");
      }}
    >
      {reference}
      <IconCopy size={14} strokeWidth={1.8} aria-hidden="true" />
      <span className="sr-only">{copied ? "Copied" : ""}</span>
    </button>
  );
}
