import type { ApiError } from "@/api/errors";

export function pluralize(n: number, one: string, many: string): string {
  return n === 1 ? one : many;
}
export function formatShare(value: number | null): string {
  return value == null ? "—" : `${Math.round(value * 100)}%`;
}
export function formatCount(n: number | null): string {
  return n == null ? "—" : String(n);
}
export function nOfN(numerator: number | null, denominator: number | null, noun: string): string {
  if (denominator == null) return "—";
  if (denominator === 0) return `0 ${noun}`;
  return `${numerator ?? 0} of ${denominator} ${noun}`;
}
export function formatSeconds(ms: number | null): string {
  return ms == null ? "—" : `${(ms / 1000).toFixed(1)} s`;
}
export function formatCents(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}
export function formatTileValue(t: { value: number | null; unit: string }): string {
  if (t.unit === "ms") return formatSeconds(t.value);
  if (t.unit === "share") return formatShare(t.value);
  return formatCount(t.value);
}
/** "2026-10-20" -> noon Chicago time, which keeps the same calendar date in CDT and CST. */
export function dateOnlyToIso(date: string): string {
  return `${date}T12:00:00-05:00`;
}
export function readErrorText(err: ApiError | undefined, didntLoad: string): string {
  if (err?.code === "RESET_IN_PROGRESS") return "The demo is resetting. Try again in a few seconds.";
  if (err?.code === "REQUEST_RATE_LIMITED") return "Try again in a moment.";
  return didntLoad;
}
