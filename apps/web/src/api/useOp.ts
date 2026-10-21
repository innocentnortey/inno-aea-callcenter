import { useCallback, useEffect, useRef, useState } from "react";
import { callOp, type CallArgs, type OkBody, type OperationId } from "./client";
import { ApiError, toApiError } from "./errors";
import { onRefetchAll } from "./refetch";

export type OpStatus = "idle" | "loading" | "success" | "error";

export function useOp<K extends OperationId>(
  op: K,
  args: CallArgs<K> | null,
  opts?: { pollMs?: number; pauseWhenHidden?: boolean; refetchOnFocus?: boolean },
): { data: OkBody<K> | undefined; error: ApiError | undefined; status: OpStatus; isRefetching: boolean; refetch(): Promise<void> } {
  const [data, setData] = useState<unknown>(undefined);
  const [error, setError] = useState<ApiError | undefined>(undefined);
  const [status, setStatus] = useState<OpStatus>(args === null ? "idle" : "loading");
  const [isRefetching, setIsRefetching] = useState(false);
  const argsRef = useRef(args);
  argsRef.current = args;
  const ctrlRef = useRef<AbortController | null>(null);
  const hasData = useRef(false);
  const key = op + JSON.stringify(args);
  const keyRef = useRef(key);
  keyRef.current = key;
  // The key whose result `data`/`error` hold; a different current key means they belong to the previous args.
  const [owner, setOwner] = useState(key);
  const pauseWhenHidden = opts?.pauseWhenHidden ?? true;

  const run = useCallback(async () => {
    const a = argsRef.current;
    if (a === null) return;
    ctrlRef.current?.abort();
    const ctrl = new AbortController();
    ctrlRef.current = ctrl;
    if (hasData.current) setIsRefetching(true);
    else setStatus("loading");
    try {
      const res = await callOp(op, { ...(a as object), signal: ctrl.signal } as CallArgs<K>);
      if (ctrl.signal.aborted) return;
      hasData.current = true;
      setOwner(keyRef.current);
      setData(() => res);
      setError(undefined);
      setStatus("success");
    } catch (e) {
      if (ctrl.signal.aborted) return;
      setOwner(keyRef.current);
      setError(toApiError(e));
      setStatus("error");
    } finally {
      if (!ctrl.signal.aborted) setIsRefetching(false);
    }
  }, [op]);

  const enabled = key !== op + "null";
  useEffect(() => {
    hasData.current = false;
    if (!enabled) {
      setStatus("idle");
      setData(undefined);
      setError(undefined);
      return;
    }
    void run();
    return () => ctrlRef.current?.abort();
  }, [key, enabled, run]);

  useEffect(() => onRefetchAll(() => void run()), [run]);

  const pollMs = opts?.pollMs;
  useEffect(() => {
    if (!pollMs) return;
    let t: ReturnType<typeof setTimeout>;
    let stopped = false;
    const tick = async () => {
      if (stopped) return;
      if (!pauseWhenHidden || document.visibilityState === "visible") await run();
      if (!stopped) t = setTimeout(tick, pollMs);
    };
    t = setTimeout(tick, pollMs);
    return () => { stopped = true; clearTimeout(t); };
  }, [pollMs, pauseWhenHidden, run]);

  const refetchOnFocus = opts?.refetchOnFocus ?? false;
  useEffect(() => {
    if (!refetchOnFocus) return;
    const h = () => void run();
    window.addEventListener("focus", h);
    return () => window.removeEventListener("focus", h);
  }, [refetchOnFocus, run]);

  const stale = owner !== key;
  return {
    data: stale ? undefined : (data as OkBody<K> | undefined),
    error: stale ? undefined : error,
    status: stale && enabled ? "loading" : status,
    isRefetching,
    refetch: run,
  };
}

export function useAction<K extends OperationId>(op: K): {
  run(args?: CallArgs<K>): Promise<OkBody<K>>;
  pending: boolean;
  error: ApiError | undefined;
  data: OkBody<K> | undefined;
  reset(): void;
} {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ApiError | undefined>(undefined);
  const [data, setData] = useState<unknown>(undefined);
  const run = useCallback(async (args?: CallArgs<K>) => {
    setPending(true);
    setError(undefined);
    try {
      const res = await callOp(op, args);
      setData(() => res);
      return res;
    } catch (e) {
      const err = toApiError(e);
      setError(err);
      throw err;
    } finally {
      setPending(false);
    }
  }, [op]);
  const reset = useCallback(() => { setError(undefined); setData(undefined); }, []);
  return { run, pending, error, data: data as OkBody<K> | undefined, reset };
}
