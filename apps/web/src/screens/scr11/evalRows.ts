import type { components } from "@/api/types.gen";
import { formatShare } from "../reads/format";

type EvalResponse = components["schemas"]["EvalResponse"];
type EvalRun = components["schemas"]["EvalRun"];
type EvalMeasure = components["schemas"]["EvalMeasure"];

export interface EvalRow { id: string; label: string; heldOut: EvalMeasure | null; dev: EvalMeasure | null; target: string | null }

/** Ids only align the same measure across the two runs; nothing branches on an id. */
export function buildEvalRows(splits: EvalResponse["splits"]): EvalRow[] {
  const ho = splits.held_out?.measures ?? [];
  const dv = splits.dev?.measures ?? [];
  const ids = [...ho.map((m) => m.id), ...dv.map((m) => m.id).filter((id) => !ho.some((m) => m.id === id))];
  return ids.map((id) => {
    const heldOut = ho.find((m) => m.id === id) ?? null;
    const dev = dv.find((m) => m.id === id) ?? null;
    return { id, label: (heldOut ?? dev)!.label, heldOut, dev, target: heldOut?.target ?? dev?.target ?? null };
  });
}
export function hasTargets(rows: EvalRow[]): boolean {
  return rows.some((r) => r.target != null);
}
export function formatRange(m: EvalMeasure): string | null {
  if (m.min == null || m.max == null) return null;
  return `Range over repeats: ${formatShare(m.min)} – ${formatShare(m.max)}`;
}
export function mixSummary(run: EvalRun): string {
  const sum = (origin: "transcript" | "synthetic") => run.mix.filter((m) => m.origin === origin).reduce((a, m) => a + m.count, 0);
  return `${sum("transcript")} transcript-derived and ${sum("synthetic")} labelled synthetic cases in the mix`;
}
