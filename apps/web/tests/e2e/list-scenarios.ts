// Run: npx vite-node tests/e2e/list-scenarios.ts  -> writes tests/e2e/.gen/scenarios.json
import { writeFileSync } from "node:fs";
import { allScenarios } from "../../src/dev/scenarios";
const list = allScenarios().map((s) => ({ id: s.id, screen: s.screen, route: s.route, state: s.state, role: s.role ?? null, signedIn: s.signedIn ?? null, notes: s.notes ?? "", hang: JSON.stringify(s.ops ?? {}).includes('"hang"') }));
writeFileSync(new URL("./.gen/scenarios.json", import.meta.url), JSON.stringify(list, null, 1));
console.log(list.length);
