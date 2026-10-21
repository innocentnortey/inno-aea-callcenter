import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import type { CallContext } from "@/api/transport";
import { jsonResponse } from "@/test/fakeTransport";
import { expectNo24HourTimes } from "@/test/no24h";
import { STAFFING_ON } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";
import type { Role } from "@/lib/roles";
import { opsTransport, type OpHandler } from "../reads/test/opsTransport";
import { mockDesktop } from "../reads/test/mockDesktop";
import { specExample } from "../reads/test/specExample";
import Scr07 from "./Scr07";

const seededOk: OpHandler = () => jsonResponse(200, specExample("getOversight", "SEEDED"));
function setup(handlers: Record<string, OpHandler> = {}, role: Role = "supervisor") {
  const calls: CallContext[] = [];
  const transport = opsTransport(role, { getOversight: seededOk, ...handlers }, calls);
  const view = renderWithProviders(<Scr07 />, { route: "/staff/oversight", transport, role });
  return { ...view, calls };
}
const laneTitles = ["P0 and P1", "Overdue", "Due soon", "Unowned", "Stuck waiting"];

beforeEach(() => mockDesktop());
afterEach(() => vi.useRealTimers());

describe("Scr07", () => {
  it("customer role sees the role panel and makes no staff call", async () => {
    const { calls } = setup({}, "customer");
    await screen.findByText("You're acting as the customer. Switch to a staff role to see this.");
    expect(calls.map((c) => c.op)).not.toContain("getOversight");
  });

  it("five lanes render in the fixed order with counts in the headings", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "P0 and P1 · 1" });
    const heads = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent ?? "").filter((t) => laneTitles.some((l) => t.startsWith(l)));
    expect(heads).toEqual(["P0 and P1 · 1", "Overdue · 1", "Due soon · 0", "Unowned · 2", "Stuck waiting · 0"]);
  });

  it("seeded rows land in the spec'd lanes", async () => {
    const { container } = setup();
    await screen.findByText("P0 safety case MHC-C-0008 created at 2:16 pm, unowned. Assign it.");
    const lane = (title: string) => within(screen.getByRole("heading", { level: 2, name: new RegExp(`^${title}`) }).closest("section") as HTMLElement);
    expect(lane("P0 and P1").getByRole("button", { name: /· MHC-C-0008 ·/ })).toBeTruthy();
    expect(lane("Overdue").getByRole("button", { name: /· MHC-C-0005 ·/ })).toBeTruthy();
    expect(lane("Unowned").getByRole("button", { name: /· MHC-C-0006 ·/ })).toBeTruthy();
    expect(lane("Unowned").getByRole("button", { name: /· MHC-C-0007 ·/ })).toBeTruthy();
    expect(screen.getAllByText("Demo seed")).toHaveLength(4);
    expect(screen.getByText("Open 4 min")).toBeTruthy();
    expectNo24HourTimes(container);
  });

  it("alerts newest first", async () => {
    const body = specExample("getOversight", "AFTER_ADVANCE");
    body.alerts = [{ ...body.alerts[0]!, line: "Older line.", at: "2026-10-16T08:00:00-05:00" }, ...body.alerts];
    setup({ getOversight: () => jsonResponse(200, body) });
    await screen.findByText("Older line.");
    const items = screen.getAllByRole("listitem").filter((li) => li.closest("[aria-live=polite]"));
    expect(items[items.length - 1]!.textContent).toContain("Older line.");
    expect(items[0]!.textContent).not.toContain("Older line.");
  });

  it("empty oversight keeps all five lanes and shows the sentence", async () => {
    setup({ getOversight: () => jsonResponse(200, specExample("getOversight", "NOTHING_URGENT")) });
    await screen.findByText("Nothing urgent, unowned, due soon, overdue or stuck. Every case has an owner and is on time.");
    expect(screen.getAllByText("None")).toHaveLength(5);
  });

  it("loading shows lane titles and skeletons", async () => {
    setup({ getOversight: () => new Promise<Response>(() => undefined) });
    await screen.findByRole("heading", { level: 2, name: "Stuck waiting" });
    const heads = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(heads).toEqual(expect.arrayContaining(laneTitles));
    expect(document.querySelectorAll("[data-skeleton]").length).toBe(5);
  });

  it("load failure shows the sentence and retries", async () => {
    let n = 0;
    setup({ getOversight: () => (++n === 1 ? jsonResponse(500, { error: { code: "BOOM" } }) : jsonResponse(200, specExample("getOversight", "SEEDED"))) });
    await screen.findByText("Oversight didn't load. Try again.");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByRole("heading", { level: 2, name: "P0 and P1 · 1" });
  });

  it("controls strip shows the switch, three advance buttons and the demo time", async () => {
    setup();
    await screen.findByRole("switch");
    for (const name of ["+1 hour", "+4 hours", "Next business morning (Mon 7:00 am)"]) expect(screen.getByRole("button", { name })).toBeTruthy();
    expect((await screen.findAllByText("Fri Oct 16 · 2:20 pm")).length).toBeGreaterThan(0);
    expect(screen.getByText("To go back to Fri Oct 16, reset the demo.")).toBeTruthy();
  });

  it("advance success line", async () => {
    const { calls } = setup({ advanceDemoClock: () => jsonResponse(200, specExample("advanceDemoClock", "NEXT_MORNING")) });
    await screen.findByRole("switch");
    fireEvent.click(screen.getByRole("button", { name: "Next business morning (Mon 7:00 am)" }));
    await screen.findByText("Demo time is now Mon Oct 19 · 7:00 am. 1 case became overdue.");
    await waitFor(() => expect(calls.filter((c) => c.op === "getOversight").length).toBeGreaterThanOrEqual(2));
    expect(calls.find((c) => c.op === "advanceDemoClock")!.body).toEqual({ step: "next_business_morning" });
  });

  it("advance failure line", async () => {
    setup({ advanceDemoClock: () => { throw new Error("down"); } });
    await screen.findByRole("switch");
    fireEvent.click(screen.getByRole("button", { name: "+1 hour" }));
    await screen.findByText("The clock didn't move. Try again.");
  });

  it("controls are disabled while a save is pending", async () => {
    let release: (r: Response) => void = () => undefined;
    setup({ advanceDemoClock: () => new Promise<Response>((res) => { release = res; }) });
    await screen.findByRole("switch");
    fireEvent.click(screen.getByRole("button", { name: "+4 hours" }));
    await waitFor(() => expect((screen.getByRole("button", { name: "+1 hour" }) as HTMLButtonElement).disabled).toBe(true));
    expect((screen.getByRole("button", { name: "+4 hours" }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: "Next business morning (Mon 7:00 am)" }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("switch") as HTMLInputElement).disabled).toBe(true);
    await act(async () => { release(jsonResponse(200, specExample("advanceDemoClock", "PLUS_1H"))); });
    await waitFor(() => expect((screen.getByRole("button", { name: "+1 hour" }) as HTMLButtonElement).disabled).toBe(false));
  });

  it("shift off with a waiting customer", async () => {
    setup({
      getStaffing: () => jsonResponse(200, STAFFING_ON),
      setStaffing: () => jsonResponse(200, specExample("setStaffing", "TURNED_OFF_WITH_WAITING")),
    });
    const sw = (await screen.findByRole("switch")) as HTMLInputElement;
    await waitFor(() => expect(sw.checked).toBe(true));
    fireEvent.click(sw);
    await screen.findByText("Shift ended. 1 waiting customer now has the 1-business-day promise.");
  });

  it("the shift sentence follows the mode the server reports, not the click", async () => {
    setup({
      setStaffing: () => jsonResponse(200, specExample("setStaffing", "TURNED_OFF_WITH_WAITING")),
    });
    const sw = (await screen.findByRole("switch")) as HTMLInputElement;
    await waitFor(() => expect(sw.disabled).toBe(false));
    fireEvent.click(sw); // asks for "on", the server answers "off"
    await screen.findByText("Shift ended. 1 waiting customer now has the 1-business-day promise.");
    expect(screen.queryByText("Simulated shift is on.")).toBeNull();
  });

  it("turning the shift on reads 'Simulated shift is on.' from the reported mode", async () => {
    setup({
      setStaffing: () => jsonResponse(200, specExample("setStaffing", "TURNED_ON")),
    });
    const sw = (await screen.findByRole("switch")) as HTMLInputElement;
    await waitFor(() => expect(sw.disabled).toBe(false));
    fireEvent.click(sw);
    await screen.findByText("Simulated shift is on.");
  });

  it("live queue line only while staffed", async () => {
    const body = specExample("getOversight", "SEEDED");
    body.live_queue_length = 2;
    const on = setup({ getOversight: () => jsonResponse(200, body), getStaffing: () => jsonResponse(200, STAFFING_ON) });
    await screen.findByText("2 customers waiting in chat.");
    on.unmount();
    setup({ getOversight: () => jsonResponse(200, body) });
    await screen.findByRole("heading", { level: 2, name: "P0 and P1 · 1" });
    expect(screen.queryByText("2 customers waiting in chat.")).toBeNull();
  });

  it("a changed read shows Lanes updated", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let n = 0;
    setup({ getOversight: () => jsonResponse(200, specExample("getOversight", ++n === 1 ? "SEEDED" : "AFTER_ADVANCE")) });
    await screen.findByRole("heading", { level: 2, name: "P0 and P1 · 1" });
    await act(async () => { await vi.advanceTimersByTimeAsync(10_100); });
    await screen.findByText("Lanes updated.");
    await act(async () => { await vi.advanceTimersByTimeAsync(10_100); });
    await waitFor(() => expect(screen.queryByText("Lanes updated.")).toBeNull());
  });

  it("review list link shows the new-flag count", async () => {
    setup();
    const link = await screen.findByRole("link", { name: "Review list · 3 new flags" });
    expect(link.getAttribute("href")).toBe("/staff/flags");
  });

  it("row opens the case", async () => {
    const { router } = setup();
    fireEvent.click(await screen.findByRole("button", { name: /· MHC-C-0008 ·/ }));
    expect(router.state.location.pathname).toBe("/staff/cases/MHC-C-0008");
  });

  it("no 24-hour times", async () => {
    const { container } = setup();
    await screen.findByRole("heading", { level: 2, name: "P0 and P1 · 1" });
    expectNo24HourTimes(container);
  });
});
