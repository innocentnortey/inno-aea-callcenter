// Fails when the committed generated files differ from a fresh generation.
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { ROOT, SPEC, TYPES_OUT, INDEX_OUT } from "./paths.mjs";

const tmp = path.join(ROOT, ".tmp");
fs.mkdirSync(tmp, { recursive: true });
const typesTmp = path.join(tmp, "types.check.ts");
const indexTmp = path.join(tmp, "contract.check.json");
execFileSync("npx", ["openapi-typescript", SPEC, "-o", typesTmp], { cwd: ROOT, stdio: "ignore" });
execFileSync("node", ["scripts/build-contract-index.mjs", "--out", indexTmp], { cwd: ROOT, stdio: "ignore" });
let bad = 0;
for (const [fresh, committed] of [[typesTmp, TYPES_OUT], [indexTmp, INDEX_OUT]]) {
  if (!fs.existsSync(committed) || !fs.readFileSync(fresh).equals(fs.readFileSync(committed))) {
    console.error(`stale generated file: ${path.relative(ROOT, committed)} (run npm run gen:types && npm run examples)`);
    bad++;
  }
}
if (bad) process.exit(1);
console.log("generated files are current");
