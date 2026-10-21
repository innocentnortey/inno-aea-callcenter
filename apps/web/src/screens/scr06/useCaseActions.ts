import { useCallback, useState } from "react";
import { useNavigate } from "react-router";
import { callOp } from "@/api/client";
import { toApiError } from "@/api/errors";
import type { components } from "@/api/types.gen";
import { useAnnounce } from "@/components/ui";
import type { Role } from "@/lib/roles";
import { formatTimePoint } from "@/lib/time";
import type { FormKey } from "./ActionArea";
import { focusResult } from "./ActionResult";
import type { Submission } from "./ActionForms";
import type { CaseAction, CaseState } from "./caseReducer";
import { KIND_WORD, OUTCOME_WORD } from "./caseText";
import { ClaimedNotJoinedError, claimAndJoin } from "./claimAndJoin";
import { CLAIMED_NOT_JOINED_CASE, errorText, type ActionKey, type ShownError } from "./errorCopy";

type CaseActionRequest = components["schemas"]["CaseActionRequest"];
export const RESULT_ID = "case-result";

export function useCaseActions(p: { reference: string | undefined; state: CaseState; dispatch(a: CaseAction): void; reload(): Promise<void>; role: Role }) {
  const { reference, state, dispatch, reload, role } = p;
  const navigate = useNavigate();
  const announce = useAnnounce();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ShownError | null>(null);
  const [liveError, setLiveError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [form, setForm] = useState<FormKey | null>(null);
  const version = state.detail?.case.version ?? 0;

  /** Runs one write: busy on, errors shown as copy, success line announced and focused. Returns true on success. */
  const run = useCallback(async (key: ActionKey, fn: () => Promise<string | null>, live = false): Promise<boolean> => {
    setBusy(true);
    setError(null);
    setLiveError(null);
    try {
      const line = await fn();
      if (line) {
        setResult(line);
        announce(line);
        focusResult(RESULT_ID);
      }
      setForm(null);
      return true;
    } catch (e) {
      const shown: ShownError = e instanceof ClaimedNotJoinedError
        ? { text: CLAIMED_NOT_JOINED_CASE, offerReload: false }
        : errorText(toApiError(e), key, role);
      if (live) setLiveError(shown.text); else setError(shown);
      return false;
    } finally {
      setBusy(false);
    }
  }, [announce, role]);

  const caseAction = useCallback((body: CaseActionRequest) => run(body.action, async () => {
    const res = await callOp("applyCaseAction", { path: { reference: reference! }, body });
    if (body.action === "resolve" || body.action === "close_unresolved") {
      navigate("/staff/queue", { state: { resultLine: res.result_line } });
      return null;
    }
    dispatch({ type: "summary", summary: res.case });
    return res.result_line;
  }), [run, reference, navigate, dispatch]);

  const claimNow = useCallback(() => caseAction({ action: "claim", expected_version: version }), [caseAction, version]);
  const startNow = useCallback(() => caseAction({ action: "start", expected_version: version }), [caseAction, version]);
  const claimAndJoinNow = useCallback(() => run("claim", async () => {
    let done: Awaited<ReturnType<typeof claimAndJoin>>;
    try {
      done = await claimAndJoin(reference!, version);
    } catch (e) {
      if (e instanceof ClaimedNotJoinedError) {
        // The claim stuck: take its version and lifecycle now (the next write needs them), then refresh the rest.
        dispatch({ type: "summary", summary: e.claim.case });
        void reload();
      }
      throw e;
    }
    const { claim, join } = done;
    dispatch({ type: "summary", summary: claim.case });
    dispatch({ type: "live", live: join.live, message: join.message });
    await reload();
    return claim.result_line;
  }), [run, reference, version, dispatch, reload]);
  const joinChat = useCallback(() => run("join", async () => {
    await callOp("liveChatAction", { path: { reference: reference! }, body: { action: "join" } });
    await reload();
    return "You joined the chat.";
  }), [run, reference, reload]);

  const submit = useCallback((s: Submission) => {
    if (s.kind === "case") return caseAction(s.body);
    if (s.kind === "contact") {
      return run(s.body.kind === "call" ? "log_call" : "log_email", async () => {
        const res = await callOp("recordContactActivity", { path: { reference: reference! }, body: s.body });
        dispatch({ type: "activity", activity: res.activity, summary: res.case });
        return `${KIND_WORD[res.activity.kind]} · ${OUTCOME_WORD[res.activity.outcome]} · ${res.activity.label}`;
      });
    }
    return run("flag", async () => {
      await callOp("createFlag", { body: s.body });
      return "Added to the review list.";
    });
  }, [caseAction, run, reference, dispatch]);

  const liveSend = useCallback((text: string) => run("send", async () => {
    const res = await callOp("liveChatAction", { path: { reference: reference! }, body: { action: "send", text } });
    dispatch({ type: "live", live: res.live, message: res.message });
    return null;
  }, true), [run, reference, dispatch]);
  const liveEnd = useCallback((action: "hand_back" | "close") => run(action, async () => {
    const res = await callOp("liveChatAction", { path: { reference: reference! }, body: { action } });
    const at = res.live.since ? formatTimePoint(res.live.since) : "";
    dispatch({ type: "live", live: res.live, message: res.message, eventText: action === "hand_back" ? `Handed back to the assistant at ${at}` : `Chat closed at ${at}` });
    return null;
  }, true), [run, reference, dispatch]);

  const clearError = useCallback(() => setError(null), []);
  return { busy, error, liveError, result, form, setForm, version, claimNow, startNow, claimAndJoinNow, joinChat, submit, liveSend, liveEnd, clearError };
}
