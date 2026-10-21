import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const read = (f: string) => readFileSync(path.resolve(__dirname, f), "utf8");
const tokens = read("tokens.css");
const theme = read("theme.css");
const dark = read("dark.css");
const base = read("base.css");

function section(css: string, marker: string): string {
  const start = css.indexOf(`/* @${marker}`);
  if (start < 0) throw new Error(`no section ${marker}`);
  const next = css.indexOf("/* @", start + 4);
  return css.slice(start, next < 0 ? undefined : next);
}
const count = (s: string, re: RegExp) => (s.match(re) ?? []).length;
const decl = (s: string, name: string) => new RegExp(`${name}:\\s*([^;]+);`).exec(s)?.[1].trim();

describe("token counts (design.md header tally: 179)", () => {
  it("has 30 primitives, 71 component tokens, 15 spacing, 7 lines, 2 elevation, 10 motion", () => {
    expect(count(section(tokens, "primitives"), /^\s+--[a-z0-9-]+:/gm)).toBe(30);
    expect(count(section(tokens, "components"), /^\s+--[a-z0-9-]+:/gm)).toBe(71);
    expect(count(section(tokens, "spacing"), /^\s+--space-/gm)).toBe(15);
    expect(count(section(tokens, "lines"), /^\s+--line-/gm)).toBe(7);
    expect(count(section(tokens, "elevation"), /^\s+--elev-/gm)).toBe(2);
    expect(count(section(tokens, "motion"), /^\s+--(dur|delay|ease)-/gm)).toBe(10);
  });
  it("has 21 semantic colours, 7 radii, 16 type tokens", () => {
    expect(count(section(theme, "semantic"), /^\s+--color-[a-z-]+:/gm)).toBe(21);
    expect(count(section(theme, "radius"), /^\s+--radius-/gm)).toBe(7);
    expect(count(section(theme, "type"), /^\s+--text-(?:(?!--)[a-z-])+:\s/gm)).toBe(16);
  });
  it("totals 179", () => {
    expect(30 + 21 + 71 + 16 + 15 + 7 + 7 + 2 + 10).toBe(179);
  });
});

describe("spot values", () => {
  it("light and dark colours", () => {
    expect(decl(tokens, "--cool-100")).toBe("#E5E9F0");
    expect(decl(theme, "--color-canvas")).toBe("var(--cool-100)");
    expect(decl(tokens, "--night-950")).toBe("#0B0F12");
    expect(decl(dark, "--color-canvas")).toBe("var(--night-950)");
    expect(decl(tokens, "--emerald-700")).toBe("#007847");
    expect(decl(tokens, "--emerald-500")).toBe("#00BC6F");
    expect(decl(theme, "--color-accent")).toBe("var(--emerald-700)");
    expect(decl(dark, "--color-accent")).toBe("var(--emerald-500)");
    expect(decl(tokens, "--red-700")).toBe("#B42318");
    expect(decl(tokens, "--red-600")).toBe("#C8312F");
    expect(decl(theme, "--color-safety")).toBe("var(--red-700)");
    expect(decl(dark, "--color-safety")).toBe("var(--red-600)");
  });
  it("layout tokens", () => {
    expect(decl(tokens, "--panel-width")).toBe("340px");
    expect(decl(tokens, "--col-queue")).toBe("280px");
    expect(decl(tokens, "--col-evidence")).toBe("300px");
  });
  it("dark has both selectors and colour-scheme", () => {
    expect(dark).toContain('@media (prefers-color-scheme: dark)');
    expect(dark).toContain(':root:not([data-theme="light"])');
    expect(dark).toContain(':root[data-theme="dark"]');
    expect(dark).toContain("color-scheme: light dark");
  });
  it("has the motion tokens and reduced-motion opt-in", () => {
    expect(decl(tokens, "--dur-landed-hold")).toBe("640ms");
    expect(base).toContain("prefers-reduced-motion: no-preference");
  });
});
