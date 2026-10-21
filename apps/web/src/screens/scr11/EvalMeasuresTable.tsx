import type { components } from "@/api/types.gen";
import { formatShare, nOfN } from "../reads/format";
import { formatRange, type EvalRow } from "./evalRows";

type EvalRun = components["schemas"]["EvalRun"];
type EvalMeasure = components["schemas"]["EvalMeasure"];

interface Props { rows: EvalRow[]; heldOut: EvalRun | null; dev: EvalRun | null; devLabel: string; showTarget: boolean }

function Cell({ m, noun }: { m: EvalMeasure | null; noun: string }) {
  if (!m) return <td className="px-3 py-2"><span className="text-text-muted">Not in this run</span></td>;
  const range = formatRange(m);
  return (
    <td className="px-3 py-2">
      <span className="block">{nOfN(m.numerator, m.denominator, noun)}</span>
      <span className="block text-small text-text-muted">{formatShare(m.value)}</span>
      {range ? <span className="block text-small text-text-muted">{range}</span> : null}
    </td>
  );
}

export function EvalMeasuresTable({ rows, heldOut, dev, devLabel, showTarget }: Props) {
  const runs = [heldOut && `held-out run ${heldOut.run_id}`, dev && `dev run ${dev.run_id}`].filter(Boolean).join("; ");
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-ui">
        <caption className="px-3 py-2 text-left text-small text-text-muted">{`Measures: ${runs}`}</caption>
        <thead>
          <tr className="text-left text-small text-text-muted">
            <th scope="col" className="px-3 py-2 font-semibold">Measure</th>
            {heldOut ? <th scope="col" className="px-3 py-2 font-semibold">Held-out</th> : null}
            {dev ? (
              <th scope="col" className="px-3 py-2 font-semibold">
                Dev<span className="block text-small font-normal text-text-muted">{devLabel}</span>
              </th>
            ) : null}
            {showTarget ? <th scope="col" className="px-3 py-2 font-semibold">Target</th> : null}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={`${i}-${r.label}`} className="border-t border-dashed border-border-hair">
              <th scope="row" className="px-3 py-2 text-left font-semibold">{r.label}</th>
              {heldOut ? <Cell m={r.heldOut} noun="held-out cases" /> : null}
              {dev ? <Cell m={r.dev} noun="dev cases" /> : null}
              {showTarget ? <td className="px-3 py-2">{r.target ?? "—"}</td> : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
