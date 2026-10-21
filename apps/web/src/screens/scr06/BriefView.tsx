import type { components } from "@/api/types.gen";
import { ErrorLine } from "@/components/shared/states";
import { IconDoc } from "@/components/ui";
import { BriefSection } from "./BriefSection";

type Brief = components["schemas"]["Brief"];
type Source = components["schemas"]["CaseSource"];

export function BriefView({ brief, sources, onJump }: { brief: Brief; sources: Source[]; onJump(id: string): void }) {
  if (brief.status === "being_written") return <p className="text-body">The brief is being written. The conversation is complete.</p>;
  if (brief.status === "failed") return <ErrorLine message="The brief couldn't be written. The conversation is complete." />;
  const jump = (n: number) => {
    const el = document.getElementById(`brief-${n}`);
    el?.scrollIntoView?.({ block: "nearest" });
    el?.focus();
  };
  return (
    <div className="flex flex-col gap-3">
      <p className="flex items-center gap-1 text-small text-text-muted"><IconDoc size={14} strokeWidth={1.8} aria-hidden="true" />Brief written by the assistant</p>
      <div style={{ ["--sticky-offset" as string]: "40px" }} className="sticky top-0 z-10 bg-[var(--app-bg)] py-1">
        <nav aria-label="Brief sections" className="flex gap-1">
          {brief.headings.map((h) => (
            <button
              key={h.number}
              type="button"
              aria-label={`${h.number}, ${h.title}`}
              onClick={() => jump(h.number)}
              className="motion-control min-h-8 min-w-8 rounded-control border border-border-hair bg-surface text-small font-semibold [--hover-base:var(--color-surface)] hover-mix"
            >
              {h.number}
            </button>
          ))}
        </nav>
      </div>
      <ol className="flex flex-col gap-3">
        {brief.headings.map((h) => <BriefSection key={h.number} heading={h} sources={sources} onJump={onJump} />)}
      </ol>
    </div>
  );
}
