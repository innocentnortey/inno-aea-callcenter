// Fails when the production build contains the dev layer or an external font host.
import fs from "node:fs";
import path from "node:path";
import { ROOT } from "./paths.mjs";

const dist = path.join(ROOT, "dist");
if (!fs.existsSync(dist)) {
  console.error("dist/ is missing: run npm run build first");
  process.exit(1);
}
const needles = ["__MHC_DEV_LAYER__", "mhc.dev.", "Prototype only", "prototype-synthetic", "fonts.googleapis"];
const hits = [];
function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const f = path.join(dir, e.name);
    if (e.isDirectory()) walk(f);
    else if (/\.(js|css|html)$/.test(e.name)) {
      const text = fs.readFileSync(f, "utf8");
      for (const n of needles) if (text.includes(n)) hits.push(`${path.relative(ROOT, f)}: ${n}`);
    }
  }
}
walk(dist);
if (hits.length) {
  console.error("dev layer leaked into dist:\n" + hits.join("\n"));
  process.exit(1);
}
console.log("dist is clean: no dev-layer markers");
