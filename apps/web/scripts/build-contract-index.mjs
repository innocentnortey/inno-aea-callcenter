// Builds src/api/contract.gen.json from the OpenAPI file (YAML 1.2 via the `yaml` package: OFF/ON stay strings).
import fs from "node:fs";
import path from "node:path";
import YAML from "yaml";
import { SPEC, INDEX_OUT } from "./paths.mjs";

const ALL = ["customer", "representative", "supervisor", "owner"];
const outFlag = process.argv.indexOf("--out");
const out = outFlag > -1 ? path.resolve(process.argv[outFlag + 1]) : INDEX_OUT;

const doc = YAML.parse(fs.readFileSync(SPEC, "utf8"));

function resolveRef(node) {
  let cur = node;
  let guard = 0;
  while (cur && typeof cur === "object" && typeof cur.$ref === "string" && guard++ < 20) {
    if (!cur.$ref.startsWith("#/")) break;
    cur = cur.$ref.slice(2).split("/").reduce((acc, k) => acc?.[k.replace(/~1/g, "/").replace(/~0/g, "~")], doc);
  }
  return cur;
}
function sortKeys(v) {
  if (Array.isArray(v)) return v.map(sortKeys);
  if (v && typeof v === "object") return Object.fromEntries(Object.keys(v).sort().map((k) => [k, sortKeys(v[k])]));
  return v;
}
const exampleNames = (content, type) => Object.keys(resolveRef(content?.[type])?.examples ?? {});

const operations = {};
for (const [p, item] of Object.entries(doc.paths ?? {})) {
  const shared = (item.parameters ?? []).map(resolveRef);
  for (const method of ["get", "post", "put", "patch", "delete"]) {
    const op = item[method];
    if (!op) continue;
    const params = [...shared, ...(op.parameters ?? []).map(resolveRef)];
    const pick = (where) => params.filter((x) => x.in === where).map((x) => ({ name: x.name, example: x.example ?? null }));
    const responses = [];
    const success = [];
    let stream = false;
    for (const [status, r0] of Object.entries(op.responses ?? {})) {
      const r = resolveRef(r0);
      const code = Number(status);
      if (Number.isNaN(code)) continue;
      const examples = [...exampleNames(r.content, "application/json"), ...exampleNames(r.content, "text/event-stream")];
      if (code >= 200 && code < 300) success.push(code);
      if (code === 200 && r.content?.["text/event-stream"]) stream = true;
      responses.push({ status: code, examples });
    }
    const requestExamples = {};
    const rb = resolveRef(op.requestBody);
    for (const [name, ex] of Object.entries(resolveRef(rb?.content?.["application/json"])?.examples ?? {})) {
      requestExamples[name] = resolveRef(ex)?.value;
    }
    const roles = Array.isArray(op["x-roles"]) ? op["x-roles"].map((e) => String(e).split(/\s+/)[0]) : ALL;
    operations[op.operationId] = {
      con: String(op["x-con"] ?? op["x-contract"] ?? (op.tags ?? [])[0] ?? ""),
      method: method.toUpperCase(),
      path: p,
      auth: !(Array.isArray(op.security) && op.security.length === 0),
      stream,
      roles,
      success,
      responses,
      params: { path: pick("path"), query: pick("query"), header: pick("header") },
      requestExamples,
    };
  }
}
const count = Object.keys(operations).length;
const result = sortKeys({ source: "docs/ux/03-structure/ui-contracts.openapi.yaml", specVersion: doc.info?.version ?? "", operations });
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, JSON.stringify(result, null, 2) + "\n");
console.log(`contract index: ${count} operations`);
if (count !== 30) {
  console.error(`expected 30 operations, found ${count}`);
  process.exit(1);
}
