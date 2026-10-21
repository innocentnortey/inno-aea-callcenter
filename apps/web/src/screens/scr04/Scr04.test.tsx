import { describe, expect, it } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/render";
import { jsonResponse, makeFakeTransport } from "@/test/fakeTransport";
import { CLOCK_START, SESSION_BY_ROLE, SESSION_REPRESENTATIVE, STAFFING_OFF } from "@/test/fixtures";
import type { CallContext } from "@/api/transport";
import type { Role } from "@/lib/roles";
import Scr04 from "./Scr04";

// listDemoRoles ROLES example.
const ROLES_BODY = {
  roles: [
    { role: "customer", display_name: "Customer (demo)", sees: "The chat, the demo guide, the demo inbox, monitoring and evaluation" },
    { role: "representative", display_name: "Riley, demo representative", sees: "The queue, cases, live chat and the review list" },
    { role: "supervisor", display_name: "Demo supervisor", sees: "Oversight, the review list, the queue and demo controls" },
    { role: "owner", display_name: "Demo business owner", sees: "Outcomes and cases, read only" },
  ],
};

interface Opts { role?: Role; roles?: () => Response | Promise<Response>; sw?: (ctx: CallContext) => Response | Promise<Response>; seen?: CallContext[] }
function transport(o: Opts = {}) {
  return makeFakeTransport((ctx) => {
    o.seen?.push(ctx);
    switch (ctx.op) {
      case "getSession": return jsonResponse(200, SESSION_BY_ROLE[o.role ?? "customer"]);
      case "listDemoRoles": return o.roles ? o.roles() : jsonResponse(200, ROLES_BODY);
      case "switchRole": return o.sw ? o.sw(ctx) : jsonResponse(200, SESSION_REPRESENTATIVE);
      case "getStaffing": return jsonResponse(200, STAFFING_OFF);
      case "getDemoClock": return jsonResponse(200, CLOCK_START);
      default: return jsonResponse(404, { error: { code: "NOT_FOUND" } });
    }
  });
}
const list = () => within(screen.getAllByRole("list").find((l) => l.tagName === "UL")!);

describe("Scr04 role page", () => {
  it("h1, statement and foot link", async () => {
    renderWithProviders(<Scr04 />, { route: "/role", transport: transport() });
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Choose a demo role");
    expect(screen.getByText("These are demo roles, not real accounts. There is no second password. Everything here is fictional.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Back to the demo guide" }).getAttribute("href")).toBe("/demo");
    expect(screen.getAllByRole("radiogroup", { name: "Acting as" }).length).toBeGreaterThan(0);
  });

  it("four roles from listDemoRoles with display name and sees", async () => {
    renderWithProviders(<Scr04 />, { route: "/role", transport: transport() });
    expect(await screen.findByText("Outcomes and cases, read only")).toBeTruthy();
    expect(list().getAllByText(/demo/i).length).toBeGreaterThanOrEqual(4);
    expect(screen.getByText("The queue, cases, live chat and the review list")).toBeTruthy();
  });

  it("current role is not a button and says current", async () => {
    renderWithProviders(<Scr04 />, { route: "/role", transport: transport() });
    await screen.findByText("Outcomes and cases, read only");
    await waitFor(() => expect(document.querySelector("[aria-current='true']")).not.toBeNull());
    const cur = document.querySelector("[aria-current='true']") as HTMLElement;
    expect(cur.tagName).toBe("DIV");
    expect(cur.textContent).toContain("Customer (demo)");
    expect(cur.textContent).toContain("current");
    expect(list().getAllByRole("button")).toHaveLength(3);
  });

  it("clicking a role sends PUT {role}", async () => {
    const seen: CallContext[] = [];
    renderWithProviders(<Scr04 />, { route: "/role", transport: transport({ seen }) });
    await userEvent.click(await list().findByRole("button", { name: "Riley, demo representative" }));
    await waitFor(() => expect(seen.some((c) => c.op === "switchRole")).toBe(true));
    const call = seen.find((c) => c.op === "switchRole")!;
    expect(call.method).toBe("PUT");
    expect(call.body).toEqual({ role: "representative" });
  });

  it("while switching: chosen shows Switching… and all are disabled", async () => {
    renderWithProviders(<Scr04 />, { route: "/role", transport: transport({ sw: () => new Promise<Response>(() => undefined) }) });
    await userEvent.click(await list().findByRole("button", { name: "Demo supervisor" }));
    await waitFor(() => expect(list().getByText("Switching…")).toBeTruthy());
    expect(list().getAllByRole("button").every((b) => (b as HTMLButtonElement).disabled)).toBe(true);
  });

  it("switch error shows Couldn't switch role. Try again. and keeps the current role marked", async () => {
    renderWithProviders(<Scr04 />, { route: "/role", transport: transport({ sw: () => jsonResponse(503, { error: { code: "RESET_IN_PROGRESS" } }) }) });
    await userEvent.click(await list().findByRole("button", { name: "Demo supervisor" }));
    await waitFor(() => expect(screen.getAllByText("Couldn't switch role. Try again.").length).toBeGreaterThan(0));
    expect(document.querySelector("[aria-current='true']")?.textContent).toContain("Customer (demo)");
  });

  it("roles list fails: four buttons from ROLE_LABEL, no error text", async () => {
    renderWithProviders(<Scr04 />, { route: "/role", transport: transport({ roles: () => jsonResponse(500, { error: { code: "X" } }) }) });
    await waitFor(() => expect(document.querySelector("[aria-current='true']")).not.toBeNull());
    expect(list().getAllByRole("button")).toHaveLength(3);
    expect(list().getByRole("button", { name: "Demo business owner" })).toBeTruthy();
    expect(screen.queryByText(/try again|couldn't|didn't/i)).toBeNull();
  });

  it("no password field", async () => {
    const { container } = renderWithProviders(<Scr04 />, { route: "/role", transport: transport() });
    await screen.findByText("Outcomes and cases, read only");
    expect(container.querySelector("input[type=password]")).toBeNull();
  });
});
