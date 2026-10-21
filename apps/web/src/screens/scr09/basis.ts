import type { components } from "@/api/types.gen";
import { formatClockLabel } from "@/lib/time";
import { pluralize } from "../reads/format";

type OwnerMetricsResponse = components["schemas"]["OwnerMetricsResponse"];

export function basisLine(d: Pick<OwnerMetricsResponse, "as_of" | "seeds_included" | "seed_count">): string {
  const n = d.seed_count;
  const seeds = d.seeds_included
    ? `Includes ${n} demo seed ${pluralize(n, "case", "cases")}.`
    : `Does not include the ${n} demo seed ${pluralize(n, "case", "cases")}.`;
  return `From stored conversations and cases, as of ${formatClockLabel(d.as_of)} (demo time). ${seeds} These are not targets.`;
}
export function isEmptyOwner(d: OwnerMetricsResponse): boolean {
  return [d.in_scope_correct_resolution, d.promises_kept_on_time, d.handoffs].every((m) => (m.denominator ?? 0) === 0) && d.outcomes.length === 0;
}
export function isStale(asOfIso: string, clockNowIso: string | null): boolean {
  return clockNowIso !== null && Date.parse(clockNowIso) - Date.parse(asOfIso) > 60_000;
}
