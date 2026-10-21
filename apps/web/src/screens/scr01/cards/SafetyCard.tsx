import { useState } from "react";
import { IconWarning } from "@/components/ui";
import type { BlockProps } from "../contract";

const alerted = new Set<string>();
/** Forget which safety blocks already announced (new chat, demo reset). */
export function resetAlerted(): void { alerted.clear(); }
export const resetAlertedForTests = resetAlerted;
const digits = (n: string) => n.replace(/[^\d+]/g, "");

/** Only the first mounted copy of a block announces itself (G1 may mount it pinned and in the thread). */
function useFirstMount(blockId: string): boolean {
  const [first] = useState(() => {
    const f = !alerted.has(blockId);
    alerted.add(blockId);
    return f;
  });
  return first;
}

function SafetySheet({ blockId, label, signal, children }: { blockId: string; label: string; signal: string; children: React.ReactNode }) {
  const first = useFirstMount(blockId);
  return (
    <section
      aria-label={label}
      role={first ? "alert" : undefined}
      className="rounded-none bg-[var(--safety-bg)]"
      style={{ borderBottom: "var(--line-safety)" }}
    >
      <div className="flex items-center gap-2 bg-[var(--safety-band-bg)] px-4 py-2.5 text-[color:var(--safety-band-text)]">
        <IconWarning size={18} strokeWidth={1.8} aria-hidden="true" />
        <span className="t-signal">{signal}</span>
      </div>
      {children}
    </section>
  );
}

export function SafetyCard({ block }: BlockProps<"safety">) {
  return (
    <div>
      <SafetySheet blockId={block.block_id} label="Danger: safety instruction" signal={block.signal_word}>
        <ol className="t-title list-decimal space-y-1 py-3 pl-9 pr-4">
          {block.steps.map((s) => <li key={s}>{s}</li>)}
        </ol>
        <div className="px-4 pb-4">
          <a
            href={`tel:${digits(block.call_key.number)}`}
            className="block min-h-12 rounded-none bg-[var(--safety-btn-bg)] px-4 py-3 text-center font-semibold text-[color:var(--safety-btn-text)] focus-visible:outline-[var(--focus-ring-on-safety)]"
          >
            {block.call_key.label}
          </a>
        </div>
      </SafetySheet>
      <p className="mt-2 text-small text-text-muted">{block.contact_line}</p>
    </div>
  );
}

export function ConditionalSafetyCard({ block }: BlockProps<"conditional_safety">) {
  return (
    <SafetySheet blockId={block.block_id} label="Warning: safety instruction" signal={block.level}>
      <p className="t-title px-4 py-3">{block.text}</p>
      <p className="px-4 pb-4 text-ui">{block.emergency_line}</p>
    </SafetySheet>
  );
}
