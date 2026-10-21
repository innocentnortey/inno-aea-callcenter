import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { Time, TimeWindow } from "./Time";

describe("Time", () => {
  it("renders a <time datetime> in 12-hour demo time", () => {
    const { container } = render(<Time iso="2026-10-19T19:00:00-05:00" format="point" />);
    const el = container.querySelector("time");
    expect(el?.getAttribute("datetime")).toBe("2026-10-19T19:00:00-05:00");
    expect(el?.textContent).toBe("7:00 pm");
  });
  it("renders the fallback for null", () => {
    const { container } = render(<Time iso={null} format="point" fallback="No due time: safety" />);
    expect(container.textContent).toBe("No due time: safety");
    expect(container.querySelector("time")).toBeNull();
  });
  it("hero arrow is aria-hidden with a hidden 'to'", () => {
    const { container } = render(<TimeWindow startIso="2026-10-21T08:00:00-05:00" endIso="2026-10-21T12:00:00-05:00" arrow variant="hero" />);
    const arrow = container.querySelector("[aria-hidden=true]");
    expect(arrow?.textContent).toContain("→");
    expect(container.querySelector(".sr-only")?.textContent).toContain("to");
  });
  it("never applies uppercase to a time", () => {
    const { container } = render(<Time iso="2026-10-19T19:00:00-05:00" format="short" variant="meta" />);
    expect(container.innerHTML).not.toMatch(/uppercase|t-section|t-signal/);
  });
});
