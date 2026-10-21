import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueueRow } from "./QueueRow";
import { expectNo24HourTimes } from "@/test/no24h";
import type { components } from "@/api/types.gen";

type Row = components["schemas"]["QueueRow"];
// getQueue SEEDED examples (MHC-C-0008, MHC-C-0005, MHC-C-0007)
const P0: Row = { reference: "MHC-C-0008", priority: { level: "P0", word: "Safety" }, reason: "Gas smell reported in chat", customer_display_name: "No name given", owner: null, created_at: "2026-10-16T14:16:00-05:00", due_at: null, due_label: null, due_state: "no_due_time", wake_up_at: null, lifecycle: "unassigned", follow_up_short: null, seed: true, brief_status: "ready", queued_at: null, age_label: "Open 4 min" };
const OVERDUE: Row = { ...P0, reference: "MHC-C-0005", priority: { level: "P3", word: "Standard" }, reason: "Refund request", customer_display_name: "Dana Whitaker", due_at: "2026-10-16T09:00:00-05:00", due_label: "Fri Oct 16 · 9:00 am", due_state: "overdue", follow_up_short: "Email" };

describe("QueueRow", () => {
  it("has the specified accessible name", () => {
    render(<ul><QueueRow row={P0} /></ul>);
    // WCAG 2.5.3: no aria-label, so the name is the visible text and starts with the reason the row shows first.
    const btn = screen.getByRole("button", { name: /^Gas smell reported in chat P0 · Safety/ });
    expect(btn.hasAttribute("aria-label")).toBe(false);
    expect(btn.textContent).toContain("MHC-C-0008");
    const name = btn.textContent ?? "";
    for (const visible of ["Gas smell reported in chat", "P0 · Safety", "No name given", "MHC-C-0008", "No due time: safety", "Unowned"]) expect(name).toContain(visible);
  });
  it("shows Overdue as a strong tag with an icon and no red", () => {
    const { container } = render(<ul><QueueRow row={OVERDUE} /></ul>);
    const tag = [...container.querySelectorAll("[data-tone=strong]")].find((t) => t.textContent === "Overdue");
    expect(tag).toBeTruthy();
    expect(tag?.querySelector("svg")).toBeTruthy();
    expect(container.innerHTML).not.toMatch(/red/);
  });
  it("shows Demo seed, Unowned and the no-due words", () => {
    const { container } = render(<ul><QueueRow row={P0} /></ul>);
    expect(container.textContent).toContain("Demo seed");
    expect(container.textContent).toContain("Unowned");
    expect(container.textContent).toContain("No due time: safety");
  });
  it("marks the selected row and keeps times 12-hour", () => {
    const { container } = render(<ul><QueueRow row={OVERDUE} selected /></ul>);
    expect(screen.getByRole("button").getAttribute("aria-current")).toBe("true");
    expectNo24HourTimes(container);
  });
  it("renders a link when href is given", () => {
    render(<ul><QueueRow row={P0} href="/staff/cases/MHC-C-0008" /></ul>);
    expect(screen.getByRole("link").getAttribute("href")).toBe("/staff/cases/MHC-C-0008");
  });
});
