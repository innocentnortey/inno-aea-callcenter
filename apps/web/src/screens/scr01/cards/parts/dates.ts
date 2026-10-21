import { DEMO_TZ } from "@/lib/time";

const OFFSET_FMT = new Intl.DateTimeFormat("en-US", { timeZone: DEMO_TZ, timeZoneName: "longOffset" });

function offsetAt(utcIso: string): string {
  const name = OFFSET_FMT.formatToParts(new Date(utcIso)).find((p) => p.type === "timeZoneName")?.value ?? "GMT";
  if (name === "GMT") return "+00:00";
  return name.replace("GMT", "");
}

/** "2026-10-21", "08:00" -> "2026-10-21T08:00:00-05:00" (Chicago offset for that date). */
export function chicagoIso(date: string, hhmm: string): string {
  return `${date}T${hhmm}:00${offsetAt(`${date}T${hhmm}:00Z`)}`;
}
/** window "08:00-12:00" */
export function windowIsos(date: string, window: string): { startIso: string; endIso: string } {
  const [s, e] = window.split("-");
  return { startIso: chicagoIso(date, s), endIso: chicagoIso(date, e) };
}
/** Safe input for formatDayShort / formatDayLong (a date-only string would parse as UTC midnight). */
export function dayIso(date: string): string {
  return chicagoIso(date, "12:00");
}
/** "8:00 am – 12:00 pm" -> "8:00 am to 12:00 pm" */
export function spokenWindow(windowLabel: string): string {
  return windowLabel.replace(" – ", " to ");
}
/** "2026-11-01" -> "Nov 1, 2026" */
export function formatMonthDayYear(date: string): string {
  return new Intl.DateTimeFormat("en-US", { timeZone: DEMO_TZ, month: "short", day: "numeric", year: "numeric" }).format(new Date(dayIso(date)));
}
function to24(h: string, m: string, ap: string): string {
  let hour = Number(h) % 12;
  if (ap === "pm") hour += 12;
  return `${String(hour).padStart(2, "0")}:${m}`;
}
/** "8:00 am – 12:00 pm" -> { start: "08:00", end: "12:00" }; null when the label has another shape. */
export function parseWindowLabel(label: string): { start: string; end: string } | null {
  const m = /^(\d{1,2}):(\d{2}) (am|pm) – (\d{1,2}):(\d{2}) (am|pm)$/.exec(label);
  if (!m) return null;
  return { start: to24(m[1], m[2], m[3]), end: to24(m[4], m[5], m[6]) };
}
