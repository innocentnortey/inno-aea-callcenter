// The component kit at /__kit (mock mode only): every shared and ui component in its states, light and dark side by side.
// No API data: labels are obviously synthetic; the QueueRow literals are copied from the OpenAPI getQueue SEEDED example.
import { useState, type ReactNode } from "react";
import { cn } from "@/lib/cx";
import type { components } from "@/api/types.gen";
import { Button, Card, CardBody, CardHeader, CardRow, Checkbox, Dialog, Disclosure, Field, IconCalendar, IconClock, Kbd, Skeleton, Tag, TextArea, TextInput } from "@/components/ui";
import { AssistantMark, PersonDisc } from "@/components/shared/marks";
import { EventLine, MessageRow } from "@/components/shared/messages";
import { PriorityTag } from "@/components/shared/PriorityTag";
import { QueueRow } from "@/components/shared/QueueRow";
import { RefChip } from "@/components/shared/RefChip";
import { EmptyState, ErrorLine, ResultLine, StaleLine } from "@/components/shared/states";
import { Time, TimeWindow } from "@/components/shared/Time";
import { DemoBar, StaffingBanner } from "@/components/shell/chrome";
import { RoleSwitch } from "@/components/shell/RoleSwitch";
import { DemoStatusContext, type DemoStatusApi } from "@/state/demoStatus";
import { SessionContext, type SessionApi } from "@/state/session";
import { CLOCK_START, SESSION_REPRESENTATIVE, STAFFING_ON } from "@/test/fixtures";

type Row = components["schemas"]["QueueRow"];
// getQueue SEEDED: MHC-C-0008 (P0), MHC-C-0005 (overdue), MHC-C-0007 (on time)
const P0: Row = { reference: "MHC-C-0008", priority: { level: "P0", word: "Safety" }, reason: "Gas smell reported in chat", customer_display_name: "No name given", owner: null, created_at: "2026-10-16T14:16:00-05:00", due_at: null, due_label: null, due_state: "no_due_time", wake_up_at: null, lifecycle: "unassigned", follow_up_short: null, seed: true, brief_status: "ready", queued_at: null, age_label: "Open 4 min" };
const OVERDUE: Row = { reference: "MHC-C-0005", priority: { level: "P3", word: "Standard" }, reason: "Refund request", customer_display_name: "Dana Whitaker", owner: null, created_at: "2026-10-16T14:14:00-05:00", due_at: "2026-10-16T09:00:00-05:00", due_label: "Fri Oct 16 · 9:00 am", due_state: "overdue", wake_up_at: null, lifecycle: "unassigned", follow_up_short: "Email", seed: true, brief_status: "ready", queued_at: null, age_label: "Open 1 day 4 h" };
const ONTIME: Row = { reference: "MHC-C-0007", priority: { level: "P3", word: "Standard" }, reason: "Billing dispute", customer_display_name: "Omar Patel", owner: null, created_at: "2026-10-16T14:14:00-05:00", due_at: "2026-10-19T19:00:00-05:00", due_label: "Mon Oct 19 · 7:00 pm", due_state: "on_time", wake_up_at: null, lifecycle: "unassigned", follow_up_short: "Phone · mornings", seed: true, brief_status: "ready", queued_at: null, age_label: "Open 6 min" };
// kit-derived variants of MHC-C-0007 (waiting, being written, owned); the times reuse SEEDED values
const WAITING: Row = { ...ONTIME, lifecycle: "waiting", wake_up_at: "2026-10-19T19:00:00-05:00", brief_status: "being_written", owner: "Riley" };

const RILEY = { kind: "representative", display_name: "Riley" } as const;
const ASSISTANT = { kind: "assistant", display_name: "Meridian assistant" } as const;
const CUSTOMER = { kind: "customer", display_name: "You" } as const;

const fakeSession: SessionApi = {
  status: "ready", session: SESSION_REPRESENTATIVE, role: "representative", switching: null, switchError: null,
  switchRole: async () => undefined, signOut: async () => undefined, setSession: () => undefined,
};
const fakeDemo: DemoStatusApi = { clock: CLOCK_START, staffing: STAFFING_ON, refresh: async () => undefined, setFromChat: () => undefined, setSource: () => undefined };

function Section({ title, children }: { title: string; children: ReactNode }) {
  return <section className="mb-6"><h2 className="t-card-title mb-2">{title}</h2><div className="flex flex-col gap-3">{children}</div></section>;
}

