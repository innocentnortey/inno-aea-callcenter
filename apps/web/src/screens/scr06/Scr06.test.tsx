import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { expectNo24HourTimes } from "@/test/no24h";
import { seededQueue } from "../scr05/queue.fixtures";
import {
  apiErrorBody, callReachedResponse, claimedResponse, defaultCase, joinedResponse, liveJoinedCase, ok, renderRoute, resolvedResponse,
} from "./case.fixtures";
import type { Role } from "@/lib/roles";
import type { CallContext } from "@/api/transport";

type H = (ctx: CallContext) => Response | undefined;
const base = (extra?: H): H => (ctx) => extra?.(ctx) ?? (ctx.op === "getCase" ? ok(defaultCase()) : ctx.op === "getQueue" ? ok(seededQueue()) : undefined);
const open = (extra?: H, role: Role = "representative", route = "/staff/cases/MHC-C-0007") => renderRoute(route, role, base(extra));
const h1s = () => screen.queryAllByRole("heading", { level: 1 });

describe("SCR-6", () => {
  it("keeps exactly one h1 when the role is not allowed (customer)", async () => {
    open(undefined, "customer");
    await screen.findByText(/You're acting as the customer/i);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });
  it("customer role: gate sentence, no getCase", async () => {
    const { calls } = open(undefined, "customer");
    await screen.findByText(/You're acting as the customer/i);
    expect(calls.some((c) => c.op === "getCase")).toBe(false);
  });
  it("owner role: read-only line, no getQueue call, no buttons", async () => {
    const { calls } = open((ctx) => ctx.op === "getCase" ? ok({ ...defaultCase(), case: { ...defaultCase().case, allowed_actions: [] } }) : undefined, "owner");
    await screen.findByText("Read-only for the business owner role");
    expect(calls.some((c) => c.op === "getQueue")).toBe(false);
    expect(screen.queryByRole("button", { name: "Claim" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Log a call" })).toBeNull();
  });
  it("default renders header, promise, eight sections, Sources (5)", async () => {
    open();
    expect(await screen.findByRole("heading", { level: 1, name: "Billing dispute · P3 Standard" })).toBeTruthy();
    expect(screen.getByText("Promise shown to the customer")).toBeTruthy();
    expect(screen.getAllByRole("heading", { level: 3 }).filter((h) => /^\D/.test(h.textContent ?? "")).length).toBeGreaterThanOrEqual(8);
    expect(screen.getByRole("tab", { name: "Sources (5)" })).toBeTruthy();
    expect(screen.getAllByText("Demo seed").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Claim" })).toBeTruthy();
    expect(screen.getByText("Due Mon Oct 19 · 7:00 pm")).toBeTruthy();
  });
  it("one h1 in loading, error and loaded states", async () => {
    const { unmount } = renderRoute("/staff/cases/MHC-C-0007", "representative", (ctx) => (ctx.op === "getCase" ? new Promise<Response>(() => {}) as never : undefined));
    await screen.findByRole("heading", { level: 1, name: "Case MHC-C-0007", hidden: true });
    expect(h1s().length + document.querySelectorAll("h1").length).toBeGreaterThan(0);
    expect(document.querySelectorAll("h1")).toHaveLength(1);
    unmount();
    const nf = open((ctx) => (ctx.op === "getCase" ? ok(apiErrorBody("getCase", "404", "CASE_NOT_FOUND"), 404) : undefined));
    await screen.findByRole("heading", { level: 1, name: "Case not found" });
    expect(document.querySelectorAll("h1")).toHaveLength(1);
    nf.unmount();
    open();
    await screen.findByRole("heading", { level: 1, name: /Billing dispute/ });
    expect(document.querySelectorAll("h1")).toHaveLength(1);
  });
  it("loading shows the final layout skeletons", async () => {
    renderRoute("/staff/cases/MHC-C-0007", "representative", (ctx) => (ctx.op === "getCase" ? new Promise<Response>(() => {}) as never : undefined));
    await waitFor(() => expect(document.querySelectorAll("[data-skeleton]").length).toBeGreaterThanOrEqual(9));
  });
  it("Claim posts {action:'claim', expected_version:3} then shows the result line and focuses it", async () => {
    const { calls } = open((ctx) => (ctx.op === "applyCaseAction" ? ok(claimedResponse()) : undefined));
    fireEvent.click(await screen.findByRole("button", { name: "Claim" }));
    const line = await screen.findByText("Claimed · Riley (demo)");
    expect(calls.find((c) => c.op === "applyCaseAction")!.body).toEqual({ action: "claim", expected_version: 3 });
    await waitFor(() => expect(document.activeElement?.id).toBe("case-result"));
    expect(line).toBeTruthy();
    expect(screen.getByRole("button", { name: "Log a call" }).getAttribute("aria-disabled")).toBeNull();
    expect(within(screen.getByRole("list", { name: "Case state" })).getByText("Claimed").closest("li")!.getAttribute("aria-current")).toBe("step");
  });
  it("VERSION_CONFLICT shows the sentence and Reload refetches", async () => {
    const { calls } = open((ctx) => (ctx.op === "applyCaseAction" ? ok(apiErrorBody("applyCaseAction", "409", "VERSION_CONFLICT"), 409) : undefined));
    fireEvent.click(await screen.findByRole("button", { name: "Claim" }));
    await screen.findByText("This case changed since you opened it (Demo supervisor at 2:31 pm). Reload to see it.");
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await waitFor(() => expect(calls.filter((c) => c.op === "getCase")).toHaveLength(2));
  });
  it("REASON_REQUIRED shows the release sentence", async () => {
    open((ctx) => {
      if (ctx.op === "getCase") return ok({ ...defaultCase(), case: { ...defaultCase().case, lifecycle: "claimed", allowed_actions: ["start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag"] } });
      if (ctx.op === "applyCaseAction") return ok(apiErrorBody("applyCaseAction", "422", "REASON_REQUIRED"), 422);
      return undefined;
    });
    await userEvent.click(await screen.findByRole("button", { name: "More actions" }));
    await userEvent.click(await screen.findByRole("menuitem", { name: "Release" }));
    fireEvent.click(await screen.findByRole("button", { name: "Release" }));
    await screen.findByText("Add a reason to release this case.");
  });
  it("case not found panel", async () => {
    open((ctx) => (ctx.op === "getCase" ? ok(apiErrorBody("getCase", "404", "CASE_NOT_FOUND"), 404) : undefined), "representative", "/staff/cases/MHC-C-0099");
    await screen.findByText("Case not found");
    expect(screen.getByText(/It may have been cleared by a demo reset\./)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Back to the queue" })).toBeTruthy();
  });
  it("a streamed customer message appears and is announced", async () => {
    const { streams } = open((ctx) => (ctx.op === "getCase" ? ok(liveJoinedCase()) : undefined));
    await screen.findByText("You are replying as Riley (demo representative). The assistant is paused.");
    await waitFor(() => expect(streams.length).toBeGreaterThan(0));
    act(() => streams[0].onEvent({ event_id: 31, type: "customer_message", at: "2026-10-16T14:23:10-05:00", message: { message_id: "m-90", speaker: { kind: "customer", display_name: "You" }, at: "2026-10-16T14:23:10-05:00", text: "Thanks, that helps." } }, 31, "customer_message"));
    expect(await screen.findByText("Thanks, that helps.")).toBeTruthy();
    await waitFor(() => expect(document.querySelector('[aria-live="polite"].sr-only')?.textContent).toBe("Customer: Thanks, that helps."));
  });
  it("a streamed demo_reset shows the reset sentence", async () => {
    const { streams } = open((ctx) => (ctx.op === "getCase" ? ok(liveJoinedCase()) : undefined));
    await screen.findByText(/You are replying as Riley/);
    await waitFor(() => expect(streams.length).toBeGreaterThan(0));
    act(() => streams[0].onEvent({ event_id: 34, type: "demo_reset", at: "2026-10-16T14:25:00-05:00", line: "This chat ended because the demo was reset." }, 34, "demo_reset"));
    expect((await screen.findAllByText("This chat ended because the demo was reset.")).length).toBeGreaterThan(0);
  });
  it("source chip switches to Sources and highlights the card", async () => {
    open();
    await screen.findByRole("heading", { level: 1, name: /Billing dispute/ });
    await userEvent.click(screen.getByRole("tab", { name: "Conversation" }));
    fireEvent.click(screen.getAllByRole("button", { name: /Invoice INV-204411/ })[0]);
    await waitFor(() => expect(screen.getByRole("tab", { name: /Sources/ }).getAttribute("data-state")).toBe("active"));
    await waitFor(() => expect(document.getElementById("src-src-invoice")?.className).toContain("bg-surface-selected"));
  });
  it("claim and join runs claim, join, then getCase", async () => {
    const queued = defaultCase();
    queued.case.lifecycle = "live_queued";
    queued.case.allowed_actions = ["claim_and_join", "claim", "flag"];
    queued.live = { state: "queued", since: "2026-10-16T14:14:00-05:00", controller: "ai" };
    let joined = false;
    const { calls } = open((ctx) => {
      if (ctx.op === "getCase") return ok(joined ? liveJoinedCase() : queued);
      if (ctx.op === "applyCaseAction") return ok(claimedResponse());
      if (ctx.op === "liveChatAction") { joined = true; return ok(joinedResponse()); }
      return undefined;
    });
    fireEvent.click(await screen.findByRole("button", { name: "Claim and join" }));
    await screen.findByText("You are replying as Riley (demo representative). The assistant is paused.");
    const order = calls.map((c) => c.op).filter((o) => ["getCase", "applyCaseAction", "liveChatAction"].includes(o));
    expect(order).toEqual(["getCase", "applyCaseAction", "liveChatAction", "getCase"]);
  });
  it("claim ok then join fails: says so, and the next action uses the fresh version", async () => {
    const queued = defaultCase();
    queued.case.lifecycle = "live_queued";
    queued.case.allowed_actions = ["claim_and_join", "claim", "flag"];
    queued.live = { state: "queued", since: "2026-10-16T14:14:00-05:00", controller: "ai" };
    let getCases = 0;
    const { calls } = open((ctx) => {
      if (ctx.op === "getCase") return ++getCases === 1 ? ok(queued) : (new Promise<Response>(() => {}) as never); // the refresh never lands
      if (ctx.op === "applyCaseAction") return ok(claimedResponse());
      if (ctx.op === "liveChatAction") return ok(apiErrorBody("liveChatAction", "409", "NOT_LIVE"), 409);
      return undefined;
    });
    fireEvent.click(await screen.findByRole("button", { name: "Claim and join" }));
    await screen.findByText("You claimed this case, but joining the chat didn't go through. Try Join chat.");
    await userEvent.click(await screen.findByRole("button", { name: "More actions" }));
    await userEvent.click(await screen.findByRole("menuitem", { name: "Pick it back up" }));
    await waitFor(() => expect(calls.filter((c) => c.op === "applyCaseAction")).toHaveLength(2));
    expect(calls.filter((c) => c.op === "applyCaseAction")[1].body).toEqual({ action: "start", expected_version: 4 });
  });
  it("resolve navigates to the queue with the result line in router state", async () => {
    const claimed = defaultCase();
    claimed.case.lifecycle = "claimed";
    claimed.case.allowed_actions = ["start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag"];
    const { router } = open((ctx) => (ctx.op === "getCase" ? ok(claimed) : ctx.op === "applyCaseAction" ? ok(resolvedResponse()) : undefined));
    fireEvent.click(await screen.findByRole("button", { name: "Resolve" }));
    fireEvent.change(await screen.findByLabelText("Outcome"), { target: { value: "Credit recorded" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Resolve" }).at(-1)!);
    await waitFor(() => expect(router.state.location.pathname).toBe("/staff/queue"));
    expect(router.state.location.state).toEqual({ resultLine: "MHC-C-0007 resolved." });
  });
  it("log a call shows the activity with the demo label", async () => {
    const claimed = defaultCase();
    claimed.case.lifecycle = "claimed";
    claimed.case.allowed_actions = ["start", "log_call", "log_email", "wait", "resolve", "close_unresolved", "release", "flag"];
    open((ctx) => (ctx.op === "getCase" ? ok(claimed) : ctx.op === "recordContactActivity" ? ok(callReachedResponse(), 201) : undefined));
    fireEvent.click(await screen.findByRole("button", { name: "Log a call" }));
    fireEvent.click(screen.getByLabelText("Reached the customer"));
    fireEvent.click(screen.getByRole("button", { name: "Record" }));
    await screen.findByText("Called · Reached the customer · Demo: recorded, not sent");
  });
  it("opens the conversation tab with the message in focus from the query string", async () => {
    open(undefined, "representative", "/staff/cases/MHC-C-0007?tab=conversation&message=m-2");
    await screen.findByRole("heading", { level: 1, name: /Billing dispute/ });
    await waitFor(() => expect(screen.getByRole("tab", { name: "Conversation" }).getAttribute("data-state")).toBe("active"));
    expect(document.getElementById("msg-m-2")?.className).toContain("bg-surface-selected");
  });
  it("the highlighted message is focused without scrolling the page", async () => {
    open(undefined, "representative", "/staff/cases/MHC-C-0007?tab=conversation&message=m-2");
    await screen.findByRole("heading", { level: 1, name: /Billing dispute/ });
    await waitFor(() => expect(document.activeElement?.id).toBe("msg-m-2"));
  });
  it("a case update after a message link does not pull the tab back to Conversation", async () => {
    open((ctx) => (ctx.op === "applyCaseAction" ? ok(claimedResponse()) : undefined), "representative", "/staff/cases/MHC-C-0007?message=m-2");
    await screen.findByRole("heading", { level: 1, name: /Billing dispute/ });
    await waitFor(() => expect(screen.getByRole("tab", { name: "Conversation" }).getAttribute("data-state")).toBe("active"));
    await userEvent.click(screen.getByRole("tab", { name: /Sources/ }));
    expect(screen.getByRole("tab", { name: /Sources/ }).getAttribute("data-state")).toBe("active");
    fireEvent.click(screen.getByRole("button", { name: "Claim" }));
    await screen.findByText("Claimed · Riley (demo)");
    expect(screen.getByRole("tab", { name: /Sources/ }).getAttribute("data-state")).toBe("active");
  });
  it("no 24-hour times", async () => {
    open();
    await screen.findByRole("heading", { level: 1, name: /Billing dispute/ });
    expectNo24HourTimes(document.body);
  });
});
