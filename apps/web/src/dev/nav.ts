// Location helpers for the dev layer, which lives outside the router.
export function navigateTo(path: string): void {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
let patched = false;
/** Makes pushState/replaceState announce themselves so the panel can follow the route. */
export function patchHistory(): void {
  if (patched) return;
  patched = true;
  for (const m of ["pushState", "replaceState"] as const) {
    const orig = window.history[m].bind(window.history);
    window.history[m] = ((...args: Parameters<History["pushState"]>) => {
      orig(...args);
      window.dispatchEvent(new Event("mhc-locationchange"));
    }) as History["pushState"];
  }
}
export function subscribeLocation(cb: () => void): () => void {
  window.addEventListener("popstate", cb);
  window.addEventListener("mhc-locationchange", cb);
  return () => { window.removeEventListener("popstate", cb); window.removeEventListener("mhc-locationchange", cb); };
}
export const getPathname = () => window.location.pathname;
