import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const SRC = path.resolve(__dirname, "..");
function walk(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const f = path.join(dir, e.name);
    return e.isDirectory() ? walk(f) : /\.(ts|tsx|css)$/.test(e.name) ? [f] : [];
  });
}
const files = walk(SRC).map((f) => ({ rel: path.relative(path.resolve(SRC, ".."), f).split(path.sep).join("/"), text: readFileSync(f, "utf8") }));
const isTest = (rel: string) => /\.test\.(ts|tsx)$/.test(rel);
const offenders = (list: typeof files, re: RegExp) => list.filter((f) => re.test(f.text)).map((f) => f.rel);

describe("design guards", () => {
  it("only the safety card reads the safety tokens (F-16)", () => {
    const re = /--color-safety|--color-on-safety|--safety-|--focus-ring-on-safety|radius-sharp|bg-safety|text-safety|border-safety/;
    const list = files.filter((f) => !f.rel.startsWith("src/styles/") && !isTest(f.rel) && !/^src\/screens\/scr01\/cards\/.*[Ss]afety/.test(f.rel));
    expect(offenders(list, re)).toEqual([]);
  });
  it("no hex literals in components or screens (F-17)", () => {
    const list = files.filter((f) => /^src\/(components|screens)\//.test(f.rel) && !isTest(f.rel));
    expect(offenders(list, /#[0-9a-fA-F]{3,8}\b/)).toEqual([]);
  });
  it("no red/amber/orange Tailwind classes in components or screens", () => {
    const list = files.filter((f) => /^src\/(components|screens)\//.test(f.rel) && !isTest(f.rel));
    expect(offenders(list, /\b(?:bg|text|border|ring|fill|stroke)-(?:red|amber|orange)\b|\bred-\d|\bamber\b|\borange\b/)).toEqual([]);
  });
  it("no external font or cdn hosts (F-18)", () => {
    const list = files.filter((f) => !isTest(f.rel));
    expect(offenders(list, /fonts\.googleapis|fonts\.gstatic|cdn\./)).toEqual([]);
  });
  it("Prefer headers and the fake cookie live only in src/dev", () => {
    const list = files.filter((f) => !f.rel.startsWith("src/dev/") && !isTest(f.rel));
    expect(offenders(list, /["']Prefer["']|mhc_session=/)).toEqual([]);
  });
  it("document.cookie is written only in src/dev", () => {
    const list = files.filter((f) => !f.rel.startsWith("src/dev/") && !isTest(f.rel));
    expect(offenders(list, /document\.cookie/)).toEqual([]);
  });
});
