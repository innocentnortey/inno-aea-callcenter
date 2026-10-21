export const STALE_AFTER_MS = 120_000;
export function dataAgeMinutes(asOfIso: string, nowMs: number): number {
  return Math.max(0, Math.floor((nowMs - Date.parse(asOfIso)) / 60_000));
}
export function staleLine(asOfIso: string, nowMs: number): string | null {
  if (nowMs - Date.parse(asOfIso) <= STALE_AFTER_MS) return null;
  const n = dataAgeMinutes(asOfIso, nowMs);
  return `This data is ${n} ${n === 1 ? "minute" : "minutes"} old.`;
}
