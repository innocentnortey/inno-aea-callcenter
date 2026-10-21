import type { InboxMessage } from "./useInbox";
import { InboxMessageCard } from "./InboxMessageCard";

export interface InboxListProps {
  messages: InboxMessage[];
  copiedId: string | null;
  failedId: string | null;
  onCopy(id: string, code: string): void;
}

export function InboxList({ messages, copiedId, failedId, onCopy }: InboxListProps) {
  return (
    <ol className="mt-4 flex flex-col gap-3">
      {messages.map((m) => (
        <InboxMessageCard key={m.id} message={m} copied={copiedId === m.id} failed={failedId === m.id} onCopy={() => onCopy(m.id, m.code)} />
      ))}
    </ol>
  );
}
