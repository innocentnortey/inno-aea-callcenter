import { useNavigate } from "react-router";
import { useOp } from "@/api/useOp";
import { ErrorLine } from "@/components/shared/states";
import { QueueRow } from "@/components/shared/QueueRow";
import { Disclosure } from "@/components/ui";
import { caseHref } from "@/routes";
import { LiveRow } from "../scr05/LiveRow";

export function RailColumn({ currentRef, collapsible }: { currentRef: string | undefined; collapsible: boolean }) {
  const navigate = useNavigate();
  const q = useOp("getQueue", {}, { pollMs: 10_000 });
  const open = (ref: string) => navigate(caseHref(ref));
  const d = q.data;
  const list = d ? (
    <ul className="flex flex-col gap-1">
      {d.live.map((r) => <LiveRow key={r.reference} row={r} compact selected={r.reference === currentRef} onOpen={open} />)}
      {d.needs_my_action.map((r) => <QueueRow key={r.reference} row={r} selected={r.reference === currentRef} showStaffTags onSelect={open} />)}
    </ul>
  ) : q.status === "error" ? <ErrorLine message="The queue didn't load. Try again." onRetry={() => void q.refetch()} /> : <p className="text-small text-text-muted">Loading the queue.</p>;
  const count = d ? d.live.length + d.needs_my_action.length : 0;
  return collapsible ? (
    <Disclosure summary={<span className="t-section">Queue {"·"} {count} cases</span>}>{list}</Disclosure>
  ) : (
    <div className="flex flex-col gap-2">
      <h2 className="t-section">Queue</h2>
      {list}
    </div>
  );
}
