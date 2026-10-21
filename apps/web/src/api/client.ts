import type { operations, components } from "./types.gen";
import contract from "./contract.gen.json";
import { ApiError, toApiError } from "./errors";
import { getTransport } from "./transport";
import { emitAuthLost, emitRoleDenied } from "./refetch";

export type OperationId = keyof operations;
export type Role = "customer" | "representative" | "supervisor" | "owner";

type Resp<K extends OperationId> = operations[K]["responses"];
type SuccessStatus = 200 | 201 | 204;
type JsonBody<R> = R extends { content: { "application/json": infer B } } ? B : undefined;
/** The body of the success response (200/201/204) of operation K. */
export type OkBody<K extends OperationId> = {
  [S in keyof Resp<K> & SuccessStatus]: JsonBody<Resp<K>[S]>;
}[keyof Resp<K> & SuccessStatus];
type RB<K extends OperationId> = NonNullable<operations[K]["requestBody"]>;
export type ReqBody<K extends OperationId> =
  [RB<K>] extends [never] ? undefined
  : RB<K> extends { content: { "application/json": infer B } }
    ? (operations[K] extends { requestBody: object } ? B : B | undefined)
    : undefined;
export type PathParams<K extends OperationId> =
  operations[K] extends { parameters: { path: infer P } } ? P : undefined;
export type QueryParams<K extends OperationId> =
  operations[K] extends { parameters: { query?: infer Q } } ? Q : undefined;
export type CallArgs<K extends OperationId> =
  (PathParams<K> extends undefined ? { path?: never } : { path: PathParams<K> }) &
  (ReqBody<K> extends undefined ? { body?: never } : { body: ReqBody<K> }) &
  { query?: QueryParams<K>; signal?: AbortSignal };

export interface ParamMeta { name: string; example: string | number | null }
export interface OpMeta {
  con: string; method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"; path: string;
  auth: boolean; stream: boolean; roles: Role[]; success: number[];
  responses: { status: number; examples: string[] }[];
  params: { path: ParamMeta[]; query: ParamMeta[]; header: ParamMeta[] };
  requestExamples: Record<string, unknown>;
}
export const OPS = contract.operations as unknown as Record<OperationId, OpMeta>;
export type ApiErrorBody = components["schemas"]["ApiError"];

interface AnyArgs { path?: Record<string, unknown>; body?: unknown; query?: Record<string, unknown>; signal?: AbortSignal }

function buildUrl(meta: OpMeta, args: AnyArgs): string {
  const url = meta.path.replace(/\{([^}]+)\}/g, (_m, name: string) => {
    const v = args.path?.[name];
    if (v === undefined || v === null || v === "") throw new ApiError(0, "MISSING_PARAM", null, { param: name });
    return encodeURIComponent(String(v));
  });
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(args.query ?? {})) if (v !== undefined && v !== null) qs.set(k, String(v));
  const s = qs.toString();
  return s ? `${url}?${s}` : url;
}

export async function callOp<K extends OperationId>(op: K, args?: CallArgs<K>): Promise<OkBody<K>> {
  const meta = OPS[op];
  const a = (args ?? {}) as AnyArgs;
  const url = buildUrl(meta, a);
  const headers: Record<string, string> = { Accept: "application/json" };
  const hasBody = a.body !== undefined;
  if (hasBody) headers["Content-Type"] = "application/json";
  let res: Response;
  try {
    res = await getTransport().fetch(
      { op, method: meta.method, path: url, body: a.body },
      url,
      { method: meta.method, headers, body: hasBody ? JSON.stringify(a.body) : undefined, credentials: "include", signal: a.signal },
    );
  } catch (e) {
    throw toApiError(e);
  }
  if (res.status === 204) return undefined as OkBody<K>;
  let body: unknown = {};
  try {
    body = await res.json();
  } catch {
    body = {};
  }
  if (res.ok) return body as OkBody<K>;
  const b = body as { error?: { code?: string; details?: Record<string, unknown>; field?: string }; request_id?: string };
  const err = new ApiError(
    res.status,
    b.error?.code ?? "HTTP_" + res.status,
    body,
    b.error?.details ?? null,
    b.request_id ?? res.headers.get("X-Request-ID"),
    b.error?.field ?? null,
  );
  if (op !== "login" && err.isUnauthenticated) emitAuthLost(err.details?.reason === "expired" ? "expired" : "none");
  if (err.isRoleNotAllowed) emitRoleDenied();
  throw err;
}
