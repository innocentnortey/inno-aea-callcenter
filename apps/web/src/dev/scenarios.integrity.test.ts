import { describe, expect, it } from "vitest";
import { OPS } from "@/api/client";
import { SCREENS } from "@/routes";
import { MATRIX, STANDARD_STATES } from "./scenarios/matrix";
import { SCENARIO_FILES, allScenarios } from "./scenarios";
import type { OpForce } from "./scenarios/types";

const NA = [
  "SCR-2.partial", "SCR-3.empty", "SCR-3.partial", "SCR-4.empty", "SCR-4.partial", "SCR-7.partial", "SCR-8.partial",
  "SCR-9.success", "SCR-10.success", "SCR-10.disabled", "SCR-11.success", "SCR-11.disabled", "SCR-12.empty", "SCR-12.partial",
];
const cells = Object.entries(MATRIX).flatMap(([id, row]) => STANDARD_STATES.map((s) => ({ key: `${id}.${s}`, cell: row[s] })));

describe("state matrix", () => {
  it("has 96 cells, 82 real and the 14 n/a ones from the spec", () => {
    expect(cells).toHaveLength(96);
    expect(cells.filter((c) => c.cell.real)).toHaveLength(82);
    expect(cells.filter((c) => !c.cell.real).map((c) => c.key).sort()).toEqual([...NA].sort());
  });
  it("every n/a cell has a reason", () => {
    for (const c of cells) if (!c.cell.real) expect(c.cell.reason.startsWith("n/a:")).toBe(true);
  });
});

function pathRegex(path: string) { return new RegExp("^" + path.replace(/:[^/]+/g, "[^/]+") + "/?$"); }
function forcesOf(f: OpForce): OpForce[] { return "sequence" in f ? f.sequence.flatMap(forcesOf) : [f]; }

describe("scenarios", () => {
  const all = allScenarios();
  it("ids are unique", () => expect(new Set(all.map((s) => s.id)).size).toBe(all.length));
  for (const file of SCENARIO_FILES) {
    for (const s of file.screenScenarios.scenarios) {
      it(`${s.id} is well formed`, () => {
        expect(s.id.startsWith(file.slug === "shared" ? "shared." : file.slug.replace("-", "")) || s.id.startsWith(file.slug)).toBe(true);
        expect((STANDARD_STATES as readonly string[]).includes(s.state)).toBe(true);
        const def = s.screen === "*" ? null : SCREENS.find((x) => x.id === s.screen);
        if (s.screen !== "*") {
          expect(def).toBeTruthy();
          expect(pathRegex(def!.path).test(s.route.split("?")[0])).toBe(true);
          if (s.role) expect(def!.roles).toContain(s.role);
          const cell = MATRIX[s.screen][s.state];
          expect(cell.real).toBe(true);
        } else expect(SCREENS.some((x) => pathRegex(x.path).test(s.route.split("?")[0]))).toBe(true);
        for (const [op, force] of Object.entries(s.ops ?? {})) {
          expect(OPS).toHaveProperty(op);
          for (const f of forcesOf(force!)) {
            if ("example" in f) {
              const names = OPS[op as keyof typeof OPS].responses.flatMap((r) => r.examples);
              expect(names).toContain(f.example);
            }
          }
        }
      });
    }
  }
});
