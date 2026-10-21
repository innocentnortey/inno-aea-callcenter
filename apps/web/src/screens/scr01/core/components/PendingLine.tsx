import { AssistantMark } from "@/components/shared/marks";
import type { PendingPhase } from "../pending";

/** One quiet static row. The same node serves "replying" and "still", so only the 10 s change is announced. */
export function PendingLine({ phase }: { phase: PendingPhase }) {
  if (phase === "hidden" || phase === "gave-up") return null;
  return (
    <div role="status" className="flex min-h-[24px] items-center gap-2 text-small text-text-muted">
      <AssistantMark size={18} />
      <span>{phase === "still" ? "Still working on this…" : "Meridian assistant is replying…"}</span>
    </div>
  );
}
