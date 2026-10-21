// Sends every operation x every named example to a running Prism mock and checks status and contract violations.
import fs from "node:fs";
import { INDEX_OUT } from "./paths.mjs";

const port = process.env.MOCK_PORT ?? "4019";
const base = `http://127.0.0.1:${port}`;
const idx = JSON.parse(fs.readFileSync(INDEX_OUT, "utf8")).operations;

let total = 0;
const failures = [];
const violation = (res) => /"severity"\s*:\s*"Error"/.test(res.headers.get("sl-violations") ?? "");

function build(op, meta) {
  let path = meta.path;
  for (const p of meta.params.path) path = path.replace(`{${p.name}}`, encodeURIComponent(String(p.example ?? "x")));
  const names = Object.keys(meta.requestExamples);
  const bodyName = op === "submitTurn" ? "TEXT" : names[0];
  const body = bodyName ? meta.requestExamples[bodyName] : undefined;
  return { path, body };
}
async function send(op, meta, headers, body, path) {
  const h = { Accept: "*/*", ...headers };
  if (meta.auth) h.Cookie = "mhc_session=smoke";
  if (body !== undefined) h["Content-Type"] = "application/json";
  return fetch(base + path, { method: meta.method, headers: h, body: body === undefined ? undefined : JSON.stringify(body) });
}

for (const [op, meta] of Object.entries(idx)) {
  const { path, body } = build(op, meta);
  if (meta.stream) {
    total++;
    const res = await send(op, meta, { Prefer: "code=200, example=FRAMES" }, body, path);
    const ct = res.headers.get("content-type") ?? "";
    await res.text();
    if (res.status !== 200 || !ct.includes("text/event-stream")) failures.push(`${op} stream: status ${res.status}, content-type ${ct}`);
    continue;
  }
  for (const r of meta.responses) {
    for (const ex of r.examples) {
      total++;
      const res = await send(op, meta, { Prefer: `code=${r.status}, example=${ex}` }, body, path);
      await res.text();
      if (res.status !== r.status) failures.push(`${op} ${r.status}/${ex}: got ${res.status}`);
      else if (violation(res)) failures.push(`${op} ${r.status}/${ex}: sl-violations ${res.headers.get("sl-violations")}`);
    }
  }
  for (const [name, value] of Object.entries(meta.requestExamples)) {
    total++;
    const res = await send(op, meta, {}, value, path);
    await res.text();
    if (res.status < 200 || res.status >= 300) failures.push(`${op} request example ${name}: got ${res.status}`);
    else if (violation(res)) failures.push(`${op} request example ${name}: sl-violations`);
  }
}
// Informational: what Prism answers when the cookie is missing (the dev layer emulates 401 either way).
try {
  const res = await fetch(`${base}/api/session`);
  console.log(`probe: GET /api/session without a cookie -> ${res.status}`);
} catch (e) {
  console.log(`probe failed: ${e.message}`);
}
console.log(`${total} requests, ${failures.length} failures`);
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
