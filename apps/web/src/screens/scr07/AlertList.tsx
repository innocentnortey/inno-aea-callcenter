import { useNavigate } from "react-router";
import type { components } from "@/api/types.gen";
import { Time } from "@/components/shared/Time";
import { Button } from "@/components/ui";
import { caseHref } from "@/routes";

type Alert = components["schemas"]["Alert"];

export function AlertList({ alerts }: { alerts: Alert[] }) {
  const navigate = useNavigate();
  if (alerts.length === 0) return null;
  const sorted = [...alerts].sort((a, b) => Date.parse(b.at) - Date.parse(a.at));
  return (
    <section aria-labelledby="oversight-alerts" className="flex flex-col gap-2">
      <h2 id="oversight-alerts" className="t-card-title">Alerts</h2>
      <ul aria-live="polite" className="flex flex-col gap-2">
        {sorted.map((a, i) => (
          <li key={`${a.at}-${i}`} className="flex flex-wrap items-center gap-x-2 text-ui">
            <span className="font-semibold">{a.line}</span>
            <Time iso={a.at} format="point" variant="meta" className="text-text-muted" />
            {a.case_ref ? (
              <Button variant="text" density="console" aria-label={`Open case ${a.case_ref}`} onClick={() => navigate(caseHref(a.case_ref!))}>Open case</Button>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
