import { useEffect, useState } from "react";

export const WIDE = "(min-width: 900px)";
export const LAPTOP = "(min-width: 900px) and (pointer: fine)";

const read = (query: string) => (typeof window !== "undefined" && typeof window.matchMedia === "function" ? window.matchMedia(query).matches : false);

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => read(query));
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const mq = window.matchMedia(query);
    const on = () => setMatches(mq.matches);
    on();
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, [query]);
  return matches;
}
