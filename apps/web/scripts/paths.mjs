import { fileURLToPath } from "node:url";
import path from "node:path";
const here = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(here, "..");
export const SPEC = path.resolve(ROOT, "../../docs/ux/03-structure/ui-contracts.openapi.yaml");
export const TYPES_OUT = path.resolve(ROOT, "src/api/types.gen.ts");
export const INDEX_OUT = path.resolve(ROOT, "src/api/contract.gen.json");
