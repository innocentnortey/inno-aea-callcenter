import { cn } from "@/lib/cx";
import {
  formatClockLabel, formatDateTimeShort, formatDayShort, formatSentence, formatStaffTime, formatTimePoint,
  formatTimeRangeArrow, formatTimeRange,
} from "@/lib/time";

export type TimeFormat = "point" | "short" | "staff" | "day" | "sentence" | "clock";
export type TimeVariant = "hero" | "due" | "row" | "meta";
const FORMATTERS: Record<TimeFormat, (iso: string) => string> = {
  point: formatTimePoint, short: formatDateTimeShort, staff: formatStaffTime, day: formatDayShort, sentence: formatSentence, clock: formatClockLabel,
};
const VARIANT_CLASS: Record<TimeVariant, string> = { hero: "t-time-hero", due: "t-time-due", row: "t-time-row", meta: "t-time-meta" };

export interface TimeProps { iso: string | null; format: TimeFormat; variant?: TimeVariant; fallback?: string; className?: string }
/** A <time datetime> in 12-hour demo time. Never uppercase. */
export function Time({ iso, format, variant, fallback = "", className }: TimeProps) {
  if (!iso) return fallback ? <span className={cn(variant && VARIANT_CLASS[variant], className)}>{fallback}</span> : null;
  return (
    <time dateTime={iso} className={cn(variant && VARIANT_CLASS[variant], className)}>
      {FORMATTERS[format](iso)}
    </time>
  );
}

export interface TimeWindowProps { startIso: string; endIso: string; arrow?: boolean; variant?: TimeVariant; className?: string }
export function TimeWindow({ startIso, endIso, arrow, variant, className }: TimeWindowProps) {
  const cls = cn(variant && VARIANT_CLASS[variant], className);
  if (arrow) {
    return (
      <span className={cls}>
        <time dateTime={startIso}>{formatTimePoint(startIso)}</time>
        <span aria-hidden="true"> {"→"} </span>
        <span className="sr-only"> to </span>
        <time dateTime={endIso}>{formatTimePoint(endIso)}</time>
        <span className="sr-only">{formatTimeRangeArrow(startIso, endIso)}</span>
      </span>
    );
  }
  return (
    <span className={cls}>
      <time dateTime={startIso}>{formatTimePoint(startIso)}</time>
      {" – "}
      <time dateTime={endIso}>{formatTimePoint(endIso)}</time>
      <span className="sr-only">{formatTimeRange(startIso, endIso)}</span>
    </span>
  );
}
