// Settled.visit carries "YYYY-MM-DD" and "HH:MM-HH:MM", no ISO instant. No timezone maths here:
// new Date("2026-10-21") formatted in Chicago would show Oct 20.
const WDAY_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const WDAY_LONG = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTH_LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

function dateParts(date: string): { wday: number; month: number; day: number } | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date);
  if (!m) return null;
  const d = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])));
  return { wday: d.getUTCDay(), month: d.getUTCMonth(), day: d.getUTCDate() };
}

export function hhmmTo12h(hhmm: string): string {
  const m = /^(\d{1,2}):(\d{2})$/.exec(hhmm.trim());
  if (!m) return hhmm;
  const h = Number(m[1]);
  const period = h >= 12 ? "pm" : "am";
  const h12 = h % 12 === 0 ? 12 : h % 12;
  return `${h12}:${m[2]} ${period}`;
}
export function formatWindow(window: string, fallbackLabel: string): string {
  const m = /^(\d{1,2}:\d{2})-(\d{1,2}:\d{2})$/.exec(window.trim());
  if (!m) return fallbackLabel;
  return `${hhmmTo12h(m[1])} – ${hhmmTo12h(m[2])}`;
}
export function formatDateOnlyShort(date: string): string {
  const p = dateParts(date);
  return p ? `${WDAY_SHORT[p.wday]} ${MONTH_SHORT[p.month]} ${p.day}` : date;
}
export function formatDateOnlyLong(date: string): string {
  const p = dateParts(date);
  return p ? `${WDAY_LONG[p.wday]}, ${MONTH_LONG[p.month]} ${p.day}` : date;
}
export function visitSentence(date: string, window: string, fallbackLabel: string): string {
  const m = /^(\d{1,2}:\d{2})-(\d{1,2}:\d{2})$/.exec(window.trim());
  const when = m ? `${hhmmTo12h(m[1])} to ${hhmmTo12h(m[2])}` : fallbackLabel;
  return `${formatDateOnlyLong(date)}, ${when}`;
}
