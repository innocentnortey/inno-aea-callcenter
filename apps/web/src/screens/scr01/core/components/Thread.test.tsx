import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { expectNo24HourTimes } from "@/test/no24h";
import type { BlockProps, ReplyBlock } from "../../contract";
import type { CustomerEntry, Entry } from "../model";
import { turnExample } from "../testFixtures";
import { Thread, type ThreadProps } from "./Thread";

const seen = vi.hoisted(() => ({ props: [] as unknown[] }));
vi.mock("../../blocks", () => ({
  renderBlock: (p: BlockProps<"text">) => { seen.props.push(p); return <span data-testid="block">{p.block.type}</span>; },
}));
beforeEach(() => { seen.props = []; });

const customer = (over: Partial<CustomerEntry> = {}): CustomerEntry => ({
  kind: "customer", id: "c:1", turnId: "1", at: "2026-10-16T14:20:00-05:00", text: "hello", payload: { kind: "text", text: "hello" }, delivery: "sent", failure: null, retryable: false, attempt: 0, ...over,
});
const reply = (blocks: ReplyBlock[], live = true, id = "r1"): Entry => ({ kind: "reply", id, blocks, live });
const base = (over: Partial<ThreadProps> = {}): ThreadProps => ({
  entries: [], answered: {}, settled: turnExample("BOOKED").settled, disabled: false, dispatch: vi.fn(async () => undefined), announce: vi.fn(), landed: vi.fn(),
  phase: "hidden", scrollTarget: null, onRetry: vi.fn(), ...over,
});
const blocks = (name: string) => turnExample(name).blocks;

describe("Thread", () => {
  it("is a polite log with additions", () => {
    render(<Thread {...base({ entries: [customer()] })} />);
    const log = screen.getByRole("log");
    expect(log.getAttribute("aria-live")).toBe("polite");
    expect(log.getAttribute("aria-relevant")).toBe("additions");
  });
  it("passes renderBlock exactly the frozen BlockProps", () => {
    const p = base({ entries: [reply(blocks("ANSWER_WITH_SOURCE"))], answered: {} });
    render(<Thread {...p} />);
    const props = seen.props[0] as Record<string, unknown>;
    expect(Object.keys(props).sort()).toEqual(["announce", "answered", "block", "disabled", "dispatch", "landed", "settled"]);
    expect(props.dispatch).toBe(p.dispatch);
    expect(props.announce).toBe(p.announce);
    expect(props.landed).toBe(p.landed);
    expect(props.disabled).toBe(false);
    expect(props.answered).toBe(false);
  });
  it("history replies get no-op announce and landed so a reload stays quiet", () => {
    const p = base({ entries: [reply(blocks("ANSWER_WITH_SOURCE"), false)] });
    render(<Thread {...p} />);
    const props = seen.props[0] as BlockProps<"text">;
    expect(props.announce).not.toBe(p.announce);
    props.announce("x");
    props.landed("visit");
    expect(p.announce).not.toHaveBeenCalled();
    expect(p.landed).not.toHaveBeenCalled();
  });
  it("marks a card answered from the local answers", () => {
    const quick = blocks("QUICK_CHECKS");
    const card = quick.find((b) => "card_id" in b)!;
    render(<Thread {...base({ entries: [reply(quick)], answered: { [(card as { card_id: string }).card_id]: "x" } })} />);
    expect(seen.props.some((p) => (p as { answered: boolean }).answered)).toBe(true);
  });
  it("keeps the safety block out of the log", () => {
    render(<Thread {...base({ entries: [reply(blocks("SAFETY"))] })} />);
    expect(seen.props).toHaveLength(0);
  });
  it("puts conditional safety in the thread (not pinned)", () => {
    render(<Thread {...base({ entries: [reply(blocks("CONDITIONAL_SAFETY"))] })} />);
    expect(seen.props.some((p) => (p as { block: ReplyBlock }).block.type === "conditional_safety")).toBe(true);
  });
  it("wraps bubble blocks in the grey turn and leaves card blocks bare", () => {
    render(<Thread {...base({ entries: [reply(blocks("ANSWER_WITH_SOURCE"), true, "a"), reply(blocks("BOOKED"), true, "b")] })} />);
    const els = screen.getAllByTestId("block");
    const bubbleOf = (el: HTMLElement) => el.closest("[class*='turn-assistant-bg']");
    const text = els.find((e) => e.textContent === "text")!;
    const confirmation = els.find((e) => e.textContent === "confirmation")!;
    expect(bubbleOf(text)).not.toBeNull();
    expect(bubbleOf(confirmation)).toBeNull();
  });
  it("sits the pending line outside the log", () => {
    render(<Thread {...base({ entries: [customer({ delivery: "pending" })], phase: "replying" })} />);
    const status = screen.getByRole("status");
    expect(status.textContent).toBe("Meridian assistant is replying…");
    expect(within(screen.getByRole("log")).queryByRole("status")).toBeNull();
  });
  it("shows the failed line with Try again for a failed customer row", () => {
    const onRetry = vi.fn();
    render(<Thread {...base({ entries: [customer({ delivery: "failed", failure: "That didn't send. Your message is still here.", retryable: true })], onRetry })} />);
    expect(screen.getByText("That didn't send. Your message is still here.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalledWith("1");
  });
  it("renders event lines, staff messages and quiet lines; times are 12-hour", () => {
    const entries: Entry[] = [
      { kind: "event", id: "e1", at: "2026-10-16T14:22:00-05:00", line: "Riley (demo representative) has joined.", icon: "joined" },
      { kind: "message", id: "m1", speaker: { kind: "representative", display_name: "Riley" }, at: "2026-10-16T14:22:40-05:00", text: "Hi Omar" },
      { kind: "line", id: "l1", text: "There's no open request to attach this to." },
      customer(),
    ];
    const { container } = render(<Thread {...base({ entries })} />);
    expect(screen.getByText(/has joined\./)).toBeTruthy();
    expect(screen.getByText("Hi Omar")).toBeTruthy();
    expect(screen.getByText("There's no open request to attach this to.")).toBeTruthy();
    expectNo24HourTimes(container);
  });
  it("scrolls to and highlights the requested entry", () => {
    vi.useFakeTimers();
    const entries = [customer(), reply(blocks("HANDOFF"), true, "h1")];
    const { rerender } = render(<Thread {...base({ entries })} />);
    rerender(<Thread {...base({ entries, scrollTarget: { id: "h1", nonce: 1 } })} />);
    const el = document.querySelector('[data-entry="h1"]')!;
    expect(el.classList.contains("landed")).toBe(true);
    vi.advanceTimersByTime(1200);
    expect(el.classList.contains("landed")).toBe(false);
    vi.useRealTimers();
  });
});
