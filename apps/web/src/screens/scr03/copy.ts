export const H1 = "How this demo works";
export const REAL = [
  "The assistant and its answers",
  "Meridian's knowledge base",
  "Bookings, written to a working copy of the scheduling database",
  "What you type as Riley",
];
export const SIMULATED = [
  "The date (Fri Oct 16, 2026)",
  "Staffing (nobody is online unless you turn on the simulation)",
  "The one-time code (sent to a demo inbox)",
  "Follow-ups and calls (\"Demo: recorded, not sent\")",
];
export const STEPS = [
  "Keep the chat open in this tab.",
  "Use the role switch at the top to act as Representative (Riley), or open the console in a second tab.",
  "Ask the chat for a person.",
  "Claim and join from the queue, then switch back to Customer to see Riley's reply.",
];
export const SWITCH_LABEL = "Demo: simulate staff on shift";
export const SWITCH_HINT = "The chat will offer a live queue, and the staff console will show it.";
export const CHECKING = "Checking…";
export const READ_ERROR = "Staffing status is unavailable.";
export const WRITE_ERROR = "Staffing didn't change. Try again.";
export const STALE = "Staffing changed since you opened this page.";
export const ON_LINE = "Simulated staff on shift (demo). The banner now shows on the chat and the console.";
export const RESET_TITLE = "Reset the demo?";
export const RESET_BUTTON = "Reset the demo";
export const RESETTING = "Resetting…";
export const CANCEL = "Cancel";
export const RESET_CONSEQUENCE = "This ends every open chat, clears cases made during the demo, restores the seeded cases and sets the date back to Fri Oct 16, 2026.";
export const RESET_DONE = "Demo reset. Bookings, cases and codes are back to the start, and the date is Fri Oct 16, 2026.";
export const RESET_CHATS = " Open chats have ended.";
export const RESET_FAILED = "The reset didn't finish. Nothing was half-reset; try again.";
export const RESET_BUSY = "The demo is resetting. Try again in a few seconds.";
export const ROLE_RESET = "The demo was reset, so you're back to the customer role. Pick a role again.";

export type StaffingMode = "nobody_online" | "simulated_on_shift";

export function staffingSuccessLine(mode: StaffingMode, converted: number): string {
  if (mode === "simulated_on_shift") return ON_LINE;
  if (converted === 1) return "Shift ended. 1 waiting customer now has the 1-business-day promise.";
  if (converted > 1) return `Shift ended. ${converted} waiting customers now have the 1-business-day promise.`;
  return "Shift ended. Nobody is online.";
}

export function resetSuccessLine(openChatsEnded: number, roleWasReset: boolean): string {
  return RESET_DONE + (openChatsEnded > 0 ? RESET_CHATS : "") + (roleWasReset ? ` ${ROLE_RESET}` : "");
}
