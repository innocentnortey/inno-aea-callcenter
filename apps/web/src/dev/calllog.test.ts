import { beforeEach, describe, expect, it } from "vitest";
import { calls, clearCalls, countsByOp, logCall } from "./calllog";

const entry = (i: number) => ({ t: i, op: i % 2 ? "getQueue" : "getCase", method: "GET", path: "/p", status: 200, example: "X", ms: 1, drift: null });
beforeEach(() => clearCalls());

describe("call log", () => {
  it("keeps a ring buffer of 200", () => {
    for (let i = 0; i < 250; i++) logCall(entry(i));
    expect(calls()).toHaveLength(200);
    expect(calls()[0].t).toBe(50);
  });
  it("entries carry the documented fields and counts by op", () => {
    logCall(entry(1)); logCall(entry(2)); logCall(entry(3));
    expect(Object.keys(calls()[0]).sort()).toEqual(["drift", "example", "method", "ms", "op", "path", "status", "t"]);
    expect(countsByOp()).toEqual({ getQueue: 2, getCase: 1 });
  });
  it("is exposed through window.__mhcDev.calls()", () => {
    (window as unknown as { __mhcDev: unknown }).__mhcDev = { calls };
    logCall(entry(1));
    expect((window as unknown as { __mhcDev: { calls(): unknown[] } }).__mhcDev.calls()).toHaveLength(1);
  });
});
