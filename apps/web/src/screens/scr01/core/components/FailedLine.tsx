import { Button } from "@/components/ui";

export function FailedLine({ message, retryable, onRetry }: { message: string; retryable: boolean; onRetry: () => void }) {
  return (
    <div className="flex flex-wrap items-center justify-end gap-3 text-small">
      <p>{message}</p>
      {retryable ? <Button density="chat" onClick={onRetry}>Try again</Button> : null}
    </div>
  );
}
