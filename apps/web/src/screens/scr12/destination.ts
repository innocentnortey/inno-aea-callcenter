import { safeReturnTo } from "@/lib/returnTo";

/** Where to go after sign-in or "Continue". `returnTo` is the raw `return_to` query value. */
export function resolveDestination(returnTo: string | null | undefined, fallback: string | null | undefined): string {
  const asked = returnTo && !returnTo.startsWith("/login") ? safeReturnTo(returnTo) : "/";
  if (asked !== "/") return asked;
  return safeReturnTo(fallback ?? "/");
}
