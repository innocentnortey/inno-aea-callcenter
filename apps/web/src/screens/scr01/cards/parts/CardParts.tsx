import { useRef, type ReactNode } from "react";
import { Button, IconCheck, IconHeadset, IconInfo } from "@/components/ui";
import { cn } from "@/lib/cx";
import { Time } from "@/components/shared/Time";
import type { BlockProps, BlockType, Settled } from "../../contract";

export function InlineNotice({ children, role, id }: { children: ReactNode; role?: "alert" | "status"; id?: string }) {
  return (
    <p id={id} role={role} className="flex items-start gap-2 text-small">
      <IconInfo size={14} strokeWidth={1.8} aria-hidden="true" className="mt-0.5 shrink-0" />
      <span>{children}</span>
    </p>
  );
}
export function DoneLine({ children }: { children: ReactNode }) {
  return (
    <p className="flex items-start gap-2 text-ui">
      <IconCheck size={16} strokeWidth={1.8} aria-hidden="true" className="mt-0.5 shrink-0" />
      <span>{children}</span>
    </p>
  );
}
export function HintLine({ id, children }: { id?: string; children: ReactNode }) {
  return <p id={id} className="text-small text-text-muted">{children}</p>;
}
/** "Talk to a person": never disabled, only guarded against a double tap. */
export function PersonKey({ dispatch }: { dispatch: BlockProps<BlockType>["dispatch"] }) {
  const busy = useRef(false);
  return (
    <Button
      variant="secondary"
      icon={<IconHeadset size={16} strokeWidth={1.8} aria-hidden="true" />}
      onClick={async () => {
        if (busy.current) return;
        busy.current = true;
        try { await dispatch({ kind: "person" }); } finally { busy.current = false; }
      }}
    >
      Talk to a person
    </Button>
  );
}
export interface Step { text: string; state: "done" | "current" | "todo"; at?: string }
export function StepList({ steps }: { steps: Step[] }) {
  return (
    <ol className="space-y-1 text-ui">
      {steps.map((s) => (
        <li key={s.text} aria-current={s.state === "current" ? "step" : undefined} className={cn("flex items-start gap-2", s.state === "current" && "font-semibold", s.state === "todo" && "text-text-muted")}>
          {s.state === "done" ? <IconCheck size={16} strokeWidth={1.8} aria-hidden="true" className="mt-0.5 shrink-0" /> : <span className="inline-block size-4 shrink-0" aria-hidden="true" />}
          <span>{s.text}</span>
          {s.at ? <Time iso={s.at} format="point" variant="meta" /> : null}
        </li>
      ))}
    </ol>
  );
}
export function hasWrite(settled: Settled | null, kind: Settled["actions"][number]["kind"]): boolean {
  return Boolean(settled?.actions.some((a) => a.kind === kind));
}
export function choiceKept(block: { answered: string | null }, props: { answered: boolean }): boolean {
  return props.answered || block.answered !== null;
}
