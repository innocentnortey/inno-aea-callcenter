import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { expectNo24HourTimes } from "@/test/no24h";
import { apiErrorBody, claimedResponse, defaultCase, joinedResponse, ok, renderRoute } from "../scr06/case.fixtures";
import { caughtUpQueue, pendingBriefQueue, seededQueue, staffedQueue } from "./queue.fixtures";

type Body = Parameters<typeof ok>[0];
const queueApi = (q: () => Body) => (ctx: { op: string }) => (ctx.op === "getQueue" ? ok(q()) : undefined);
const open = () => renderRoute("/staff/queue", "representative", queueApi(seededQueue));

afterEach(() => vi.useRealTimers());

describe("SCR-5", () => {
  it("customer role renders the gate sentence and never calls getQueue", async () => {
    const { calls } = renderRoute("/staff/queue", "customer", queueApi(seededQueue));
    await screen.findByText(/You're acting as the customer/i);
    expect(calls.some((c) => c.op === "getQueue")).toBe(false);
  });
  it("default lists the four seeded rows in server order", async () => {
    open();
    await screen.findByRole("button", { name: /MHC-C-0008/ });
    const rows = screen.getAllByRole("button").filter((b) => /MHC-C-000\d/.test(b.textContent ?? ""));
    expect(rows.map((r) => /MHC-C-\d+/.exec(r.textContent!)![0])).toEqual(["MHC-C-0008", "MHC-C-0005", "MHC-C-0006", "MHC-C-0007"]);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });
  it("row accessible name for MHC-C-0008", async () => {
    open();
    expect(await screen.findByRole("button", { name: /^Gas smell reported in chat P0 · Safety .*· MHC-C-0008 · No due time: safety/ })).toBeTruthy();
  });
  it("empty state copy", async () => {
    renderRoute("/staff/queue", "representative", queueApi(caughtUpQueue));
    expect(await screen.findByText("You're all caught up.")).toBeTruthy();
    expect(screen.getByText("No case needs your action. New handoffs from the chat appear here.")).toBeTruthy();
  });
  it("loading shows five skeleton rows", () => {
    renderRoute("/staff/queue", "representative", (ctx) => (ctx.op === "getQueue" ? new Promise<Response>(() => {}) as never : undefined));
    return waitFor(() => {
      const sk = document.querySelector("[data-skeleton]");
      expect(sk?.children.length).toBe(5);
    });
  });
  it("partial shows Brief being written", async () => {
    renderRoute("/staff/queue", "representative", queueApi(pendingBriefQueue));
    expect((await screen.findAllByText("Brief being written")).length).toBeGreaterThan(0);
  });
  it("error shows retry and retry refetches", async () => {
    let n = 0;
    const { calls } = renderRoute("/staff/queue", "representative", (ctx) => {
      if (ctx.op !== "getQueue") return undefined;
      n++;
      return n === 1 ? ok(apiErrorBody("getCase", "404", "CASE_NOT_FOUND"), 500) : ok(seededQueue());
    });
    await screen.findByText("The queue didn't load. Try again.");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByRole("button", { name: /MHC-C-0008/ });
    expect(calls.filter((c) => c.op === "getQueue")).toHaveLength(2);
  });
  it("staffed queue shows the waiting row and Claim and join runs getCase, claim, join in order then navigates", async () => {
    const { calls, router } = renderRoute("/staff/queue", "representative", (ctx) => {
      switch (ctx.op) {
        case "getQueue": return ok(staffedQueue());
        case "getCase": return ok(defaultCase());
        case "applyCaseAction": return ok(claimedResponse());
        case "liveChatAction": return ok(joinedResponse());
        default: return undefined;
      }
    });
    fireEvent.click(await screen.findByRole("button", { name: "Claim and join MHC-C-0012" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/staff/cases/MHC-C-0012"));
    const order = calls.map((c) => c.op).filter((o) => ["getCase", "applyCaseAction", "liveChatAction"].includes(o));
    expect(order.slice(0, 3)).toEqual(["getCase", "applyCaseAction", "liveChatAction"]);
    expect((calls.find((c) => c.op === "applyCaseAction")!.body as { action: string; expected_version: number })).toEqual({ action: "claim", expected_version: 3 });
  });
  it("Claim and join: claim ok, join fails shows the partial sentence and stays on the queue", async () => {
    const { router } = renderRoute("/staff/queue", "representative", (ctx) => {
      switch (ctx.op) {
        case "getQueue": return ok(staffedQueue());
        case "getCase": return ok(defaultCase());
        case "applyCaseAction": return ok(claimedResponse());
        case "liveChatAction": return ok(apiErrorBody("liveChatAction", "409", "NOT_LIVE"), 409);
        default: return undefined;
      }
    });
    fireEvent.click(await screen.findByRole("button", { name: "Claim and join MHC-C-0012" }));
    await screen.findByText("You claimed the case, but joining the chat didn't go through. Open it and try Join chat.");
    expect(router.state.location.pathname).toBe("/staff/queue");
  });
  it("nobody online shows the disabled sentence", async () => {
    open();
    expect(await screen.findByText("Nobody is on shift, so there is no live queue. Turn on the simulation in the demo guide to try it.")).toBeTruthy();
  });
  it("poll finds 2 changed rows: stale line, Show them applies without moving the cursor", async () => {
    let n = 0;
    renderRoute("/staff/queue", "representative", (ctx) => {
      if (ctx.op !== "getQueue") return undefined;
      n++;
      const q = seededQueue();
      if (n > 1) { q.needs_my_action[1].owner = "Demo supervisor"; q.needs_my_action[2].owner = "Demo supervisor"; }
      return ok(q);
    });
    await screen.findByRole("button", { name: /MHC-C-0008/ });
    fireEvent.keyDown(document.body, { key: "j" });
    fireEvent.keyDown(document.body, { key: "j" });
    const selected = () => document.querySelector('[aria-current="true"]')?.textContent ?? "";
    expect(selected()).toMatch(/MHC-C-0005/);
    fireEvent(window, new Event("focus"));
    await screen.findByText("2 cases changed.", {}, { timeout: 3000 });
    fireEvent.click(screen.getByRole("button", { name: "Show them" }));
    await waitFor(() => expect(screen.queryByText("2 cases changed.")).toBeNull());
    expect(selected()).toMatch(/Refund request.*MHC-C-0005.*Demo supervisor/);
  });
  it("staffing flip applies without a stale line", async () => {
    let n = 0;
    renderRoute("/staff/queue", "representative", (ctx) => {
      if (ctx.op !== "getQueue") return undefined;
      return ok(++n === 1 ? staffedQueue() : seededQueue());
    });
    await screen.findByRole("button", { name: "Claim and join MHC-C-0012" });
    fireEvent(window, new Event("focus"));
    await screen.findByText(/Nobody is on shift/);
    expect(screen.queryByText(/cases? changed/)).toBeNull();
  });
  it("result line from router state clears after 4 s", async () => {
    const { router } = renderRoute("/staff/queue", "representative", queueApi(seededQueue));
    await screen.findByRole("button", { name: /MHC-C-0008/ });
    vi.useFakeTimers({ shouldAdvanceTime: true });
    await act(async () => { await router.navigate("/staff/queue", { state: { resultLine: "MHC-C-0007 resolved." } }); });
    expect(screen.getByText("MHC-C-0007 resolved.")).toBeTruthy();
    await act(async () => { await vi.advanceTimersByTimeAsync(4100); });
    expect(screen.queryByText("MHC-C-0007 resolved.")).toBeNull();
  });
  it("no 24-hour times", async () => {
    open();
    await screen.findByRole("button", { name: /MHC-C-0008/ });
    expectNo24HourTimes(document.body);
    expect(within(document.body).getAllByText(/^Due/).length).toBeGreaterThan(0);
  });
});
