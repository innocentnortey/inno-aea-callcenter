import { useEffect, useMemo, useRef } from "react";
import { useOp } from "@/api/useOp";
import { useAnnounce } from "@/components/ui";
import type { components } from "@/api/types.gen";
import { NEW_CODE } from "./copy";

export type InboxMessage = components["schemas"]["InboxMessage"];
export type InboxPhase = "loading" | "error" | "empty" | "list";

/** Polls the inbox every 5 s; announces a new code on any refresh after the first load. */
export function useInbox() {
  const { data, status, refetch } = useOp("listDemoInbox", {}, { pollMs: 5000, pauseWhenHidden: true, refetchOnFocus: true });
  const announce = useAnnounce();
  const seen = useRef<Set<string> | null>(null);

  const messages: InboxMessage[] = useMemo(
    () => [...(data?.messages ?? [])].sort((a, b) => Date.parse(b.at) - Date.parse(a.at)),
    [data],
  );

  useEffect(() => {
    if (!data) return;
    const ids = data.messages.map((m) => m.id);
    if (seen.current === null) { seen.current = new Set(ids); return; }
    const fresh = ids.some((id) => !seen.current!.has(id));
    ids.forEach((id) => seen.current!.add(id));
    if (fresh) announce(NEW_CODE);
  }, [data, announce]);

  // A failed refresh keeps the last list; only a first load that failed shows the error.
  const phase: InboxPhase = data === undefined ? (status === "error" ? "error" : "loading") : messages.length === 0 ? "empty" : "list";
  return { messages, phase, refetch };
}
