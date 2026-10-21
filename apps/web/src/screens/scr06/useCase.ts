import { useEffect, useReducer } from "react";
import { useOp, type OpStatus } from "@/api/useOp";
import type { ApiError } from "@/api/errors";
import { caseReducer, initialCaseState, type CaseAction, type CaseState } from "./caseReducer";

export function useCase(reference: string | undefined): {
  state: CaseState; status: OpStatus; error: ApiError | undefined; dispatch(a: CaseAction): void; reload(): Promise<void>;
} {
  const op = useOp("getCase", reference ? { path: { reference } } : null);
  const [state, dispatch] = useReducer(caseReducer, initialCaseState);
  const data = op.data;
  useEffect(() => {
    if (data) dispatch({ type: "loaded", detail: data });
  }, [data]);
  return { state, status: op.status, error: op.error, dispatch, reload: op.refetch };
}
