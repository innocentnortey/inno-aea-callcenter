import type { components } from "@/api/types.gen";
import { Time } from "@/components/shared/Time";
import { KIND_WORD, OUTCOME_WORD } from "./caseText";

type Activity = components["schemas"]["Activity"];

export function ActivityLog({ activities }: { activities: Activity[] }) {
  const sorted = [...activities].sort((a, b) => Date.parse(b.at) - Date.parse(a.at));
  return (
    <section aria-labelledby="activity-h" className="flex flex-col gap-2">
      <h2 id="activity-h" className="t-section">Activity</h2>
      {sorted.length === 0 ? <p className="text-ui text-text-muted">No activity yet.</p> : (
        <ul className="flex flex-col gap-2">
          {sorted.map((a) => (
            <li key={a.activity_id} className="flex gap-3 text-ui">
              <span className="w-14 shrink-0"><Time iso={a.at} format="point" variant="row" /></span>
              <span>
                {KIND_WORD[a.kind]} {"·"} {OUTCOME_WORD[a.outcome]}
                {a.note ? <> {"·"} {a.note}</> : null}
                {" "}{"·"} <span className="text-text-muted">{a.label}</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
