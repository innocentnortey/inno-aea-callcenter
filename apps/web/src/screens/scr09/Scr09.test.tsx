import { beforeEach, describe, expect, it } from "vitest";
import { fireEvent, screen, within } from "@testing-library/react";
import type { CallContext } from "@/api/transport";
import type { Role } from "@/lib/roles";
import { jsonResponse } from "@/test/fakeTransport";
import { expectNo24HourTimes } from "@/test/no24h";
import { renderWithProviders } from "@/test/render";
import { mockDesktop } from "../reads/test/mockDesktop";
import { opsTransport, type OpHandler } from "../reads/test/opsTransport";
import { specExample } from "../reads/test/specExample";
import Scr09 from "./Scr09";

function setup(body: unknown = specExample("getOwnerMetrics", "SEEDED"), extra: Record<string, OpHandler> = {}, role: Role = "owner") {
  const calls: CallContext[] = [];
  const transport = opsTransport(role, { getOwnerMetrics: () => jsonResponse(200, body), ...extra }, calls);
  const view = renderWithProviders(<Scr09 />, { route: "/staff/owner", transport, role });
  return { ...view, calls };
}
const tile = (name: string) => within(screen.getByRole("heading", { level: 2, name }).closest("section") as HTMLElement);
beforeEach(() => mockDesktop());

describe("Scr09", () => {
  it("customer sees the role panel", async () => {
    setup(undefined, {}, "customer");
    await screen.findByText("You're acting as the customer. Switch to a staff role to see this.");
  });

  it("three tiles with denominators", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Estimate from live chats (no verified answers)" });
    expect(tile("Estimate from live chats (no verified answers)").getByText("75%")).toBeTruthy();
    expect(tile("Estimate from live chats (no verified answers)").getByText("9 of 12 in-scope conversations")).toBeTruthy();
    expect(tile("Promises kept on time").getByText("67%")).toBeTruthy();
    expect(tile("Promises kept on time").getByText("2 of 3 promises due")).toBeTruthy();
    expect(tile("Handoffs").getByText("29%")).toBeTruthy();
    expect(tile("Handoffs").getByText("5 of 17 conversations")).toBeTruthy();
    const link = screen.getByRole("link", { name: "The measured number is on the Evaluation page (latest held-out run)." });
    expect(link.getAttribute("href")).toBe("/eval");
  });

  it("basis line names the seeds and says not targets", async () => {
    setup();
    await screen.findByText(/Includes 4 demo seed cases\. These are not targets\./);
  });

  it("outcomes table rows", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Outcomes" });
    const t = within(screen.getByRole("table", { name: "Outcomes of stored conversations" }));
    expect(t.getAllByRole("row")).toHaveLength(6);
    expect(t.getByText("9 of 17 conversations")).toBeTruthy();
    expect(t.getByText("53%")).toBeTruthy();
  });

  it("handoffs by reason rows", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Handoffs by reason" });
    const t = within(screen.getByRole("table", { name: "Handoffs by reason" }));
    expect(t.getByText("Billing dispute")).toBeTruthy();
    expect(t.getByText("2 of 5 handoffs")).toBeTruthy();
    expect(t.getByText("40%")).toBeTruthy();
  });

  it("missed promises row", async () => {
    setup();
    const t = within(await screen.findByRole("table", { name: "Missed promises" }));
    expect(t.getByRole("link", { name: "MHC-C-0005" })).toBeTruthy();
    expect(t.getByText("Fri Oct 16 · 9:00 am")).toBeTruthy();
    expect(t.getByText("Open, overdue")).toBeTruthy();
  });

  it("open the cases expands in place and announces the count", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Handoffs" });
    fireEvent.click(tile("Handoffs").getByRole("button", { name: "Open the cases" }));
    const list = await screen.findByRole("heading", { level: 3, name: /Handoffs/ });
    const section = list.closest("section")!;
    expect(within(section).getByText(/MHC-C-0007/).closest("li")!.textContent).toBe("MHC-C-0007 · Billing dispute · Unassigned");
    expect(within(section).getByRole("link", { name: "MHC-C-0008" })).toBeTruthy();
    await screen.findByText("2 cases listed.");
  });

  it("the estimate tile has no case link when case_refs is empty", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Estimate from live chats (no verified answers)" });
    const t = tile("Estimate from live chats (no verified answers)");
    expect(t.getByText("No cases to open.")).toBeTruthy();
    expect(t.queryByRole("button")).toBeNull();
  });

  it("empty shows the sentence and dash tiles", async () => {
    setup(specExample("getOwnerMetrics", "EMPTY"));
    await screen.findByText("No outcomes yet.");
    expect(screen.getByText("Numbers appear once conversations end. Nothing here is a target.")).toBeTruthy();
    expect(screen.getAllByText("—").length).toBeGreaterThanOrEqual(3);
    expect(screen.getByText("0 in-scope conversations")).toBeTruthy();
    expect(screen.getByText("0 promises due")).toBeTruthy();
    expect(screen.getByText("0 conversations")).toBeTruthy();
  });

  it("partial shows a dash with its reason while the others show numbers", async () => {
    const b = specExample("getOwnerMetrics", "SEEDED");
    b.promises_kept_on_time = { ...b.promises_kept_on_time, numerator: 0, denominator: 0, value: null, null_reason: "No promises are due yet.", case_refs: [] };
    setup(b);
    await screen.findByText("No promises are due yet.");
    expect(tile("Promises kept on time").getByText("—")).toBeTruthy();
    expect(screen.getByText("75%")).toBeTruthy();
  });

  it("stale line when the demo clock moved", async () => {
    const { calls } = setup(undefined, { getDemoClock: () => jsonResponse(200, specExample("getDemoClock", "ADVANCED")) });
    await screen.findByText("These numbers are as of 2:20 pm; the demo time is now Mon 7:00 am.");
    const before = calls.filter((c) => c.op === "getOwnerMetrics").length;
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
    await screen.findByText("These numbers are as of 2:20 pm; the demo time is now Mon 7:00 am.");
    await new Promise((r) => setTimeout(r, 50));
    expect(calls.filter((c) => c.op === "getOwnerMetrics").length).toBe(before + 1);
  });

  it("error shows the sentence", async () => {
    const calls: CallContext[] = [];
    renderWithProviders(<Scr09 />, { route: "/staff/owner", role: "owner", transport: opsTransport("owner", { getOwnerMetrics: () => jsonResponse(500, { error: { code: "X" } }) }, calls) });
    await screen.findByText("Outcomes didn't load. Try again.");
  });

  it("links to Monitoring and Evaluation", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Handoffs" });
    expect(screen.getByRole("link", { name: "Monitoring" }).getAttribute("href")).toBe("/monitoring");
    expect(screen.getByRole("link", { name: "Evaluation" }).getAttribute("href")).toBe("/eval");
  });

  it("no containment word", async () => {
    const { container } = setup();
    await screen.findByRole("heading", { level: 2, name: "Handoffs" });
    expect(container.textContent).not.toMatch(/containment/i);
  });

  it("no 24-hour times", async () => {
    const { container } = setup();
    await screen.findByRole("heading", { level: 2, name: "Handoffs" });
    expectNo24HourTimes(container);
  });
});
