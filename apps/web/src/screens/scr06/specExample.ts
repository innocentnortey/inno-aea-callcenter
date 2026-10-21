// Test-only: reads a named example out of the OpenAPI file, so tests quote the contract instead of retyping it.
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import YAML from "yaml";

let doc: any; // eslint-disable-line @typescript-eslint/no-explicit-any
function load() {
  if (!doc) {
    // 5 levels up from apps/web/src/screens/scr06 reach the repo root; string paths, because jsdom replaces URL
    const file = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../../../docs/ux/03-structure/ui-contracts.openapi.yaml");
    doc = YAML.parse(readFileSync(file, "utf8"));
  }
  return doc;
}
export function specExample<T>(p: string, method: "get" | "post", status: string, name: string): T {
  const d = load();
  let r = d.paths[p][method].responses[status];
  if (r.$ref) r = d.components.responses[String(r.$ref).split("/").pop() as string]; // shared responses such as CaseNotFound
  const v = r.content["application/json"].examples[name].value;
  return structuredClone(v) as T;
}
