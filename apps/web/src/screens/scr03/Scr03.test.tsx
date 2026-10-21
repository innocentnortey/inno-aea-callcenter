import { afterEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/render";
import { jsonResponse, makeFakeTransport } from "@/test/fakeTransport";
import { CLOCK_START, SESSION_BY_ROLE, SESSION_CUSTOMER, STAFFING_OFF, STAFFING_ON } from "@/test/fixtures";
import type { CallContext } from "@/api/transport";
import type { Role } from "@/lib/roles";
import Scr03 from "./Scr03";

// setStaffing TURNED_ON / TURNED_OFF_WITH_WAITING and resetDemo RESET examples.
const TURNED_ON = { mode: "simulated_on_shift", label: "Simulated staff on shift (demo)", converted_cases: 0 };
const TURNED_OFF = { mode: "nobody_online", label: "Nobody online", converted_cases: 1 };
const RESET = { ok: true, open_chats_ended: 2, clock: CLOCK_START, roles_reset: 1 };

interface World {
  role: Role;
  staffing: typeof STAFFING_OFF;
  set?: () => Response | Promise<Response>;
  reset?: () => Response | Promise<Response>;
  seen: CallContext[];
}
function world(over: Partial<World> = {}): World {
  return { role: "customer", staffing: STAFFING_OFF, seen: [], ...over };
}
function transport(w: World) {
  return makeFakeTransport((ctx) => {
    w.seen.push(ctx);
    switch (ctx.op) {
      case "getSession": return jsonResponse(200, SESSION_BY_ROLE[w.role]);
      case "getStaffing": return jsonResponse(200, w.staffing);
      case "getDemoClock": return jsonResponse(200, CLOCK_START);
      case "setStaffing": return w.set ? w.set() : jsonResponse(200, TURNED_ON);
      case "resetDemo": return w.reset ? w.reset() : jsonResponse(200, RESET);
      default: return jsonResponse(404, { error: { code: "NOT_FOUND" } });
    }
  });
}
const render = (w: World) => renderWithProviders(<Scr03 />, { route: "/demo", transport: transport(w) });
const count = (w: World, op: string) => w.seen.filter((c) => c.op === op).length;
const sw = () => screen.getByRole("switch", { name: "Demo: simulate staff on shift" }) as HTMLInputElement;

afterEach(() => vi.useRealTimers());

describe("Scr03 demo guide", () => {
  it("header and static regions render with the staffing call pending", () => {
    render(world({ set: undefined, staffing: STAFFING_OFF }));
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("How this demo works");
    expect(screen.getByRole("heading", { level: 2, name: "What is real and what is simulated" })).toBeTruthy();
    expect(screen.getByRole("heading", { level: 3, name: "Real" })).toBeTruthy();
    expect(screen.getByRole("heading", { level: 3, name: "Simulated" })).toBeTruthy();
    expect(screen.getByRole("heading", { level: 2, name: "Reset the demo" })).toBeTruthy();
  });

  it("default: switch off, label Nobody online, links with hrefs and targets, four steps", async () => {
    render(world());
    await waitFor(() => expect(sw().disabled).toBe(false));
    expect(sw().checked).toBe(false);
    expect(screen.getAllByText("Nobody online").length).toBeGreaterThan(0);
    expect(screen.getByText("The chat will offer a live queue, and the staff console will show it.")).toBeTruthy();
    const link = (n: string) => screen.getByRole("link", { name: n });
    expect(link("Chat").getAttribute("href")).toBe("/");
    expect(link("Chat").getAttribute("target")).toBeNull();
    expect(link("Demo inbox").getAttribute("href")).toBe("/demo/inbox");
    expect(link("Demo inbox").getAttribute("target")).toBe("_blank");
    expect(link("Staff queue").getAttribute("href")).toBe("/staff/queue");
    expect(link("Staff queue").getAttribute("target")).toBe("_blank");
    expect(link("Monitoring").getAttribute("href")).toBe("/monitoring");
    expect(link("Evaluation").getAttribute("href")).toBe("/eval");
    const steps = screen.getByRole("heading", { name: "How to play both roles" }).closest("section")!;
    expect(within(steps).getAllByRole("listitem")).toHaveLength(4);
  });

  it("loading: Checking… and switch disabled", () => {
    render(world());
    expect(screen.getAllByText("Checking…").length).toBeGreaterThan(0);
    expect(sw().disabled).toBe(true);
  });

  it("read error: message and retry", async () => {
    const w = world();
    const t = transport(w);
    const inner = t.fetch;
    t.fetch = (ctx, u, i) => (ctx.op === "getStaffing" ? Promise.reject(new TypeError("down")) : inner(ctx, u, i));
    renderWithProviders(<Scr03 />, { route: "/demo", transport: t });
    expect(await screen.findByText("Staffing status is unavailable.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Try again" })).toBeTruthy();
    expect(sw().disabled).toBe(true);
    expect(screen.getByRole("heading", { level: 3, name: "Real" })).toBeTruthy();
  });

  it("turn on: body {mode}, switch disabled while pending, exact success line, demo status refreshed", async () => {
    let release: (r: Response) => void = () => undefined;
    const w = world({ set: () => new Promise<Response>((r) => { release = r; }) });
    render(w);
    await waitFor(() => expect(sw().disabled).toBe(false));
    const statusBefore = count(w, "getDemoClock");
    await userEvent.click(sw());
    await waitFor(() => expect(sw().disabled).toBe(true));
    expect(sw().checked).toBe(true);
    expect(w.seen.find((c) => c.op === "setStaffing")!.body).toEqual({ mode: "simulated_on_shift" });
    w.staffing = STAFFING_ON;
    await act(async () => { release(jsonResponse(200, TURNED_ON)); });
    expect(await screen.findByText("Simulated staff on shift (demo). The banner now shows on the chat and the console.")).toBeTruthy();
    expect(count(w, "getDemoClock")).toBeGreaterThan(statusBefore);
    expect(sw().checked).toBe(true);
  });

  it.each([
    [1, "Shift ended. 1 waiting customer now has the 1-business-day promise."],
    [2, "Shift ended. 2 waiting customers now have the 1-business-day promise."],
    [0, "Shift ended. Nobody is online."],
  ])("turn off with %i converted: exact line", async (n, line) => {
    const w = world({ staffing: STAFFING_ON, set: () => jsonResponse(200, { ...TURNED_OFF, converted_cases: n }) });
    render(w);
    await waitFor(() => expect(sw().checked).toBe(true));
    w.staffing = STAFFING_OFF;
    await userEvent.click(sw());
    expect(await screen.findByText(line)).toBeTruthy();
  });

  it("write error: exact line and the switch reverts", async () => {
    const w = world({ set: () => jsonResponse(503, { error: { code: "RESET_IN_PROGRESS" } }) });
    render(w);
    await waitFor(() => expect(sw().disabled).toBe(false));
    await userEvent.click(sw());
    expect(await screen.findByText("Staffing didn't change. Try again.")).toBeTruthy();
    await waitFor(() => expect(sw().checked).toBe(false));
  });

  it("stale: change elsewhere shows the line and moves the switch; an own write does not", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const w = world({ set: () => jsonResponse(200, TURNED_ON) });
    render(w);
    await waitFor(() => expect(sw().disabled).toBe(false));
    // own write: no stale line
    w.staffing = STAFFING_ON;
    fireEvent.click(sw());
    await screen.findByText(/Simulated staff on shift \(demo\)\. The banner/);
    await act(async () => { await vi.advanceTimersByTimeAsync(10100); });
    expect(screen.queryByText("Staffing changed since you opened this page.")).toBeNull();
    // changed elsewhere
    w.staffing = STAFFING_OFF;
    await act(async () => { await vi.advanceTimersByTimeAsync(10100); });
    expect(await screen.findByText("Staffing changed since you opened this page.")).toBeTruthy();
    expect(sw().checked).toBe(false);
  });

  it("reset dialog: opens with exact text, Cancel has focus, Cancel sends nothing", async () => {
    const w = world();
    render(w);
    await userEvent.click(screen.getByRole("button", { name: "Reset the demo" }));
    const dlg = await screen.findByRole("dialog", { name: "Reset the demo?" });
    expect(within(dlg).getByText("This ends every open chat, clears cases made during the demo, restores the seeded cases and sets the date back to Fri Oct 16, 2026.")).toBeTruthy();
    expect(document.activeElement).toBe(within(dlg).getByRole("button", { name: "Cancel" }));
    await userEvent.click(within(dlg).getByRole("button", { name: "Cancel" }));
    expect(count(w, "resetDemo")).toBe(0);
  });

  async function confirmReset() {
    await userEvent.click(screen.getByRole("button", { name: "Reset the demo" }));
    const dlg = await screen.findByRole("dialog", { name: "Reset the demo?" });
    await userEvent.click(within(dlg).getByRole("button", { name: "Reset the demo" }));
  }
  const base = "Demo reset. Bookings, cases and codes are back to the start, and the date is Fri Oct 16, 2026.";

  it("reset confirm: body {confirm:true}, button Resetting… and disabled, exact success line with Open chats have ended", async () => {
    let release: (r: Response) => void = () => undefined;
    const w = world({ reset: () => new Promise<Response>((r) => { release = r; }) });
    render(w);
    await confirmReset();
    expect(w.seen.find((c) => c.op === "resetDemo")!.body).toEqual({ confirm: true });
    const busy = await screen.findByRole("button", { name: "Resetting…" });
    expect((busy as HTMLButtonElement).disabled).toBe(true);
    await act(async () => { release(jsonResponse(200, RESET)); });
    expect(await screen.findByText(`${base} Open chats have ended.`)).toBeTruthy();
  });

  it("reset with no chats ended omits that sentence", async () => {
    const w = world({ reset: () => jsonResponse(200, { ...RESET, open_chats_ended: 0, roles_reset: 0 }) });
    render(w);
    await confirmReset();
    expect(await screen.findByText(base)).toBeTruthy();
  });

  it("reset returns the role to customer: getSession re-read, header shows Customer, role-reset sentence appended", async () => {
    const w = world({ role: "representative", reset: () => { w.role = "customer"; return jsonResponse(200, RESET); } });
    render(w);
    await waitFor(() => expect(screen.getAllByRole("radio").some((r) => /Riley.*current/.test(r.getAttribute("aria-label") ?? ""))).toBe(true));
    const sessionCalls = count(w, "getSession");
    await confirmReset();
    expect(await screen.findByText(`${base} Open chats have ended. The demo was reset, so you're back to the customer role. Pick a role again.`)).toBeTruthy();
    expect(count(w, "getSession")).toBeGreaterThan(sessionCalls);
    await waitFor(() => expect(screen.getAllByRole("radio").some((r) => r.getAttribute("aria-label") === `${SESSION_CUSTOMER.display_name}, current`)).toBe(true));
  });

  it("reset failure: exact line, button enabled again", async () => {
    const w = world({ reset: () => jsonResponse(500, { error: { code: "RESET_FAILED" } }) });
    render(w);
    await confirmReset();
    expect(await screen.findByText("The reset didn't finish. Nothing was half-reset; try again.")).toBeTruthy();
    expect((screen.getByRole("button", { name: "Reset the demo" }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("reset 409: disabled for retry_after_ms with the busy line", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const w = world({ reset: () => jsonResponse(409, { error: { code: "RESET_IN_PROGRESS", details: { retry_after_ms: 3000 } } }) });
    render(w);
    await waitFor(() => expect(sw().disabled).toBe(false));
    fireEvent.click(screen.getByRole("button", { name: "Reset the demo" }));
    const dlg = await screen.findByRole("dialog", { name: "Reset the demo?" });
    fireEvent.click(within(dlg).getByRole("button", { name: "Reset the demo" }));
    expect(await screen.findByText("The demo is resetting. Try again in a few seconds.")).toBeTruthy();
    expect((screen.getByRole("button", { name: "Resetting…" }) as HTMLButtonElement).disabled).toBe(true);
    await act(async () => { await vi.advanceTimersByTimeAsync(3100); });
    expect((screen.getByRole("button", { name: "Reset the demo" }) as HTMLButtonElement).disabled).toBe(false);
  });
});
