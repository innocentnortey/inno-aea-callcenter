import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatAction } from "../../contract";

/** Wraps dispatch with a double-tap guard. `run` resolves true when the action went through. */
export function useCardAction(dispatch: (a: ChatAction) => Promise<void>): { pending: boolean; run(a: ChatAction): Promise<boolean> } {
  const [pending, setPending] = useState(false);
  const inFlight = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  const run = useCallback(async (a: ChatAction): Promise<boolean> => {
    if (inFlight.current) return false;
    inFlight.current = true;
    setPending(true);
    try {
      await dispatch(a);
      return true;
    } catch {
      return false;
    } finally {
      inFlight.current = false;
      if (mounted.current) setPending(false);
    }
  }, [dispatch]);
  return { pending, run };
}
