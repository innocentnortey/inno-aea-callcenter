// Test-only: the OpenAPI file as data. Loads the document once and exposes (a) named response and error examples by
// operationId, (b) a small strict JSON-Schema checker for request bodies, (c) the walk that finds nullable keys.
// Nothing here edits the spec. Tag: UNIT (fake transport) helper, never evidence about a real server.
import { readFileSync } from "node:fs";
import { resolve as resolvePath } from "node:path";
import YAML from "yaml";
import { OPS, type OperationId } from "@/api/client";

/* eslint-disable @typescript-eslint/no-explicit-any -- raw YAML */
export type Json = any;
let doc: Json | null = null;
export function spec(): Json {
  doc ??= YAML.parse(readFileSync(resolvePath(process.cwd(), "../../docs/ux/03-structure/ui-contracts.openapi.yaml"), "utf8"));
  return doc;
}
const clone = <T,>(v: T): T => structuredClone(v);
export function ref(node: Json): Json {
  let cur = node;
  for (let i = 0; cur && typeof cur.$ref === "string" && i < 20; i++) {
    cur = cur.$ref.slice(2).split("/").reduce((a: Json, k: string) => a?.[k], spec());
  }
  return cur;
}
/** The templated path key in the spec for an operationId. */
export function specPath(op: OperationId): string {
  for (const [p, ms] of Object.entries<Json>(spec().paths)) for (const m of Object.values<Json>(ms)) if (m?.operationId === op) return p;
  throw new Error(`no operation ${op}`);
}
function opNode(op: OperationId): Json {
  for (const ms of Object.values<Json>(spec().paths)) for (const m of Object.values<Json>(ms)) if (m?.operationId === op) return m;
  throw new Error(`no operation ${op}`);
}
/** Every response example of an operation for a status (shared $ref responses resolved), name -> body. */
export function responseExamples(op: OperationId, status: number | string): Record<string, Json> {
  const r = ref(opNode(op).responses?.[String(status)]);
  const ex = ref(r?.content?.["application/json"])?.examples ?? {};
  return Object.fromEntries(Object.entries<Json>(ex).map(([k, v]) => [k, clone(ref(v).value)]));
}
/** A named example body of operation `op` at `status` (2xx, 4xx or 5xx). Throws when the spec has no such example. */
export function specBody<T = Json>(op: OperationId, status: number | string, name: string): T {
  const ex = responseExamples(op, status)[name];
  if (ex === undefined) throw new Error(`no example ${op}/${status}/${name}`);
  return ex as T;
}
/** An error body built from the spec's own error example (resolves shared components.responses such as RoleNotAllowed). */
export function specError(op: OperationId, status: number, name: string): Json {
  return specBody(op, status, name);
}
/** Every error code the spec lists for an operation (any 4xx/5xx example). */
export function errorCodesOf(op: OperationId): Set<string> {
  const out = new Set<string>();
  for (const s of Object.keys(opNode(op).responses ?? {})) {
    if (Number(s) < 400) continue;
    for (const b of Object.values<Json>(responseExamples(op, s))) if (b?.error?.code) out.add(b.error.code);
  }
  return out;
}
export function allErrorCodes(): Set<string> {
  const out = new Set<string>();
  for (const ms of Object.values<Json>(spec().paths)) for (const m of Object.values<Json>(ms)) if (m?.operationId) for (const c of errorCodesOf(m.operationId)) out.add(c);
  return out;
}
/** The text/event-stream FRAMES example of a stream operation (ids 12..14 for chat, 5..6 for case) and its event schema. */
export function streamFrames(op: "streamChatEvents" | "streamCaseEvents"): { text: string; eventSchema: Json } {
  const c = ref(opNode(op).responses["200"]).content["text/event-stream"];
  return { text: c.examples.FRAMES.value as string, eventSchema: c.schema.contentSchema };
}
export function successSchema(op: OperationId, status: number | string): Json {
  const r = ref(opNode(op).responses?.[String(status)]);
  return ref(r?.content?.["application/json"])?.schema;
}
export function requestSchema(op: OperationId): Json | undefined {
  return ref(opNode(op).requestBody)?.content?.["application/json"]?.schema;
}
export function requestExamples(op: OperationId): Record<string, Json> {
  const ex = ref(opNode(op).requestBody)?.content?.["application/json"]?.examples ?? {};
  return Object.fromEntries(Object.entries<Json>(ex).map(([k, v]) => [k, clone(ref(v).value)]));
}
/** Operations that take a JSON request body. */
export function requestOps(): OperationId[] {
  return (Object.keys(OPS) as OperationId[]).filter((o) => requestSchema(o) !== undefined);
}

