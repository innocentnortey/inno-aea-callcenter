// Pure: decides how one API call is answered in mock mode. Numbered steps are the precedence (first match wins).
import type { OpMeta, OperationId } from "@/api/client";
import type { CallContext } from "@/api/transport";
import type { DefaultMap } from "./defaults";
import type { OpForce } from "./scenarios/types";
import { CASE_OPS, pickCaseCall, pickTurnExample } from "./directors";
import type { World } from "./world";

export type Resolution = (
  | { kind: "short-circuit"; response: { status: number; body?: unknown } } // answered without Prism
  | { kind: "prism"; prefer: string; delayMs: number; transform?: (b: any) => any } // eslint-disable-line @typescript-eslint/no-explicit-any
  | { kind: "network-fail"; delayMs: number }
  | { kind: "hang" }
) & { effects?: Partial<World> };

/** The HTTP status that carries `example` for this op; `status` disambiguates a name under two statuses. */
export function statusOfExample(meta: OpMeta, example: string, status?: number): number {
  if (status) return status;
  return meta.responses.find((r) => r.examples.includes(example))?.status ?? 200;
}
/** The `{reference}` path parameter of this call's concrete URL, or null. */
export function referenceOf(ctx: CallContext, meta: OpMeta): string | null {
  if (!meta.path.includes("{reference}")) return null;
  const esc = meta.path.replace(/[.*+?^$()|[\]\\]/g, "\\$&").replace(/\{[^}]+\}/g, (m) => (m === "{reference}" ? "([^/?#]+)" : "[^/?#]+"));
  const m = new RegExp(`${esc}(?:[?#]|$)`).exec(ctx.path);
  if (!m) return null;
  try { return decodeURIComponent(m[1]); } catch { return m[1]; }
}
const prefer = (status: number, example: string) => `code=${status}, example=${example}`;

export function resolveCall(
  ctx: CallContext,
  meta: OpMeta,
  world: World,
  defaults: DefaultMap,
  takeSequenceStep: (op: OperationId) => OpForce | undefined,
): Resolution {
  const op = ctx.op;
  const forced: OpForce | undefined = world.forces[op];
  const step = forced && "sequence" in forced ? takeSequenceStep(op) : forced;
  const delayOf = (f?: OpForce) => (f && "delayMs" in f && f.delayMs !== undefined ? f.delayMs : typeof world.delayMs === "number" ? world.delayMs : 0);

  // 1. login
  if (op === "login") {
    if (world.refuseNextLogin) return { kind: "prism", prefer: prefer(401, "LOGIN_FAILED"), delayMs: delayOf(step), effects: { refuseNextLogin: false } };
    return { kind: "prism", prefer: prefer(200, "LOGGED_IN"), delayMs: delayOf(step) };
  }
  // 2. signed out / expired
  if (meta.auth && !world.signedIn) return { kind: "prism", prefer: prefer(401, "UNAUTHENTICATED"), delayMs: 0 };
  if (meta.auth && world.expireNext) return { kind: "prism", prefer: prefer(401, "UNAUTHENTICATED_EXPIRED"), delayMs: 0, effects: { signedIn: false, expireNext: false } };
  // 3. an explicit force
  if (step) {
    if ("hang" in step) return { kind: "hang" };
    if ("fail" in step) return { kind: "network-fail", delayMs: step.delayMs ?? 0 };
    if ("example" in step) {
      return { kind: "prism", prefer: prefer(statusOfExample(meta, step.example, step.status), step.example), delayMs: delayOf(step), transform: step.transform };
    }
  }
  if (world.delayMs === "hang") return { kind: "hang" };
  // 4. role emulation
  if (!meta.roles.includes(world.role)) {
    if (world.roleResetPending) return { kind: "prism", prefer: prefer(403, "ROLE_NOT_ALLOWED_ROLE_RESET"), delayMs: delayOf(), effects: { roleResetPending: false } };
    return { kind: "prism", prefer: prefer(403, "ROLE_NOT_ALLOWED"), delayMs: delayOf() };
  }
  // 5. getSession from the last login/switchRole body
  if (op === "getSession" && world.sessionBody) return { kind: "short-circuit", response: { status: 200, body: world.sessionBody } };
  // 5b. switchRole answers with the example for the role asked for (nothing invented: the spec's own TO_* bodies)
  if (op === "switchRole") {
    const role = (ctx.body as { role?: string } | undefined)?.role ?? "customer";
    return { kind: "prism", prefer: prefer(200, `TO_${role.toUpperCase()}`), delayMs: delayOf() };
  }
  // 6. the chat director picks the submitTurn example
  if (op === "submitTurn") {
    const name = pickTurnExample(ctx.body as never, { world });
    return { kind: "prism", prefer: prefer(statusOfExample(meta, name), name), delayMs: delayOf() };
  }
  // 6b. the case director (G4) picks getQueue/getCase/applyCaseAction/liveChatAction/recordContactActivity; no explicit force reaches here
  if (CASE_OPS.includes(op)) {
    const pick = pickCaseCall({ op, reference: referenceOf(ctx, meta), body: ctx.body, world });
    if (pick) return { kind: "prism", prefer: prefer(statusOfExample(meta, pick.example, pick.status), pick.example), delayMs: delayOf(), transform: pick.transform };
  }
  // 6c. setStaffing answers with the example for the mode asked for (the spec has only TURNED_ON and TURNED_OFF_WITH_WAITING)
  if (op === "setStaffing") {
    const mode = (ctx.body as { mode?: string } | undefined)?.mode;
    if (mode === "simulated_on_shift" || mode === "nobody_online") {
      const name = mode === "simulated_on_shift" ? "TURNED_ON" : "TURNED_OFF_WITH_WAITING";
      return { kind: "prism", prefer: prefer(statusOfExample(meta, name), name), delayMs: delayOf() };
    }
  }
  // 7. defaults table
  const name = defaults(op, world);
  if (name) return { kind: "prism", prefer: prefer(statusOfExample(meta, name), name), delayMs: delayOf() };
  return { kind: "prism", prefer: "", delayMs: delayOf() };
}
