import { IconInfo, Tag } from "@/components/ui";
import { formatTimePoint } from "@/lib/time";
import { cn } from "@/lib/cx";
import { humanizeKey } from "./caseText";

type Rec = Record<string, unknown>;
export interface SnapshotTableProps { snapshot: Rec; current: Rec | null; asOf: string; unavailable: boolean }

export function SnapshotTable({ snapshot, current, asOf, unavailable }: SnapshotTableProps) {
  const keys = Object.keys(snapshot);
  if (keys.length === 1 && keys[0] === "passage") {
    const now = current && typeof current.passage === "string" ? current.passage : null;
    return (
      <div className="flex flex-col gap-2">
        <blockquote className="rounded-control bg-surface-well p-3 text-body">{String(snapshot.passage)}</blockquote>
        {now && now !== snapshot.passage ? (
          <>
            <p className="text-small font-semibold">Now</p>
            <blockquote className="rounded-control bg-surface-well p-3 text-body">{now}</blockquote>
          </>
        ) : null}
      </div>
    );
  }
  const showNow = !unavailable && current != null;
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-ui">
        <caption className="sr-only">What the AI saw and what is true now</caption>
        <thead>
          <tr className="text-left text-small text-text-muted">
            <th scope="col" className="py-1 pr-2 font-normal"><span className="sr-only">Field</span></th>
            <th scope="col" className="py-1 px-2 text-right font-semibold">What the AI saw</th>
            {showNow ? <th scope="col" className="py-1 pl-2 text-right font-semibold">Now {"·"} {formatTimePoint(asOf)}</th> : null}
          </tr>
        </thead>
        <tbody>
          {keys.map((k) => {
            const changed = showNow && String(snapshot[k]) !== String(current?.[k]);
            return (
              <tr key={k} className="border-t border-dashed border-border-hair">
                <th scope="row" className="py-1 pr-2 text-left font-normal">{humanizeKey(k)}</th>
                <td className="py-1 px-2 text-right tabular-nums">{String(snapshot[k])}</td>
                {showNow ? (
                  <td className={cn("py-1 pl-2 text-right tabular-nums", changed && "font-semibold")}>
                    {String(current?.[k] ?? "")}
                    {changed ? <Tag tone="strong" className="ml-1" icon={<IconInfo size={14} strokeWidth={1.8} aria-hidden="true" />}>Changed since</Tag> : null}
                  </td>
                ) : null}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
