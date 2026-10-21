import { useEffect, useState } from "react";
import type { components } from "@/api/types.gen";

type Flag = components["schemas"]["Flag"];

/** The first read is what "opened the page" means. Later additions are counted, not shown, until showNew(). */
export function useShownFlags(flags: Flag[] | undefined): { shown: Flag[]; newCount: number; showNew(): void } {
  const [shownIds, setShownIds] = useState<string[] | null>(null);
  useEffect(() => {
    if (flags && shownIds === null) setShownIds(flags.map((f) => f.flag_id));
  }, [flags, shownIds]);
  const shown = flags && shownIds ? flags.filter((f) => shownIds.includes(f.flag_id)) : [];
  const newCount = flags && shownIds ? flags.filter((f) => !shownIds.includes(f.flag_id)).length : 0;
  const showNew = () => { if (flags) setShownIds(flags.map((f) => f.flag_id)); };
  return { shown, newCount, showNew };
}
