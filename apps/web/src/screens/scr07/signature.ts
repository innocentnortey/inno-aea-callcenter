import type { components } from "@/api/types.gen";
import { LANES } from "./copy";

type OversightResponse = components["schemas"]["OversightResponse"];

/** What the supervisor would notice changing. Excludes as_of, demo_now and age labels, which change on every read. */
export function oversightSignature(o: OversightResponse): string {
  return JSON.stringify({
    a: o.alerts.map((x) => [x.type, x.case_ref, x.line]),
    l: LANES.map(({ key }) => [
      o.lanes[key].count,
      o.lanes[key].rows.map((r) => [r.reference, r.owner, r.priority.level, r.due_state, r.lifecycle]),
    ]),
    q: o.live_queue_length,
    f: o.new_flags_count,
  });
}
