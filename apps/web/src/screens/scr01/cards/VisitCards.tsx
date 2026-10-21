import type { ReactNode } from "react";
import { Card, CardHeader, CardRow, IconCheck, Tag } from "@/components/ui";
import { Time, TimeWindow } from "@/components/shared/Time";
import { formatDayLong, formatDayShort, formatTimePoint } from "@/lib/time";
import type { BlockProps, Settled } from "../contract";
import { DoneLine, StepList, hasWrite } from "./parts/CardParts";
import { chicagoIso, dayIso, parseWindowLabel, spokenWindow, windowIsos } from "./parts/dates";
import { useLandedOnce } from "./parts/landed";

type WindowBlock = { appointment_id: number; date: string; window_label: string };

function windowFor(block: WindowBlock, settled: Settled | null): { startIso: string; endIso: string } | null {
  const v = settled?.visit;
  if (v && v.appointment_id === block.appointment_id) return windowIsos(block.date, v.window);
  const p = parseWindowLabel(block.window_label);
  return p ? { startIso: chicagoIso(block.date, p.start), endIso: chicagoIso(block.date, p.end) } : null;
}

function VisitBody({ block, settled, children }: { block: WindowBlock & { technician: string; fee_line: string }; settled: Settled | null; children?: ReactNode }) {
  const win = windowFor(block, settled);
  return (
    <div className="space-y-2 p-3">
      {win ? <TimeWindow arrow variant="hero" startIso={win.startIso} endIso={win.endIso} /> : <p className="t-time-hero">{block.window_label}</p>}
      {win ? <p className="text-ui text-text-muted">{`${formatDayLong(dayIso(block.date))} · arrives between ${formatTimePoint(win.startIso)} and ${formatTimePoint(win.endIso)}`}</p> : null}
      <div>
        <CardRow label="Date"><Time iso={dayIso(block.date)} format="day" variant="row" /></CardRow>
        <CardRow label="Technician">{block.technician}</CardRow>
        <CardRow label="Fee that applies">{block.fee_line}</CardRow>
      </div>
      {children}
    </div>
  );
}

export function ConfirmationCard(props: BlockProps<"confirmation">) {
  const { block, settled } = props;
  const booked = hasWrite(settled, "booked") || hasWrite(settled, "moved");
  useLandedOnce(block.block_id, "visit", `Your visit: ${formatDayLong(dayIso(block.date))}, ${spokenWindow(block.window_label)}`, props);
  return (
    <Card>
      <CardHeader icon={<IconCheck size={16} strokeWidth={1.8} aria-hidden="true" />} title="Your visit" hint="Your booking" meta={booked ? <Tag icon={<IconCheck size={14} strokeWidth={1.8} aria-hidden="true" />}>Booked</Tag> : null} />
      <VisitBody block={block} settled={settled}>
        <div className="space-y-2">
          <h4 className="text-small font-semibold">What happens next</h4>
          <StepList steps={block.timeline.map((text, i) => ({ text, state: i === 0 ? "done" : i === 1 ? "current" : "todo", at: i === 0 ? block.at : undefined }))} />
          <p className="text-ui">{block.free_change_note}</p>
        </div>
        <CardRow label="Keep this" hint="Save or screenshot this">{`${formatDayShort(dayIso(block.date))} · ${block.window_label}`}</CardRow>
      </VisitBody>
    </Card>
  );
}

export function AppointmentCard({ block, settled }: BlockProps<"appointment">) {
  return (
    <Card>
      <CardHeader icon={<IconCheck size={16} strokeWidth={1.8} aria-hidden="true" />} title={block.label} hint="Your booking" />
      <VisitBody block={block} settled={settled} />
    </Card>
  );
}

export function CancelledCard(props: BlockProps<"cancelled">) {
  const { block, settled } = props;
  const done = hasWrite(settled, "cancelled");
  return (
    <div className="space-y-1">
      {done ? <CancelledDone {...props} /> : null}
      <p className="text-ui">{block.fee_line}</p>
    </div>
  );
}
function CancelledDone(props: BlockProps<"cancelled">) {
  const label = formatDayShort(dayIso(props.block.date));
  useLandedOnce(props.block.block_id, "visit", `Visit on ${label} cancelled`, props);
  return <DoneLine>{`Your visit on ${label} is cancelled.`}</DoneLine>;
}
