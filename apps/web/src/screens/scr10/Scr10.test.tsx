import { afterEach, describe, expect, it, vi } from "vitest";
import { act, screen, waitFor, within } from "@testing-library/react";
import type { CallContext } from "@/api/transport";
import type { Role } from "@/lib/roles";
import { jsonResponse } from "@/test/fakeTransport";
import { expectNo24HourTimes } from "@/test/no24h";
import { renderWithProviders } from "@/test/render";
import { opsTransport, type OpHandler } from "../reads/test/opsTransport";
import { specExample } from "../reads/test/specExample";
import Scr10 from "./Scr10";

function setup(handler: OpHandler | string = "DEFAULT", role: Role = "customer") {
  const calls: CallContext[] = [];
  const h: OpHandler = typeof handler === "string" ? () => jsonResponse(200, specExample("getMonitoring", handler)) : handler;
  const view = renderWithProviders(<Scr10 />, { route: "/monitoring", role, transport: opsTransport(role, { getMonitoring: h }, calls) });
  return { ...view, calls };
}
const section = (name: string) => within(screen.getByRole("region", { name }));
const row = (s: ReturnType<typeof section>, label: string) => s.getByText(label).closest("div")!.parentElement!;
afterEach(() => vi.useRealTimers());

describe("Scr10", () => {
  it("renders for the customer role", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Health" });
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getAllByRole("radiogroup", { name: "Acting as" }).length).toBeGreaterThan(0);
    expect(screen.queryByText(/Switch to a staff role/)).toBeNull();
  });

  it("updated line", async () => {
    setup();
    await screen.findByText("Updated 2:20 pm · redacted · traces are not shown here");
  });

  it("health rows", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Health" });
    const h = section("Health");
    expect(row(h, "Conversations").textContent).toContain("18");
    expect(row(h, "Turns").textContent).toContain("74");
    expect(row(h, "Failures").textContent).toContain("1 of 74 turns");
    expect(row(h, "Latency p50").textContent).toContain("4.2 s");
    expect(row(h, "Latency p95").textContent).toContain("10.2 s");
    expect(h.getByText("$6.12 of $30.00 daily cap")).toBeTruthy();
    expect(row(h, "Last health-check restart").textContent).toContain("Thu Oct 15 · 10:41 pm");
    expect(row(h, "Trace export").textContent).toContain("sent 70 of 74");
  });

  it("health and correctness are separate sections", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Correctness" });
    expect(section("Health").queryByText(/Estimate of correct resolution/)).toBeNull();
    expect(section("Correctness").getByText(/Estimate of correct resolution/)).toBeTruthy();
    expect(section("Correctness").getByText("9 of 12 live conversations")).toBeTruthy();
    expect(section("Correctness").getByText("75%")).toBeTruthy();
    expect(section("Correctness").getByText("Billing dispute")).toBeTruthy();
  });

  it("firing first", async () => {
    setup("FIRING");
    await screen.findByRole("heading", { level: 2, name: "Alerts" });
    const items = within(screen.getByRole("heading", { level: 2, name: "Alerts" }).closest("section")!).getAllByRole("listitem");
    const firing = items.filter((li) => li.textContent?.includes("Firing"));
    expect(firing.length).toBe(2);
    expect(items.slice(0, 2)).toEqual(firing);
    expect(items.slice(2).every((li) => li.textContent?.startsWith("Quiet"))).toBe(true);
    expect(screen.getByText("Cap reached")).toBeTruthy();
  });

  it("partial shows the reason in place of the value", async () => {
    setup("TOO_FEW_TURNS");
    await screen.findByRole("heading", { level: 2, name: "Health" });
    expect(screen.getAllByText("Not enough turns yet (fewer than 20)")).toHaveLength(2);
    expect(row(section("Health"), "Conversations").textContent).toContain("18");
  });

  it("empty shows the sentence", async () => {
    setup("EMPTY");
    await screen.findByText("No conversations since the last reset, so there is nothing to measure yet.");
    expect(screen.getAllByText("No turns yet").length).toBeGreaterThan(0);
    expect(row(section("Health"), "Last health-check restart").textContent).toContain("Thu Oct 15");
  });

  it("error shows the sentence", async () => {
    setup(() => jsonResponse(500, { error: { code: "X" } }));
    await screen.findByText("Monitoring didn't load. Try again.");
  });

  it("resetting shows the reset sentence", async () => {
    setup(() => jsonResponse(503, { error: { code: "RESET_IN_PROGRESS", details: null }, request_id: "r" }));
    await screen.findByText("The demo is resetting. Try again in a few seconds.");
  });

  it("stale data line", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "setInterval", "Date"], shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-10-16T14:25:00-05:00"));
    setup();
    await screen.findByText("This data is 5 minutes old.");
  });

  it("no stale line when the data is fresh", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "setInterval", "Date"], shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-10-16T14:21:00-05:00"));
    setup();
    await screen.findByRole("heading", { level: 2, name: "Health" });
    expect(screen.queryByText(/This data is/)).toBeNull();
  });

  it("announces a newly firing alert only", async () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "setInterval", "Date"], shouldAdvanceTime: true });
    vi.setSystemTime(new Date("2026-10-16T14:20:00-05:00"));
    let n = 0;
    setup(() => jsonResponse(200, specExample("getMonitoring", ++n === 1 ? "DEFAULT" : "FIRING")));
    await screen.findByRole("heading", { level: 2, name: "Health" });
    const live = () => document.querySelector("[aria-live][aria-atomic]")!.textContent;
    expect(live()).toBe("");
    await act(async () => { await vi.advanceTimersByTimeAsync(30_100); });
    await waitFor(() => expect(live()).toContain("Spend reached the $30 daily cap"));
    const before = live();
    await act(async () => { await vi.advanceTimersByTimeAsync(30_100); });
    expect(live()).toBe(before);
  });

  it("definitions present", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Health" });
    expect(screen.getByText("What each measure counts")).toBeTruthy();
    expect(screen.getByText(/Live conversations started since the last reset/)).toBeTruthy();
  });

  it("no trace links", async () => {
    const { container } = setup("FAILURE_AND_TRACE_FIRING");
    await screen.findByRole("heading", { level: 2, name: "Health" });
    expect(Array.from(container.querySelectorAll("a[href]")).some((a) => /trace/i.test(a.getAttribute("href") ?? ""))).toBe(false);
  });

  it("no 24-hour times", async () => {
    const { container } = setup();
    await screen.findByRole("heading", { level: 2, name: "Health" });
    expectNo24HourTimes(container);
  });
});
