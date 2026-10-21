import { expect, it } from "vitest";
import { realStates } from "@/screens/matrix";
import { SCENARIO_FILES } from "./scenarios";

// A group flips `complete: true` in its final commit; until then the file is skipped so the foundation suite passes with stubs.
for (const file of SCENARIO_FILES.filter((f) => f.slug !== "shared")) {
  const run = file.screenScenarios.complete === true ? it : it.skip;
  run(`${file.slug} covers every real standard state of ${file.screens.join(", ")}`, () => {
    for (const screen of file.screens) {
      for (const state of realStates(screen)) {
        const have = file.screenScenarios.scenarios.filter((s) => s.screen === screen && s.state === state);
        expect(have.length, `${screen} ${state}`).toBeGreaterThan(0);
      }
    }
  });
}
it("shared scenarios exist", () => {
  expect(SCENARIO_FILES.find((f) => f.slug === "shared")!.screenScenarios.scenarios.length).toBeGreaterThanOrEqual(6);
});
