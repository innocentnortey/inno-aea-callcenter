import { RefChip } from "@/components/shared/RefChip";
import { IconClock, Tag } from "@/components/ui";
import type { ActionPlan, MenuKey } from "./actionPlan";
import { caseTitle, createdLine, dueHeadline, headerStatusLine, ownerLine, type CaseDetail } from "./caseText";
import { SplitButton } from "./SplitButton";

export interface CaseHeaderProps {
  detail: CaseDetail; nowIso: string; plan: ActionPlan; onPrimary(): void; onMenu(k: MenuKey): void; busy: boolean;
}

export function CaseHeader({ detail, nowIso, plan, onPrimary, onMenu, busy }: CaseHeaderProps) {
  const c = detail.case;
  const status = headerStatusLine(detail, nowIso);
  return (
    <header className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="rounded-tag bg-surface-well px-2 py-1 text-lead font-medium">{caseTitle(c)}</h1>
        <RefChip reference={c.reference} copyable />
        {!plan.readOnly ? <div className="ml-auto"><SplitButton primary={plan.primary} menu={plan.menu} onPrimary={onPrimary} onMenu={onMenu} busy={busy} /></div> : null}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <p className="t-time-due">{dueHeadline(c)}</p>
        {c.due_state === "overdue" ? <Tag tone="strong" icon={<IconClock size={14} strokeWidth={1.8} aria-hidden="true" />}>Overdue</Tag> : null}
        {c.seed ? <Tag>Demo seed</Tag> : null}
      </div>
      <p className="text-small text-text-muted">{createdLine(c)} {"·"} {ownerLine(c)}</p>
      <p aria-live="polite" className="text-ui">{status}</p>
    </header>
  );
}
