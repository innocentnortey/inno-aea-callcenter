import { type ReactNode } from "react";
import { cn } from "@/lib/cx";
import type { components } from "@/api/types.gen";
import { Time } from "./Time";

type Speaker = components["schemas"]["Speaker"];
const KIND_LABEL: Record<Speaker["kind"], string> = { assistant: "Meridian assistant", customer: "You", representative: "Representative", event: "System" };

export interface SpeakerLineProps { speaker: Speaker; at?: string; align?: "left" | "right"; className?: string }
export function SpeakerLine({ speaker, at, align = "left", className }: SpeakerLineProps) {
  const name = speaker.display_name ?? KIND_LABEL[speaker.kind];
  return (
    <p className={cn("flex items-baseline gap-1 text-small", align === "right" && "justify-end", className)}>
      <span className="font-semibold">{name}</span>
      {at ? (
        <>
          <span className="text-text-muted" aria-hidden="true"> {"·"} </span>
          <Time iso={at} format="point" variant="meta" className="text-text-muted" />
        </>
      ) : null}
    </p>
  );
}

export interface MessageRowProps { speaker: Speaker; at: string; layout: "bubble" | "flat"; children: ReactNode; className?: string }
export function MessageRow({ speaker, at, layout, children, className }: MessageRowProps) {
  const right = speaker.kind === "customer";
  const bubble: Record<string, string> = {
    assistant: "bg-[var(--turn-assistant-bg)]",
    customer: "bg-[var(--turn-customer-bg)]",
    representative: "bg-[var(--turn-rep-bg)] border border-[color:var(--turn-rep-edge)]",
  };
  return (
    <div className={cn("flex flex-col gap-1", right && "items-end", className)}>
      <SpeakerLine speaker={speaker} at={at} align={right ? "right" : "left"} />
      {layout === "bubble" ? (
        <div className={cn("max-w-[62ch] rounded-card px-3 py-2 text-body", bubble[speaker.kind] ?? "bg-[var(--turn-assistant-bg)]", right ? "rounded-tr-tip" : "rounded-tl-tip")}>
          {children}
        </div>
      ) : (
        <div className="max-w-[62ch] text-body">{children}</div>
      )}
    </div>
  );
}

export interface EventLineProps { icon?: ReactNode; at?: string; children: ReactNode; className?: string }
export function EventLine({ icon, at, children, className }: EventLineProps) {
  return (
    <div className={cn("flex items-center gap-3 text-small text-[color:var(--event-text)]", className)}>
      <span className="h-px flex-1 bg-[var(--event-line)]" aria-hidden="true" />
      <span className="flex items-center gap-1">
        <span className="sr-only">System event: </span>
        {icon}
        {children}
        {at ? <Time iso={at} format="point" variant="meta" /> : null}
      </span>
      <span className="h-px flex-1 bg-[var(--event-line)]" aria-hidden="true" />
    </div>
  );
}
