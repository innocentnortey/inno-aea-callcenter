import { act, renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { ApiError } from "@/api/errors";
import { refetchAll } from "@/api/refetch";
import { AnnounceProvider } from "@/components/ui/LiveRegion";
import { DemoStatusContext, type DemoStatusApi } from "@/state/demoStatus";
import { chatEvents } from "@/dev/stream/events";
import type { ChatGateway } from "./gateway";
import type { StartSessionResponse, TurnResponse } from "./model";
import { RATE_HOLD_MS } from "./pending";
import { THREAD_KEY } from "./storage";
import { followUpExample, handoffExample, startExample, threadExample, turnExample } from "./testFixtures";
import { useChat } from "./useChat";

const memory = vi.hoisted(() => ({ reset: vi.fn() }));
vi.mock("../cards/resetCardMemory", () => ({ resetCardMemory: memory.reset }));

const stream = vi.hoisted(() => ({ spec: null as unknown, cb: null as ((d: unknown, id: number | null, t: string) => void) | null, status: "open" }));
vi.mock("@/api/useEventStream", () => ({
  useEventStream: (spec: unknown, cb: (d: unknown, id: number | null, t: string) => void) => { stream.spec = spec; stream.cb = cb; return { status: stream.status, lastEventId: null }; },
}));

type Fake = { [K in keyof ChatGateway]: Mock<ChatGateway[K]> };
function fakeGateway(over: Partial<ChatGateway> = {}): Fake {
  const g = {
    start: vi.fn(async () => startExample()),
    resume: vi.fn(async () => threadExample("OPEN")),
    submit: vi.fn(async () => turnExample("ANSWER_WITH_SOURCE")),
    requestPerson: vi.fn(async () => handoffExample("CASE_CREATED")),
    saveFollowUp: vi.fn(async () => followUpExample()),
    ...over,
  };
  return g as unknown as Fake;
}
const demo = (): DemoStatusApi => ({ clock: null, staffing: null, refresh: vi.fn(async () => undefined), setFromChat: vi.fn(), setSource: vi.fn() });
let demoApi = demo();
const wrapper = ({ children }: { children: ReactNode }) => (
  <AnnounceProvider><DemoStatusContext.Provider value={demoApi}>{children}</DemoStatusContext.Provider></AnnounceProvider>
);
const setup = (g: ChatGateway) => renderHook(() => useChat(g), { wrapper });
const ready = async (g: ChatGateway) => { const h = setup(g); await waitFor(() => expect(h.result.current.state.phase).toBe("ready")); return h; };
const apiErr = (status: number, code: string, details: Record<string, unknown> | null = null) => new ApiError(status, code, null, details);

beforeEach(() => { sessionStorage.clear(); demoApi = demo(); stream.status = "open"; });
afterEach(() => { vi.useRealTimers(); });

describe("useChat: start and resume", () => {
  it("starts a chat, stores the thread, shows the greeting and opens the stream", async () => {
    const g = fakeGateway();
    const { result } = await ready(g);
    expect(g.start).toHaveBeenCalledTimes(1);
    expect(g.resume).not.toHaveBeenCalled();
    expect(JSON.parse(sessionStorage.getItem(THREAD_KEY)!).threadId).toBe(startExample().thread_id);
    expect(result.current.state.entries[0]).toMatchObject({ id: "greeting" });
    expect(stream.spec).toMatchObject({ op: "streamChatEvents", path: { thread_id: startExample().thread_id }, lastEventId: startExample().events.last_event_id });
    expect(demoApi.setFromChat).toHaveBeenCalled();
    expect(demoApi.setSource).toHaveBeenCalledWith("chat");
  });
  it("resumes a stored thread instead of starting", async () => {
    sessionStorage.setItem(THREAD_KEY, JSON.stringify({ threadId: "thr_9d41", limits: startExample().limits }));
    const g = fakeGateway();
    await ready(g);
    expect(g.resume).toHaveBeenCalledWith("thr_9d41");
    expect(g.start).not.toHaveBeenCalled();
    expect(demoApi.refresh).toHaveBeenCalled();
  });
  it("404 on resume clears storage and starts a new chat", async () => {
    sessionStorage.setItem(THREAD_KEY, JSON.stringify({ threadId: "old", limits: startExample().limits }));
    const g = fakeGateway({ resume: vi.fn(async () => { throw apiErr(404, "SESSION_NOT_FOUND"); }) });
    const { result } = await ready(g);
    expect(g.start).toHaveBeenCalled();
    expect(result.current.state.ended).toBeNull();
    expect(JSON.parse(sessionStorage.getItem(THREAD_KEY)!).threadId).toBe(startExample().thread_id);
  });
  it("410 on resume shows an ended chat", async () => {
    sessionStorage.setItem(THREAD_KEY, JSON.stringify({ threadId: "old", limits: startExample().limits }));
    const g = fakeGateway({ resume: vi.fn(async () => { throw apiErr(410, "SESSION_ENDED"); }) });
    const { result } = await ready(g);
    expect(result.current.state.ended).toBe("gone");
    expect(result.current.composerLock).toMatchObject({ reason: "ended", hint: "This chat has ended." });
    expect(g.start).not.toHaveBeenCalled();
  });
  it("a failed start offers a retry", async () => {
    const start = vi.fn().mockRejectedValueOnce(new ApiError(0, "NETWORK", null)).mockResolvedValue(startExample());
    const { result } = setup(fakeGateway({ start }));
    await waitFor(() => expect(result.current.state.phase).toBe("start-failed"));
    expect(result.current.state.startFailure).toBe("The chat didn't start. Try again.");
    act(() => result.current.retryStart());
    await waitFor(() => expect(result.current.state.phase).toBe("ready"));
  });
});

describe("useChat: turns", () => {
  it("shows the customer row at once, then the reply; choices mark the card answered", async () => {
    let release!: () => void;
    const submit = vi.fn(async () => turnExample("ANSWER_WITH_SOURCE"));
    submit.mockImplementationOnce(() => new Promise<TurnResponse>((r) => { release = () => r(turnExample("ANSWER_WITH_SOURCE")); }));
    const g = fakeGateway({ submit });
    const { result } = await ready(g);
    let p!: Promise<void>;
    act(() => { p = result.current.dispatch({ kind: "text", text: "  hello " }); });
    expect(result.current.state.entries.at(-1)).toMatchObject({ kind: "customer", text: "hello", delivery: "pending" });
    expect(result.current.state.pending).not.toBeNull();
    await act(async () => { release(); await p; });
    expect(result.current.state.pending).toBeNull();
    expect(result.current.state.entries.at(-1)).toMatchObject({ kind: "reply" });
    await act(async () => { await result.current.dispatch({ kind: "choice", cardId: "qc-1", option: "skip_and_book" }); });
    expect(result.current.state.answered).toEqual({ "qc-1": "skip_and_book" });
    expect(g.submit.mock.calls[1][1].payload).toEqual({ kind: "choice", card_id: "qc-1", option: "skip_and_book" });
  });
  it("ignores empty text and a second send while pending", async () => {
    const g = fakeGateway({ submit: vi.fn(() => new Promise<TurnResponse>(() => undefined)) });
    const { result } = await ready(g);
    await act(async () => { await result.current.dispatch({ kind: "text", text: "   " }); });
    expect(g.submit).not.toHaveBeenCalled();
    act(() => { void result.current.dispatch({ kind: "text", text: "a" }); });
    await act(async () => { await result.current.dispatch({ kind: "text", text: "b" }); });
    expect(g.submit).toHaveBeenCalledTimes(1);
  });
  it("Try again re-sends the same turn_id; an empty retry id means the latest customer turn", async () => {
    const submit = vi.fn().mockRejectedValueOnce(new ApiError(0, "NETWORK", null)).mockResolvedValue(turnExample("ANSWER_WITH_SOURCE"));
    const g = fakeGateway({ submit });
    const { result } = await ready(g);
    await act(async () => { await result.current.dispatch({ kind: "text", text: "hi" }); });
    const failed = result.current.state.entries.find((e) => e.kind === "customer")!;
    expect(failed).toMatchObject({ delivery: "failed", failure: "That didn't send. Your message is still here.", retryable: true });
    await act(async () => { await result.current.dispatch({ kind: "retry", turnId: "" }); });
    expect(submit.mock.calls[1][1].turn_id).toBe(submit.mock.calls[0][1].turn_id);
    expect(result.current.state.entries.find((e) => e.kind === "customer")).toMatchObject({ delivery: "sent" });
    expect(result.current.state.entries.filter((e) => e.kind === "customer")).toHaveLength(1);
  });
  it("TURN_IN_PROGRESS waits retry_after_ms and retries with the same turn_id", async () => {
    vi.useFakeTimers();
    const submit = vi.fn().mockRejectedValueOnce(apiErr(409, "TURN_IN_PROGRESS", { retry_after_ms: 1500 })).mockResolvedValue(turnExample("ANSWER_WITH_SOURCE"));
    const g = fakeGateway({ submit });
    const { result } = setup(g);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    let p!: Promise<void>;
    act(() => { p = result.current.dispatch({ kind: "text", text: "hi" }); });
    await act(async () => { await vi.advanceTimersByTimeAsync(1000); });
    expect(submit).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(600); await p; });
    expect(submit).toHaveBeenCalledTimes(2);
    expect(submit.mock.calls[1][1].turn_id).toBe(submit.mock.calls[0][1].turn_id);
    expect(result.current.state.pending).toBeNull();
  });
  it("gives up at browser_give_up_after_ms and marks the turn failed", async () => {
    vi.useFakeTimers();
    const g = fakeGateway({ submit: vi.fn(() => new Promise<TurnResponse>(() => undefined)) });
    const { result } = setup(g);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    let p!: Promise<void>;
    act(() => { p = result.current.dispatch({ kind: "text", text: "hi" }); });
    await act(async () => { await vi.advanceTimersByTimeAsync(64999); });
    expect(result.current.state.pending).not.toBeNull();
    await act(async () => { await vi.advanceTimersByTimeAsync(1); await p; });
    expect(result.current.state.entries.find((e) => e.kind === "customer")).toMatchObject({ delivery: "failed" });
    expect(result.current.state.pending).toBeNull();
  });
  it("a 410 on a turn ends the chat; dispatch never rejects", async () => {
    const g = fakeGateway({ submit: vi.fn(async () => { throw apiErr(410, "SESSION_ENDED"); }) });
    const { result } = await ready(g);
    let outcome = "resolved";
    await act(async () => { await result.current.dispatch({ kind: "text", text: "hi" }).catch(() => { outcome = "rejected"; }); });
    expect(outcome).toBe("resolved");
    expect(result.current.state.ended).toBe("gone");
    expect(result.current.state.entries.find((e) => e.kind === "customer")).toMatchObject({ delivery: "failed", retryable: false });
  });
  it("RATE_LIMITED locks the field then releases; SPEND_CAP locks for good; BOOKING_CAP does not lock", async () => {
    vi.useFakeTimers();
    const submit = vi.fn().mockResolvedValueOnce(turnExample("RATE_LIMITED")).mockResolvedValueOnce(turnExample("BOOKING_CAP")).mockResolvedValueOnce(turnExample("SPEND_CAP_REACHED"));
    const { result } = setup(fakeGateway({ submit }));
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    await act(async () => { await result.current.dispatch({ kind: "text", text: "a" }); });
    expect(result.current.composerLock?.reason).toBe("rate");
    await act(async () => { await result.current.dispatch({ kind: "text", text: "blocked" }); });
    expect(submit).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(RATE_HOLD_MS); });
    expect(result.current.composerLock).toBeNull();
    await act(async () => { await result.current.dispatch({ kind: "text", text: "b" }); });
    expect(result.current.composerLock).toBeNull();
    await act(async () => { await result.current.dispatch({ kind: "text", text: "c" }); });
    expect(result.current.composerLock?.reason).toBe("spend");
  });
  it("a verified write lands the Identity block; G2 lands the rest itself", async () => {
    const res = { ...turnExample("VERIFIED_ACCOUNT_INVOICE") };
    expect(res.writes.some((w) => w.kind === "verified")).toBe(true);
    const { result } = await ready(fakeGateway({ submit: vi.fn(async () => res) }));
    await act(async () => { await result.current.dispatch({ kind: "text", text: "x" }); });
    expect(result.current.landing?.target).toBe("identity");
    expect(result.current.landingText).toMatch(/^Identity: /);
    const booked = await ready(fakeGateway({ submit: vi.fn(async () => turnExample("BOOKED")) }));
    await act(async () => { await booked.result.current.dispatch({ kind: "text", text: "x" }); });
    expect(booked.result.current.landing).toBeNull();
  });
});

