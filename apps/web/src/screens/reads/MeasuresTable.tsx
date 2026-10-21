import type { components } from "@/api/types.gen";
import { Button } from "@/components/ui";
import { formatShare, nOfN } from "./format";

type Measure = components["schemas"]["Measure"];
export interface MeasuresTableProps {
  caption: string;
  firstColumn: string;
  rows: Measure[];
  noun: string;
  openKey: string | null;
  onOpen(key: string, measure: Measure): void;
  panelId: string;
  keyPrefix?: string;
}

export function MeasuresTable({ caption, firstColumn, rows, noun, openKey, onOpen, panelId, keyPrefix = "r" }: MeasuresTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-ui">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="text-left text-small text-text-muted">
            <th scope="col" className="px-3 py-2 font-semibold">{firstColumn}</th>
            <th scope="col" className="px-3 py-2 font-semibold">Count</th>
            <th scope="col" className="px-3 py-2 font-semibold">Share</th>
            <th scope="col" className="px-3 py-2 font-semibold"><span className="sr-only">Cases</span></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((m, i) => {
            const key = `${keyPrefix}-${i}`;
            const canOpen = (m.denominator ?? 0) > 0 && m.case_refs.length > 0;
            return (
              <tr key={`${i}-${m.label}`} className="border-t border-dashed border-border-hair">
                <th scope="row" className="px-3 py-2 text-left font-semibold">{m.label}</th>
                <td className="px-3 py-2">{nOfN(m.numerator, m.denominator, noun)}</td>
                <td className="px-3 py-2">
                  {formatShare(m.value)}
                  {m.value == null && m.null_reason ? <span className="block text-small text-text-muted">{m.null_reason}</span> : null}
                </td>
                <td className="px-3 py-2">
                  {canOpen ? (
                    <Button
                      variant="text" density="console" aria-label={`Open the cases for ${m.label}`}
                      aria-expanded={openKey === key} aria-controls={panelId} onClick={() => onOpen(key, m)}
                    >
                      Open the cases
                    </Button>
                  ) : (
                    <span className="text-small text-text-muted">No cases to open.</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
