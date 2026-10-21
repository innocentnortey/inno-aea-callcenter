import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { EventEntry } from "./EventEntry";
import { FailedLine } from "./FailedLine";
import { PendingLine } from "./PendingLine";
import { StartingGreeting } from "./StartingGreeting";

afterEach(() => vi.useRealTimers());

describe("PendingLine", () => {
  it("is empty when hidden or gave up; static text for replying and still", () => {
    const { rerender, container } = render(<PendingLine phase="hidden" />);
    expect(container.textContent).toBe("");
    rerender(<PendingLine phase="replying" />);
    expect(screen.getByRole("status").textContent).toBe("Meridian assistant is replying…");
    const node = screen.getByRole("status");
    rerender(<PendingLine phase="still" />);
    expect(screen.getByRole("status")).toBe(node);
    expect(node.textContent).toBe("Still working on this…");
    rerender(<PendingLine phase="gave-up" />);
    expect(container.textContent).toBe("");
  });
});
describe("FailedLine", () => {
  it("shows the message and Try again", () => {
    const onRetry = vi.fn();
    render(<FailedLine message="That didn't send. Your message is still here." retryable onRetry={onRetry} />);
    expect(screen.getByText("That didn't send. Your message is still here.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalled();
  });
  it("omits Try again when not retryable", () => {
    render(<FailedLine message="This chat has ended." retryable={false} onRetry={vi.fn()} />);
    expect(screen.queryByRole("button")).toBeNull();
  });
});
describe("StartingGreeting", () => {
  it("skeleton for the first second, then words", () => {
    vi.useFakeTimers();
    const { container } = render(<StartingGreeting phase="starting" message={null} onRetry={vi.fn()} />);
    expect(container.querySelector("[data-skeleton]")).not.toBeNull();
    act(() => { vi.advanceTimersByTime(1000); });
    expect(container.querySelector("[data-skeleton]")).toBeNull();
    expect(screen.getByText("Starting the chat…")).toBeTruthy();
  });
  it("start-failed shows the message and a retry", () => {
    const onRetry = vi.fn();
    render(<StartingGreeting phase="start-failed" message="The chat didn't start. Try again." onRetry={onRetry} />);
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalled();
  });
});
describe("EventEntry", () => {
  it("prints the server line with a hidden System event prefix", () => {
    render(<EventEntry entry={{ kind: "event", id: "e", at: "2026-10-16T14:22:00-05:00", line: "Riley (demo representative) has joined.", icon: "joined" }} />);
    expect(screen.getByText("System event:")).toBeTruthy();
    expect(screen.getByText(/Riley \(demo representative\) has joined\./)).toBeTruthy();
  });
});
