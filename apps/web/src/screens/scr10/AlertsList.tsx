import type { components } from "@/api/types.gen";
import { Time } from "@/components/shared/Time";
import { IconWarning, Tag } from "@/components/ui";

type MonitorAlert = components["schemas"]["MonitorAlert"];

export function AlertsList({ alerts }: { alerts: MonitorAlert[] }) {
  const sorted = [...alerts].sort((a, b) => Number(b.state === "firing") - Number(a.state === "firing"));
  return (
    <section aria-labelledby="monitor-alerts" className="flex flex-col gap-2">
      <h2 id="monitor-alerts" className="t-card-title">Alerts</h2>
      <ul className="flex flex-col gap-2">
        {sorted.map((a) => (
          <li key={a.type} className="flex flex-wrap items-center gap-x-2 gap-y-1 text-ui">
            {a.state === "firing" ? (
              <>
                <Tag tone="strong" icon={<IconWarning size={14} strokeWidth={1.8} aria-hidden="true" />}>Firing</Tag>
                <span className="font-semibold">{a.decision_line}</span>
                {a.fired_at ? <span className="text-time-meta text-text-muted">since <Time iso={a.fired_at} format="point" variant="meta" /></span> : null}
              </>
            ) : (
              <>
                <Tag>Quiet</Tag>
                <span className="text-text-muted">{a.decision_line}</span>
              </>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
