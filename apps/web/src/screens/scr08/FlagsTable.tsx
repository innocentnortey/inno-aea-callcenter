import { useState } from "react";
import { Link } from "react-router";
import type { components } from "@/api/types.gen";
import { Time } from "@/components/shared/Time";
import { Button, Field, Tag, TextInput } from "@/components/ui";
import { caseHref } from "@/routes";

type Flag = components["schemas"]["Flag"];
const KIND: Record<Flag["target"], string> = { answer: "Answer", brief: "Brief", escalation: "Escalation" };

export interface FlagsTableProps {
  flags: Flag[]; canReview: boolean; hintId: string;
  editing: string | null; onEdit(flagId: string | null): void;
  onReview(flag: Flag, note: string | null): Promise<void>; pendingId: string | null; rowError: { id: string; message: string } | null;
}

const cell = "px-3 py-2 align-top max-[699px]:flex max-[699px]:justify-between max-[699px]:gap-3";
function Label({ children }: { children: string }) {
  return <span className="text-small text-text-muted min-[700px]:sr-only">{children}</span>;
}

export function FlagsTable({ flags, canReview, hintId, editing, onEdit, onReview, pendingId, rowError }: FlagsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-ui">
        <caption className="sr-only">Flags, newest first</caption>
        <thead className="max-[699px]:sr-only">
          <tr className="text-left text-small text-text-muted">
            {["Kind", "Reason", "Case", "Flagged", "Status", "Action"].map((h) => <th key={h} scope="col" className="px-3 py-2 font-semibold">{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {flags.map((f) => (
            <tr key={f.flag_id} className="border-t border-dashed border-border-hair max-[699px]:block max-[699px]:py-2">
              <td className={cell}><Label>Kind</Label><span className="font-semibold">{KIND[f.target]}</span></td>
              <td className={cell}>
                <Label>Reason</Label>
                <span>
                  {f.reason ?? "No reason given."}
                  {f.note ? <span className="block text-small text-text-muted">Note: {f.note}</span> : null}
                </span>
              </td>
              <td className={cell}>
                <Label>Case</Label>
                <span className="flex flex-col">
                  <Link to={caseHref(f.case_ref)} className="t-ref link-text">{f.case_ref}</Link>
                  {f.message_id ? (
                    <Link to={`${caseHref(f.case_ref)}?tab=conversation&message=${encodeURIComponent(f.message_id)}`} className="text-small link-text">Open the message</Link>
                  ) : null}
                </span>
              </td>
              <td className={cell}>
                <Label>Flagged</Label>
                <span className="flex flex-col"><span>{f.flagged_by}</span><Time iso={f.at} format="short" variant="meta" className="text-text-muted" /></span>
              </td>
              <td className={cell}>
                <Label>Status</Label>
                <span className="flex flex-col items-start gap-1">
                  <Tag tone={f.status === "new" ? "strong" : "plain"}>{f.status === "new" ? "New" : "Reviewed"}</Tag>
                  {f.status === "reviewed" && f.reviewed_by ? <span className="text-small text-text-muted">by {f.reviewed_by}</span> : null}
                  {f.status === "reviewed" && f.reviewed_note ? <span className="text-small text-text-muted">{f.reviewed_note}</span> : null}
                </span>
              </td>
              <td className={cell}>
                <Label>Action</Label>
                <span className="flex flex-col items-start gap-2">
                  {f.status === "new" ? (
                    editing === f.flag_id ? (
                      <ReviewEditor flag={f} pending={pendingId === f.flag_id} onCancel={() => onEdit(null)} onConfirm={(note) => onReview(f, note)} />
                    ) : (
                      <Button
                        density="console" disabled={!canReview} aria-describedby={canReview ? undefined : hintId}
                        aria-label={`Mark reviewed, flag on ${f.case_ref}`} onClick={() => onEdit(f.flag_id)}
                      >
                        Mark reviewed
                      </Button>
                    )
                  ) : null}
                  {rowError && rowError.id === f.flag_id ? <span className="text-small">{rowError.message}</span> : null}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ReviewEditor({ flag, pending, onCancel, onConfirm }: { flag: Flag; pending: boolean; onCancel(): void; onConfirm(note: string | null): Promise<void> }) {
  const [note, setNote] = useState("");
  return (
    <div className="flex flex-col gap-2">
      <Field label="Note (optional)">
        {({ id, describedBy }) => <TextInput id={id} density="console" aria-describedby={describedBy} value={note} onChange={(e) => setNote(e.target.value)} />}
      </Field>
      <div className="flex gap-2">
        <Button variant="primary" density="console" loading={pending} aria-label={`Mark reviewed, flag on ${flag.case_ref}`} onClick={() => void onConfirm(note.trim() === "" ? null : note.trim())}>
          Mark reviewed
        </Button>
        <Button density="console" onClick={onCancel}>Cancel</Button>
      </div>
    </div>
  );
}
