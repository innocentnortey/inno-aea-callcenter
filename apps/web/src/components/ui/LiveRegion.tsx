import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

export function LiveRegion({ politeness = "polite", children }: { politeness?: "polite" | "assertive"; children?: ReactNode }) {
  return (
    <div className="sr-only" aria-live={politeness} aria-atomic="true">
      {children}
    </div>
  );
}

const AnnounceContext = createContext<(msg: string) => void>(() => undefined);
export function useAnnounce(): (msg: string) => void {
  return useContext(AnnounceContext);
}
/** Mounts the one polite region; useAnnounce() writes to it. */
export function AnnounceProvider({ children }: { children: ReactNode }) {
  const [msg, setMsg] = useState("");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pending = useRef("");
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);
  const announce = useCallback((m: string) => {
    // clear first so repeating the same sentence is announced again
    setMsg("");
    // One timer: announcements landing inside the window are read together, in order, never dropped.
    pending.current = timer.current ? `${pending.current} ${m}` : m;
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      timer.current = null;
      setMsg(pending.current);
    }, 20);
  }, []);
  const value = useMemo(() => announce, [announce]);
  return (
    <AnnounceContext.Provider value={value}>
      {children}
      <LiveRegion>{msg}</LiveRegion>
    </AnnounceContext.Provider>
  );
}
