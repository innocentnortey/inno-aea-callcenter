import { useEffect, useRef, useState } from "react";
import { getTransport, type StreamSpec, type StreamStatus } from "./transport";

export function useEventStream(
  spec: Omit<StreamSpec, "onEvent" | "onStatus"> | null,
  onEvent: (data: unknown, id: number | null, type: string) => void,
): { status: StreamStatus; lastEventId: number | null } {
  const [status, setStatus] = useState<StreamStatus>("closed");
  const [lastEventId, setLastEventId] = useState<number | null>(null);
  const cb = useRef(onEvent);
  cb.current = onEvent;
  const key = spec ? JSON.stringify(spec) : "";
  const specRef = useRef(spec);
  specRef.current = spec;

  useEffect(() => {
    const s = specRef.current;
    if (!s) { setStatus("closed"); return; }
    let current = true; // false once this handle is closed: its late frames and statuses are ignored
    const handle = getTransport().openStream({
      ...s,
      onEvent: (data, id, type) => {
        if (!current) return;
        if (id !== null) setLastEventId(id);
        cb.current(data, id, type);
      },
      onStatus: (st) => { if (current) setStatus(st); },
    });
    return () => { current = false; handle.close(); };
  }, [key]);

  return { status, lastEventId };
}
