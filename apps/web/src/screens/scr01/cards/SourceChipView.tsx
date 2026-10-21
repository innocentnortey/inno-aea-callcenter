import type { components } from "@/api/types.gen";
import { Disclosure, IconDoc, IconQuote } from "@/components/ui";

type SourceChip = components["schemas"]["SourceChip"];

/** A "Source" chip that opens the quoted passage. Shows version_label, never an invented date. */
export function SourceChipView({ source }: { source: SourceChip }) {
  return (
    <Disclosure
      className="mt-2"
      summary={
        <span
          aria-label={`Source: ${source.file}, ${source.section}, ${source.version_label}`}
          className="inline-flex min-h-[var(--target-min)] items-center gap-2 rounded-control border border-[color:var(--chip-edge)] bg-[var(--chip-bg)] px-2 text-small"
        >
          <IconDoc size={14} strokeWidth={1.8} aria-hidden="true" />
          <span className="font-semibold">Source</span>
          <span className="t-ref">{source.file}</span>
          <span>{source.section}</span>
          <span className="text-text-muted">{source.version_label}</span>
        </span>
      }
    >
      <p className="mt-1 text-small text-text-muted">Where this comes from</p>
      <blockquote className="mt-1 flex gap-2 rounded-control bg-surface-well p-3 text-ui">
        <IconQuote size={14} strokeWidth={1.8} aria-hidden="true" className="mt-0.5 shrink-0" />
        <span>{source.excerpt}</span>
      </blockquote>
    </Disclosure>
  );
}
