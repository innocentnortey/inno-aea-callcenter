import { useId } from "react";
import { useNavigate } from "react-router";
import type { components } from "@/api/types.gen";
import { QueueRow } from "@/components/shared/QueueRow";
import { Button, Card, CardHeader, Skeleton } from "@/components/ui";
import { caseHref } from "@/routes";

type LaneData = components["schemas"]["Lane"];
type Row = components["schemas"]["QueueRow"];

export function Lane({ title, lane, loading, onAssign }: { title: string; lane?: LaneData; loading?: boolean; onAssign(row: Row): void }) {
  const navigate = useNavigate();
  const id = useId();
  return (
    <Card aria-labelledby={id}>
      <CardHeader as="h2" title={<span id={id}>{lane ? `${title} · ${lane.count}` : title}</span>} />
      <div className="p-2">
        {loading || !lane ? (
          <Skeleton height={44} rows={2} />
        ) : lane.rows.length === 0 ? (
          <p className="px-3 py-2 text-ui text-text-muted">None</p>
        ) : (
          lane.rows.map((row) => (
            <div key={row.reference} className="flex items-start gap-2">
              <div className="min-w-0 flex-1">
                <ul><QueueRow row={row} showStaffTags onSelect={(ref) => navigate(caseHref(ref))} /></ul>
                {row.age_label ? <p className="px-[9px] text-time-meta text-text-muted">{row.age_label}</p> : null}
              </div>
              <Button density="console" aria-label={`Assign ${row.reference}`} onClick={() => onAssign(row)}>Assign</Button>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
