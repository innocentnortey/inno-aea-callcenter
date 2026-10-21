import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useLocation, useNavigate } from "react-router";
import { callOp } from "@/api/client";
import { toApiError } from "@/api/errors";
import { onAuthLost, onRoleDenied, refetchAll } from "@/api/refetch";
import type { components } from "@/api/types.gen";
import { useAnnounce } from "@/components/ui/LiveRegion";
import { HOME_BY_ROLE, STAY_ON_ROLE_CHANGE, type Role } from "@/lib/roles";

type SessionInfo = components["schemas"]["SessionInfo"];

export interface SessionApi {
  status: "loading" | "ready" | "signed-out";
  session: SessionInfo | null;
  role: Role | null;
  switching: Role | null; // the role being switched to; all four segments disabled while non-null
  switchError: string | null; // "Couldn't switch role. Try again."
  switchRole(role: Role): Promise<void>;
  signOut(): Promise<void>;
  setSession(s: SessionInfo): void; // used by the login screen after a successful login
  /** Why the session was lost ("expired" from a 401 with details.reason = "expired"); RequireSession forwards it to /login. */
  lostReason?: "none" | "expired";
}

export const SessionContext = createContext<SessionApi | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<SessionApi["status"]>("loading");
  const [session, setSessionState] = useState<SessionInfo | null>(null);
  const [switching, setSwitching] = useState<Role | null>(null);
  const [switchError, setSwitchError] = useState<string | null>(null);
  const [lostReason, setLostReason] = useState<"none" | "expired">("none");
  const navigate = useNavigate();
  const location = useLocation();
  const announce = useAnnounce();
  const locRef = useRef(location);
  locRef.current = location;

  const goToLogin = useCallback((reason: "none" | "expired") => {
    setStatus("signed-out");
    setSessionState(null);
    setLostReason(reason);
    const loc = locRef.current;
    if (loc.pathname === "/login") return; // a 401 on the login page is the normal signed-out case
    const qs = new URLSearchParams({ return_to: loc.pathname + loc.search, reason });
    navigate(`/login?${qs.toString()}`, { replace: true });
  }, [navigate]);

  useEffect(() => {
    let alive = true;
    callOp("getSession")
      .then((s) => { if (alive) { setSessionState(s); setStatus("ready"); } })
      .catch((e) => {
        if (!alive) return;
        const err = toApiError(e);
        if (err.status === 401) goToLogin(err.details?.reason === "expired" ? "expired" : "none");
        else setStatus("signed-out");
      });
    return () => { alive = false; };
  }, [goToLogin]);

  useEffect(() => onAuthLost((reason) => goToLogin(reason)), [goToLogin]);

  // A 403 ROLE_NOT_ALLOWED means the role on the server is not the one shown (a demo reset sends it back to customer):
  // read the session again so the role gate and the role switch show the real role.
  useEffect(() => onRoleDenied(() => {
    callOp("getSession").then((s) => setSessionState(s)).catch(() => undefined); // a 401 here raises auth-lost on its own
  }), []);

  const setSession = useCallback((s: SessionInfo) => { setSessionState(s); setStatus("ready"); }, []);

  const switchRole = useCallback(async (role: Role) => {
    setSwitching(role);
    setSwitchError(null);
    try {
      const next = await callOp("switchRole", { body: { role } });
      setSessionState(next);
      setStatus("ready");
      announce(`Now acting as ${next.display_name}`);
      refetchAll();
      if (!STAY_ON_ROLE_CHANGE.includes(locRef.current.pathname)) navigate(HOME_BY_ROLE[role]);
    } catch (e) {
      const err = toApiError(e);
      if (err.status !== 401) setSwitchError("Couldn't switch role. Try again.");
    } finally {
      setSwitching(null);
    }
  }, [announce, navigate]);

  const signOut = useCallback(async () => {
    try {
      await callOp("logout");
    } catch {
      /* the session is dropped on this side either way */
    }
    setSessionState(null);
    setStatus("signed-out");
    navigate("/login");
  }, [navigate]);

  const value = useMemo<SessionApi>(() => ({
    status, session, role: session?.role ?? null, switching, switchError, switchRole, signOut, setSession, lostReason,
  }), [status, session, switching, switchError, switchRole, signOut, setSession, lostReason]);

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionApi {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used inside SessionProvider");
  return ctx;
}
