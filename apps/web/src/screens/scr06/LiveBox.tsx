import { useEffect, useId, useRef, useState } from "react";
import { Button, Card, CardBody, TextArea } from "@/components/ui";

export interface LiveBoxProps {
  mode: "active" | "disabled";
  ownerName: string | null;
  onSend(text: string): Promise<boolean>;
  onHandBack(): void;
  onClose(): void;
  error?: string | null;
  endedByReset: boolean;
  busy: boolean;
}

export function LiveBox({ mode, ownerName, onSend, onHandBack, onClose, error, endedByReset, busy }: LiveBoxProps) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  const id = useId();
  const active = mode === "active" && !endedByReset && !busy;
  const head = endedByReset
    ? "This chat ended because the demo was reset."
    : mode === "active"
      ? `You are replying as ${ownerName ? ownerName + " (demo representative)" : "the demo representative"}. The assistant is paused.`
      : "This chat is no longer live.";
  useEffect(() => { if (mode === "active") ref.current?.focus(); }, [mode]);
  return (
    <Card>
      <CardBody className="flex flex-col gap-2">
        <p className="text-ui font-semibold" role="status">{head}</p>
        {!endedByReset ? (
          <>
            <label htmlFor={id} className="text-small font-semibold">Reply</label>
            <TextArea id={id} ref={ref} density="console" value={text} disabled={!active} onChange={(e) => setText(e.target.value)} />
            <div className="flex flex-wrap gap-2">
              <Button
                variant="send" density="console" disabled={!active}
                onClick={async () => { if (await onSend(text)) { setText(""); ref.current?.focus(); } }}
              >
                Send
              </Button>
              <Button variant="secondary" density="console" disabled={!active} onClick={onHandBack}>Hand back to the assistant</Button>
              <Button variant="secondary" density="console" disabled={!active} onClick={onClose}>Close the chat</Button>
            </div>
          </>
        ) : null}
        {error ? <p className="text-ui" role="status">{error}</p> : null}
      </CardBody>
    </Card>
  );
}