// ---------------------------------------------------------------------------------------------------------------
// Strict checker. The spec sets no additionalProperties, so a closed object is the audit's choice: a key that no
// `properties` entry (through $ref, allOf and the matching oneOf branch) declares is an error.
const isObj = (v: unknown): v is Record<string, unknown> => typeof v === "object" && v !== null && !Array.isArray(v);
const deepEq = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);
const typeOk = (t: string, v: unknown): boolean =>
  t === "null" ? v === null : t === "string" ? typeof v === "string" : t === "boolean" ? typeof v === "boolean"
  : t === "integer" ? Number.isInteger(v) : t === "number" ? typeof v === "number" : t === "array" ? Array.isArray(v) : t === "object" ? isObj(v) : true;
const FORMAT: Record<string, RegExp> = {
  "date-time": /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(Z|[+-]\d\d:\d\d)$/,
  date: /^\d{4}-\d\d-\d\d$/,
  uuid: /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
};
interface Out { evaluated: Set<string>; declared: boolean }
function check(schema: Json, v: unknown, path: string, errs: string[], closing: boolean): Out {
  const out: Out = { evaluated: new Set(), declared: false };
  const s = ref(schema);
  if (!s || s === true) return out;
  if ("const" in s && !deepEq(s.const, v)) errs.push(`${path}: expected const ${JSON.stringify(s.const)}`);
  if (s.enum && !s.enum.some((e: unknown) => deepEq(e, v))) errs.push(`${path}: ${JSON.stringify(v)} is not in the enum`);
  if (s.type) {
    const ts: string[] = Array.isArray(s.type) ? s.type : [s.type];
    if (!ts.some((t) => typeOk(t, v))) { errs.push(`${path}: expected ${ts.join("|")}, got ${v === null ? "null" : Array.isArray(v) ? "array" : typeof v}`); return out; }
  }
  if (typeof v === "string") {
    if (s.minLength !== undefined && v.length < s.minLength) errs.push(`${path}: shorter than ${s.minLength}`);
    if (s.maxLength !== undefined && v.length > s.maxLength) errs.push(`${path}: longer than ${s.maxLength}`);
    if (s.pattern && !new RegExp(s.pattern).test(v)) errs.push(`${path}: does not match ${s.pattern}`);
    if (s.format && FORMAT[s.format] && !FORMAT[s.format].test(v)) errs.push(`${path}: not a ${s.format}`);
  }
  if (typeof v === "number") {
    if (s.minimum !== undefined && v < s.minimum) errs.push(`${path}: below ${s.minimum}`);
    if (s.maximum !== undefined && v > s.maximum) errs.push(`${path}: above ${s.maximum}`);
  }
  if (Array.isArray(v)) {
    if (s.minItems !== undefined && v.length < s.minItems) errs.push(`${path}: fewer than ${s.minItems} items`);
    if (s.maxItems !== undefined && v.length > s.maxItems) errs.push(`${path}: more than ${s.maxItems} items`);
    if (s.items) v.forEach((x, i) => check(s.items, x, `${path}[${i}]`, errs, true));
  }
  if (isObj(v)) {
    for (const k of s.required ?? []) if (!(k in v)) errs.push(`${path}.${k}: required key is missing`);
    if (s.properties) {
      out.declared = true;
      for (const [k, ps] of Object.entries<Json>(s.properties)) if (k in v) { out.evaluated.add(k); check(ps, v[k], `${path}.${k}`, errs, true); }
    }
  }
  for (const part of s.allOf ?? []) {
    const o = check(part, v, path, errs, false);
    o.evaluated.forEach((k) => out.evaluated.add(k));
    out.declared ||= o.declared;
  }
  if (s.oneOf) {
    const passing: Out[] = [];
    const failures: string[][] = [];
    for (const b of s.oneOf) {
      const e: string[] = [];
      const o = check(b, v, path, e, false);
      if (e.length === 0) passing.push(o); else failures.push(e);
    }
    if (passing.length !== 1) {
      const disc = s.discriminator?.propertyName;
      const pick = disc && isObj(v) ? failures.find((f) => !f.some((m) => m.includes(`.${disc}:`))) : undefined;
      errs.push(`${path}: matches ${passing.length} oneOf branches, expected 1${pick ? " (" + pick.join("; ") + ")" : ""}`);
    }
    for (const o of passing) { o.evaluated.forEach((k) => out.evaluated.add(k)); out.declared ||= o.declared; }
  }
  if (closing && isObj(v) && out.declared) {
    for (const k of Object.keys(v)) if (!out.evaluated.has(k)) errs.push(`${path}.${k}: unknown key (the schema declares no such property)`);
  }
  return out;
}
/** Violations of `schema` by `value`, with unknown keys counted as violations. Empty means valid. */
export function violations(schema: Json, value: unknown, root = "$"): string[] {
  const errs: string[] = [];
  check(schema, value, root, errs, true);
  return errs;
}
/** Same check, but unknown keys allowed (used on the spec's own response examples as a self-test of the checker). */
export function violationsLoose(schema: Json, value: unknown): string[] {
  return violations(schema, value).filter((m) => !m.includes("unknown key"));
}

