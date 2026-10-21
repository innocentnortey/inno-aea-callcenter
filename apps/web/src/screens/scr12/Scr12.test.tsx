import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/render";
import { jsonResponse, makeFakeTransport } from "@/test/fakeTransport";
import { CLOCK_START, SESSION_CUSTOMER, STAFFING_OFF } from "@/test/fixtures";
import type { CallContext } from "@/api/transport";
import Scr12 from "./Scr12";

// login LOGGED_IN example body (placeholders only; no real credentials exist in the repo).
const LOGGED_IN = { session: SESSION_CUSTOMER, landing: "/" };
const REFUSED = "That username or password didn't work. Check the README and try again.";

interface Opts { signedIn?: boolean; login?: (ctx: CallContext) => Response | Promise<Response>; seen?: CallContext[] }
function transport(o: Opts = {}) {
  return makeFakeTransport((ctx) => {
    o.seen?.push(ctx);
    switch (ctx.op) {
      case "getSession": return o.signedIn ? jsonResponse(200, SESSION_CUSTOMER) : jsonResponse(401, { error: { code: "UNAUTHENTICATED", details: { reason: "none" } } });
      case "login": return o.login ? o.login(ctx) : jsonResponse(200, LOGGED_IN);
      case "logout": return jsonResponse(204);
      case "getStaffing": return jsonResponse(200, STAFFING_OFF);
      case "getDemoClock": return jsonResponse(200, CLOCK_START);
      default: return jsonResponse(404, { error: { code: "NOT_FOUND" } });
    }
  });
}
const fail = (status: number, code: string) => () => jsonResponse(status, { error: { code } });

async function fill(user = "<demo-username>", pass = "<demo-password>") {
  await userEvent.type(screen.getByLabelText("Username"), user);
  await userEvent.type(screen.getByLabelText("Password"), pass);
}

