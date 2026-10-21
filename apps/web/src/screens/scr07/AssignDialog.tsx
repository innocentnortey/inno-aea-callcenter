import { useState } from "react";
import { ApiError } from "@/api/errors";
import type { components } from "@/api/types.gen";
import { useAction, useOp } from "@/api/useOp";
import { ErrorLine } from "@/components/shared/states";
import { Button, Dialog, Field, TextArea } from "@/components/ui";
import { formatStaffTime } from "@/lib/time";
import { ASSIGNEES, PRIORITY_WORD, REASON_MISSING, type PriorityLevel } from "./copy";

type Row = components["schemas"]["QueueRow"];
export interface AssignDialogProps { row: Row | null; onClose(): void; onDone(line: string): Promise<void> }

export function AssignDialog({ row, onClose, onDone }: AssignDialogProps) {
  return (
    <Dialog open={row !== null} onClose={onClose} title={row ? `Assign or change priority · ${row.reference}` : ""} initialFocus="first">
      {row ? <AssignForm key={row.reference} row={row} onClose={onClose} onDone={onDone} /> : null}
    </Dialog>
  );
}

function AssignForm({ row, onClose, onDone }: { row: Row; onClose(): void; onDone(line: string): Promise<void> }) {
  const detail = useOp("getCase", { path: { reference: row.reference } });
  const action = useAction("applyCaseAction");
  const [mode, setMode] = useState<"assign" | "priority">("assign");
  const [assignee, setAssignee] = useState<"riley" | "supervisor">("riley");
  const [priority, setPriority] = useState<PriorityLevel>(row.priority.level as PriorityLevel);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [conflict, setConflict] = useState(false);
  const version = detail.data?.case.version;
  const canSubmit = reason.trim().length > 0 && version !== undefined && !action.pending;
  const ref = row.reference;

  async function submit() {
    if (version === undefined) return;
    setError(null);
    setConflict(false);
    const body = mode === "assign"
      ? ({ action: "assign", expected_version: version, assignee, reason: reason.trim() } as const)
      : ({ action: "change_priority", expected_version: version, priority, reason: reason.trim() } as const);
    try {
      await action.run({ path: { reference: ref }, body });
    } catch (e) {
      const err = e instanceof ApiError ? e : new ApiError(0, "NETWORK", null);
      if (err.code === "REASON_REQUIRED") setError(REASON_MISSING);
      else if (err.code === "VERSION_CONFLICT") {
        const d = err.details as { changed_by?: string; changed_at?: string } | null;
        const who = d?.changed_by ?? "someone";
        setError(`This case changed since you opened it (${who}${d?.changed_at ? ` at ${formatStaffTime(d.changed_at)}` : ""}). Reload to see it.`);
        setConflict(true);
      } else if (err.isRoleNotAllowed) setError("Assigning is for the demo supervisor.");
      else if (err.code === "CASE_NOT_FOUND") setError("That case isn't there any more. It may have been cleared by a demo reset.");
      else setError("Couldn't save. Try again.");
      return;
    }
    const line = mode === "assign"
      ? `Assigned ${ref} to ${ASSIGNEES.find((a) => a.value === assignee)!.label}.`
      : `Priority of ${ref} changed to ${priority} · ${PRIORITY_WORD[priority]}.`;
    await onDone(line);
    onClose();
  }

  const ownerErr = error;
  return (
    <form className="flex flex-col gap-3" onSubmit={(e) => { e.preventDefault(); if (canSubmit) void submit(); }}>
      <fieldset className="flex flex-col gap-1">
        <legend className="text-small font-semibold">What do you want to do?</legend>
        <label className="inline-flex min-h-[var(--target-min)] items-center gap-2 text-ui">
          <input type="radio" name="mode" checked={mode === "assign"} onChange={() => setMode("assign")} /> Assign to a person
        </label>
        <label className="inline-flex min-h-[var(--target-min)] items-center gap-2 text-ui">
          <input type="radio" name="mode" checked={mode === "priority"} onChange={() => setMode("priority")} /> Change priority
        </label>
      </fieldset>
      {mode === "assign" ? (
        <fieldset className="flex flex-col gap-1">
          <legend className="text-small font-semibold">Owner</legend>
          {ASSIGNEES.map((a) => (
            <label key={a.value} className="inline-flex min-h-[var(--target-min)] items-center gap-2 text-ui">
              <input type="radio" name="assignee" checked={assignee === a.value} onChange={() => setAssignee(a.value)} /> {a.label}
            </label>
          ))}
        </fieldset>
      ) : (
        <fieldset className="flex flex-col gap-1">
          <legend className="text-small font-semibold">Priority</legend>
          {(Object.keys(PRIORITY_WORD) as PriorityLevel[]).map((p) => (
            <label key={p} className="inline-flex min-h-[var(--target-min)] items-center gap-2 text-ui">
              <input type="radio" name="priority" checked={priority === p} onChange={() => setPriority(p)} /> {`${p} · ${PRIORITY_WORD[p]}`}
            </label>
          ))}
        </fieldset>
      )}
      <Field label="Reason" hint="Required." error={ownerErr ?? undefined}>
        {({ id, describedBy, invalid }) => (
          <TextArea id={id} density="console" aria-required="true" aria-describedby={describedBy} invalid={invalid} value={reason} onChange={(e) => setReason(e.target.value)} />
        )}
      </Field>
      {conflict ? <div><Button variant="text" density="console" onClick={() => { setError(null); setConflict(false); void detail.refetch(); }}>Reload</Button></div> : null}
      {version === undefined && !detail.error ? <p className="text-small text-text-muted">Loading the case{"…"}</p> : null}
      {detail.error && detail.data === undefined ? <ErrorLine message="Couldn't load this case. Try again." onRetry={() => void detail.refetch()} /> : null}
      <div className="flex justify-end gap-2">
        <Button density="console" data-dialog-cancel onClick={onClose}>Cancel</Button>
        <Button type="submit" variant="primary" density="console" loading={action.pending} disabled={!canSubmit}>
          {mode === "assign" ? "Assign" : "Change priority"}
        </Button>
      </div>
    </form>
  );
}
