// Synthetic bodies quoted from the OpenAPI named examples (docs/ux/03-structure/ui-contracts.openapi.yaml).
import type { components } from "@/api/types.gen";

type SessionInfo = components["schemas"]["SessionInfo"];

/** getSession / login LOGGED_IN example: CUSTOMER */
export const SESSION_CUSTOMER: SessionInfo = {
  authenticated: true,
  role: "customer",
  display_name: "Customer (demo)",
  sees: ["Chat", "Demo guide", "Demo inbox", "Monitoring", "Evaluation"],
  signed_in_at: "2026-10-16T14:00:00-05:00",
};
/** getSession example: REPRESENTATIVE (also switchRole TO_REPRESENTATIVE) */
export const SESSION_REPRESENTATIVE: SessionInfo = {
  authenticated: true,
  role: "representative",
  display_name: "Riley, demo representative",
  sees: ["Queue", "Cases", "Live chat", "Review list"],
  signed_in_at: "2026-10-16T14:00:00-05:00",
};
/** switchRole example TO_SUPERVISOR */
export const SESSION_SUPERVISOR: SessionInfo = {
  authenticated: true,
  role: "supervisor",
  display_name: "Demo supervisor",
  sees: ["Oversight", "Review list", "Queue", "Demo controls"],
  signed_in_at: "2026-10-16T14:00:00-05:00",
};
/** switchRole example TO_OWNER */
export const SESSION_OWNER: SessionInfo = {
  authenticated: true,
  role: "owner",
  display_name: "Demo business owner",
  sees: ["Outcomes", "Cases (read only)"],
  signed_in_at: "2026-10-16T14:00:00-05:00",
};
export const SESSION_BY_ROLE: Record<SessionInfo["role"], SessionInfo> = {
  customer: SESSION_CUSTOMER,
  representative: SESSION_REPRESENTATIVE,
  supervisor: SESSION_SUPERVISOR,
  owner: SESSION_OWNER,
};
/** getStaffing example OFF */
export const STAFFING_OFF: components["schemas"]["Staffing"] = { mode: "nobody_online", label: "Nobody online", banner: null };
/** getStaffing example ON */
export const STAFFING_ON: components["schemas"]["Staffing"] = {
  mode: "simulated_on_shift",
  label: "Simulated staff on shift (demo)",
  banner: "Simulated staffing (demo). No Meridian employee is online.",
};
/** getDemoClock example START */
export const CLOCK_START: components["schemas"]["DemoClock"] = {
  now: "2026-10-16T14:20:00-05:00",
  label: "Fri Oct 16, 2026 · 2:20 pm",
  date_label: "Fri Oct 16, 2026 (demo date)",
};