// ---------------------------------------------------------------------------------------------------------------
// Keys that may be absent: every property whose schema allows null, or that the schema does not list as required.
type Pattern = string[]; // key path; "*" stands for every element of an array
function effective(schema: Json, v: unknown): { props: Record<string, Json>; required: Set<string> } {
  const props: Record<string, Json> = {};
  const required = new Set<string>();
  const visit = (sc: Json) => {
    const s = ref(sc);
    if (!s) return;
    Object.assign(props, s.properties ?? {});
    for (const r of s.required ?? []) required.add(r);
    for (const p of s.allOf ?? []) visit(p);
    if (s.oneOf) for (const b of s.oneOf) { const e: string[] = []; check(b, v, "$", e, false); if (e.length === 0) { visit(b); break; } }
  };
  visit(schema);
  return { props, required };
}
const allowsNull = (sc: Json): boolean => {
  const s = ref(sc);
  if (!s) return false;
  const t = Array.isArray(s.type) ? s.type : [s.type];
  return t.includes("null") || (s.oneOf ?? s.anyOf ?? []).some((b: Json) => allowsNull(b));
};
export interface OmitPattern { path: Pattern; nullable: boolean }
export function omissiblePatterns(schema: Json, value: unknown): Pattern[] {
  return omitPatterns(schema, value).map((p) => p.path);
}
/** Every key of `value` that may be absent, with whether the schema also allows null there. */
export function omitPatterns(schema: Json, value: unknown): OmitPattern[] {
  const found = new Map<string, OmitPattern>();
  const walk = (sc: Json, v: unknown, path: Pattern) => {
    const s = ref(sc);
    if (Array.isArray(v) && s?.items) { for (const x of v) walk(s.items, x, [...path, "*"]); return; }
    if (!isObj(v)) return;
    const { props, required } = effective(sc, v);
    for (const [k, ps] of Object.entries(props)) {
      if (!(k in v)) continue;
      const nullable = allowsNull(ps);
      if (nullable || !required.has(k)) {
        const key = [...path, k].join(".");
        const prev = found.get(key);
        found.set(key, { path: [...path, k], nullable: (prev?.nullable ?? true) && nullable });
      }
      walk(ps, v[k], [...path, k]);
    }
  };
  walk(schema, value, []);
  return [...found.values()];
}
export function deleteAt<T>(body: T, pattern: Pattern): T {
  const out = clone(body);
  const go = (node: unknown, rest: string[]) => {
    if (rest.length === 0 || node === null || typeof node !== "object") return;
    const [k, ...tail] = rest;
    if (k === "*") { if (Array.isArray(node)) node.forEach((x) => go(x, tail)); return; }
    const o = node as Record<string, unknown>;
    if (tail.length === 0) delete o[k]; else go(o[k], tail);
  };
  go(out, pattern);
  return out;
}
/** `nulled` is the same body with the omitted keys set to null instead (only when every omitted key allows null). */
export interface Variant<T> { label: string; body: T; nulled: T | null }
export function setNullAt<T>(body: T, pattern: Pattern): T {
  const out = clone(body);
  const go = (node: unknown, rest: string[]) => {
    if (rest.length === 0 || node === null || typeof node !== "object") return;
    const [k, ...tail] = rest;
    if (k === "*") { if (Array.isArray(node)) node.forEach((x) => go(x, tail)); return; }
    const o = node as Record<string, unknown>;
    if (tail.length === 0) { if (k in o) o[k] = null; } else go(o[k], tail);
  };
  go(out, pattern);
  return out;
}
/**
 * The "keys omitted" variants of a body: every omissible key deleted on its own (all array elements at once, since the
 * server serialises one schema), then every omissible key deleted together. A key the example already lacks is not listed.
 */
