// All times are shown 12-hour in the demo timezone. Strings are assembled from parts because newer ICU puts
// U+202F before AM/PM and capitalises it.
export const DEMO_TZ = "America/Chicago";

const fmt = (opts: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat("en-US", { timeZone: DEMO_TZ, ...opts });
const F = {
  time: fmt({ hour: "numeric", minute: "2-digit", hour12: true }),
  wdayShort: fmt({ weekday: "short" }),
  wdayLong: fmt({ weekday: "long" }),
  monthShort: fmt({ month: "short" }),
  monthLong: fmt({ month: "long" }),
  day: fmt({ day: "numeric" }),
  year: fmt({ year: "numeric" }),
};
function part(f: Intl.DateTimeFormat, iso: string, type: Intl.DateTimeFormatPartTypes): string {
  return f.formatToParts(new Date(iso)).find((p) => p.type === type)?.value ?? "";
}
export function formatTimePoint(iso: string): string {
  const hour = part(F.time, iso, "hour");
  const minute = part(F.time, iso, "minute");
  const dp = part(F.time, iso, "dayPeriod").toLowerCase();
  return `${hour}:${minute} ${dp}`;
}
export function formatTimeRange(startIso: string, endIso: string): string {
  return `${formatTimePoint(startIso)} – ${formatTimePoint(endIso)}`;
}
export function formatTimeRangeArrow(startIso: string, endIso: string): string {
  return `${formatTimePoint(startIso)} → ${formatTimePoint(endIso)}`;
}
const wShort = (iso: string) => part(F.wdayShort, iso, "weekday");
const mShort = (iso: string) => part(F.monthShort, iso, "month");
const dNum = (iso: string) => part(F.day, iso, "day");
export function formatDateTimeShort(iso: string): string {
  return `${wShort(iso)} ${mShort(iso)} ${dNum(iso)} · ${formatTimePoint(iso)}`;
}
export function formatStaffTime(iso: string): string {
  return `${wShort(iso)} ${formatTimePoint(iso)}`;
}
export function formatDayShort(iso: string): string {
  return `${wShort(iso)} ${mShort(iso)} ${dNum(iso)}`;
}
export function formatDayLong(iso: string): string {
  return `${part(F.wdayLong, iso, "weekday")}, ${part(F.monthLong, iso, "month")} ${dNum(iso)}, ${part(F.year, iso, "year")}`;
}
export function formatSentence(iso: string): string {
  return `${part(F.wdayLong, iso, "weekday")}, ${part(F.monthLong, iso, "month")} ${dNum(iso)}, ${formatTimePoint(iso)}`;
}
export function formatClockLabel(iso: string): string {
  return `${wShort(iso)} ${mShort(iso)} ${dNum(iso)} · ${formatTimePoint(iso)}`;
}
export function formatDemoDate(iso: string): string {
  return `${wShort(iso)} ${mShort(iso)} ${dNum(iso)}, ${part(F.year, iso, "year")} (demo date)`;
}
