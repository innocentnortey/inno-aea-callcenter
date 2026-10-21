// UNIT (fake transport), G-01: keys OMITTED, not null.
// For each named 2xx example the spec offers, src/test/spec.ts derives variants that delete every nullable or optional key
// one at a time (all array elements at once) and all together. Each variant is rendered through the real screen.
// Asserts: no throw, one h1, no "undefined" / "NaN" / "null" text, the same buttons, and the same visible text as the
// null version of the same body (null is the fallback the existing tests already pin down).
// Bodies come only from the spec's named examples. MOCK-ONLY/UNIT evidence; nothing here ran against a real server.
import { beforeEach, afterEach, describe, expect, it } from "vitest";
import { omittedExampleVariants, type Variant } from "@/test/spec";
import { captureConsoleErrors, expectSensible, shotScreen, TARGETS } from "@/test/readTargets";
import { configure } from "@testing-library/react";
/** Under the full parallel suite the first lazy screen chunk can take longer than the 1 s default. */
configure({ asyncUtilTimeout: 4000 });

/* eslint-disable @typescript-eslint/no-explicit-any -- spec bodies are walked as plain JSON */
beforeEach(() => captureConsoleErrors());
afterEach(() => { sessionStorage.clear(); });

describe("UNIT (fake transport) G-01: screens with keys omitted instead of null", () => {
  for (const t of TARGETS) {
    describe(t.name, () => {
      for (const ex of t.examples) {
        const variants = omittedExampleVariants<any>(t.op, t.status, ex);
        it(`${ex}: has keys to omit`, () => { expect(variants.length).toBeGreaterThan(0); });
        it.each(variants.map((v) => [v.label, v] as [string, Variant<any>]))(`${ex}: %s`, async (_l, v) => {
          const run = (body: unknown) => shotScreen(t.route, t.role, t.op, t.status, body, t.extra, t.before);
          const nulled = v.nulled ? await run(v.nulled) : null;
          const shot = await run(v.body);
          expectSensible(`${t.name} ${ex} ${v.label}`, shot, nulled);
        }, 20_000);
      }
    });
  }
});