export function omittedVariants<T>(schema: Json, body: T): Variant<T>[] {
  const patterns = omitPatterns(schema, body);
  if (patterns.length === 0) return [];
  const mk = (label: string, ps: OmitPattern[]): Variant<T> => {
    let omitted = clone(body);
    let nulled: T | null = ps.every((p) => p.nullable) ? clone(body) : null;
    // deepest first so a parent key removed later does not hide a child
    for (const p of [...ps].sort((x, y) => y.path.length - x.path.length)) {
      omitted = deleteAt(omitted, p.path);
      if (nulled) nulled = setNullAt(nulled, p.path);
    }
    return { label, body: omitted, nulled };
  };
  return [...patterns.map((p) => mk(`omit ${p.path.join(".")}`, [p])), mk("omit all", patterns)];
}
// ---------------------------------------------------------------------------------------------------------------
// Empty arrays: every non-empty array the schema lets be empty (no minItems above 0), emptied one location at a time.
export function emptiablePatterns(schema: Json, value: unknown): Pattern[] {
  const found = new Map<string, Pattern>();
  const walk = (sc: Json, v: unknown, path: Pattern) => {
    const s = ref(sc);
    if (Array.isArray(v)) {
      if (v.length > 0 && !(s?.minItems > 0)) found.set(path.join("."), path);
      if (s?.items) for (const x of v) walk(s.items, x, [...path, "*"]);
      return;
    }
    if (!isObj(v)) return;
    const { props } = effective(sc, v);
    for (const [k, ps] of Object.entries(props)) if (k in v) walk(ps, v[k], [...path, k]);
  };
  walk(schema, value, []);
  return [...found.values()].filter((p) => p.length > 0);
}
function setEmptyAt<T>(body: T, pattern: Pattern): T {
  const out = clone(body);
  const go = (node: unknown, rest: string[]) => {
    if (rest.length === 0 || node === null || typeof node !== "object") return;
    const [k, ...tail] = rest;
    if (k === "*") { if (Array.isArray(node)) node.forEach((x) => go(x, tail)); return; }
    const o = node as Record<string, unknown>;
    if (tail.length === 0) { if (Array.isArray(o[k])) o[k] = []; } else go(o[k], tail);
  };
  go(out, pattern);
  return out;
}
/** One variant per emptiable array location, then all of them together. */
export function emptiedVariants<T>(schema: Json, body: T): { label: string; body: T }[] {
  const patterns = emptiablePatterns(schema, body);
  if (patterns.length === 0) return [];
  let all = clone(body);
  for (const p of [...patterns].sort((a, b) => a.length - b.length)) all = setEmptyAt(all, p); // shallowest first: a parent emptied hides its children
  return [...patterns.map((p) => ({ label: `empty ${p.join(".")}`, body: setEmptyAt(body, p) })), { label: "empty all", body: all }];
}
export function emptiedExampleVariants<T = Json>(op: OperationId, status: number, name: string): { label: string; body: T }[] {
  return emptiedVariants(successSchema(op, status), specBody<T>(op, status, name));
}

/** Variants of a named example of operation `op`. */
export function omittedExampleVariants<T = Json>(op: OperationId, status: number, name: string): Variant<T>[] {
  return omittedVariants(successSchema(op, status), specBody<T>(op, status, name));
}
/* eslint-enable @typescript-eslint/no-explicit-any */
