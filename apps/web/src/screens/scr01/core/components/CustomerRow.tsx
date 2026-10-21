import { MessageRow } from "@/components/shared/messages";
import type { CustomerEntry } from "../model";
import { FailedLine } from "./FailedLine";

export function CustomerRow({ entry, onRetry }: { entry: CustomerEntry; onRetry: (turnId: string) => void }) {
  return (
    <div className="flex flex-col gap-2">
      <MessageRow speaker={{ kind: "customer", display_name: "You" }} at={entry.at ?? ""} layout="bubble">
        <p className="whitespace-pre-wrap [overflow-wrap:anywhere]">{entry.text}</p>
      </MessageRow>
      {entry.delivery === "failed" && entry.failure ? (
        <FailedLine message={entry.failure} retryable={entry.retryable} onRetry={() => onRetry(entry.turnId)} />
      ) : null}
    </div>
  );
}
