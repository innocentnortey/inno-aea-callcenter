import { describe, expect, it } from "vitest";
import { LINKS, SCREENS, caseHref } from "./routes";

describe("routes", () => {
  it("has 12 unique screens", () => {
    expect(SCREENS).toHaveLength(12);
    expect(new Set(SCREENS.map((s) => s.id)).size).toBe(12);
    expect(new Set(SCREENS.map((s) => s.path)).size).toBe(12);
    expect(new Set(SCREENS.map((s) => s.slug)).size).toBe(12);
  });
  it("only the login screen is public", () => {
    expect(SCREENS.filter((s) => s.public).map((s) => s.id)).toEqual(["SCR-12"]);
    expect(SCREENS.find((s) => s.id === "SCR-12")?.public).toBe(true);
  });
  it("every link target resolves", () => {
    const ids = new Set(SCREENS.map((s) => s.id as string));
    const literals = new Set(["role-home", "asked-for-else-SCR-1", "previous-else-SCR-5"]);
    for (const l of LINKS) expect(ids.has(l.to) || literals.has(l.to)).toBe(true);
    expect(LINKS.some((l) => l.newTab)).toBe(true);
  });
  it("builds a case href", () => {
    expect(caseHref("MHC-C-0007")).toBe("/staff/cases/MHC-C-0007");
    expect(caseHref("a b")).toBe("/staff/cases/a%20b");
  });
});
