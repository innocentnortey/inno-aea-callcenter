import { formatClockLabel } from "@/lib/time";

export const LANES = [
  { key: "p0_p1", title: "P0 and P1" },
  { key: "overdue", title: "Overdue" },
  { key: "due_soon", title: "Due soon" },
  { key: "unowned", title: "Unowned" },
  { key: "stuck_waiting", title: "Stuck waiting" },
] as const;
export type LaneKey = (typeof LANES)[number]["key"];

export const EMPTY_ALL = "Nothing urgent, unowned, due soon, overdue or stuck. Every case has an owner and is on time.";
export const NO_BACK = "To go back to Fri Oct 16, reset the demo.";
export const LOAD_ERROR = "Oversight didn't load. Try again.";
export const CLOCK_ERROR = "The clock didn't move. Try again.";
export const STAFFING_ERROR = "Staffing didn't change. Try again.";
export const REASON_MISSING = "Add a reason to assign this case.";
export const ADVANCE_STEPS = [
  { step: "plus_1h", label: "+1 hour" },
  { step: "plus_4h", label: "+4 hours" },
  { step: "next_business_morning", label: "Next business morning (Mon 7:00 am)" },
] as const;

export const PRIORITY_WORD = { P0: "Safety", P1: "Danger", P2: "Time-sensitive", P3: "Standard", P4: "Routine" } as const;
export type PriorityLevel = keyof typeof PRIORITY_WORD;
export const ASSIGNEES = [
  { value: "riley", label: "Riley (demo)" },
  { value: "supervisor", label: "Demo supervisor" },
] as const;

function overdueSentence(n: number): string {
  if (n === 0) return "No case became overdue.";
  if (n === 1) return "1 case became overdue.";
  return `${n} cases became overdue.`;
}
export function advanceLine(nowIso: string, becameOverdue: number): string {
  return `Demo time is now ${formatClockLabel(nowIso)}. ${overdueSentence(becameOverdue)}`;
}
export function shiftLine(turnedOn: boolean, converted: number): string {
  if (turnedOn) return "Simulated shift is on.";
  if (converted === 0) return "Simulated shift is off.";
  if (converted === 1) return "Shift ended. 1 waiting customer now has the 1-business-day promise.";
  return `Shift ended. ${converted} waiting customers now have the 1-business-day promise.`;
}
export function liveQueueLine(n: number): string {
  if (n === 0) return "No customers waiting in chat.";
  if (n === 1) return "1 customer waiting in chat.";
  return `${n} customers waiting in chat.`;
}
export function reviewListLine(newFlags: number): string {
  if (newFlags === 0) return "Review list · no new flags";
  if (newFlags === 1) return "Review list · 1 new flag";
  return `Review list · ${newFlags} new flags`;
}
