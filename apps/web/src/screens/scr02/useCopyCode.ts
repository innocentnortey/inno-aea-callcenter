import { useCallback, useEffect, useRef, useState } from "react";

const SHOW_MS = 2000;

/** Copies a code to the clipboard and reports which message just copied (or failed) for 2 s. */
export function useCopyCode() {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [failedId, setFailedId] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  const copy = useCallback(async (id: string, code: string) => {
    if (timer.current) clearTimeout(timer.current);
    let ok = true;
    try {
      await navigator.clipboard.writeText(code);
    } catch {
      ok = false;
    }
    setCopiedId(ok ? id : null);
    setFailedId(ok ? null : id);
    timer.current = setTimeout(() => { setCopiedId(null); setFailedId(null); }, SHOW_MS);
  }, []);

  return { copiedId, failedId, copy };
}
