import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { Button, IconHeadset, TextArea } from "@/components/ui";
import type { ChatAction } from "../../contract";
import type { ChatState, Limits } from "../model";
import type { ComposerLock } from "../useChat";
import { LAPTOP, useMediaQuery } from "../useMediaQuery";

export interface ComposerProps {
  lock: ComposerLock | null;
  pending: boolean;
  replying: ChatState["replying"];
  limits: Limits | null;
  dispatch(a: ChatAction): Promise<void>;
  /** True when a typed message would be accepted right now (same guards as sending); false keeps the draft in the field. */
  canSend?(): boolean;
}

/** R7. DOM order is the focus order: "Talk to a person" first (WCAG 3.2.6), then the field, then Send. */
export function Composer({ lock, pending, replying, limits, dispatch, canSend: accepts }: ComposerProps) {
  const [text, setText] = useState("");
  const laptop = useMediaQuery(LAPTOP);
  const field = useRef<HTMLTextAreaElement>(null);
  const focused = useRef(false);
  const human = replying.kind === "human";
  const who = replying.display_name ?? "the representative";
  const ended = lock?.reason === "ended";
  const fieldLocked = lock !== null;
  const canSend = !fieldLocked && !pending && text.trim() !== "";

  useEffect(() => {
    if (focused.current || !laptop || lock !== null) return;
    focused.current = true; // once, on a laptop, when the chat first opens; never re-grabbed later (a safety card must not pull focus)
    field.current?.focus();
  }, [laptop, lock]);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!canSend) return;
    if (accepts && !accepts()) return; // refused by the chat's guards: the draft stays
    const value = text;
    setText("");
    void dispatch({ kind: "text", text: value });
  };
  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (laptop && e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); submit(); }
  };

  return (
    <form aria-label="Send a message" onSubmit={submit} className="flex flex-none flex-col gap-2 border-t border-border-hair bg-surface px-3.5 py-3">
      {ended ? (
        <Button variant="primary" onClick={() => void dispatch({ kind: "newChat" })}>Start a new chat</Button>
      ) : (
        <Button variant="secondary" icon={<IconHeadset size={16} strokeWidth={1.8} aria-hidden="true" />} onClick={() => void dispatch({ kind: "person" })} className="w-full min-[900px]:w-auto min-[900px]:self-start">
          Talk to a person
        </Button>
      )}
      <div className="flex items-end gap-2">
        <div className="min-w-0 flex-1">
          <label htmlFor="chat-message" className="sr-only">{human ? `Message to ${who}` : "Message"}</label>
          <TextArea
            id="chat-message"
            ref={field}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            disabled={fieldLocked}
            maxLength={limits?.max_message_chars ?? 2000}
            placeholder={human ? `Message ${who}` : "Type a message"}
            rows={2}
          />
        </div>
        <Button variant="send" type="submit" aria-label="Send" disabled={!canSend} className="min-w-[var(--target-min)]">Send</Button>
      </div>
      {lock?.hint ? <p className="text-small text-text-muted">{lock.hint}</p> : null}
    </form>
  );
}
