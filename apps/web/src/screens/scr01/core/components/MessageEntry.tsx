import { MessageRow } from "@/components/shared/messages";
import type { Entry } from "../model";

export function MessageEntry({ entry }: { entry: Extract<Entry, { kind: "message" }> }) {
  return (
    <MessageRow speaker={entry.speaker} at={entry.at} layout="bubble">
      <p className="whitespace-pre-wrap [overflow-wrap:anywhere]">{entry.text}</p>
    </MessageRow>
  );
}
