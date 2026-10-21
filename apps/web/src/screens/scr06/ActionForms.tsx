import { useId, useState, type FormEvent, type ReactNode } from "react";
import type { components } from "@/api/types.gen";
import { Button, Field, TextArea, TextInput } from "@/components/ui";
import { demoDate, TIME_OPTIONS, toDemoIso } from "./wakeUp";

type CaseActionRequest = components["schemas"]["CaseActionRequest"];
type ActivityRequest = components["schemas"]["ActivityRequest"];
type FlagRequest = components["schemas"]["FlagRequest"];

export type Submission =
  | { kind: "case"; body: CaseActionRequest }
  | { kind: "contact"; body: ActivityRequest }
  | { kind: "flag"; body: FlagRequest };
export interface FormProps { onSubmit(s: Submission): void; onCancel(): void; busy: boolean; version: number }

function Shell(props: { title?: string; submit: string; onSubmit(): void; onCancel(): void; busy: boolean; children: ReactNode; hint?: string }) {
  const submit = (e: FormEvent) => { e.preventDefault(); props.onSubmit(); };
  return (
    <form
      onSubmit={submit}
      onKeyDown={(e) => { if (e.key === "Escape") { e.stopPropagation(); props.onCancel(); } }}
      className="flex flex-col gap-3 rounded-card bg-surface-well p-3"
    >
      {props.title ? <p className="t-card-title">{props.title}</p> : null}
      {props.children}
      {props.hint ? <p className="text-small text-text-muted">{props.hint}</p> : null}
      <div className="flex items-center gap-2">
        <Button type="submit" variant="primary" density="console" loading={props.busy}>{props.submit}</Button>
        <Button variant="text" density="console" onClick={props.onCancel}>Cancel</Button>
      </div>
    </form>
  );
}

function TextFormFactory(label: string, submit: string, build: (text: string, version: number) => CaseActionRequest) {
  return function TextForm({ onSubmit, onCancel, busy, version }: FormProps) {
    const [text, setText] = useState("");
    return (
      <Shell submit={submit} busy={busy} onCancel={onCancel} onSubmit={() => onSubmit({ kind: "case", body: build(text, version) })}>
        <Field label={label}>{(ids) => <TextArea id={ids.id} density="console" autoFocus value={text} onChange={(e) => setText(e.target.value)} />}</Field>
      </Shell>
    );
  };
}
export const ReleaseForm = TextFormFactory("Reason", "Release", (reason, v) => ({ action: "release", expected_version: v, reason }));
export const ResolveForm = TextFormFactory("Outcome", "Resolve", (outcome, v) => ({ action: "resolve", expected_version: v, outcome }));
export const CloseForm = TextFormFactory("Reason", "Close unresolved", (reason, v) => ({ action: "close_unresolved", expected_version: v, reason }));

