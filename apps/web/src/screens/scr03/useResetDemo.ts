import { useCallback, useEffect, useRef, useState } from "react";
import { callOp } from "@/api/client";
import { ApiError } from "@/api/errors";
import { refetchAll } from "@/api/refetch";
import { useAction } from "@/api/useOp";
import { useDemoStatus } from "@/state/demoStatus";
import { useSession } from "@/state/session";
import { RESET_BUSY, RESET_FAILED, resetSuccessLine } from "./copy";

const DEFAULT_RETRY_MS = 5000;

/** Confirm, reset, then re-read the session: the login stays but the role goes back to customer (G-1). */
export function useResetDemo() {
  const reset = useAction("resetDemo");
  const session = useSession();
  const demoStatus = useDemoStatus();
  const [open, setOpen] = useState(false);
  const [blocked, setBlocked] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  const confirm = useCallback(async () => {
    const roleBefore = session.role;
    setOpen(false);
    setResult(null);
    try {
      const res = await reset.run({ body: { confirm: true } });
      let roleNow = roleBefore;
      try {
        const s = await callOp("getSession");
        session.setSession(s);
        roleNow = s.role;
      } catch { /* the header keeps the last role it knew */ }
      refetchAll();
      await demoStatus.refresh();
      setResult(resetSuccessLine(res.open_chats_ended, roleBefore !== "customer" && roleNow === "customer"));
    } catch (e) {
      if (e instanceof ApiError && (e.status === 409 || e.code === "RESET_IN_PROGRESS")) {
        const ms = typeof e.details?.retry_after_ms === "number" ? e.details.retry_after_ms : DEFAULT_RETRY_MS;
        setResult(RESET_BUSY);
        setBlocked(true);
        timer.current = setTimeout(() => setBlocked(false), ms);
      } else {
        setResult(RESET_FAILED);
      }
    }
  }, [reset, session, demoStatus]);

  return { open, setOpen, confirm, busy: reset.pending || blocked, result };
}
