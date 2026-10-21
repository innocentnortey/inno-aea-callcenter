// UNIT (fake transport): self-test of the spec helpers in ./spec.ts (strict checker, keys-omitted variants, error examples).
// MOCK-ONLY/UNIT: proves the helper against the OpenAPI file; says nothing about a real server.
import { describe, expect, it } from "vitest";
import { OPS, type OperationId } from "@/api/client";
import {
  allErrorCodes, deleteAt, errorCodesOf, omissiblePatterns, omittedExampleVariants, requestExamples, requestOps, requestSchema,
  responseExamples, spec, specError, successSchema, violations, violationsLoose,
} from "./spec";

const ops = Object.keys(OPS) as OperationId[];

describe("UNIT (fake transport): spec helpers", () => {
  it("every named 2xx example validates against its own response schema (checker self-test)", () => {
    let n = 0;
    for (const op of ops) {
      for (const s of OPS[op].success) {
        const schema = successSchema(op, s);
        if (!schema) continue;
        for (const [name, body] of Object.entries(responseExamples(op, s))) {
          expect(violationsLoose(schema, body), `${op}/${s}/${name}`).toEqual([]);
          n++;
        }
      }
    }
    expect(n).toBeGreaterThan(100);
  });

  it("every named error example validates against ApiError", () => {
    const apiError = spec().components.schemas.ApiError;
    let n = 0;
    for (const op of ops) {
      for (const r of OPS[op].responses.filter((x) => x.status >= 400)) {
        for (const [name, body] of Object.entries(responseExamples(op, r.status))) {
          expect(violationsLoose(apiError, body), `${op}/${r.status}/${name}`).toEqual([]);
          n++;
        }
      }
    }
    expect(n).toBeGreaterThan(60);
  });

  it("every named request example is accepted by the strict checker", () => {
    for (const op of requestOps()) {
      for (const [name, body] of Object.entries(requestExamples(op))) expect(violations(requestSchema(op), body), `${op}/${name}`).toEqual([]);
    }
  });

  it("the strict checker rejects an extra key, a wrong type, a missing key and a bad enum", () => {
    const schema = requestSchema("setStaffing");
    const good = Object.values(requestExamples("setStaffing"))[0] as Record<string, unknown>;
    expect(violations(schema, good)).toEqual([]);
    expect(violations(schema, { ...good, extra: 1 }).join()).toMatch(/unknown key/);
    expect(violations(schema, {}).join()).toMatch(/required key is missing/);
    expect(violations(schema, { mode: 5 }).join()).toMatch(/expected/);
    const turn = requestSchema("submitTurn");
    expect(violations(turn, { turn_id: "7d3f3a1c-6f4e-4a3b-9c0c-2b1f3c4d5e6f", payload: { kind: "text", text: "hi", extra: true } }).join()).toMatch(/unknown key/);
    expect(violations(turn, { turn_id: "7d3f3a1c-6f4e-4a3b-9c0c-2b1f3c4d5e6f", payload: { kind: "nope" } }).join()).toMatch(/oneOf/);
    expect(violations(turn, { turn_id: "not-a-uuid", payload: { kind: "text", text: "hi" } }).join()).toMatch(/uuid/);
    expect(violations(turn, { turn_id: "7d3f3a1c-6f4e-4a3b-9c0c-2b1f3c4d5e6f", payload: { kind: "text", text: "" } }).join()).toMatch(/shorter/);
  });

  it("omitted variants delete one nullable key at a time and then all of them, and only nullable or optional keys", () => {
    const base = responseExamples("getQueue", 200).SEEDED as { needs_my_action: Record<string, unknown>[] };
    const patterns = omissiblePatterns(successSchema("getQueue", 200), base);
    expect(patterns.map((p) => p.join("."))).toContain("needs_my_action.*.owner");
    const variants = omittedExampleVariants<typeof base>("getQueue", 200, "SEEDED");
    expect(variants.length).toBe(patterns.length + 1);
    const noOwner = variants.find((v) => v.label === "omit needs_my_action.*.owner")!;
    expect(noOwner.body.needs_my_action.every((r) => !("owner" in r))).toBe(true);
    expect(noOwner.body.needs_my_action.every((r) => "reference" in r && "due_state" in r)).toBe(true);
    const all = variants.at(-1)!;
    expect(all.label).toBe("omit all");
    for (const p of patterns) expect(JSON.stringify(deleteAt(all.body, p))).toBe(JSON.stringify(all.body));
    // required non-nullable keys are never deleted
    expect(patterns.map((p) => p.join("."))).not.toContain("needs_my_action");
    expect(all.body.needs_my_action[0]).toBeTruthy();
  });

  it("specError resolves shared responses and the code lists", () => {
    expect(specError("getQueue", 403, "ROLE_NOT_ALLOWED_ROLE_RESET").error.code).toBe("ROLE_NOT_ALLOWED");
    expect(specError("listDemoInbox", 429, "REQUEST_RATE_LIMITED").error.code).toBe("REQUEST_RATE_LIMITED");
    expect(errorCodesOf("applyCaseAction")).toEqual(new Set(["VALIDATION_ERROR", "UNAUTHENTICATED", "ROLE_NOT_ALLOWED", "CASE_NOT_FOUND", "VERSION_CONFLICT", "CASE_ALREADY_CLAIMED", "NOT_ALLOWED_IN_STATE", "REASON_REQUIRED", "WAKE_UP_REQUIRED", "OUTCOME_REQUIRED"]));
    expect(allErrorCodes().has("LOGIN_FAILED")).toBe(true);
  });
});
