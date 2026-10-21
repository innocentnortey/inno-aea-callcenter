import { useCallback, useEffect, useState } from "react";
import type { components } from "@/api/types.gen";
import type { ApiError } from "@/api/errors";
import { useOp, type OpStatus } from "@/api/useOp";
import { countChangedRows } from "./queueDiff";

type QueueResponse = components["schemas"]["QueueResponse"];

/** The queue, polled every 10 s. The list under the user's eye changes only when they ask, except when staffing flips. */
export function useQueueFeed(): {
  shown: QueueResponse | undefined; status: OpStatus; error: ApiError | undefined; isRefetching: boolean;
  changedCount: number; showChanged(): void; retry(): void;
} {
  const q = useOp("getQueue", {}, { pollMs: 10_000, refetchOnFocus: true });
  const [shown, setShown] = useState<QueueResponse | undefined>(undefined);
  const fresh = q.data;
  useEffect(() => {
    if (!fresh) return;
    setShown((cur) => {
      if (!cur) return fresh;
      if (fresh.staffing.mode !== cur.staffing.mode) return fresh;
      return countChangedRows(cur, fresh) === 0 ? fresh : cur;
    });
  }, [fresh]);
  const changedCount = shown && fresh && shown !== fresh ? countChangedRows(shown, fresh) : 0;
  const showChanged = useCallback(() => { if (fresh) setShown(fresh); }, [fresh]);
  const refetch = q.refetch;
  const retry = useCallback(() => { void refetch(); }, [refetch]);
  return { shown, status: q.status, error: q.error, isRefetching: q.isRefetching, changedCount, showChanged, retry };
}