describe("Scr12 login", () => {
  it("default: h1, statement, hints, Show password, foot, no role switch, Username focused, Sign in disabled", async () => {
    renderWithProviders(<Scr12 />, { route: "/login", transport: transport() });
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Demo access");
    expect(screen.getByText("This is a demonstration of Meridian's assistant. These are not Meridian accounts, and everything here is fictional.")).toBeTruthy();
    expect(screen.getAllByText("From the README")).toHaveLength(2);
    expect(screen.getByLabelText("Show password")).toBeTruthy();
    expect(screen.getByText("The username and password are in the README that came with the submission.")).toBeTruthy();
    expect(screen.queryByRole("radiogroup")).toBeNull();
    await waitFor(() => expect(document.activeElement).toBe(screen.getByLabelText("Username")));
    expect((screen.getByRole("button", { name: "Sign in" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.queryByText(/forgot|create account|need help|staff login/i)).toBeNull();
  });

  it("Show password switches the field type", async () => {
    renderWithProviders(<Scr12 />, { route: "/login", transport: transport() });
    expect(screen.getByLabelText("Password").getAttribute("type")).toBe("password");
    await userEvent.click(screen.getByLabelText("Show password"));
    expect(screen.getByLabelText("Password").getAttribute("type")).toBe("text");
  });

  it("Sign in enables only when both fields are filled", async () => {
    renderWithProviders(<Scr12 />, { route: "/login", transport: transport() });
    const btn = screen.getByRole("button", { name: "Sign in" }) as HTMLButtonElement;
    await userEvent.type(screen.getByLabelText("Username"), "<demo-username>");
    expect(btn.disabled).toBe(true);
    await userEvent.type(screen.getByLabelText("Password"), "x");
    expect(btn.disabled).toBe(false);
  });

  it("Enter submits the body {username,password} and nothing goes to the URL", async () => {
    const seen: CallContext[] = [];
    const { router } = renderWithProviders(<Scr12 />, { route: "/login", transport: transport({ seen }) });
    await fill();
    await userEvent.type(screen.getByLabelText("Password"), "{Enter}");
    await waitFor(() => expect(seen.some((c) => c.op === "login")).toBe(true));
    expect(seen.find((c) => c.op === "login")!.body).toEqual({ username: "<demo-username>", password: "<demo-password>" });
    expect(router.state.location.search).not.toContain("demo-password");
  });

  it("in flight: Signing in…, fields read-only", async () => {
    renderWithProviders(<Scr12 />, { route: "/login", transport: transport({ login: () => new Promise<Response>(() => undefined) }) });
    await fill();
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    const btn = await screen.findByRole("button", { name: "Signing in…" });
    expect((btn as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByLabelText("Username") as HTMLInputElement).readOnly).toBe(true);
    expect((screen.getByLabelText("Password") as HTMLInputElement).readOnly).toBe(true);
  });

  it("LOGIN_FAILED: exact line, password cleared, username kept, Password focused, both fields aria-invalid and described by the message", async () => {
    renderWithProviders(<Scr12 />, { route: "/login", transport: transport({ login: fail(401, "LOGIN_FAILED") }) });
    await fill();
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    const msg = await screen.findByText(REFUSED);
    expect(msg.getAttribute("aria-live")).toBe("polite");
    const u = screen.getByLabelText("Username") as HTMLInputElement;
    const p = screen.getByLabelText("Password") as HTMLInputElement;
    expect(u.value).toBe("<demo-username>");
    expect(p.value).toBe("");
    expect(document.activeElement).toBe(p);
    for (const el of [u, p]) {
      expect(el.getAttribute("aria-invalid")).toBe("true");
      expect(el.getAttribute("aria-describedby")).toContain("login-message");
    }
  });

  it("LOGIN_RATE_LIMITED gives the identical sentence and handling", async () => {
    renderWithProviders(<Scr12 />, { route: "/login", transport: transport({ login: fail(429, "LOGIN_RATE_LIMITED") }) });
    await fill();
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText(REFUSED)).toBeTruthy();
    expect((screen.getByLabelText("Password") as HTMLInputElement).value).toBe("");
    expect(screen.getByLabelText("Username").getAttribute("aria-invalid")).toBe("true");
  });

  it("network failure: Couldn't reach the demo. Try again., fields kept", async () => {
    const t = transport();
    const inner = t.fetch;
    t.fetch = (ctx, url, init) => (ctx.op === "login" ? Promise.reject(new TypeError("down")) : inner(ctx, url, init));
    renderWithProviders(<Scr12 />, { route: "/login", transport: t });
    await fill();
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("Couldn't reach the demo. Try again.")).toBeTruthy();
    expect((screen.getByLabelText("Password") as HTMLInputElement).value).toBe("<demo-password>");
    expect(screen.getByLabelText("Username").getAttribute("aria-invalid")).toBeNull();
  });

  it("success: setSession and navigate to return_to", async () => {
    const { router } = renderWithProviders(<Scr12 />, { route: "/login?return_to=%2Fstaff%2Fqueue", transport: transport() });
    await fill();
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/staff/queue"));
  });

  it("success without return_to goes to /", async () => {
    const { router } = renderWithProviders(<Scr12 />, { route: "/login", transport: transport() });
    await fill();
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
  });

  it("unsafe return_to goes to /", async () => {
    const { router } = renderWithProviders(<Scr12 />, { route: "/login?return_to=%2F%2Fevil.com", transport: transport() });
    await fill();
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
  });

  it("reason=expired shows the ended line; reason=none does not", async () => {
    const a = renderWithProviders(<Scr12 />, { route: "/login?reason=expired", transport: transport() });
    expect(screen.getByText("Your demo session ended, so please sign in again.")).toBeTruthy();
    a.unmount();
    renderWithProviders(<Scr12 />, { route: "/login?reason=none", transport: transport() });
    expect(screen.queryByText("Your demo session ended, so please sign in again.")).toBeNull();
  });

  it("already signed in (getSession 200): sentence, Continue and Sign out, form hidden", async () => {
    renderWithProviders(<Scr12 />, { route: "/login", transport: transport({ signedIn: true }) });
    expect(await screen.findByText("You're already signed in. Continue to the demo, or sign out.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Continue" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Sign out" })).toBeTruthy();
    expect(screen.queryByLabelText("Username")).toBeNull();
  });

  it("Continue goes to return_to or the role home", async () => {
    const a = renderWithProviders(<Scr12 />, { route: "/login?return_to=%2Fdemo", transport: transport({ signedIn: true }) });
    await userEvent.click(await screen.findByRole("button", { name: "Continue" }));
    await waitFor(() => expect(a.router.state.location.pathname).toBe("/demo"));
    a.unmount();
    const b = renderWithProviders(<Scr12 />, { route: "/login", transport: transport({ signedIn: true }) });
    await userEvent.click(await screen.findByRole("button", { name: "Continue" }));
    await waitFor(() => expect(b.router.state.location.pathname).toBe("/"));
  });

  it("Sign out calls logout", async () => {
    const seen: CallContext[] = [];
    renderWithProviders(<Scr12 />, { route: "/login", transport: transport({ signedIn: true, seen }) });
    await userEvent.click(await screen.findByRole("button", { name: "Sign out" }));
    await waitFor(() => expect(seen.some((c) => c.op === "logout")).toBe(true));
  });

  it("no flash of the already-signed-in panel after a successful login", async () => {
    renderWithProviders(<Scr12 />, { route: "/login", transport: transport() });
    let flashed = false;
    const obs = new MutationObserver(() => { if (screen.queryByText(/already signed in/)) flashed = true; });
    obs.observe(document.body, { childList: true, subtree: true });
    await fill();
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(screen.queryByRole("button", { name: /Sign in|Signing in/ })).not.toBeNull());
    await new Promise((r) => setTimeout(r, 30));
    obs.disconnect();
    expect(flashed).toBe(false);
  });
});
