import { useCallback, useEffect, useRef, useState } from "react";
import { useAction, useOp } from "@/api/useOp";
import { useDemoStatus } from "@/state/demoStatus";
import type { StaffingMode } from "./copy";

export type StaffingResult =
  | { kind: "success"; mode: StaffingMode; converted: number }
  | { kind: "error" }
  | { kind: "stale" };

/** Reads staffing (re-read every 10 s and on focus) and writes it; own writes never raise the "changed" line. */
export function useStaffingControl() {
  const { data, status, refetch } = useOp("getStaffing", {}, { pollMs: 10000, pauseWhenHidden: true, refetchOnFocus: true });
  const setStaffing = useAction("setStaffing");
  const demoStatus = useDemoStatus();
  const [pendingMode, setPendingMode] = useState<StaffingMode | null>(null);
  const [result, setResult] = useState<StaffingResult | null>(null);
  const lastKnown = useRef<StaffingMode | null>(null);
  const pendingRef = useRef<StaffingMode | null>(null);

  useEffect(() => {
    if (!data) return;
    if (lastKnown.current === null) { lastKnown.current = data.mode; return; }
    if (pendingRef.current === null && data.mode !== lastKnown.current) {
      lastKnown.current = data.mode;
      setResult({ kind: "stale" });
    }
  }, [data]);

  const toggle = useCallback(async (next: boolean) => {
    const mode: StaffingMode = next ? "simulated_on_shift" : "nobody_online";
    pendingRef.current = mode;
    setPendingMode(mode);
    setResult(null);
    try {
      const r = await setStaffing.run({ body: { mode } });
      lastKnown.current = r.mode;
      setResult({ kind: "success", mode: r.mode, converted: r.converted_cases });
      await demoStatus.refresh();
      await refetch();
    } catch {
      setResult({ kind: "error" });
    } finally {
      pendingRef.current = null;
      setPendingMode(null);
    }
  }, [setStaffing, demoStatus, refetch]);

  const checked = pendingMode ? pendingMode === "simulated_on_shift" : data?.mode === "simulated_on_shift";
  return {
    label: data?.label ?? null,
    phase: data ? "ready" : status === "error" ? "error" : "loading",
    checked,
    disabled: data === undefined || pendingMode !== null,
    result,
    toggle,
    refetch,
  } as const;
}
