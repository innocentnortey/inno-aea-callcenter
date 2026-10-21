type Cb = () => void;
const refetchSubs = new Set<Cb>();
export function onRefetchAll(cb: Cb): () => void {
  refetchSubs.add(cb);
  return () => void refetchSubs.delete(cb);
}
export function refetchAll(): void {
  [...refetchSubs].forEach((cb) => cb());
}

type AuthCb = (reason: "none" | "expired") => void;
const authSubs = new Set<AuthCb>();
export function onAuthLost(cb: AuthCb): () => void {
  authSubs.add(cb);
  return () => void authSubs.delete(cb);
}
export function emitAuthLost(reason: "none" | "expired"): void {
  [...authSubs].forEach((cb) => cb(reason));
}

/** A 403 ROLE_NOT_ALLOWED came back (a demo reset or a role change on the server): the session must be read again. */
const roleSubs = new Set<Cb>();
export function onRoleDenied(cb: Cb): () => void {
  roleSubs.add(cb);
  return () => void roleSubs.delete(cb);
}
export function emitRoleDenied(): void {
  [...roleSubs].forEach((cb) => cb());
}
