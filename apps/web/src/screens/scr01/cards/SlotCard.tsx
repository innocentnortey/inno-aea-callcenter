import { useState } from "react";
import * as Tabs from "@radix-ui/react-tabs";
import { Button, Card, CardHeader, CardRow, IconCalendar, Tag } from "@/components/ui";
import { cn } from "@/lib/cx";
import type { BlockProps } from "../contract";
import { HintLine, choiceKept } from "./parts/CardParts";
import { OptionTile } from "./parts/OptionTile";
import { useCardAction } from "./parts/useCardAction";

export function SlotCard(props: BlockProps<"slot_card">) {
  const { block } = props;
  const { pending, run } = useCardAction(props.dispatch);
  const [picked, setPicked] = useState<string | null>(null);
  const firstOpen = block.days.find((d) => d.open_count > 0) ?? block.days[0];
  const [tab, setTab] = useState(firstOpen?.date ?? "");
  const kept = choiceKept(block, props);
  const locked = kept || props.disabled || pending;
  const chosen = block.answered ?? picked;

  return (
    <Card>
      <CardHeader
        icon={<IconCalendar size={16} strokeWidth={1.8} aria-hidden="true" />}
        title="Choose a window"
        hint="The technician arrives any time in the window you pick"
        meta={<span className="inline-flex items-center gap-2">{block.urgent ? <Tag tone="strong">Urgent</Tag> : null}<span>this week</span></span>}
      />
      <div className="space-y-3 p-3">
        <Tabs.Root value={tab} onValueChange={setTab}>
          <Tabs.List aria-label="Day" className="flex gap-1 overflow-x-auto border-b border-border-hair">
            {block.days.map((d) => {
              const [top, ...rest] = d.label.split(" · ");
              return (
                <Tabs.Trigger
                  key={d.date}
                  value={d.date}
                  className={cn("motion-control min-h-[var(--target-min)] shrink-0 px-3 text-ui", "data-[state=active]:border-b-2 data-[state=active]:border-[color:var(--tab-underline)] data-[state=active]:font-semibold")}
                >
                  <span className="block">{top}</span>
                  {rest.length ? <span className="block text-small text-text-muted">{rest.join(" · ")}</span> : null}
                </Tabs.Trigger>
              );
            })}
          </Tabs.List>
          {block.days.map((d) => (
            <Tabs.Content key={d.date} value={d.date} className="pt-3">
              <div className="grid grid-cols-2 gap-2">
                {d.windows.map((w) => {
                  const suffix = w.taken ? "taken" : w.member_only ? "members only" : "open";
                  return (
                    <OptionTile
                      key={w.slot_id}
                      label={<span className="t-time-row">{w.window_label}</span>}
                      accessibleName={`${w.window_label}, ${suffix}`}
                      taken={w.taken}
                      selected={chosen === w.slot_id}
                      disabled={locked}
                      tag={w.member_only ? <Tag>Members</Tag> : undefined}
                      onClick={() => setPicked(w.slot_id)}
                    />
                  );
                })}
              </div>
            </Tabs.Content>
          ))}
        </Tabs.Root>
        <CardRow label="Standard fee" hint="What you pay if you're not a member">{block.standard_fee.display}</CardRow>
        <HintLine>{block.hint}</HintLine>
        {block.members_note ? <HintLine>{block.members_note}</HintLine> : null}
        {!chosen ? <HintLine>Choose a window to continue.</HintLine> : null}
        <Button variant="primary" disabled={!picked || locked} onClick={() => picked && void run({ kind: "choice", cardId: block.card_id, option: picked })}>
          Continue with this window
        </Button>
      </div>
    </Card>
  );
}
