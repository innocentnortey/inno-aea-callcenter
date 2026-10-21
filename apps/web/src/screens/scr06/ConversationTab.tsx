import type { components } from "@/api/types.gen";
import { EventLine, MessageRow } from "@/components/shared/messages";
import type { LocalEvent } from "./caseReducer";
import { LiveBox, type LiveBoxProps } from "./LiveBox";

type ChatLine = components["schemas"]["ChatLine"];
export interface ConversationTabProps {
  messages: ChatLine[];
  events: LocalEvent[];
  focusMessage?: string | null;
  liveBox: LiveBoxProps | null;
}

export function ConversationTab({ messages, events, focusMessage, liveBox }: ConversationTabProps) {
  const items = [
    ...messages.map((m) => ({ at: m.at, node: (
      <div key={m.message_id} id={`msg-${m.message_id}`} tabIndex={-1} className={m.message_id === focusMessage ? "rounded-control bg-surface-selected p-1 outline-none" : "outline-none"}>
        <MessageRow speaker={m.speaker} at={m.at} layout="flat">{m.text}</MessageRow>
      </div>
    ) })),
    ...events.map((e) => ({ at: e.at, node: <EventLine key={e.id} at={e.at}>{e.text}</EventLine> })),
  ].sort((a, b) => Date.parse(a.at) - Date.parse(b.at));
  return (
    <div className="flex flex-col gap-3">
      <div aria-live="polite" className="flex flex-col gap-3">
        {items.length === 0 ? <p className="text-ui text-text-muted">Nothing recorded.</p> : items.map((i) => i.node)}
      </div>
      {liveBox ? <LiveBox {...liveBox} /> : null}
    </div>
  );
}
