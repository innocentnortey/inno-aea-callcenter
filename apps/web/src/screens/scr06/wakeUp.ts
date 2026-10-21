const TZ = "America/Chicago";
function offsetMinutes(ms: number): number {
  const part = new Intl.DateTimeFormat("en-US", { timeZone: TZ, timeZoneName: "longOffset" }).formatToParts(ms).find((p) => p.type === "timeZoneName")?.value ?? "GMT";
  const m = /GMT([+-])(\d{1,2}):?(\d{2})?/.exec(part);
  if (!m) return 0;
  const mins = Number(m[2]) * 60 + Number(m[3] ?? 0);
  return m[1] === "-" ? -mins : mins;
}
function offsetString(mins: number): string {
  const sign = mins < 0 ? "-" : "+";
  const a = Math.abs(mins);
  return `${sign}${String(Math.floor(a / 60)).padStart(2, "0")}:${String(a % 60).padStart(2, "0")}`;
}
/** `date` is YYYY-MM-DD and `time` HH:mm in the demo time zone; returns an ISO string with the right offset. */
export function toDemoIso(date: string, time: string): string | undefined {
  if (!date || !time) return undefined;
  const wall = `${date}T${time}:00`;
  const guess = Date.parse(wall + "Z");
  if (Number.isNaN(guess)) return undefined;
  const off = offsetMinutes(guess - offsetMinutes(guess) * 60000);
  return wall + offsetString(off);
}
/** The demo-zone calendar date (YYYY-MM-DD) of an ISO instant, for a date input's `min`. */
export function demoDate(iso: string): string {
  const p = new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(iso));
  return p;
}
export const TIME_OPTIONS: { value: string; label: string }[] = Array.from({ length: 29 }, (_, i) => {
  const mins = 6 * 60 + i * 30;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return {
    value: `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`,
    label: `${h % 12 || 12}:${String(m).padStart(2, "0")} ${h >= 12 ? "pm" : "am"}`,
  };
});
