import { useId, type ReactNode } from "react";
import { Button, Card, CardBody, CardHeader, Tag } from "@/components/ui";

export interface MetricTileProps {
  heading: string;
  estimate?: boolean;
  value: string;
  denominatorLine: string;
  reason?: string | null;
  extra?: ReactNode;
  caseRefs: string[];
  denominator: number | null;
  open: boolean;
  onToggle(): void;
  panelId: string;
}

export function MetricTile(p: MetricTileProps) {
  const headingId = useId();
  const canOpen = (p.denominator ?? 0) > 0 && p.caseRefs.length > 0;
  return (
    <Card aria-labelledby={headingId}>
      <CardHeader as="h2" title={<span id={headingId}>{p.heading}</span>} meta={p.estimate ? <Tag>Estimate</Tag> : undefined} />
      <CardBody className="flex flex-col gap-1">
        <p className="t-time-hero">{p.value}</p>
        <p className="text-ui text-text-muted">{p.denominatorLine}</p>
        {p.reason ? <p className="text-small text-text-muted">{p.reason}</p> : null}
        {p.extra}
        {canOpen ? (
          <div>
            <Button variant="text" density="console" aria-expanded={p.open} aria-controls={p.panelId} onClick={p.onToggle}>Open the cases</Button>
          </div>
        ) : (
          <p className="text-small text-text-muted">No cases to open.</p>
        )}
      </CardBody>
    </Card>
  );
}
