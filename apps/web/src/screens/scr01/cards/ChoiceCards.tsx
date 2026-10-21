import { useState } from "react";
import { Button, Card } from "@/components/ui";
import type { BlockProps } from "../contract";
import { OptionTile } from "./parts/OptionTile";
import { choiceKept } from "./parts/CardParts";
import { useCardAction } from "./parts/useCardAction";
import { SourceChipView } from "./SourceChipView";

export function BurningCheckCard(props: BlockProps<"burning_check">) {
  const { block } = props;
  const { pending, run } = useCardAction(props.dispatch);
  const [picked, setPicked] = useState<string | null>(null);
  const kept = choiceKept(block, props);
  const locked = kept || props.disabled || pending;
  const chosen = block.answered ?? picked;
  return (
    <Card>
      <div className="space-y-3 p-3">
        <p className="text-body">{block.question}</p>
        <div className="flex flex-wrap gap-2">
          {block.options.map((o) => (
            <OptionTile
              key={o.option}
              label={o.label}
              selected={chosen === o.option}
              disabled={locked || o.disabled}
              onClick={() => { setPicked(o.option); void run({ kind: "choice", cardId: block.card_id, option: o.option }); }}
            />
          ))}
        </div>
      </div>
    </Card>
  );
}

export function QuickChecksCard(props: BlockProps<"quick_checks">) {
  const { block } = props;
  const { pending, run } = useCardAction(props.dispatch);
  const locked = choiceKept(block, props) || props.disabled || pending;
  return (
    <Card>
      <div className="space-y-3 p-3">
        <p className="text-body">{block.offer_text}</p>
        {block.checks ? (
          <ul className="list-disc space-y-2 pl-5 text-ui">
            {block.checks.map((c) => (
              <li key={c.text}>
                {c.text}
                <SourceChipView source={c.source} />
              </li>
            ))}
          </ul>
        ) : null}
        <div className="flex flex-wrap gap-2">
          {block.options.map((o) => (
            <Button
              key={o.option}
              variant={o.option === "skip_and_book" ? "primary" : "secondary"}
              disabled={locked || o.disabled}
              onClick={() => void run({ kind: "choice", cardId: block.card_id, option: o.option })}
            >
              {o.label}
            </Button>
          ))}
        </div>
      </div>
    </Card>
  );
}

export function UrgencyQuestionsCard(props: BlockProps<"urgency_questions">) {
  const { block } = props;
  const { pending, run } = useCardAction(props.dispatch);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [skipped, setSkipped] = useState(false);
  const kept = choiceKept(block, props);
  const locked = kept || props.disabled || pending || skipped;
  const skip = block.options.find((o) => o.option === "skip");

  const pick = (qid: string, option: string) => {
    const next = { ...answers, [qid]: option };
    setAnswers(next);
    if (block.questions.every((q) => next[q.question_id])) {
      void run({ kind: "choice", cardId: block.card_id, option: block.questions.map((q) => `${q.question_id}:${next[q.question_id]}`).join(";") });
    }
  };
  return (
    <Card>
      <div className="space-y-4 p-3">
        {block.questions.map((q) => (
          <fieldset key={q.question_id} className="space-y-2">
            <legend className="text-body">{q.text}</legend>
            <div className="flex flex-wrap gap-2">
              {q.answers.map((a) => (
                <OptionTile
                  key={a.option}
                  label={a.label}
                  selected={answers[q.question_id] === a.option}
                  disabled={locked || a.disabled}
                  onClick={() => pick(q.question_id, a.option)}
                />
              ))}
            </div>
          </fieldset>
        ))}
        {skip ? (
          <Button
            variant="text"
            disabled={locked}
            onClick={() => { setSkipped(true); void run({ kind: "choice", cardId: block.card_id, option: "skip" }); }}
          >
            {skip.label}
          </Button>
        ) : null}
      </div>
    </Card>
  );
}
