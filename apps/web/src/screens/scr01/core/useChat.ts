import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { ApiError } from "@/api/errors";
import { onRefetchAll } from "@/api/refetch";
import { useEventStream } from "@/api/useEventStream";
import { newTurnId } from "@/lib/ids";
import { useAnnounce } from "@/components/ui/LiveRegion";
import { useDemoStatus } from "@/state/demoStatus";
import type { ChatAction, Settled } from "../contract";
import { apiGateway, type ChatGateway } from "./gateway";
import type { ChatEvent, ChatState, CustomerEntry, Limits, TurnPayload } from "./model";
import { initialState } from "./model";
import { DEFAULT_LIMITS, RATE_HOLD_MS, type PendingPhase } from "./pending";
import { chatReducer } from "./reducer";
import { describe, MSG } from "./errors";
import { customerRowText } from "./rowText";
import { landingText as buildLandingText, landingsFromWrites, type LandTarget } from "./settledSummary";
import { clearThread, loadThread, saveThread } from "./storage";
import { usePendingPhase } from "./usePendingPhase";
import { resetCardMemory } from "../cards/resetCardMemory";

export type StreamStatus = "connecting" | "open" | "reconnecting" | "closed";
export interface ComposerLock { reason: "rate" | "spend" | "ended" | "starting"; hint: string }
export const LANDING_MS = 1200;

const sleep = (ms: number, signal: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    const t = setTimeout(resolve, ms);
    signal.addEventListener("abort", () => { clearTimeout(t); reject(new Error("aborted")); }, { once: true });
  });
const GAVE_UP = Symbol("gave-up");

