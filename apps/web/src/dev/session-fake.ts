// The only document.cookie writers in the app. The real server sets the cookie; the mock layer fakes it so Prism accepts calls.
import type { Role } from "@/api/client";
import type { ApiTransport } from "@/api/transport";
import { getWorld, setWorld } from "./world";

export const FAKE_COOKIE = "mhc_session=prototype-synthetic; path=/; SameSite=Lax";
export function setSessionCookie(): void { document.cookie = FAKE_COOKIE; }
export function clearSessionCookie(): void { document.cookie = "mhc_session=; path=/; max-age=0; SameSite=Lax"; }

/** Any non-empty username and password is accepted; the panel offers these switches. */
export const fakeLoginRules = {
  accepts: (username: string, password: string) => username.trim().length > 0 && password.length > 0,
  refuseNext: () => setWorld({ refuseNextLogin: true }),
  expireSession: () => setWorld({ expireNext: true }),
  resetRole: () => setWorld({ role: "customer", sessionBody: null, roleResetPending: true }),
};

/**
 * Sets the dev role and fetches the matching session body from Prism's switchRole example,
 * so getSession answers it later (nothing is invented: the body is the spec's TO_* example).
 */
export async function applyRole(base: ApiTransport, role: Role): Promise<void> {
  if (role === "customer") { setWorld({ role, sessionBody: null }); return; }
  setWorld({ role });
  try {
    const res = await base.fetch(
      { op: "switchRole", method: "PUT", path: "/api/session/role", body: { role } },
      "/api/session/role",
      { method: "PUT", headers: { Accept: "application/json", "Content-Type": "application/json", Prefer: `code=200, example=TO_${role.toUpperCase()}` }, body: JSON.stringify({ role }), credentials: "include" },
    );
    if (res.ok) setWorld({ sessionBody: await res.json() });
  } catch {
    /* Prism not reachable: getSession falls back to the customer example */
  }
  void getWorld;
}
