import { useState, type FormEvent } from "react";
import { Button, Card, CardHeader, Field, IconUser, TextInput } from "@/components/ui";
import type { BlockProps } from "../contract";
import { HintLine, choiceKept } from "./parts/CardParts";
import { useCardAction } from "./parts/useCardAction";

type Key = "name" | "phone" | "customer_id" | "invoice_number";
const LABEL: Record<Key, string> = { name: "Name on the account", phone: "Phone", customer_id: "Customer ID", invoice_number: "Invoice number" };
const SWITCH: Record<string, string> = { "name,phone": "Use my name and phone instead", customer_id: "Use my customer ID instead", invoice_number: "Use my invoice number instead" };
const DEMO_HINT = "Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries.";

export function LocatePromptCard(props: BlockProps<"locate_prompt">) {
  const { block } = props;
  const { pending, run } = useCardAction(props.dispatch);
  const [active, setActive] = useState(0);
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | undefined>();
  const [sent, setSent] = useState(false);
  const locked = choiceKept(block, props) || props.disabled || pending || sent;
  const set = block.field_sets[active] ?? [];

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (set.some((k) => !(values[k] ?? "").trim())) { setError("Fill in every field above."); return; } // client copy
    setError(undefined);
    const out: Record<string, string> = {};
    for (const k of set) out[k] = values[k].trim();
    const ok = await run({ kind: "form", cardId: block.card_id, values: out });
    if (ok) { setSent(true); setValues({}); }
  };
  return (
    <Card>
      <CardHeader icon={<IconUser size={16} strokeWidth={1.8} aria-hidden="true" />} title="Verify" hint="Prove it's your account" meta="Before booking" />
      <form onSubmit={submit} className="space-y-3 p-3" noValidate>
        <p className="text-body">{block.reason_text}</p>
        {set.map((k, i) => (
          <Field key={k} label={LABEL[k as Key]} error={i === set.length - 1 ? error : undefined}>
            {({ id, describedBy, invalid }) => (
              <TextInput
                id={id}
                name={k}
                type={k === "phone" ? "tel" : "text"}
                autoComplete={k === "phone" ? "tel" : "off"}
                aria-describedby={describedBy}
                invalid={invalid}
                disabled={locked}
                value={values[k] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [k]: e.target.value }))}
              />
            )}
          </Field>
        ))}
        {block.field_sets.length > 1 ? (
          <div className="flex flex-wrap gap-2">
            {block.field_sets.map((s, i) => i === active ? null : (
              <Button key={s.join(",")} variant="text" disabled={locked} onClick={() => { setActive(i); setError(undefined); }}>
                {SWITCH[s.join(",")] ?? "Use another detail instead"}
              </Button>
            ))}
          </div>
        ) : null}
        <Button type="submit" variant="primary" disabled={locked}>Send the code</Button>
        <HintLine>{DEMO_HINT}</HintLine>
      </form>
    </Card>
  );
}
