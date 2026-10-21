import type { components } from "@/api/types.gen";

type QueueRow = components["schemas"]["QueueRow"];
type QueueResponse = components["schemas"]["QueueResponse"];

export function rowSignature(r: QueueRow): string {
  return JSON.stringify([r.reference, r.priority.level, r.owner, r.lifecycle, r.due_at, r.due_state, r.wake_up_at, r.brief_status, r.follow_up_short, r.queued_at]);
}
function index(q: QueueResponse): Map<string, string> {
  return new Map([...q.live, ...q.needs_my_action].map((r) => [r.reference, rowSignature(r)]));
}
/** Rows added, removed or changed between two reads. as_of and age_label change on every read and are ignored. */
export function countChangedRows(shown: QueueResponse, fresh: QueueResponse): number {
  const a = index(shown);
  const b = index(fresh);
  let n = 0;
  for (const [ref, sig] of a) if (!b.has(ref) || b.get(ref) !== sig) n++;
  for (const ref of b.keys()) if (!a.has(ref)) n++;
  return n;
}
