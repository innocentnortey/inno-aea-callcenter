import { describe, expect, it } from "vitest";
import { resolveDestination } from "./destination";

describe("resolveDestination", () => {
  it.each([
    ["/staff/queue", "/", "/staff/queue"],
    [null, "/", "/"],
    ["//evil.com", "/", "/"],
    ["https://x", "/", "/"],
    ["/login?return_to=%2Fx", "/", "/"],
    ["/\\evil", "/", "/"],
    [undefined, "/staff/owner", "/staff/owner"],
    ["/demo/inbox?x=1", "/", "/demo/inbox?x=1"],
  ] as const)("(%s, %s) gives %s", (returnTo, fallback, expected) => {
    expect(resolveDestination(returnTo, fallback)).toBe(expected);
  });
});