describe("useChat: person, follow-up, new chat", () => {
  it("first tap adds the row and the card; a second tap adds nothing and scrolls to the card", async () => {
    const requestPerson = vi.fn().mockResolvedValueOnce(handoffExample("CASE_CREATED")).mockResolvedValueOnce(handoffExample("ALREADY_OPEN"));
    const { result } = await ready(fakeGateway({ requestPerson }));
    await act(async () => { await result.current.dispatch({ kind: "person" }); });
    expect(result.current.state.entries).toHaveLength(3);
    expect(result.current.state.entries[1]).toMatchObject({ kind: "customer", text: "Talk to a person" });
    await act(async () => { await result.current.dispatch({ kind: "person" }); });
    expect(result.current.state.entries).toHaveLength(3);
    expect(result.current.scrollTarget?.id).toBe(result.current.state.entries[2].id);
    expect(result.current.landing?.target).toBe("request");
  });
  it("HANDOFF_FAILED shows a quiet line and keeps the key usable", async () => {
    const requestPerson = vi.fn().mockRejectedValueOnce(apiErr(503, "HANDOFF_FAILED")).mockResolvedValue(handoffExample("CASE_CREATED"));
    const { result } = await ready(fakeGateway({ requestPerson }));
    await act(async () => { await result.current.dispatch({ kind: "person" }); });
    expect(result.current.state.entries.at(-1)).toMatchObject({ kind: "line", text: "We couldn't reach a person just now. Tap Talk to a person to try again." });
    await act(async () => { await result.current.dispatch({ kind: "person" }); });
    expect(result.current.state.entries.some((e) => e.kind === "reply" && e.id.startsWith("person:"))).toBe(true);
  });
  it("Talk to a person during start waits for the start", async () => {
    let release!: () => void;
    const g = fakeGateway({ start: vi.fn(() => new Promise<StartSessionResponse>((r) => { release = () => r(startExample()); })) });
    const { result } = setup(g);
    let p!: Promise<void>;
    act(() => { p = result.current.dispatch({ kind: "person" }); });
    expect(g.requestPerson).not.toHaveBeenCalled();
    await act(async () => { release(); await p; });
    expect(g.requestPerson).toHaveBeenCalledTimes(1);
  });
  it("follow-up replaces settled; a 409 adds the quiet line", async () => {
    const fu = followUpExample();
    const saveFollowUp = vi.fn().mockResolvedValueOnce(fu).mockRejectedValueOnce(apiErr(409, "NOT_ALLOWED_IN_STATE"));
    const { result } = await ready(fakeGateway({ saveFollowUp }));
    const action = { kind: "followUp", channel: "phone", destination: "on_record", window: "morning" } as const;
    await act(async () => { await result.current.dispatch(action); });
    expect(result.current.state.settled).toEqual(fu.settled);
    await act(async () => { await result.current.dispatch(action); });
    expect(result.current.state.entries.at(-1)).toMatchObject({ kind: "line", text: "There's no open request to attach this to." });
  });
  it("new chat and a demo reset clear the cards' once-per-block memory", async () => {
    memory.reset.mockClear();
    const { result } = await ready(fakeGateway());
    act(() => { stream.cb?.({ ...chatEvents.demo_reset(), event_id: 60 }, 60, "demo_reset"); });
    expect(memory.reset).toHaveBeenCalledTimes(1);
    await act(async () => { await result.current.dispatch({ kind: "newChat" }); });
    expect(memory.reset).toHaveBeenCalledTimes(2);
  });
  it("canSend is false while the chat is ended and true again after a new chat", async () => {
    const g = fakeGateway();
    const { result } = await ready(g);
    expect(result.current.canSend()).toBe(true);
    act(() => { stream.cb?.(chatEvents.chat_closed(), 5, "chat_closed"); });
    expect(result.current.canSend()).toBe(false);
    await act(async () => { await result.current.dispatch({ kind: "text", text: "hi" }); });
    expect(g.submit).not.toHaveBeenCalled();
    await act(async () => { await result.current.dispatch({ kind: "newChat" }); });
    await waitFor(() => expect(result.current.state.phase).toBe("ready"));
    expect(result.current.canSend()).toBe(true);
  });
  it("new chat clears storage and starts again after an ended chat", async () => {
    const { result } = await ready(fakeGateway());
    act(() => { stream.cb?.(chatEvents.chat_closed(), 5, "chat_closed"); });
    expect(result.current.state.ended).toBe("closed");
    expect(stream.spec).toBeNull();
    const g2 = startExample();
    await act(async () => { await result.current.dispatch({ kind: "newChat" }); });
    await waitFor(() => expect(result.current.state.phase).toBe("ready"));
    expect(result.current.state.ended).toBeNull();
    expect(result.current.state.threadId).toBe(g2.thread_id);
    expect(stream.spec).not.toBeNull();
  });
});

