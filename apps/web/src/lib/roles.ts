export type Role = "customer" | "representative" | "supervisor" | "owner";
export const ROLES: readonly Role[] = ["customer", "representative", "supervisor", "owner"];
export const ROLE_LABEL: Record<Role, { short: string; phone: string; full: string }> = {
  customer: { short: "Customer", phone: "Customer", full: "Customer (demo)" },
  representative: { short: "Representative", phone: "Rep", full: "Riley, demo representative" },
  supervisor: { short: "Supervisor", phone: "Supervisor", full: "Demo supervisor" },
  owner: { short: "Owner", phone: "Owner", full: "Demo business owner" },
}; // runtime display names still come from getSession / listDemoRoles; these are the phone/short labels and test fallbacks
export const HOME_BY_ROLE: Record<Role, string> = {
  customer: "/",
  representative: "/staff/queue",
  supervisor: "/staff/oversight",
  owner: "/staff/owner",
};
export const STAY_ON_ROLE_CHANGE: readonly string[] = ["/demo/inbox", "/demo", "/monitoring", "/eval"];
export const CONSOLE_NAV: Record<Exclude<Role, "customer">, { label: string; to: string }[]> = {
  representative: [{ label: "Queue", to: "/staff/queue" }, { label: "Review list", to: "/staff/flags" }],
  supervisor: [{ label: "Oversight", to: "/staff/oversight" }, { label: "Review list", to: "/staff/flags" }, { label: "Queue", to: "/staff/queue" }],
  owner: [{ label: "Outcomes", to: "/staff/owner" }, { label: "Review list", to: "/staff/flags" }],
}; // owner's nav is a decision of the foundation plan (IA gives none)
