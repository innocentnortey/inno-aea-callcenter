import { useId } from "react";
import { Time } from "@/components/shared/Time";
import { Button, Tag, VisuallyHidden } from "@/components/ui";
import { COPIED, COPY, COPY_FAILED, STATUS_WORD } from "./copy";
import type { InboxMessage } from "./useInbox";

export interface InboxMessageCardProps {
  message: InboxMessage;
  copied: boolean;
  failed: boolean;
  onCopy(): void;
}

export function InboxMessageCard({ message: m, copied, failed, onCopy }: InboxMessageCardProps) {
  const statusId = useId();
  return (
    <li className="rounded-card border border-[color:var(--card-edge)] bg-[var(--card-bg)] p-3">
      <p className="text-small text-text-muted">
        To {m.to_masked} {"·"} <Time iso={m.at} format="staff" />
      </p>
      <p className="mt-1 text-body">{m.body}</p>
      <p className="mt-1">
        <b className="t-code">
          <span aria-hidden="true">{m.code}</span>
          <VisuallyHidden>{m.code.split("").join(" ")}</VisuallyHidden>
        </b>
      </p>
      <div className="mt-2 flex flex-wrap items-center gap-3">
        <Tag id={statusId}>{STATUS_WORD[m.status]}</Tag>
        {m.status === "active" ? (
          <span className="text-small text-text-muted">Expires <Time iso={m.expires_at} format="point" /></span>
        ) : null}
        <Button disabled={m.status !== "active"} aria-describedby={statusId} onClick={onCopy}>{COPY}</Button>
        <span aria-live="polite" className="text-small">{copied ? COPIED : failed ? COPY_FAILED : ""}</span>
      </div>
    </li>
  );
}
