import { formatStaffTime } from "@/lib/time";
import type { Settled } from "../contract";
import type { Write } from "./model";
import { formatDateOnlyShort, formatWindow, visitSentence } from "./visit";

type Request = NonNullable<Settled["request"]>;
type FollowUp = NonNullable<Request["followup"]>;
export type LandTarget = "visit" | "request" | "identity";

export function stripLine(s: Settled | null, danger: boolean): string {
  if (danger) return "DANGER · Leave the home immediately";
  const parts: string[] = [];
  if (s?.visit) parts.push(`${formatDateOnlyShort(s.visit.date)} · ${formatWindow(s.visit.window, s.visit.window_label)}`);
  if (s?.request) {
    parts.push(s.request.reference);
    if (s.request.due_at) parts.push(`due ${formatStaffTime(s.request.due_at)}`);
  }
  return parts.length ? parts.join(" · ") : "Nothing yet";
}
export function promiseSentence(r: Request): string {
  const label = r.due_label && r.due_label.trim() !== "" ? `, ${r.due_label}` : "";
  return `${r.promise_text}${label}.`;
}
export function followUpLabel(f: FollowUp): string {
  if (f.channel === "email") return "Email";
  const w = { morning: "mornings", afternoon: "afternoons", any: "any time" }[f.window];
  return `Phone · ${w}`;
}
export function identityLine(i: Settled["identity"]): string {
  switch (i.status) {
    case "not_checked": return "Not checked. Only needed for private details.";
    case "code_sent": return `Code sent to ${i.hint ?? "the phone on record"}`;
    case "verified": return i.hint ? `Verified for this chat · ${i.hint}` : "Verified for this chat";
    default: return "I can't confirm your account here. A representative will help."; // not_verified, locked
  }
}
export function landingText(target: LandTarget, s: Settled): string {
  if (target === "visit") return s.visit ? `Your visit: ${visitSentence(s.visit.date, s.visit.window, s.visit.window_label)}` : "Your visit";
  if (target === "request") return s.request ? `Your request: ${promiseSentence(s.request)}` : "Your request";
  return `Identity: ${identityLine(s.identity)}`;
}
export function landingsFromWrites(writes: Write[]): LandTarget[] {
  const out: LandTarget[] = [];
  const add = (t: LandTarget) => { if (!out.includes(t)) out.push(t); };
  for (const w of writes) {
    if (w.kind === "booked" || w.kind === "moved" || w.kind === "cancelled") add("visit");
    else if (w.kind === "change_request_sent") { add("visit"); add("request"); }
    else if (w.kind === "case_opened" || w.kind === "followup_saved") add("request");
    else if (w.kind === "verified") add("identity");
  }
  return out;
}
