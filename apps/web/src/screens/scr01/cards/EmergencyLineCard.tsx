import { Card } from "@/components/ui";
import { IconPhone } from "@/components/ui";
import type { BlockProps } from "../contract";

const digits = (n: string) => n.replace(/[^\d+]/g, "");

export function EmergencyLineCard({ block }: BlockProps<"emergency_line">) {
  return (
    <Card style={{ border: "var(--line-emergency)" }}>
      <div className="flex items-start gap-3 p-3">
        <IconPhone size={18} strokeWidth={1.8} aria-hidden="true" className="mt-1 shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="text-body">{block.lead_text}</p>
          <a href={`tel:${digits(block.number)}`} className="t-title inline-flex min-h-[var(--target-min)] items-center gap-2">
            <span>{block.number}</span>
            <span>{block.number_note}</span>
          </a>
          {block.separate_line ? (
            <>
              <hr className="my-2 border-t border-dashed border-border-hair" />
              <p className="text-ui">{block.separate_line}</p>
            </>
          ) : null}
        </div>
      </div>
    </Card>
  );
}
