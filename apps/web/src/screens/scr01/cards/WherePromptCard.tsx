import { useState, type FormEvent } from "react";
import { Button, Card, Field, TextInput } from "@/components/ui";
import type { BlockProps } from "../contract";
import { choiceKept } from "./parts/CardParts";
import { useCardAction } from "./parts/useCardAction";

export function WherePromptCard(props: BlockProps<"where_prompt">) {
  const { block } = props;
  const { pending, run } = useCardAction(props.dispatch);
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | undefined>();
  const [sent, setSent] = useState(false);
  const locked = choiceKept(block, props) || props.disabled || pending || sent;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const v = value.trim();
    if (!v) { setError("Enter a ZIP code or city."); return; } // client copy
    setError(undefined);
    const ok = await run({ kind: "form", cardId: block.card_id, values: { zip_or_city: v } });
    if (ok) setSent(true);
  };
  return (
    <Card>
      <form onSubmit={submit} className="space-y-3 p-3" noValidate>
        <Field label={block.label} error={error}>
          {({ id, describedBy, invalid }) => (
            <TextInput id={id} name="zip_or_city" autoComplete="postal-code" aria-describedby={describedBy} invalid={invalid} disabled={locked} value={value} onChange={(e) => setValue(e.target.value)} />
          )}
        </Field>
        <Button type="submit" variant="primary" disabled={locked}>{block.submit_label}</Button>
      </form>
    </Card>
  );
}
