import { parse } from "yaml";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { OkBody, OperationId } from "@/api/client";

type Json = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any -- walking an untyped YAML document
// Vite refuses `?raw` for a file outside the project root, so the spec is read with node:fs (tests run in node).
const SPEC_PATH = resolve(process.cwd(), "../../docs/ux/03-structure/ui-contracts.openapi.yaml"); // vitest runs from apps/web
let spec: Json | null = null;

/** Returns a deep copy of a named response example from the OpenAPI file, so tests never hand-copy a body. */
export function specExample<K extends OperationId>(op: K, name: string, status = 200): OkBody<K> {
  spec ??= parse(readFileSync(SPEC_PATH, "utf8")) as Json;
  for (const methods of Object.values(spec.paths as Json)) {
    for (const operation of Object.values(methods as Json)) {
      if ((operation as Json)?.operationId !== op) continue;
      const ex = (operation as Json).responses?.[String(status)]?.content?.["application/json"]?.examples?.[name];
      if (ex) return structuredClone(ex.value) as OkBody<K>;
    }
  }
  throw new Error(`no example ${op}/${status}/${name}`);
}
