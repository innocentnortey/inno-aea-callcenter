import { cn } from "@/lib/cx";
export interface SkeletonProps { height: number; width?: number | string; rows?: number; className?: string }
/** Static well-coloured blocks at the final height. No shimmer. */
export function Skeleton({ height, width = "100%", rows = 1, className }: SkeletonProps) {
  return (
    <div aria-hidden="true" data-skeleton className={cn("flex flex-col gap-2", className)}>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="rounded-control bg-surface-well" style={{ height, width }} />
      ))}
    </div>
  );
}