export function useChat(gateway: ChatGateway = apiGateway) {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const stateRef = useRef<ChatState>(state);
  stateRef.current = state;
  const demo = useDemoStatus();
  const demoRef = useRef(demo);
  demoRef.current = demo;
  const announce = useAnnounce();
  const announceRef = useRef(announce);
  announceRef.current = announce;

  const [streamStart, setStreamStart] = useState<{ threadId: string; lastEventId: number } | null>(null);
  const [landing, setLanding] = useState<{ target: LandTarget; nonce: number } | null>(null);
  const [landingText, setLandingText] = useState("");
  const [scrollTarget, setScrollTarget] = useState<{ id: string; nonce: number } | null>(null);

  const threadRef = useRef<string | null>(null);
  const limitsRef = useRef<Limits>(DEFAULT_LIMITS);
  const startPromise = useRef<Promise<void> | null>(null);
  const startedRef = useRef(false);
  const turnBusy = useRef(false);
  const personBusy = useRef(false);
  const nonce = useRef(0);
  const landingRef = useRef<LandTarget | null>(null);
  const landTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rateTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ---- landings (the panel wash and its polite sentence) ----
  const land = useCallback((target: LandTarget, settledNow?: Settled) => {
    if (landingRef.current === target) return; // idempotent within the wash
    landingRef.current = target;
    setLanding({ target, nonce: ++nonce.current });
    const s = settledNow ?? stateRef.current.settled;
    if (s) setLandingText(buildLandingText(target, s));
    if (landTimer.current) clearTimeout(landTimer.current);
    landTimer.current = setTimeout(() => { landingRef.current = null; setLanding(null); setLandingText(""); }, LANDING_MS);
  }, []);

  // ---- start / resume ----
  const bootstrap = useCallback((allowResume: boolean) => {
    const run = async () => {
      const stored = allowResume ? loadThread() : null;
      if (stored) {
        try {
          const thread = await gateway.resume(stored.threadId);
          threadRef.current = thread.thread_id;
          limitsRef.current = stored.limits;
          dispatch({ type: "RESUME_OK", thread, limits: stored.limits });
          demoRef.current.setFromChat({ clock: thread.demo_clock });
          void demoRef.current.refresh(); // staffing is authoritative from getStaffing, not the thread
          setStreamStart({ threadId: thread.thread_id, lastEventId: thread.last_event_id });
          return;
        } catch (e) {
          const status = e instanceof ApiError ? e.status : 0;
          if (status === 410) { limitsRef.current = stored.limits; dispatch({ type: "RESUME_GONE", limits: stored.limits }); return; }
          if (status !== 404) { dispatch({ type: "START_FAIL", message: describe(e, "start").message }); return; }
          clearThread(); // 404: the thread is gone, start a new one
        }
      }
      try {
        const res = await gateway.start();
        threadRef.current = res.thread_id;
        limitsRef.current = res.limits;
        saveThread({ threadId: res.thread_id, limits: res.limits });
        dispatch({ type: "START_OK", res });
        demoRef.current.setFromChat({ clock: res.demo_clock, staffing: res.staffing });
        setStreamStart({ threadId: res.thread_id, lastEventId: res.events.last_event_id });
      } catch (e) {
        dispatch({ type: "START_FAIL", message: describe(e, "start").message });
      }
    };
    const p = run().finally(() => { if (startPromise.current === p) startPromise.current = null; });
    startPromise.current = p;
  }, [gateway]);

  useEffect(() => {
    demoRef.current.setSource("chat");
    return () => demoRef.current.setSource("poll");
  }, []);
  useEffect(() => {
    if (startedRef.current) return; // StrictMode runs effects twice; bootstrap once
    startedRef.current = true;
    bootstrap(true);
  }, [bootstrap]);
  useEffect(() => () => {
    if (landTimer.current) clearTimeout(landTimer.current);
    if (rateTimer.current) clearTimeout(rateTimer.current);
  }, []);

  const retryStart = useCallback(() => {
    dispatch({ type: "START_BEGIN" });
    bootstrap(true);
  }, [bootstrap]);

  // ---- stream (CON-3) ----
  const onEvent = useCallback((data: unknown, id: number | null, type: string) => {
    const event = data as ChatEvent;
    if (!type || !event || typeof event !== "object") return;
    const key = String(id ?? event.event_id);
    dispatch({ type: "EVENT", key, event });
    const d = demoRef.current;
    const say = (m: string) => announceRef.current(m);
    switch (event.type) {
      case "staffing_changed": d.setFromChat({ staffing: event.staffing }); say(event.line); break;
      case "clock_changed": d.setFromChat({ clock: event.demo_clock }); break;
      case "shift_ended": void d.refresh(); say(event.line); break;
      case "staff_message": say(`${event.speaker.display_name ?? "Representative"}: ${event.text}`); break;
      case "demo_reset": resetCardMemory(); say(event.line); break;
      case "representative_joined": case "ai_paused": case "ai_resumed": case "chat_closed": say(event.line); break;
      default: break;
    }
  }, []);
  const streamSpec = useMemo(
    () => (streamStart && !state.ended ? { op: "streamChatEvents" as const, path: { thread_id: streamStart.threadId }, lastEventId: streamStart.lastEventId } : null),
    [streamStart, state.ended],
  );
  const stream = useEventStream(streamSpec, onEvent);

  // ---- locks ----
  const composerLock = useMemo<ComposerLock | null>(() => {
    if (state.ended) return { reason: "ended", hint: MSG.ended };
    if (state.phase !== "ready") return { reason: "starting", hint: "" };
    if (state.lastNotice?.code === "RATE_LIMITED" && state.rateHeld) return { reason: "rate", hint: state.lastNotice.text };
    if (state.lastNotice?.code === "SPEND_CAP_REACHED") return { reason: "spend", hint: state.lastNotice.text };
    return null;
  }, [state.ended, state.phase, state.lastNotice, state.rateHeld]);
  const lockRef = useRef(composerLock);
  lockRef.current = composerLock;

  // ---- turns ----
  const execTurn = useCallback(async (entry: CustomerEntry) => {
    const threadId = threadRef.current;
    if (!threadId) return;
    const ac = new AbortController();
    const body = { turn_id: entry.turnId, payload: entry.payload as TurnPayload };
    const run = (async () => {
      for (;;) {
        try {
          return await gateway.submit(threadId, body, ac.signal);
        } catch (e) {
          if (e instanceof ApiError && e.status === 409 && e.code === "TURN_IN_PROGRESS") {
            const ms = typeof e.details?.retry_after_ms === "number" ? e.details.retry_after_ms : 1000;
            await sleep(ms, ac.signal); // same turn_id on the next call
            continue;
          }
          throw e;
        }
      }
    })();
    run.catch(() => undefined); // an aborted loop must not surface as unhandled
    let timer: ReturnType<typeof setTimeout> | undefined;
    const giveUp = new Promise<typeof GAVE_UP>((resolve) => { timer = setTimeout(() => resolve(GAVE_UP), limitsRef.current.browser_give_up_after_ms); });
    try {
      const res = await Promise.race([run, giveUp]);
      if (res === GAVE_UP) {
        ac.abort();
        dispatch({ type: "TURN_FAIL", turnId: entry.turnId, message: MSG.sendFailed, retryable: true });
        return;
      }
      dispatch({ type: "TURN_OK", turnId: entry.turnId, res });
      // G2's cards land visit and request themselves; the identity landing has no block, so it is ours.
      if (landingsFromWrites(res.writes).includes("identity")) {
        land("identity", res.settled);
      }
      if (res.notice?.code === "RATE_LIMITED") {
        if (rateTimer.current) clearTimeout(rateTimer.current);
        rateTimer.current = setTimeout(() => dispatch({ type: "RATE_HOLD_END" }), RATE_HOLD_MS);
      }
    } catch (e) {
      const d = describe(e, "turn");
      if (d.ended) dispatch({ type: "ENDED", reason: d.ended });
      dispatch({ type: "TURN_FAIL", turnId: entry.turnId, message: d.message, retryable: d.ended ? false : d.retryable });
    } finally {
      clearTimeout(timer);
      turnBusy.current = false;
    }
  }, [gateway, land]);

  /** The one set of guards for sending a customer turn; the composer asks it before clearing the draft. */
  const canSend = useCallback((): boolean => {
    const s = stateRef.current;
    if (!threadRef.current || s.ended || s.pending || turnBusy.current) return false;
    return lockRef.current?.reason !== "rate" && lockRef.current?.reason !== "spend";
  }, []);

  const sendTurn = useCallback(async (payload: TurnPayload, action: ChatAction) => {
    if (!canSend()) return;
    const s = stateRef.current;
    turnBusy.current = true;
    const turnId = newTurnId();
    const entry: CustomerEntry = {
      kind: "customer", id: `c:${turnId}`, turnId, at: null, text: customerRowText(action, s.entries), payload,
      delivery: "pending", failure: null, retryable: false, attempt: 0,
    };
    if (action.kind === "choice") dispatch({ type: "ANSWERED", cardId: action.cardId, option: action.option });
    if (action.kind === "code") dispatch({ type: "ANSWERED", cardId: action.cardId, option: "code" });
    if (action.kind === "form") dispatch({ type: "ANSWERED", cardId: action.cardId, option: "form" });
    dispatch({ type: "SEND_BEGIN", entry, startedAtMs: Date.now() });
    await execTurn(entry);
  }, [execTurn, canSend]);

  const runPerson = useCallback(async (turnId: string) => {
    if (personBusy.current) return;
    personBusy.current = true;
    try {
      if (!threadRef.current && startPromise.current) await startPromise.current;
      const threadId = threadRef.current;
      if (!threadId || stateRef.current.ended) return;
      const entry: CustomerEntry = {
        kind: "customer", id: `c:${turnId}`, turnId, at: null, text: "Talk to a person", payload: { kind: "person" },
        delivery: "sent", failure: null, retryable: false, attempt: 0,
      };
      try {
        const res = await gateway.requestPerson(threadId, turnId);
        dispatch({ type: "PERSON_OK", turnId, res, entry });
        if (res.result === "already_open") {
          const target = [...stateRef.current.entries].reverse().find(
            (e) => e.kind === "reply" && e.blocks.some((b) => b.type === "handoff" || b.type === "live_queued"),
          );
          if (target) setScrollTarget({ id: target.id, nonce: ++nonce.current });
          land("request", res.settled);
        }
      } catch (e) {
        const d = describe(e, "person");
        if (d.ended) dispatch({ type: "ENDED", reason: d.ended });
        else dispatch({ type: "LINE", id: `person-fail:${turnId}`, text: d.message });
      }
    } finally {
      personBusy.current = false;
    }
  }, [gateway, land]);

  const dispatchAction = useCallback(async (a: ChatAction): Promise<void> => {
    try {
      switch (a.kind) {
        case "text": {
          const text = a.text.trim();
          if (text) await sendTurn({ kind: "text", text }, { kind: "text", text });
          return;
        }
        case "choice": return await sendTurn({ kind: "choice", card_id: a.cardId, option: a.option }, a);
        case "code": return await sendTurn({ kind: "code", card_id: a.cardId, code: a.code }, a);
        case "form": return await sendTurn({ kind: "form", card_id: a.cardId, values: a.values }, a);
        case "retry": {
          const s = stateRef.current;
          if (s.ended || s.pending || turnBusy.current || !threadRef.current) return;
          const customers = s.entries.filter((e): e is CustomerEntry => e.kind === "customer" && e.payload.kind !== "person");
          // "" means "the turn this reply answers": the latest customer turn
          const entry = a.turnId === "" ? customers[customers.length - 1] : s.entries.find((e): e is CustomerEntry => e.kind === "customer" && e.turnId === a.turnId);
          if (!entry) return;
          turnBusy.current = true;
          dispatch({ type: "RETRY_BEGIN", turnId: entry.turnId, startedAtMs: Date.now() });
          return await execTurn({ ...entry, attempt: entry.attempt + 1 });
        }
        case "person": return await runPerson(newTurnId());
        case "followUp": {
          const threadId = threadRef.current;
          if (!threadId || stateRef.current.ended) return;
          try {
            const res = await gateway.saveFollowUp(threadId, { channel: a.channel, destination: a.destination, window: a.window });
            dispatch({ type: "FOLLOWUP_OK", res });
          } catch (e) {
            const d = describe(e, "followup");
            if (d.ended) dispatch({ type: "ENDED", reason: d.ended });
            else dispatch({ type: "LINE", id: `followup-fail:${nonce.current++}`, text: d.message });
          }
          return;
        }
        case "newChat": {
          clearThread();
          resetCardMemory();
          threadRef.current = null;
          turnBusy.current = false;
          personBusy.current = false;
          setStreamStart(null);
          dispatch({ type: "START_BEGIN" });
          bootstrap(false);
          return;
        }
      }
    } catch {
      /* dispatch never rejects: every failure is shown as a line */
    }
  }, [sendTurn, execTurn, runPerson, gateway, bootstrap]);

  // ---- resync after refetchAll (also how the mock reaches resume-class states) ----
  useEffect(() => onRefetchAll(() => {
    const id = threadRef.current;
    if (!id || stateRef.current.pending) return;
    gateway.resume(id).then(
      (thread) => {
        dispatch({ type: "RESYNC_OK", thread });
        demoRef.current.setFromChat({ clock: thread.demo_clock });
        void demoRef.current.refresh();
      },
      (e) => { const d = describe(e, "start"); if (d.ended) dispatch({ type: "ENDED", reason: d.ended }); },
    );
  }), [gateway]);

  const phase: PendingPhase = usePendingPhase(state.pending, state.limits);
  const stableAnnounce = useCallback((m: string) => announceRef.current(m), []);
  return {
    state, phase, streamStatus: stream.status as StreamStatus, composerLock, landing, landingText, scrollTarget,
    dispatch: dispatchAction, canSend, land, retryStart, announce: stableAnnounce,
  };
}
