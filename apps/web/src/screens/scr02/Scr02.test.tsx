import { afterEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "@/test/render";
import { jsonResponse, makeFakeTransport } from "@/test/fakeTransport";
import { CLOCK_START, SESSION_CUSTOMER, STAFFING_OFF } from "@/test/fixtures";
import { expectNo24HourTimes } from "@/test/no24h";
import Scr02 from "./Scr02";

// listDemoInbox ONE_ACTIVE / USED_AND_EXPIRED examples (msg-1 code 482913, msg-2 code 117204).
const MSG1 = { id: "msg-1", at: "2026-10-16T14:07:00-05:00", to_masked: "···02", body: "Your Meridian code is 482913.", code: "482913", status: "active", expires_at: "2026-10-16T14:17:00-05:00" };
const MSG2 = { id: "msg-2", at: "2026-10-16T13:40:00-05:00", to_masked: "···02", body: "Your Meridian code is 117204.", code: "117204", status: "used", expires_at: "2026-10-16T13:50:00-05:00" };
const MSG3 = { ...MSG2, id: "msg-3", at: "2026-10-16T13:00:00-05:00", code: "555000", status: "expired" };
const ONE_ACTIVE = { messages: [MSG1] };
const EMPTY = { messages: [] };

function transport(inbox: () => Response, calls?: { n: number }) {
  return makeFakeTransport((ctx) => {
    switch (ctx.op) {
      case "getSession": return jsonResponse(200, SESSION_CUSTOMER);
      case "listDemoInbox": if (calls) calls.n += 1; return inbox();
      case "getStaffing": return jsonResponse(200, STAFFING_OFF);
      case "getDemoClock": return jsonResponse(200, CLOCK_START);
      default: return jsonResponse(404, { error: { code: "NOT_FOUND" } });
    }
  });
}
const ok = (b: unknown) => () => jsonResponse(200, b);
const render = (inbox: () => Response, calls?: { n: number }) => renderWithProviders(<Scr02 />, { route: "/demo/inbox", transport: transport(inbox, calls) });

afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

describe("Scr02 inbox", () => {
  it("header: h1, statement, role switch present", async () => {
    render(ok(ONE_ACTIVE));
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Simulated messages");
    expect(screen.getByText("Simulated messages. Nothing is sent to anyone. This exists only so reviewers can complete verification.")).toBeTruthy();
    expect(screen.getAllByRole("radiogroup", { name: "Acting as" }).length).toBeGreaterThan(0);
    expect(screen.getByText("Demo delivery inbox", { exact: false })).toBeTruthy();
    expect(screen.getByText("This inbox carries codes only. Follow-ups are recorded on the case, never sent.")).toBeTruthy();
  });

  it("default: newest message with masked recipient, 12-hour time, code, Active status and expiry", async () => {
    const { container } = render(ok({ messages: [MSG2, MSG1] }));
    await screen.findByText("Your Meridian code is 482913.");
    const items = screen.getAllByRole("listitem");
    expect(items[0].textContent).toContain("To ···02");
    expect(items[0].textContent).toContain("2:07 pm");
    expect(items[0].textContent).toContain("482913");
    expect(items[0].textContent).toContain("Active");
    expect(items[0].textContent).toContain("Expires 2:17 pm");
    expect(items[1].textContent).toContain("Used");
    expectNo24HourTimes(container);
  });

  it("code is read digit by digit", async () => {
    render(ok(ONE_ACTIVE));
    expect(await screen.findByText("4 8 2 9 1 3")).toBeTruthy();
  });

  it("empty: exact copy and Back to the chat", async () => {
    render(ok(EMPTY));
    expect(await screen.findByText("No codes yet.")).toBeTruthy();
    expect(screen.getByText("When the chat sends a code, it appears here. Ask the chat about your bill or book a visit to get one.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Back to the chat" }).getAttribute("href")).toBe("/");
  });

  it("loading: skeleton and header", () => {
    render(() => jsonResponse(200, ONE_ACTIVE));
    expect(screen.getByTestId("inbox-loading")).toBeTruthy();
    expect(screen.getByRole("heading", { level: 1 })).toBeTruthy();
  });

  it("error then retry", async () => {
    let fail = true;
    render(() => (fail ? jsonResponse(503, { error: { code: "RESET_IN_PROGRESS" } }) : jsonResponse(200, ONE_ACTIVE)));
    expect(await screen.findByText("The inbox didn't load. Try again.")).toBeTruthy();
    fail = false;
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("Your Meridian code is 482913.")).toBeTruthy();
  });

  it("used and expired: copy disabled, status words", async () => {
    render(ok({ messages: [MSG2, MSG3] }));
    await screen.findByText("Used");
    expect(screen.getByText("Expired")).toBeTruthy();
    for (const b of screen.getAllByRole("button", { name: "Copy code" })) expect((b as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getAllByRole("button", { name: "Copy code" })[0].getAttribute("aria-describedby")).toBeTruthy();
  });

  it("copy: writes the code, shows Copied for 2 s", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });
    render(ok(ONE_ACTIVE));
    const btn = await screen.findByRole("button", { name: "Copy code" });
    vi.useFakeTimers({ shouldAdvanceTime: true });
    await act(async () => { fireEvent.click(btn); });
    expect(writeText).toHaveBeenCalledWith("482913");
    expect(screen.getByText("Copied")).toBeTruthy();
    await act(async () => { await vi.advanceTimersByTimeAsync(2100); });
    expect(screen.queryByText("Copied")).toBeNull();
  });

  it("copy failure shows the fallback line", async () => {
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText: vi.fn().mockRejectedValue(new Error("no")) } });
    render(ok(ONE_ACTIVE));
    fireEvent.click(await screen.findByRole("button", { name: "Copy code" }));
    expect(await screen.findByText("Copy didn't work. Select the code and copy it.")).toBeTruthy();
  });

  it("polls every 5 s", async () => {
    const calls = { n: 0 };
    vi.useFakeTimers({ shouldAdvanceTime: true });
    render(ok(ONE_ACTIVE), calls);
    await screen.findByText("Your Meridian code is 482913.");
    const before = calls.n;
    await act(async () => { await vi.advanceTimersByTimeAsync(5100); });
    expect(calls.n).toBeGreaterThan(before);
  });

  it("new code is announced after the first load only", async () => {
    let step = 0;
    vi.useFakeTimers({ shouldAdvanceTime: true });
    render(() => jsonResponse(200, step === 0 ? EMPTY : ONE_ACTIVE));
    await screen.findByText("No codes yet.");
    // first load never announces
    expect(document.querySelector("[aria-live][aria-atomic]")?.textContent).toBe("");
    step = 1;
    await act(async () => { await vi.advanceTimersByTimeAsync(5100); });
    await act(async () => { await vi.advanceTimersByTimeAsync(100); });
    expect(document.querySelector("[aria-live][aria-atomic]")?.textContent).toBe("New code received");
  });

  it("back to the chat: focuses the opener when there is one", async () => {
    const focus = vi.fn();
    vi.stubGlobal("opener", { closed: false, focus });
    const { router } = render(ok(EMPTY));
    await screen.findByText("No codes yet.");
    fireEvent.click(screen.getByRole("link", { name: "Back to the chat" }));
    expect(focus).toHaveBeenCalled();
    expect(router.state.location.pathname).toBe("/demo/inbox");
  });

  it("back to the chat: navigates to / when there is no opener", async () => {
    vi.stubGlobal("opener", null);
    const { router } = render(ok(EMPTY));
    await screen.findByText("No codes yet.");
    fireEvent.click(screen.getByRole("link", { name: "Back to the chat" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
  });

  it("no sms/email wording, no 24-hour times", async () => {
    const { container } = render(ok({ messages: [MSG1, MSG2, MSG3] }));
    await screen.findByText("Expired");
    expect(container.textContent).not.toMatch(/sms|e-?mail/i);
    expectNo24HourTimes(container);
  });
});
