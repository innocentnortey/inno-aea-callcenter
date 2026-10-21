import fs from "node:fs";
import path from "node:path";
import { ROOT } from "./paths.mjs";
const out = path.join(ROOT, "public/fonts/LICENSES");
fs.mkdirSync(out, { recursive: true });
for (const name of ["instrument-sans", "inter", "geist-mono"]) {
  const src = path.join(ROOT, "node_modules/@fontsource", name, "LICENSE");
  fs.copyFileSync(src, path.join(out, `${name}-OFL.txt`));
  console.log(`copied ${name}`);
}
