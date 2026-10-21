import { render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Settled } from "../../contract";
import { startExample, turnExample } from "../testFixtures";
import { SettledAside, type SettledAsideProps } from "./SettledAside";

const empty = (): Settled => startExample().settled;
const props = (over: Partial<SettledAsideProps> = {}): SettledAsideProps => ({
  settled: empty(), danger: false, replying: { kind: "ai", display_name: null }, staffingOn: false, landing: null, ...over,
});
function mockWide(wide: boolean) {
  window.matchMedia = ((q: string) => ({ matches: wide && q.includes("900"), media: q, addEventListener: () => {}, removeEventListener: () => {} })) as unknown as typeof window.matchMedia;
}
const original = window.matchMedia;
afterEach(() => { window.matchMedia = original; vi.useRealTimers(); });

describe("SettledAside", () => {
  it("phone: a collapsed strip with the one-line summary inside one named aside", () => {
    mockWide(false);
    render(<SettledAside {...props()} />);
    expect(screen.getByRole("complementary", { name: "What's settled" })).toBeTruthy();
    expect(screen.getByTestId("strip-line").textContent).toBe("Nothing yet");
    expect(document.querySelector("details")?.hasAttribute("open")).toBe(false);
  });
  it("wide: the panel is open with every block and its empty copy", () => {
    mockWide(true);
    render(<SettledAside {...props()} />);
    expect(document.querySelector("details")).toBeNull();
    const aside = screen.getByRole("complementary", { name: "What's settled" });
    for (const t of ["Nothing booked yet.", "No request open.", "Not checked. Only needed for private details.", "What's been confirmed so far"]) expect(within(aside).getByText(t)).toBeTruthy();
    expect(within(aside).queryByText("Replying")).toBeNull();
  });
  it("shows Replying only while the simulation is on", () => {
    mockWide(true);
    render(<SettledAside {...props({ staffingOn: true, replying: { kind: "human", display_name: "Riley" } })} />);
    expect(screen.getByText("Replying")).toBeTruthy();
    expect(screen.getByText("Riley (demo representative). Assistant paused.")).toBeTruthy();
  });
  it("fills visit and request from settled, with the change-request line", () => {
    mockWide(true);
    const change = turnExample("CHANGE_REQUEST").settled;
    render(<SettledAside {...props({ settled: change })} />);
    expect(screen.getByText("Original stays until a representative confirms.")).toBeTruthy();
    expect(screen.getAllByText(/MHC-C-/).length).toBeGreaterThan(0);
    expect(screen.queryByText("Nothing booked yet.")).toBeNull();
  });
  it("danger: header and the danger strip line only", () => {
    mockWide(false);
    render(<SettledAside {...props({ danger: true, settled: turnExample("BOOKED").settled })} />);
    expect(screen.getByTestId("strip-line").textContent).toBe("DANGER · Leave the home immediately");
    expect(screen.queryByText("Your visit")).toBeNull();
    expect(screen.queryByText("Identity")).toBeNull();
  });
  it("landing washes the matching header, then the class goes when the landing clears", () => {
    mockWide(true);
    const { rerender } = render(<SettledAside {...props({ landing: { target: "visit", nonce: 1 } })} />);
    const header = screen.getByText("Your visit").closest("div.flex");
    expect(header?.className).toContain("landed");
    rerender(<SettledAside {...props({ landing: null })} />);
    expect(screen.getByText("Your visit").closest("div.flex")?.className).not.toContain("landed");
  });
  it("never prints a 24-hour time", () => {
    mockWide(true);
    const { container } = render(<SettledAside {...props({ settled: turnExample("BOOKED").settled })} />);
    expect(container.textContent).not.toMatch(/\b(?:1[3-9]|2[0-3]):[0-5]\d\b/);
  });
});
