import { defaultTransport } from "@/api/transport";
import { refetchAll } from "@/api/refetch";
import type { Role } from "@/api/client";
import { screenById } from "@/routes";
import { navigateTo } from "./nav";
import { applyRole } from "./session-fake";
import { allScenarios } from "./scenarios";
import { setActiveStreamScript } from "./stream/dev-stream";
import { getWorld, setWorld } from "./world";
import type { World } from "./world";

const PARAM_KEYS = ["signedin", "role", "staffing", "ex", "delay", "scenario"];

/** Writes the world back into the URL so the address reproduces the state; other params are kept. */
export function syncUrl(world: World = getWorld()): void {
  const q = new URLSearchParams(window.location.search);
  PARAM_KEYS.forEach((k) => q.delete(k));
  q.set("signedin", world.signedIn ? "1" : "0");
  if (world.role !== "customer") q.set("role", world.role);
  if (world.staffing === "simulated_on_shift") q.set("staffing", "on");
  const ex = Object.entries(world.forces).flatMap(([op, f]) => (f && "example" in f && !f.transform ? [`${op}:${f.status ? `${f.status}/` : ""}${f.example}`] : []));
  if (ex.length) q.set("ex", ex.join(","));
  if (world.delayMs) q.set("delay", String(world.delayMs));
  if (world.scenarioId) q.set("scenario", world.scenarioId);
  const search = q.toString();
  window.history.replaceState(window.history.state, "", window.location.pathname + (search ? `?${search}` : "") + window.location.hash);
}

export async function applyScenario(id: string): Promise<void> {
  const sc = allScenarios().find((s) => s.id === id);
  if (!sc) { console.error(`[dev] unknown scenario ${id}`); return; }
  const role: Role = sc.role ?? (sc.screen === "*" ? getWorld().role : screenById(sc.screen).roles[0]);
  setWorld({ signedIn: sc.signedIn ?? sc.screen !== "SCR-12", forces: sc.ops ?? {}, staffing: sc.staffing ?? getWorld().staffing, scenarioId: id, expireNext: false });
  await applyRole(defaultTransport, role);
  setActiveStreamScript(sc.stream ?? null);
  syncUrl();
  const url = new URL(sc.route, window.location.origin);
  const q = new URLSearchParams(window.location.search);
  url.search = q.toString();
  navigateTo(url.pathname + url.search);
  refetchAll();
}
