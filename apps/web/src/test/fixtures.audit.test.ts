// UNIT (fake transport), G-05: audit of the HAND-WRITTEN error bodies in the existing tests.
// New tests build error bodies with specError() (src/test/spec.ts), which reads the spec's own error examples. The older
// tests wrote `{ error: { code: "..." } }` by hand. This test cannot rewrite them (existing tests are not edited), so it
// pins the residual: a hand-written body naming a code the spec never lists is a drift risk, and a NEW hand-written body
// anywhere fails here until it is moved to specError(). MOCK-ONLY/UNIT; it says nothing about a real server.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { allErrorCodes } from "./spec";

const SRC = resolve(process.cwd(), "src");
function testFiles(dir: string): string[] {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n);
    return statSync(p).isDirectory() ? testFiles(p) : /\.test\.tsx?$/.test(n) ? [p] : [];
  });
}
const SELF = "test/fixtures.audit.test.ts";
const LITERAL = /error:\s*\{\s*code:\s*"([A-Za-z_0-9]+)"/g;
function literals(): Record<string, string[]> {
  const out: Record<string, string[]> = {};
  for (const f of testFiles(SRC)) {
    const rel = relative(SRC, f).split("\\").join("/");
    if (rel === SELF) continue;
    const codes = [...readFileSync(f, "utf8").matchAll(LITERAL)].map((m) => m[1]);
    if (codes.length) out[rel] = codes;
  }
  return out;
}

/** Existing hand-written bodies, by file. Shrinks as tests move to specError(); never grows. */
const KNOWN_HANDWRITTEN = 29;
/** Codes in those bodies that the spec never lists (client-internal or invented). */
const NOT_IN_SPEC = new Set(["X", "BOOM", "NOT_FOUND", "NETWORK", "MISSING_PARAM"]);

describe("UNIT (fake transport) G-05: hand-written error bodies in the older tests", () => {
  const found = literals();
  const all = Object.values(found).flat();
  const spec = allErrorCodes();
  it("the spec's own error codes are the reference list", () => {
    for (const c of ["UNAUTHENTICATED", "ROLE_NOT_ALLOWED", "VERSION_CONFLICT", "RESET_IN_PROGRESS", "LOGIN_FAILED", "TURN_IN_PROGRESS"]) expect(spec.has(c), c).toBe(true);
  });
  it("no hand-written body names a code outside the spec except the recorded ones", () => {
    const off = new Set(all.filter((c) => !spec.has(c)));
    expect([...off].sort()).toEqual([...NOT_IN_SPEC].filter((c) => off.has(c)).sort());
    for (const c of off) expect(NOT_IN_SPEC.has(c), `new off-spec code ${c}`).toBe(true);
  });
  it("the number of hand-written bodies has not grown (move new ones to specError)", () => {
    expect(all.length).toBeLessThanOrEqual(KNOWN_HANDWRITTEN);
  });
  it("the new G-xx test files contain no hand-written error body", () => {
    for (const f of ["api/transport.stream.test.ts", "api/requests.audit.test.tsx", "state/session.stream.test.tsx", "state/roleDenied.test.tsx", "screens/errors.spec.test.tsx", "screens/omitted.keys.test.tsx", "screens/actions.omitted.test.tsx", "screens/scr01/chat.omitted.test.tsx"]) {
      expect(found[f], f).toBeUndefined();
    }
  });
  it("reports the residual (file -> codes) for the handoff", () => {
    expect(Object.keys(found).length).toBeGreaterThan(0);
  });
});
