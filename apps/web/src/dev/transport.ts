import { OPS, type OperationId } from "@/api/client";
import { refetchAll } from "@/api/refetch";
import type { ApiTransport, CallContext } from "@/api/transport";
import { logCall } from "./calllog";
import { defaultExample } from "./defaults";
import { reactions } from "./reactions";
import { resolveCall } from "./resolve";
import type { DevCtx, OpForce } from "./scenarios/types";
import { createDevStreamOpener, emitToStream } from "./stream/dev-stream";
import { getWorld, setWorld, takeSequenceStep } from "./world";

/** Prism flags contract drift in an `sl-violations` header (severity Error) or answers 422 with its own problem type. */
export function detectDrift(res: Response, body: unknown): string | null {
  const v = res.headers.get("sl-violations");
  if (v && /"severity"\s*:\s*"Error"/.test(v)) return v;
  const type = (body as { type?: unknown } | null)?.type;
  if (typeof type === "string" && type.includes("stoplight.io/prism/errors")) return `${type}: ${(body as { detail?: string }).detail ?? ""}`;
  return null;
}

function devCtx(extra: Pick<DevCtx, "response" | "request">): DevCtx {
  return {
    ...extra,
    get world() { return getWorld(); },
    setForce(op: OperationId, force: OpForce | null) {
      const forces = { ...getWorld().forces };
      if (force) forces[op] = force; else delete forces[op];
      setWorld({ forces });
    },
    setRole(role) { setWorld({ role }); },
    setStaffing(mode) { setWorld({ staffing: mode }); },
    emit(thread, event) { emitToStream(thread, event); },
    refetch() { refetchAll(); },
  };
}

function parseExample(prefer: string): string | null {
  return /example=([^,\s]+)/.exec(prefer)?.[1] ?? null;
}

export function wrapTransport(base: ApiTransport): ApiTransport {
  async function devFetch(ctx: CallContext, url: string, init: RequestInit): Promise<Response> {
    const t0 = performance.now();
    const meta = OPS[ctx.op];
    const world = getWorld();
    const r = resolveCall(ctx, meta, world, defaultExample, takeSequenceStep);
    if (r.effects) setWorld(r.effects);
    const wait = (ms: number) => (ms > 0 ? new Promise((res) => setTimeout(res, ms)) : Promise.resolve());

    if (r.kind === "hang") return new Promise<Response>(() => {});
    if (r.kind === "network-fail") {
      await wait(r.delayMs);
      logCall({ t: Date.now(), op: ctx.op, method: ctx.method, path: url, status: 0, example: null, ms: Math.round(performance.now() - t0), drift: null });
      throw new TypeError("Failed to fetch (forced by the dev layer)");
    }
    await wait("delayMs" in r ? r.delayMs : 0);

    let res: Response;
    let example: string | null = null;
    if (r.kind === "short-circuit") {
      res = new Response(JSON.stringify(r.response.body ?? {}), { status: r.response.status, headers: { "Content-Type": "application/json", "X-Request-ID": "dev" } });
    } else {
      example = parseExample(r.prefer);
      const headers = new Headers(init.headers);
      if (r.prefer) headers.set("Prefer", r.prefer);
      res = await base.fetch(ctx, url, { ...init, headers });
    }

    let body: unknown = undefined;
    const isJson = (res.headers.get("content-type") ?? "").includes("json");
    if (isJson) { try { body = await res.clone().json(); } catch { body = undefined; } }
    const drift = r.kind === "prism" ? detectDrift(res, body) : null;
    if (drift) {
      console.error(`[contract drift] ${ctx.op} ${ctx.method} ${url}: ${drift}`);
      logCall({ t: Date.now(), op: ctx.op, method: ctx.method, path: url, status: 599, example, ms: Math.round(performance.now() - t0), drift });
      return new Response(JSON.stringify({ error: { code: "CONTRACT_DRIFT", details: { drift } } }), { status: 599, headers: { "Content-Type": "application/json" } });
    }
    if (r.kind === "prism" && r.transform && isJson && body !== undefined) {
      const next = r.transform(body);
      res = new Response(JSON.stringify(next), { status: res.status, headers: res.headers });
      body = next;
    }
    logCall({ t: Date.now(), op: ctx.op, method: ctx.method, path: url, status: res.status, example, ms: Math.round(performance.now() - t0), drift: null });

    // Reactions run after the response is recorded.
    for (const rx of reactions) {
      if (rx.when.op !== ctx.op) continue;
      if (rx.when.status !== undefined && rx.when.status !== res.status) continue;
      if (rx.when.example !== undefined && rx.when.example !== example) continue;
      rx.then(devCtx({ response: { status: res.status, body }, request: ctx.body }));
    }
    return res;
  }
  return { fetch: devFetch, openStream: createDevStreamOpener(devFetch) };
}
