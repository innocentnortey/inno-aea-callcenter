import * as Tabs from "@radix-ui/react-tabs";
import type { components } from "@/api/types.gen";
import { caseHref } from "@/routes";
import { SourceCard } from "./SourceCard";
import { ConversationTab, type ConversationTabProps } from "./ConversationTab";

type Source = components["schemas"]["CaseSource"];
export type EvidenceTab = "sources" | "conversation";
export interface EvidenceColumnProps {
  sources: Source[];
  asOf: string;
  highlight: string | null;
  tab: EvidenceTab;
  onTab(t: EvidenceTab): void;
  conversation: ConversationTabProps;
  otherCases: components["schemas"]["CaseDetail"]["other_cases"];
}

const TRIGGER = "motion-control min-h-[var(--target-min)] px-3 text-ui font-semibold text-text-muted data-[state=active]:border-b-2 data-[state=active]:border-[color:var(--tab-underline)] data-[state=active]:text-text";

export function EvidenceColumn(p: EvidenceColumnProps) {
  return (
    <aside aria-label="Evidence" className="flex flex-col gap-3 p-4">
      <div>
        <h2 className="t-section">Evidence</h2>
        <p className="text-small text-text-muted">What the AI saw, next to what is true now</p>
      </div>
      <Tabs.Root value={p.tab} onValueChange={(v) => p.onTab(v as EvidenceTab)}>
        <Tabs.List aria-label="Evidence" className="flex border-b border-border-hair">
          <Tabs.Trigger value="sources" className={TRIGGER}>Sources ({p.sources.length})</Tabs.Trigger>
          <Tabs.Trigger value="conversation" className={TRIGGER}>Conversation</Tabs.Trigger>
        </Tabs.List>
        <Tabs.Content value="sources" className="flex flex-col gap-3 pt-3">
          {p.sources.length === 0 ? <p className="text-ui text-text-muted">Nothing recorded.</p> : null}
          {p.sources.map((s) => <SourceCard key={s.source_id} source={s} asOf={p.asOf} highlighted={p.highlight === s.source_id} />)}
        </Tabs.Content>
        <Tabs.Content value="conversation" className="pt-3"><ConversationTab {...p.conversation} /></Tabs.Content>
      </Tabs.Root>
      {p.otherCases.length > 0 ? (
        <section aria-labelledby="other-cases-h">
          <h3 id="other-cases-h" className="text-small font-semibold">Other cases for this customer</h3>
          <ul className="mt-1 flex flex-col gap-1 text-ui">
            {p.otherCases.map((o) => (
              <li key={o.reference}><a href={caseHref(o.reference)} className="link-text t-ref">{o.reference}</a> {o.status.replace(/_/g, " ")}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </aside>
  );
}
