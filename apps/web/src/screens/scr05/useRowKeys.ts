import { useEffect, useRef, useState } from "react";

function isTyping(t: EventTarget | null): boolean {
  if (!(t instanceof HTMLElement)) return false;
  return ["INPUT", "TEXTAREA", "SELECT"].includes(t.tagName) || t.isContentEditable || t.closest("dialog") !== null;
}

/** J / K move a cursor over references, Enter opens it. The cursor is a reference, so a reorder never moves it. */
export function useRowKeys(
  refs: string[],
  opts: { onOpen(ref: string): void; enabled: boolean },
): { cursor: string | null; setCursor(ref: string | null): void } {
  const [cursor, setCursor] = useState<string | null>(null);
  const live = useRef({ refs, cursor, onOpen: opts.onOpen });
  live.current = { refs, cursor, onOpen: opts.onOpen };

  // If the cursor's row vanished, clamp to the nearest remaining reference.
  const gone = cursor !== null && !refs.includes(cursor);
  useEffect(() => {
    if (gone) setCursor(refs[0] ?? null);
  }, [gone, refs]);

  useEffect(() => {
    if (!opts.enabled) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey || isTyping(e.target)) return;
      const { refs: r, cursor: c, onOpen } = live.current;
      if (e.key === "j" || e.key === "k") {
        if (r.length === 0) return;
        const i = c === null ? -1 : r.indexOf(c);
        const next = c === null || i < 0 ? 0 : Math.max(0, Math.min(r.length - 1, i + (e.key === "j" ? 1 : -1)));
        setCursor(r[next]);
        queueMicrotask(() => document.querySelector('[aria-current="true"]')?.scrollIntoView?.({ block: "nearest" }));
      } else if (e.key === "Enter" && c !== null && document.activeElement === document.body) {
        onOpen(c);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [opts.enabled]);

  return { cursor, setCursor };
}
