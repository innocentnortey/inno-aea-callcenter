import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AnnounceProvider, useAnnounce } from "./LiveRegion";

let announce: (m: string) => void = () => undefined;
function Grab() { announce = useAnnounce(); return null; }
const region = (c: HTMLElement) => c.querySelector("[aria-live]")!.textContent;

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("AnnounceProvider", () => {
  it("announces one message after the clear window", () => {
    const { container } = render(<AnnounceProvider><Grab /></AnnounceProvider>);
    act(() => announce("Saved."));
    expect(region(container)).toBe("");
    act(() => { vi.advanceTimersByTime(25); });
    expect(region(container)).toBe("Saved.");
  });
  it("two announcements inside the window are both kept, in order", () => {
    const { container } = render(<AnnounceProvider><Grab /></AnnounceProvider>);
    act(() => { announce("First."); vi.advanceTimersByTime(5); announce("Second."); });
    act(() => { vi.advanceTimersByTime(30); });
    expect(region(container)).toBe("First. Second.");
  });
  it("a later announcement after the window replaces the earlier one", () => {
    const { container } = render(<AnnounceProvider><Grab /></AnnounceProvider>);
    act(() => { announce("First."); vi.advanceTimersByTime(30); announce("Second."); vi.advanceTimersByTime(30); });
    expect(region(container)).toBe("Second.");
  });
  it("clears the pending timer on unmount", () => {
    const { unmount } = render(<AnnounceProvider><Grab /></AnnounceProvider>);
    act(() => announce("Bye."));
    unmount();
    expect(vi.getTimerCount()).toBe(0);
  });
});
