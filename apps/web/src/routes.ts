import { ROLES, type Role } from "@/lib/roles";

export type ScreenId = "SCR-1" | "SCR-2" | "SCR-3" | "SCR-4" | "SCR-5" | "SCR-6" | "SCR-7" | "SCR-8" | "SCR-9" | "SCR-10" | "SCR-11" | "SCR-12";
export interface ScreenDef {
  id: ScreenId; slug: string; path: string; title: string; roles: Role[];
  frame: "chat" | "console" | "page" | "auth"; public?: boolean; group: "G1" | "G2" | "G3" | "G4" | "G5";
}
export const ALL: Role[] = [...ROLES];
export const SCREENS: ScreenDef[] = [
  { id: "SCR-1", slug: "scr01", path: "/", title: "Customer chat", roles: ALL, frame: "chat", group: "G1" },
  { id: "SCR-2", slug: "scr02", path: "/demo/inbox", title: "Demo delivery inbox", roles: ALL, frame: "page", group: "G3" },
  { id: "SCR-3", slug: "scr03", path: "/demo", title: "Demo guide and controls", roles: ALL, frame: "page", group: "G3" },
  { id: "SCR-4", slug: "scr04", path: "/role", title: "Role switch", roles: ALL, frame: "page", group: "G3" },
  { id: "SCR-5", slug: "scr05", path: "/staff/queue", title: "Representative queue", roles: ["representative", "supervisor"], frame: "console", group: "G4" },
  { id: "SCR-6", slug: "scr06", path: "/staff/cases/:reference", title: "Case view", roles: ["representative", "supervisor", "owner"], frame: "console", group: "G4" },
  { id: "SCR-7", slug: "scr07", path: "/staff/oversight", title: "Supervisor oversight", roles: ["supervisor"], frame: "console", group: "G5" },
  { id: "SCR-8", slug: "scr08", path: "/staff/flags", title: "Review list of flags", roles: ["representative", "supervisor", "owner"], frame: "console", group: "G5" },
  { id: "SCR-9", slug: "scr09", path: "/staff/owner", title: "Business-owner outcomes", roles: ["owner", "supervisor"], frame: "console", group: "G5" },
  { id: "SCR-10", slug: "scr10", path: "/monitoring", title: "Monitoring", roles: ALL, frame: "page", group: "G5" },
  { id: "SCR-11", slug: "scr11", path: "/eval", title: "Evaluation report", roles: ALL, frame: "page", group: "G5" },
  { id: "SCR-12", slug: "scr12", path: "/login", title: "Demo login", roles: ALL, frame: "auth", group: "G3", public: true },
];
export function caseHref(reference: string): string {
  return "/staff/cases/" + encodeURIComponent(reference);
}
export function screenById(id: ScreenId): ScreenDef {
  const s = SCREENS.find((x) => x.id === id);
  if (!s) throw new Error(`unknown screen ${id}`);
  return s;
}

export interface LinkDef { from: string[]; action: string; to: string; newTab?: boolean }
/** IA.md "Cross-screen links". `to` is a ScreenId or one of: role-home, asked-for-else-SCR-1, previous-else-SCR-5. */
export const LINKS: LinkDef[] = [
  { from: ["SCR-1"], action: "Demo guide", to: "SCR-3" },
  { from: ["SCR-1 code card"], action: "Open the demo inbox", to: "SCR-2", newTab: true },
  { from: ["any"], action: "Role switch: Customer", to: "SCR-1" },
  { from: ["any"], action: "Role switch: Representative / Supervisor / Owner", to: "role-home" },
  { from: ["SCR-12"], action: "Sign in", to: "asked-for-else-SCR-1" },
  { from: ["any"], action: "Session ended", to: "SCR-12" },
  { from: ["any"], action: "Sign out", to: "SCR-12" },
  { from: ["SCR-5", "SCR-7", "SCR-8", "SCR-9"], action: "Open a case", to: "SCR-6" },
  { from: ["SCR-9", "SCR-3"], action: "Monitoring", to: "SCR-10" },
  { from: ["SCR-9", "SCR-3"], action: "Evaluation", to: "SCR-11" },
  { from: ["SCR-6"], action: "Back to queue", to: "previous-else-SCR-5" },
];
