import type { ReactNode } from "react";
import { Button } from "@/components/ui";
import { cn } from "@/lib/cx";
import type { ActionPlan, BarKey } from "./actionPlan";

export type FormKey = "release" | "wait" | "resolve" | "close_unresolved" | "log_call" | "log_email" | "flag" | "assign" | "change_priority";
const BAR_FORM: Partial<Record<BarKey, FormKey>> = { log_call: "log_call", log_email: "log_email", flag: "flag", assign: "assign", change_priority: "change_priority" };

export interface ActionAreaProps {
  plan: ActionPlan;
  onBar(key: BarKey): void;
  form: ReactNode;
  error: { text: string; offerReload: boolean } | null;
  onReload(): void;
  result: ReactNode;
  log: ReactNode;
}

export function barFormKey(key: BarKey): FormKey | null { return BAR_FORM[key] ?? null; }

export function ActionArea({ plan, onBar, form, error, onReload, result, log }: ActionAreaProps) {
  const reasons = [...new Set(plan.bar.filter((b) => !b.enabled && b.reason).map((b) => b.reason as string))];
  return (
    <section aria-label="Actions" className="flex flex-col gap-3">
      {plan.readOnly ? (
        <p className="text-ui text-text-muted">Read-only for the business owner role</p>
      ) : (
        <>
          <div className="flex flex-wrap gap-2">
            {plan.bar.map((b) => (
              <Button
                key={b.key} variant="secondary" density="console"
                aria-disabled={!b.enabled || undefined}
                className={cn(!b.enabled && "cursor-not-allowed bg-surface-well text-text-muted")}
                onClick={() => { if (b.enabled) onBar(b.key); }}
              >
                {b.label}
              </Button>
            ))}
          </div>
          {reasons.length > 0 ? <ul className="text-small text-text-muted">{reasons.map((r) => <li key={r}>{r}</li>)}</ul> : null}
          {form}
        </>
      )}
      {error ? (
        <div className="flex flex-wrap items-center gap-2 text-ui" role="status">
          <p>{error.text}</p>
          {error.offerReload ? <Button variant="text" density="console" onClick={onReload}>Reload</Button> : null}
        </div>
      ) : null}
      {result}
      {log}
    </section>
  );
}
