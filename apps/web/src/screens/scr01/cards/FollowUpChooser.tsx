import { useState } from "react";
import { Button } from "@/components/ui";
import type { BlockOf, ChatAction, Settled } from "../contract";
import { DoneLine } from "./parts/CardParts";
import { useCardAction } from "./parts/useCardAction";

export interface FollowUpChooserProps {
  block: BlockOf<"handoff">;
  settled: Settled | null;
  dispatch(a: ChatAction): Promise<void>;
  announce(m: string): void;
  landed(t: "visit" | "request" | "identity"): void;
  disabled: boolean;
}
type Channel = "email" | "phone";
type Window = "morning" | "afternoon" | "any";

function Radio({ name, value, checked, onChange, children }: { name: string; value: string; checked: boolean; onChange(): void; children: string }) {
  return (
    <label className="flex min-h-[var(--target-min)] cursor-pointer items-center gap-2 rounded-control border border-[color:var(--tile-edge)] bg-[var(--tile-bg)] px-3 text-ui">
      <input type="radio" name={name} value={value} checked={checked} onChange={onChange} className="size-4 accent-[var(--color-accent)]" />
      {children}
    </label>
  );
}

export function FollowUpChooser({ block, settled, dispatch, announce, landed, disabled }: FollowUpChooserProps) {
  const chooser = block.followup_chooser;
  const { pending, run } = useCardAction(dispatch);
  const [channel, setChannel] = useState<Channel>(chooser.channels.some((c) => c.channel === "email") ? "email" : (chooser.channels[0]?.channel ?? "email"));
  const [win, setWin] = useState<Window>("any");
  const saved = settled?.request && settled.request.reference === block.reference ? settled.request.followup : null;
  if (saved) return <DoneLine>{saved.saved_line}</DoneLine>;

  const chosen = chooser.channels.find((c) => c.channel === channel);
  const save = async () => {
    const destination = chooser.general_only || !chosen?.on_record ? "general" : "on_record";
    const ok = await run({ kind: "followUp", channel, destination, window: channel === "phone" ? win : "any" });
    if (ok) { landed("request"); announce("Follow-up saved"); }
  };
  const group = `channel-${block.block_id}`;
  return (
    <div className="space-y-3">
      <fieldset className="space-y-2">
        <legend className="text-small font-semibold">{chooser.legend}</legend>
        {chooser.channels.map((c) => (
          <Radio key={c.channel} name={group} value={c.channel} checked={channel === c.channel} onChange={() => setChannel(c.channel)}>{c.label}</Radio>
        ))}
      </fieldset>
      {channel === "phone" ? (
        <fieldset className="space-y-2">
          <legend className="text-small font-semibold">Best time to call</legend>
          {chooser.windows.map((w) => (
            <Radio key={w.window} name={`window-${block.block_id}`} value={w.window} checked={win === w.window} onChange={() => setWin(w.window)}>{w.label}</Radio>
          ))}
        </fieldset>
      ) : null}
      <Button variant="primary" loading={pending} disabled={disabled} onClick={() => void save()}>Save my choice</Button>
    </div>
  );
}
