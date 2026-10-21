import type { OperationId, Role } from "@/api/client";
import { ROLES } from "@/lib/roles";
import type { components } from "@/api/types.gen";
import type { OpForce } from "./scenarios/types";

export interface World {
  signedIn: boolean; role: Role; sessionBody: components["schemas"]["SessionInfo"] | null; // body of the last login/switchRole (for getSession)
  staffing: "nobody_online" | "simulated_on_shift";
  expireNext: boolean; refuseNextLogin: boolean; roleResetPending: boolean;
  delayMs: number | "hang" | 0; // global; per-op OpForce wins
  forces: Partial<Record<OperationId, OpForce>>; // current forces (sequences carry a cursor inside the store, not the force)
  scenarioId: string | null;
}

const KEY = "mhc.dev.world";
function fresh(): World {
  return {
    signedIn: false, role: "customer", sessionBody: null, staffing: "nobody_online",
    expireNext: false, refuseNextLogin: false, roleResetPending: false, delayMs: 0, forces: {}, scenarioId: null,
  };
}
// Forces can hold functions (transform), so only the JSON-safe parts are persisted.
function persistable(w: World): unknown {
  const forces = Object.fromEntries(Object.entries(w.forces).filter(([, f]) => f && !("transform" in f)));
  return { ...w, forces };
}
function load(): World {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (raw) return { ...fresh(), ...(JSON.parse(raw) as Partial<World>) };
  } catch { /* unreadable: start fresh */ }
  return fresh();
}

let world: World = load();
const subs = new Set<() => void>();
const cursors = new Map<OperationId, number>();

export function getWorld(): World { return world; }
export function setWorld(patch: Partial<World>): void {
  world = { ...world, ...patch };
  if (patch.forces) cursors.clear();
  try { sessionStorage.setItem(KEY, JSON.stringify(persistable(world))); } catch { /* storage unavailable */ }
  subs.forEach((cb) => cb());
}
export function subscribe(cb: () => void): () => void { subs.add(cb); return () => void subs.delete(cb); }
export function resetWorld(): void { world = fresh(); cursors.clear(); setWorld({}); }

/** The next step of a force.sequence for `op`; the last entry repeats. */
export function takeSequenceStep(op: OperationId): OpForce | undefined {
  const f = world.forces[op];
  if (!f || !("sequence" in f)) return f;
  const i = cursors.get(op) ?? 0;
  cursors.set(op, i + 1);
  return f.sequence[Math.min(i, f.sequence.length - 1)];
}

export interface ParsedParams {
  patch: Partial<World>;
  theme?: "light" | "dark";
  scenario?: string;
}
/** URL params read once at install: ?signedin ?role ?staffing ?ex ?delay ?theme ?scenario. */
export function parseParams(search: string): ParsedParams {
  const q = new URLSearchParams(search);
  const patch: Partial<World> = {};
  const out: ParsedParams = { patch };
  const si = q.get("signedin");
  if (si === "0" || si === "1") patch.signedIn = si === "1";
  const role = q.get("role");
  if (role && (ROLES as readonly string[]).includes(role)) patch.role = role as Role;
  const st = q.get("staffing");
  if (st === "on" || st === "off") patch.staffing = st === "on" ? "simulated_on_shift" : "nobody_online";
  const ex = q.get("ex");
  if (ex) {
    const forces: Partial<Record<OperationId, OpForce>> = {};
    for (const part of ex.split(",")) {
      const [op, rest] = part.split(":");
      if (!op || !rest) continue;
      const m = /^(\d{3})\/(.+)$/.exec(rest);
      forces[op as OperationId] = m ? { example: m[2], status: Number(m[1]) } : { example: rest };
    }
    patch.forces = forces;
  }
  const delay = q.get("delay");
  if (delay === "hang") patch.delayMs = "hang";
  else if (delay && !Number.isNaN(Number(delay))) patch.delayMs = Number(delay);
  const theme = q.get("theme");
  if (theme === "light" || theme === "dark") out.theme = theme;
  const sc = q.get("scenario");
  if (sc) out.scenario = sc;
  return out;
}