export function WaitForm({ onSubmit, onCancel, busy, version, nowIso }: FormProps & { nowIso: string }) {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [reason, setReason] = useState("");
  const build = (): CaseActionRequest => {
    const wake = toDemoIso(date, time);
    return { action: "wait", expected_version: version, ...(wake ? { wake_up_at: wake } : {}), ...(reason ? { reason } : {}) };
  };
  return (
    <Shell submit="Set waiting" busy={busy} onCancel={onCancel} onSubmit={() => onSubmit({ kind: "case", body: build() })}>
      <Field label="Wake-up date">{(ids) => <TextInput id={ids.id} density="console" autoFocus type="date" min={demoDate(nowIso)} value={date} onChange={(e) => setDate(e.target.value)} />}</Field>
      <Field label="Wake-up time">
        {(ids) => (
          <select id={ids.id} className="min-h-[var(--target-min)] w-full rounded-control border border-[color:var(--field-edge)] bg-[var(--field-bg)] px-3 text-ui" value={time} onChange={(e) => setTime(e.target.value)}>
            <option value="">Choose a time</option>
            {TIME_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        )}
      </Field>
      <Field label="Reason (optional)">{(ids) => <TextInput id={ids.id} density="console" value={reason} onChange={(e) => setReason(e.target.value)} />}</Field>
    </Shell>
  );
}

function Radios<T extends string>(p: { legend: string; options: { value: T; label: string }[]; value: T | ""; onChange(v: T): void }) {
  const name = useId();
  return (
    <fieldset className="flex flex-col gap-1">
      <legend className="text-small font-semibold">{p.legend}</legend>
      {p.options.map((o, i) => (
        <label key={o.value} className="flex min-h-[var(--target-min)] items-center gap-2 text-ui">
          <input type="radio" name={name} value={o.value} checked={p.value === o.value} autoFocus={i === 0} required onChange={() => p.onChange(o.value)} className="size-4 accent-[var(--color-accent)]" />
          {o.label}
        </label>
      ))}
    </fieldset>
  );
}

export function ContactForm({ kind, onSubmit, onCancel, busy, version }: FormProps & { kind: "call" | "email" }) {
  const [outcome, setOutcome] = useState<ActivityRequest["outcome"] | "">("");
  const [note, setNote] = useState("");
  return (
    <Shell
      title={kind === "call" ? "Log a call" : "Log an email"} submit="Record" busy={busy} onCancel={onCancel}
      hint={kind === "call" ? "Demo: recorded, not sent. No call is placed." : "Demo: recorded, not sent."}
      onSubmit={() => onSubmit({ kind: "contact", body: { kind, outcome: outcome as ActivityRequest["outcome"], ...(note ? { note } : {}), expected_version: version } })}
    >
      <Radios<ActivityRequest["outcome"]> legend="Outcome" value={outcome} onChange={setOutcome} options={[
        { value: "reached", label: "Reached the customer" }, { value: "no_answer", label: "No answer" }, { value: "left_message", label: "Left a message" },
      ]} />
      <Field label="Note">{(ids) => <TextArea id={ids.id} density="console" value={note} onChange={(e) => setNote(e.target.value)} />}</Field>
    </Shell>
  );
}

export function FlagForm({ reference, lastAssistantMessageId, onSubmit, onCancel, busy }: Omit<FormProps, "version"> & { reference: string; lastAssistantMessageId: string | null }) {
  const [target, setTarget] = useState<FlagRequest["target"] | "">("");
  const [note, setNote] = useState("");
  return (
    <Shell
      title="Flag" submit="Add to review list" busy={busy} onCancel={onCancel}
      onSubmit={() => onSubmit({ kind: "flag", body: {
        case_ref: reference, target: target as FlagRequest["target"],
        ...(note ? { reason: note } : {}),
        ...(target === "answer" && lastAssistantMessageId ? { message_id: lastAssistantMessageId } : {}),
      } })}
    >
      <Radios<FlagRequest["target"]> legend="What is wrong" value={target} onChange={setTarget} options={[
        { value: "answer", label: "An answer was wrong" }, { value: "brief", label: "The brief left something out" }, { value: "escalation", label: "The escalation was not needed" },
      ]} />
      <Field label="Note">{(ids) => <TextArea id={ids.id} density="console" value={note} onChange={(e) => setNote(e.target.value)} />}</Field>
    </Shell>
  );
}

const selectCls = "min-h-[var(--target-min)] w-full rounded-control border border-[color:var(--field-edge)] bg-[var(--field-bg)] px-3 text-ui";
export function AssignForm({ onSubmit, onCancel, busy, version }: FormProps) {
  const [assignee, setAssignee] = useState<"riley" | "supervisor">("riley");
  const [reason, setReason] = useState("");
  return (
    <Shell submit="Assign" busy={busy} onCancel={onCancel} onSubmit={() => onSubmit({ kind: "case", body: { action: "assign", expected_version: version, assignee, reason } })}>
      <Field label="Assign to">
        {(ids) => (
          <select id={ids.id} autoFocus className={selectCls} value={assignee} onChange={(e) => setAssignee(e.target.value as "riley" | "supervisor")}>
            <option value="riley">Riley (demo representative)</option>
            <option value="supervisor">Demo supervisor</option>
          </select>
        )}
      </Field>
      <Field label="Reason">{(ids) => <TextArea id={ids.id} density="console" value={reason} onChange={(e) => setReason(e.target.value)} />}</Field>
    </Shell>
  );
}

const PRIORITIES = [["P0", "Safety"], ["P1", "Danger"], ["P2", "Time-sensitive"], ["P3", "Standard"], ["P4", "Routine"]] as const;
export function PriorityForm({ onSubmit, onCancel, busy, version }: FormProps) {
  const [priority, setPriority] = useState<"P0" | "P1" | "P2" | "P3" | "P4">("P3");
  const [reason, setReason] = useState("");
  return (
    <Shell submit="Change priority" busy={busy} onCancel={onCancel} onSubmit={() => onSubmit({ kind: "case", body: { action: "change_priority", expected_version: version, priority, reason } })}>
      <Field label="Priority">
        {(ids) => (
          <select id={ids.id} autoFocus className={selectCls} value={priority} onChange={(e) => setPriority(e.target.value as typeof priority)}>
            {PRIORITIES.map(([l, w]) => <option key={l} value={l}>{l} {"·"} {w}</option>)}
          </select>
        )}
      </Field>
      <Field label="Reason">{(ids) => <TextArea id={ids.id} density="console" value={reason} onChange={(e) => setReason(e.target.value)} />}</Field>
    </Shell>
  );
}