describe("useChat: stream and resync", () => {
  it("events update state and the demo bar", async () => {
    const { result } = await ready(fakeGateway());
    act(() => { stream.cb?.({ ...chatEvents.staffing_changed(), event_id: 41 }, 41, "staffing_changed"); });
    expect(demoApi.setFromChat).toHaveBeenCalledWith({ staffing: expect.objectContaining({ mode: "simulated_on_shift" }) });
    act(() => { stream.cb?.({ ...chatEvents.clock_changed(), event_id: 42 }, 42, "clock_changed"); });
    expect(demoApi.setFromChat).toHaveBeenCalledWith({ clock: expect.objectContaining({ label: expect.any(String) }) });
    act(() => { stream.cb?.({ ...chatEvents.representative_joined(), event_id: 43 }, 43, "representative_joined"); });
    expect(result.current.state.replying.kind).toBe("human");
    act(() => { stream.cb?.({ ...chatEvents.representative_joined(), event_id: 43 }, 43, "representative_joined"); });
    expect(result.current.state.entries.filter((e) => e.kind === "event")).toHaveLength(2); // staffing + joined, no duplicate
  });
  it("reports the stream status", async () => {
    stream.status = "reconnecting";
    const { result } = await ready(fakeGateway());
    expect(result.current.streamStatus).toBe("reconnecting");
  });
  it("refetchAll re-reads the thread; a 410 ends the chat", async () => {
    const resume = vi.fn(async () => threadExample("OPEN"));
    const g = fakeGateway({ resume });
    const { result } = await ready(g);
    act(() => refetchAll());
    await waitFor(() => expect(resume).toHaveBeenCalledTimes(1));
    resume.mockRejectedValueOnce(apiErr(410, "SESSION_ENDED"));
    act(() => refetchAll());
    await waitFor(() => expect(result.current.state.ended).toBe("gone"));
  });
});
