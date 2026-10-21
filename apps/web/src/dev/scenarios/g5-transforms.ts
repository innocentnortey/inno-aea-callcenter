// Pure body transforms for the G5 scenarios. Each takes the Prism example body and returns a new, still valid body.
import type { components } from "@/api/types.gen";

type OversightResponse = components["schemas"]["OversightResponse"];
type OwnerMetricsResponse = components["schemas"]["OwnerMetricsResponse"];
type FlagsResponse = components["schemas"]["FlagsResponse"];
type MonitoringResponse = components["schemas"]["MonitoringResponse"];

export function withLiveQueue(n: number): (b: OversightResponse) => OversightResponse {
  return (b) => ({ ...b, live_queue_length: n });
}

export function withoutRow(reference: string): (b: OversightResponse) => OversightResponse {
  return (b) => {
    const lanes = { ...b.lanes };
    for (const key of Object.keys(lanes) as (keyof typeof lanes)[]) {
      const lane = lanes[key];
      if (!lane.rows.some((r) => r.reference === reference)) continue;
      const rows = lane.rows.filter((r) => r.reference !== reference);
      lanes[key] = { ...lane, rows, count: Math.max(0, lane.count - (lane.rows.length - rows.length)) };
    }
    return { ...b, lanes };
  };
}

export function withNullPromises(b: OwnerMetricsResponse): OwnerMetricsResponse {
  return {
    ...b,
    promises_kept_on_time: { ...b.promises_kept_on_time, numerator: 0, denominator: 0, value: null, null_reason: "No promises are due yet.", case_refs: [] },
    missed_promises: [],
  };
}

export function withExtraFlag(b: FlagsResponse): FlagsResponse {
  const first = b.flags[0];
  if (!first) return b;
  return {
    ...b,
    flags: [
      ...b.flags,
      { ...first, flag_id: "flg-4", message_id: null, reason: null, note: null, flagged_by: "Demo supervisor", at: "2026-10-16T14:55:00-05:00", status: "new", reviewed_by: null, reviewed_note: null },
    ],
  };
}

export function withReviewed(flagId: string, reviewed: { by: string | null; note: string | null }): (b: FlagsResponse) => FlagsResponse {
  return (b) => ({
    ...b,
    flags: b.flags.map((f) => (f.flag_id === flagId ? { ...f, status: "reviewed" as const, reviewed_by: reviewed.by, reviewed_note: reviewed.note } : f)),
  });
}

export function rebaseMonitoring(ageMs: number): (b: MonitoringResponse) => MonitoringResponse {
  return (b) => ({ ...b, as_of: new Date(Date.now() - ageMs).toISOString() });
}
