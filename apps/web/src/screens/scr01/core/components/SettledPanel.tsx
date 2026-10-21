import type { ReactNode } from "react";
import { cn } from "@/lib/cx";
import { Card, CardHeader, CardRow } from "@/components/ui";
import { RefChip } from "@/components/shared/RefChip";
import { Time } from "@/components/shared/Time";
import type { Settled } from "../../contract";
import type { ChatState } from "../model";
import { followUpLabel, identityLine, promiseSentence, type LandTarget } from "../settledSummary";
import { formatDateOnlyShort, formatWindow } from "../visit";

export interface SettledPanelProps {
  settled: Settled | null; danger: boolean; replying: ChatState["replying"]; staffingOn: boolean;
  landing: { target: LandTarget; nonce: number } | null;
}

function Block({ title, hint, target, landing, empty, children }: { title: string; hint?: string; target?: LandTarget; landing: SettledPanelProps["landing"]; empty?: boolean; children: ReactNode }) {
  const landed = target !== undefined && landing?.target === target;
  return (
    <Card className={cn(empty && "border-dashed bg-transparent")} data-block={target}>
      <CardHeader as="h3" title={title} hint={hint} className={cn(landed && "landed")} key={landed ? landing?.nonce : "rest"} />
      <div className="px-3 py-2 text-ui">{children}</div>
    </Card>
  );
}

/** R4 body. Renders from `settled` only (N-4, N-27), never from the last turn. */
export function SettledPanel({ settled, danger, replying, staffingOn, landing }: SettledPanelProps) {
  const v = settled?.visit ?? null;
  const r = settled?.request ?? null;
  const originalStays = v ? v.status === "original_stays" || v.change_request != null : false;
  const earlier = (settled?.actions ?? []).filter((a) => a.kind === "booked" || a.kind === "moved" || a.kind === "cancelled").slice(0, -1);
  return (
    <div className="flex flex-col gap-3 p-3.5">
      <div>
        <h2 className="t-name">{"What's settled"}</h2>
        <p className="text-small text-text-muted">{"What's been confirmed so far"}</p>
      </div>
      {danger ? null : (
        <>
          {staffingOn ? (
            <Block title="Replying" hint="Who is answering you now" landing={landing}>
              {replying.kind === "human" ? `${replying.display_name ?? "A representative"} (demo representative). Assistant paused.` : "The automated assistant"}
            </Block>
          ) : null}
          <Block title="Your visit" hint="Your booking" target="visit" landing={landing} empty={!v}>
            {v ? (
              <div>
                <p className="t-time-hero">{formatWindow(v.window, v.window_label)}</p>
                <p className="text-small text-text-muted">{formatDateOnlyShort(v.date)}</p>
                <CardRow label="Technician">{v.technician}</CardRow>
                <CardRow label="Fee">{v.fee_line}</CardRow>
                {originalStays ? <p className="text-small">Original stays until a representative confirms.</p> : null}
                {v.change_request ? (
                  <>
                    <CardRow label="Requested">{v.change_request.wanted_text}</CardRow>
                    <CardRow label="Fee">{v.change_request.fee_line}</CardRow>
                  </>
                ) : null}
                {earlier.length > 0 ? (
                  <ul className="mt-2 text-small text-text-muted">
                    {earlier.map((a, i) => <li key={`${a.turn_id}:${i}`}>{a.summary}</li>)}
                  </ul>
                ) : null}
              </div>
            ) : "Nothing booked yet."}
          </Block>
          <Block title="Your request" target="request" landing={landing} empty={!r}>
            {r ? (
              <div>
                <CardRow label="Reference" hint="Your reference number"><RefChip reference={r.reference} copyable /></CardRow>
                {r.live_queued && replying.kind === "human" ? (
                  <p className="t-lead">A representative has joined this chat.</p>
                ) : r.live_queued ? (
                  <p className="t-lead">{r.promise_text}</p>
                ) : (
                  <p className="t-lead">{promiseSentence(r)}</p>
                )}
                {r.due_at ? (
                  <CardRow label="Due" hint="The latest we've promised to get back to you">
                    <Time iso={r.due_at} format="short" variant="due" />
                  </CardRow>
                ) : null}
                <CardRow label="Follow-up">{r.followup ? followUpLabel(r.followup) : "Not chosen yet"}</CardRow>
              </div>
            ) : "No request open."}
          </Block>
          <Block title="Identity" hint="Whether you've confirmed it's you" target="identity" landing={landing}>
            {settled ? identityLine(settled.identity) : "Not checked. Only needed for private details."}
          </Block>
        </>
      )}
    </div>
  );
}