function Showcase() {
  const [open, setOpen] = useState(false);
  return (
    <SessionContext.Provider value={fakeSession}>
      <DemoStatusContext.Provider value={fakeDemo}>
        <div className="flex flex-col gap-2 bg-canvas p-4 text-text">
          <Section title="Buttons">
            <div className="flex flex-wrap gap-2">
              <Button variant="primary">Primary</Button><Button>Secondary</Button><Button variant="send">Send</Button><Button variant="text">Text button</Button>
              <Button variant="primary" loading>Loading</Button><Button disabled>Disabled</Button><Button density="console">Console</Button>
            </div>
          </Section>
          <Section title="Fields">
            <Field label="Example field" hint="A hint under the label">{(f) => <TextInput id={f.id} aria-describedby={f.describedBy} placeholder="" />}</Field>
            <Field label="Invalid field" error="An example message">{(f) => <TextInput id={f.id} aria-describedby={f.describedBy} invalid={f.invalid} />}</Field>
            <Field label="Text area">{(f) => <TextArea id={f.id} />}</Field>
            <Checkbox label="Example checkbox" />
          </Section>
          <Section title="Tags and priorities">
            <div className="flex flex-wrap gap-2">
              <Tag>Plain</Tag><Tag tone="strong" icon={<IconClock size={14} />}>Strong</Tag>
              {(["P0", "P1", "P2", "P3", "P4"] as const).map((l, i) => <PriorityTag key={l} priority={{ level: l, word: (["Safety", "Danger", "Time-sensitive", "Standard", "Routine"] as const)[i] }} />)}
            </div>
          </Section>
          <Section title="Card, skeleton, disclosure, dialog">
            <Card><CardHeader icon={<IconCalendar size={16} />} title="Example card" hint="hint" meta="meta" /><CardBody><CardRow label="Example label">Example value</CardRow><CardRow label="Reference" mono>MHC-C-0007</CardRow></CardBody></Card>
            <Skeleton height={20} rows={2} />
            <Disclosure summary="Example disclosure">Hidden content</Disclosure>
            <Button onClick={() => setOpen(true)}>Open example dialog</Button>
            <Dialog open={open} onClose={() => setOpen(false)} title="Example dialog" initialFocus="cancel">
              <p>Example dialog body.</p>
              <div className="mt-3 flex gap-2"><Button data-dialog-cancel onClick={() => setOpen(false)}>Cancel</Button></div>
            </Dialog>
          </Section>
          <Section title="Times, references, marks">
            <p><Time iso="2026-10-19T19:00:00-05:00" format="short" variant="row" /> <TimeWindow startIso="2026-10-21T08:00:00-05:00" endIso="2026-10-21T12:00:00-05:00" arrow variant="hero" /></p>
            <p className="flex items-center gap-2"><RefChip reference="MHC-C-0007" copyable /><AssistantMark size={24} /><PersonDisc initial="R" /><Kbd>J</Kbd></p>
          </Section>
          <Section title="Messages">
            <MessageRow speaker={ASSISTANT} at="2026-10-16T14:20:00-05:00" layout="bubble">Assistant example</MessageRow>
            <MessageRow speaker={CUSTOMER} at="2026-10-16T14:21:00-05:00" layout="bubble">Customer example</MessageRow>
            <MessageRow speaker={RILEY} at="2026-10-16T14:22:00-05:00" layout="bubble">Representative example</MessageRow>
            <MessageRow speaker={RILEY} at="2026-10-16T14:22:00-05:00" layout="flat">Flat transcript example</MessageRow>
            <EventLine at="2026-10-16T14:22:00-05:00">Example event</EventLine>
          </Section>
          <Section title="Lines and states">
            <ErrorLine message="Example error line." onRetry={() => undefined} /><EmptyState title="Example empty" body="Example body" /><StaleLine actionLabel="Show them" onAction={() => undefined}>Example stale line.</StaleLine><ResultLine>Example result line.</ResultLine>
          </Section>
          <Section title="Queue rows">
            <ul className="flex flex-col gap-1">
              <QueueRow row={P0} /><QueueRow row={OVERDUE} /><QueueRow row={ONTIME} selected /><QueueRow row={WAITING} />
            </ul>
          </Section>
          <Section title="Shell">
            <DemoBar /><StaffingBanner /><RoleSwitch /><RoleSwitch variant="row" density="console" />
          </Section>
        </div>
      </DemoStatusContext.Provider>
    </SessionContext.Provider>
  );
}

export function Kit() {
  return (
    <main id="main" tabIndex={-1}>
      <h1 className="t-title p-4">Component kit (prototype only)</h1>
      <div className={cn("grid min-[900px]:grid-cols-2")}>
        <div data-kit-theme="light" className="bg-canvas text-text"><Showcase /></div>
        <div data-kit-theme="dark" className="bg-canvas text-text"><Showcase /></div>
      </div>
    </main>
  );
}
