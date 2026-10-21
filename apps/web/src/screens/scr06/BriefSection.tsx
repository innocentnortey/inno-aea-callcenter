import type { components } from "@/api/types.gen";
import { Card, IconInfo, IconQuestion, IconQuote, Tag } from "@/components/ui";
import { cn } from "@/lib/cx";
import { SourceChip } from "./SourceChip";

type Heading = components["schemas"]["BriefHeading"];
type Source = components["schemas"]["CaseSource"];

export function BriefSection({ heading, sources, onJump }: { heading: Heading; sources: Source[]; onJump(id: string): void }) {
  const claims = heading.key === "says";
  const quoted = heading.key === "needs" || heading.key === "told";
  const empty = heading.not_generated || heading.items.length === 0;
  return (
    <li id={`brief-${heading.number}`} tabIndex={-1} className="scroll-mt-2 outline-none">
      <Card className={cn(claims && "border-dashed border-[color:var(--color-border-control)] bg-surface-well")}>
        <div className="flex flex-wrap items-center gap-2 px-3 pt-3">
          <Tag>{heading.number}</Tag>
          <h3 className="t-card-title">{heading.title}</h3>
          {!heading.checked ? <Tag tone="strong" icon={<IconQuestion size={14} strokeWidth={1.8} aria-hidden="true" />}>Customer says {"·"} not checked</Tag> : null}
        </div>
        {heading.trimmed ? (
          <p className="flex items-center gap-1 px-3 pt-2 text-small text-text-muted">
            <IconInfo size={14} strokeWidth={1.8} aria-hidden="true" />
            {heading.trim_note ?? "Something here didn't match the record and was removed."}
          </p>
        ) : null}
        <div className="p-3">
          {empty ? (
            <p className="text-ui text-text-muted">Nothing recorded.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {heading.items.map((it, i) => (
                <li key={i} className="flex flex-col gap-1 text-body">
                  <span className={cn("flex items-start gap-2", quoted && "font-semibold")}>
                    {quoted ? <IconQuote size={14} strokeWidth={1.8} aria-hidden="true" className="mt-1 shrink-0" /> : null}
                    {heading.key === "decide" ? <IconQuestion size={14} strokeWidth={1.8} aria-hidden="true" className="mt-1 shrink-0" /> : null}
                    <span>{it.text}</span>
                  </span>
                  {!claims && it.kind !== "claim" && it.source_ids.length > 0 ? (
                    <span className="flex flex-wrap gap-1">
                      {it.source_ids.map((id) => <SourceChip key={id} source={sources.find((s) => s.source_id === id)} changed={it.changed} onJump={onJump} />)}
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </div>
      </Card>
    </li>
  );
}
