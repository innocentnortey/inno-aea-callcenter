import type { components } from "@/api/types.gen";
import { Card, CardBody, CardHeader, IconCheck, IconDoc, IconInfo, Tag } from "@/components/ui";
import { cn } from "@/lib/cx";
import { SnapshotTable } from "./SnapshotTable";

type Source = components["schemas"]["CaseSource"];

export function SourceCard({ source, asOf, highlighted }: { source: Source; asOf: string; highlighted: boolean }) {
  return (
    <Card id={`src-${source.source_id}`} tabIndex={-1} className={cn("outline-none", highlighted && "bg-surface-selected")}>
      <CardHeader
        icon={<IconDoc size={16} strokeWidth={1.8} aria-hidden="true" />}
        title={source.title}
        hint={<span className="t-ref text-caption">{source.ref} {"·"} {source.version_label}</span>}
        meta={source.audience === "staff_only" ? <Tag>Staff only</Tag> : undefined}
      />
      <CardBody className="flex flex-col gap-2">
        {source.current_unavailable ? <p className="text-ui">This record can't be read right now; the snapshot is shown alone.</p> : null}
        <SnapshotTable
          snapshot={source.snapshot as Record<string, unknown>}
          current={source.current as Record<string, unknown> | null}
          asOf={asOf}
          unavailable={source.current_unavailable}
        />
        {!source.current_unavailable ? (
          <p className="flex items-center gap-1 border-t border-dashed border-border-hair pt-2 text-small">
            {source.changed_since ? (
              <><IconInfo size={14} strokeWidth={1.8} aria-hidden="true" /><span className="font-semibold">{source.changed_note}</span></>
            ) : (
              <><IconCheck size={14} strokeWidth={1.8} aria-hidden="true" /><span>{source.changed_note ?? "No change since the snapshot"}</span></>
            )}
          </p>
        ) : null}
      </CardBody>
    </Card>
  );
}
