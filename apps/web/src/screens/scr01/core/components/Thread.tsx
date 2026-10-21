import { useEffect, useRef } from "react";
import type { BlockProps } from "../../contract";
import type { ChatState } from "../model";
import type { PendingPhase } from "../pending";
import { AssistantGroup } from "./AssistantGroup";
import { CustomerRow } from "./CustomerRow";
import { EventEntry } from "./EventEntry";
import { MessageEntry } from "./MessageEntry";
import { PendingLine } from "./PendingLine";

type Shared = Pick<BlockProps<"text">, "settled" | "dispatch" | "announce" | "landed">;
export interface ThreadProps extends Shared {
  entries: ChatState["entries"];
  answered: ChatState["answered"];
  disabled: boolean;
  phase: PendingPhase;
  scrollTarget: { id: string; nonce: number } | null;
  onRetry: (turnId: string) => void;
}
const reduced = () => typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** R6. The log holds entries only; the pending line sits just below it, outside role="log", so "replying" is not announced as an addition. */
export function Thread({ entries, answered, settled, disabled, dispatch, announce, landed, phase, scrollTarget, onRetry }: ThreadProps) {
  const log = useRef<HTMLDivElement>(null);
  const count = entries.length;
  const lastKind = entries[count - 1]?.kind;
  useEffect(() => {
    const last = log.current?.lastElementChild as HTMLElement | null | undefined;
    last?.scrollIntoView?.({ block: lastKind === "reply" ? "start" : "end", behavior: reduced() ? "auto" : "smooth" });
  }, [count, lastKind]);
  useEffect(() => {
    if (!scrollTarget) return;
    const el = Array.from(log.current?.children ?? []).find((c) => c.getAttribute("data-entry") === scrollTarget.id) as HTMLElement | undefined;
    if (!el) return;
    el.scrollIntoView?.({ block: "center", behavior: reduced() ? "auto" : "smooth" });
    el.classList.add("landed");
    const t = setTimeout(() => el.classList.remove("landed"), 1200);
    return () => { clearTimeout(t); el.classList.remove("landed"); };
  }, [scrollTarget]);
  return (
    <div className="min-h-0 flex-1 overflow-y-auto px-3.5 py-3">
      <div ref={log} role="log" aria-live="polite" aria-relevant="additions" aria-label="Conversation" className="flex flex-col gap-3">
        {entries.map((e) => (
          <div key={e.id} data-entry={e.id} className="flex flex-col gap-3">
            {e.kind === "customer" ? <CustomerRow entry={e} onRetry={onRetry} />
              : e.kind === "reply" ? <AssistantGroup entryId={e.id} blocks={e.blocks} live={e.live} settled={settled} answered={answered} disabled={disabled} dispatch={dispatch} announce={announce} landed={landed} />
              : e.kind === "message" ? <MessageEntry entry={e} />
              : e.kind === "event" ? <EventEntry entry={e} />
              : <p className="text-small text-text-muted">{e.text}</p>}
          </div>
        ))}
      </div>
      <div className="mt-3"><PendingLine phase={phase} /></div>
    </div>
  );
}
