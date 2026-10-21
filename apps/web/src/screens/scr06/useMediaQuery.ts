import { useEffect, useState } from "react";

export function useMediaQuery(query: string, fallback = false): boolean {
  const supported = typeof window !== "undefined" && typeof window.matchMedia === "function";
  const [matches, setMatches] = useState(() => (supported ? window.matchMedia(query).matches : fallback));
  useEffect(() => {
    if (!supported) return;
    const mql = window.matchMedia(query);
    const on = () => setMatches(mql.matches);
    on();
    mql.addEventListener("change", on);
    return () => mql.removeEventListener("change", on);
  }, [query, supported]);
  return matches;
}
