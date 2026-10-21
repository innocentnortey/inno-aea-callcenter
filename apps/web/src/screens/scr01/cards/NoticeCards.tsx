import { Button, Card, CardHeader, IconClock, IconInfo } from "@/components/ui";
import type { BlockProps } from "../contract";
import { InlineNotice, PersonKey } from "./parts/CardParts";
import { useCardAction } from "./parts/useCardAction";

export function NoticeCard(props: BlockProps<"notice">) {
  const { block } = props;
  const { pending, run } = useCardAction(props.dispatch);
  switch (block.code) {
    case "TURN_TIMEOUT":
      return (
        <Card>
          <CardHeader icon={<IconClock size={16} strokeWidth={1.8} aria-hidden="true" />} title={block.text} />
          <div className="flex flex-wrap gap-2 p-3">
            <Button variant="primary" loading={pending} disabled={props.answered} onClick={() => void run({ kind: "retry", turnId: "" })}>Try again</Button>
            <PersonKey dispatch={props.dispatch} />
          </div>
        </Card>
      );
    case "BUSY":
      return (
        <div className="space-y-2">
          <p className="text-body">{block.text}</p>
          <PersonKey dispatch={props.dispatch} />
        </div>
      );
    case "AI_PAUSED":
      return (
        <div className="space-y-2">
          <InlineNotice>{block.text}</InlineNotice>
          {block.person_key ? <PersonKey dispatch={props.dispatch} /> : null}
        </div>
      );
    default:
      return (
        <Card>
          <div className="space-y-3 p-3">
            <p className="flex items-start gap-2 text-body">
              <IconInfo size={16} strokeWidth={1.8} aria-hidden="true" className="mt-1 shrink-0" />
              <span>{block.text}</span>
            </p>
            {block.person_key ? <PersonKey dispatch={props.dispatch} /> : null}
          </div>
        </Card>
      );
  }
}

export function FailureOfferCard({ block, dispatch }: BlockProps<"failure_offer">) {
  return (
    <div className="space-y-2">
      <p className="text-body">{block.text}</p>
      {block.person_key ? <PersonKey dispatch={dispatch} /> : null}
    </div>
  );
}
export function NoInfoCard({ block, dispatch }: BlockProps<"no_info">) {
  return (
    <div className="space-y-2">
      <p className="text-body">{block.text}</p>
      {block.person_key ? <PersonKey dispatch={dispatch} /> : null}
    </div>
  );
}
