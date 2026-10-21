import { useEffect, useRef, useState, type FormEvent } from "react";
import { Button, Card, CardHeader, Field, IconUser, TextInput } from "@/components/ui";
import type { BlockProps } from "../contract";
import { HintLine } from "./parts/CardParts";
import { useCardAction } from "./parts/useCardAction";

const DEMO_HINT = "Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries.";
const focused = new Set<string>();
export function resetFocusedForTests(): void { focused.clear(); }

export function CodePromptCard(props: BlockProps<"code_prompt">) {
  const { block } = props;
  const { pending, run } = useCardAction(props.dispatch);
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | undefined>();
  const input = useRef<HTMLInputElement>(null);
  const state = block.state;
  const isLocked = state === "locked";
  const resend = block.options.find((o) => o.option === "resend");
  const fieldOff = isLocked || state === "expired" || props.disabled || props.answered;

  useEffect(() => {
    if (state !== "wrong" || focused.has(block.block_id)) return;
    focused.add(block.block_id);
    input.current?.focus();
  }, [state, block.block_id]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(value)) { setError("Enter the 6-digit code."); return; } // client copy
    setError(undefined);
    const code = value;
    setValue("");
    await run({ kind: "code", cardId: block.card_id, code });
  };
  return (
    <Card>
      <CardHeader icon={<IconUser size={16} strokeWidth={1.8} aria-hidden="true" />} title="Verify" hint="Prove it's your account" meta={isLocked ? "Locked" : "Code sent"} />
      <form onSubmit={submit} className="space-y-3 p-3" noValidate>
        <p className="t-lead">{`I've sent a 6-digit code to ${block.hint}. Please type it here.`}</p>
        <Field label="6-digit code" error={error}>
          {({ id, describedBy, invalid }) => (
            <TextInput
              ref={input}
              id={id}
              name="code"
              className="t-code"
              inputMode="numeric"
              autoComplete="one-time-code"
              pattern="[0-9]*"
              maxLength={6}
              aria-describedby={describedBy}
              invalid={invalid || state === "wrong" || state === "expired"}
              disabled={fieldOff}
              value={value}
              onChange={(e) => setValue(e.target.value.replace(/\D/g, ""))}
            />
          )}
        </Field>
        {state === "sent" || state === "wrong" ? (
          <Button type="submit" variant="primary" disabled={fieldOff || pending}>Verify</Button>
        ) : null}
        {state === "expired" && block.resend_offered && resend ? (
          <Button variant="primary" disabled={props.disabled || pending} onClick={() => void run({ kind: "choice", cardId: block.card_id, option: "resend" })}>{resend.label}</Button>
        ) : null}
        {!isLocked ? (
          <p>
            <a href={block.inbox_link} target="_blank" rel="noopener noreferrer" className="link-text inline-flex min-h-[var(--target-min)] items-center text-ui font-semibold">Open the demo inbox →</a>
          </p>
        ) : null}
        <HintLine>{DEMO_HINT}</HintLine>
      </form>
    </Card>
  );
}
