import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { callOp } from "@/api/client";
import { onRefetchAll } from "@/api/refetch";
import type { components } from "@/api/types.gen";
import { useSession } from "./session";

type DemoClock = components["schemas"]["DemoClock"];
type Staffing = components["schemas"]["Staffing"];

export interface DemoStatusApi {
  clock: DemoClock | null;
  staffing: Staffing | null;
  refresh(): Promise<void>;
  setFromChat(next: Partial<{ clock: DemoClock; staffing: Staffing }>): void;
  setSource(src: "poll" | "chat"): void;
}
export const DemoStatusContext = createContext<DemoStatusApi | null>(null);

const POLL_MS = 10_000;

export function DemoStatusProvider({ children }: { children: ReactNode }) {
  const { status } = useSession();
  const [clock, setClock] = useState<DemoClock | null>(null);
  const [staffing, setStaffing] = useState<Staffing | null>(null);
  const [source, setSource] = useState<"poll" | "chat">("poll");
  const alive = useRef(true);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);

  const refresh = useCallback(async () => {
    const [c, s] = await Promise.allSettled([callOp("getDemoClock"), callOp("getStaffing")]);
    if (!alive.current) return;
    if (c.status === "fulfilled") setClock(c.value);
    if (s.status === "fulfilled") setStaffing(s.value);
  }, []);

  useEffect(() => {
    if (status !== "ready") return;
    void refresh();
    const off = onRefetchAll(() => void refresh());
    const onFocus = () => void refresh();
    window.addEventListener("focus", onFocus);
    return () => { off(); window.removeEventListener("focus", onFocus); };
  }, [status, refresh]);

  useEffect(() => {
    if (status !== "ready" || source !== "poll") return;
    let t: ReturnType<typeof setTimeout>;
    let stopped = false;
    const tick = async () => {
      if (stopped) return;
      if (document.visibilityState === "visible") await refresh();
      if (!stopped) t = setTimeout(tick, POLL_MS);
    };
    t = setTimeout(tick, POLL_MS);
    return () => { stopped = true; clearTimeout(t); };
  }, [status, source, refresh]);

  const setFromChat = useCallback((next: Partial<{ clock: DemoClock; staffing: Staffing }>) => {
    if (next.clock) setClock(next.clock);
    if (next.staffing) setStaffing(next.staffing);
  }, []);

  const value = useMemo<DemoStatusApi>(() => ({ clock, staffing, refresh, setFromChat, setSource }), [clock, staffing, refresh, setFromChat]);
  return <DemoStatusContext.Provider value={value}>{children}</DemoStatusContext.Provider>;
}

export function useDemoStatus(): DemoStatusApi {
  const ctx = useContext(DemoStatusContext);
  if (!ctx) throw new Error("useDemoStatus must be used inside DemoStatusProvider");
  return ctx;
}
