import { Fragment } from "react";
import { IconCheck, IconChevron, Tag } from "@/components/ui";
import { LIFECYCLE_LABEL, type CaseSummary } from "./caseText";

type Lifecycle = CaseSummary["lifecycle"];

export function lifecycleSteps(lifecycle: Lifecycle, staffedPath: boolean): { key: string; label: string; current: boolean; done: boolean }[] {
  const terminal = lifecycle === "resolved" || lifecycle === "closed_unresolved";
  const keys: string[] = [...(staffedPath ? ["live_queued"] : []), "unassigned", "claimed", "in_progress", "waiting", terminal ? lifecycle : "final"];
  const cur = terminal ? keys.length - 1 : keys.indexOf(lifecycle);
  return keys.map((k, i) => ({
    key: k,
    label: k === "final" ? "Resolved / Closed unresolved" : LIFECYCLE_LABEL[k as Lifecycle],
    current: i === cur,
    done: i < cur,
  }));
}

export function LifecycleLine({ lifecycle, staffedPath }: { lifecycle: Lifecycle; staffedPath: boolean }) {
  const steps = lifecycleSteps(lifecycle, staffedPath);
  return (
    <ol aria-label="Case state" className="flex flex-wrap items-center gap-1 text-small">
      {steps.map((s, i) => (
        <Fragment key={s.key}>
          <li className="flex items-center gap-1" aria-current={s.current ? "step" : undefined}>
            {s.current ? (
              <Tag tone="strong">{s.label}</Tag>
            ) : s.done ? (
              <span className="flex items-center gap-1 text-text-muted"><IconCheck size={14} strokeWidth={1.8} aria-hidden="true" />{s.label}</span>
            ) : (
              <span className="text-text-muted">{s.label}</span>
            )}
          </li>
          {i < steps.length - 1 ? <li aria-hidden="true" className="-rotate-90 text-text-muted"><IconChevron size={14} strokeWidth={1.8} /></li> : null}
        </Fragment>
      ))}
    </ol>
  );
}
