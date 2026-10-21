import { describe, expect, it } from "vitest";
import { safeReturnTo } from "./returnTo";

describe("safeReturnTo", () => {
  it("keeps a same-origin path", () => expect(safeReturnTo("/staff/queue")).toBe("/staff/queue"));
  it("keeps a query string", () => expect(safeReturnTo("/staff/cases/MHC-C-0007?x=1")).toBe("/staff/cases/MHC-C-0007?x=1"));
  it.each(["//evil.com", "https://x", "/\\evil", "", null, undefined, "/a\nb", "/a\tb", "/a\u0000b", "/a\u001fb"])("rejects %j", (v) => {
    expect(safeReturnTo(v as string | null | undefined)).toBe("/");
  });
});
