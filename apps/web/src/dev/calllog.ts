export interface CallEntry { t: number; op: string; method: string; path: string; status: number; example: string | null; ms: number; drift: string | null }
const MAX = 200;
let entries: CallEntry[] = [];
const subs = new Set<() => void>();
export function logCall(e: CallEntry): void {
  entries = [...entries, e].slice(-MAX);
  subs.forEach((cb) => cb());
}
export function calls(): CallEntry[] { return entries; }
export function clearCalls(): void { entries = []; subs.forEach((cb) => cb()); }
export function subscribeCalls(cb: () => void): () => void { subs.add(cb); return () => void subs.delete(cb); }
export function countsByOp(): Record<string, number> {
  const out: Record<string, number> = {};
  for (const e of entries) out[e.op] = (out[e.op] ?? 0) + 1;
  return out;
}
