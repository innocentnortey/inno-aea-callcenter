import { type ReactNode } from "react";
import { cn } from "@/lib/cx";
import { Button } from "@/components/ui/Button";

/** Errors are polite lines, never role="alert". */
export function ErrorLine({ message, onRetry, className }: { message: string; onRetry?: () => void; className?: string }) {
  return (
    <div className={cn("flex flex-wrap items-center gap-3 text-ui", className)}>
      <p>{message}</p>
      {onRetry ? <Button density="console" onClick={onRetry}>Try again</Button> : null}
    </div>
  );
}
export function EmptyState({ title, body, action, className }: { title: string; body?: string; action?: ReactNode; className?: string }) {
  return (
    <div className={cn("flex flex-col items-start gap-1 py-4", className)}>
      <p className="t-card-title">{title}</p>
      {body ? <p className="text-ui text-text-muted">{body}</p> : null}
      {action}
    </div>
  );
}
export function StaleLine({ children, actionLabel, onAction, className }: { children: ReactNode; actionLabel?: string; onAction?: () => void; className?: string }) {
  return (
    <div className={cn("flex items-center gap-2 text-ui", className)} role="status">
      <span>{children}</span>
      {actionLabel ? <Button variant="text" density="console" onClick={onAction}>{actionLabel}</Button> : null}
    </div>
  );
}
export function ResultLine({ children, id, className }: { children: ReactNode; id?: string; className?: string }) {
  return (
    <p id={id} tabIndex={-1} role="status" className={cn("text-ui", className)}>
      {children}
    </p>
  );
}
