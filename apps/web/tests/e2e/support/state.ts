// G-02: pluggable e2e state setup. One interface, two implementations chosen by E2E_TARGET=mock|real.
//
//   mock (default): enters states through the dev layer's URL parameters (?signedin ?role ?staffing ?scenario), as the
//                   specs always did. Needs Prism (:4019) and `vite --mode mock` (:5184); playwright.config.ts starts both.
//   real:           signs in through the actual login screen (SCR-12) and drives role, staffing and reset only through
//                   the product's own screens (role switch, SCR-3). No dev parameter is ever sent. A scenario that needs
//                   dev-only forcing (forced error, forced example, seeded row) is skipped with the reason.
//
// Real mode talks to whatever E2E_BASE_URL points at (default http://127.0.0.1:5184): a `npm run dev` server whose /api
// proxies to the real backend. Demo credentials: E2E_USERNAME / E2E_PASSWORD (default demo / demo).
import { expect, test, type Page } from "@playwright/test";

export type Role = "customer" | "representative" | "supervisor" | "owner";
export type Target = "mock" | "real";
export interface EnterOpts {
  /** Simulated staffing on/off before the page under test is shown. */
  staffing?: "on" | "off";
  /** A named dev-layer scenario. Real mode skips the test with a reason. */
  scenario?: string;
}
export interface ScenarioRef { id: string; route: string }

export interface E2EState {
  readonly target: Target;
  /** Sign in as `role` and land on `path`. */
  signInAs(page: Page, role: Role, path: string, opts?: EnterOpts): Promise<void>;
  /** Visit `path` with no session. */
  visitSignedOut(page: Page, path: string): Promise<void>;
  /** Load a named scenario's route in its state (mock only; real skips). */
  applyScenario(page: Page, sc: ScenarioRef, opts?: { dark?: boolean }): Promise<void>;
  /** Turn simulated staffing on or off for the current session's demo, keeping the current page. */
  setStaffing(page: Page, on: boolean): Promise<void>;
  /** Reset the demo to its seeded state. In real mode this resets the shared backend for everyone. */
  reset(page: Page): Promise<void>;
}

export const TARGET: Target = process.env.E2E_TARGET === "real" ? "real" : "mock";
export const ROLE_RADIO: Record<Role, RegExp> = {
  customer: /Customer/, representative: /Riley/, supervisor: /supervisor/i, owner: /owner/i,
};
const HOME: Record<Role, string> = { customer: "/", representative: "/staff/queue", supervisor: "/staff/oversight", owner: "/staff/owner" };

function withParams(path: string, params: Record<string, string>): string {
  const [p, q = ""] = path.split("?");
  const sp = new URLSearchParams(q);
  for (const [k, v] of Object.entries(params)) sp.set(k, v);
  return `${p}?${sp}`;
}

class MockState implements E2EState {
  readonly target = "mock" as const;
  async signInAs(page: Page, role: Role, path: string, opts: EnterOpts = {}) {
    const params: Record<string, string> = { signedin: "1", role };
    if (opts.staffing) params.staffing = opts.staffing;
    if (opts.scenario) params.scenario = opts.scenario;
    await page.goto(withParams(path, params));
  }
  async visitSignedOut(page: Page, path: string) { await page.goto(withParams(path, { signedin: "0" })); }
  async applyScenario(page: Page, sc: ScenarioRef, opts: { dark?: boolean } = {}) {
    await page.goto(withParams(sc.route, { scenario: sc.id, ...(opts.dark ? { theme: "dark" } : {}) }));
  }
  async setStaffing(page: Page, on: boolean) {
    // The dev world survives in sessionStorage across navigations, so reloading with ?staffing= keeps the sign-in.
    const u = new URL(page.url());
    u.searchParams.set("staffing", on ? "on" : "off");
    await page.goto(u.toString());
  }
  async reset(page: Page) {
    await page.context().clearCookies();
    await page.goto("/login?signedin=0");
    await page.evaluate(() => sessionStorage.clear());
  }
}

const SKIP_SCENARIO = (id: string) => `scenario ${id} needs dev-layer forcing (forced response/state); it cannot be reached through the product`;

class RealState implements E2EState {
  readonly target = "real" as const;
  private get username() { return process.env.E2E_USERNAME ?? "demo"; }
  private get password() { return process.env.E2E_PASSWORD ?? "demo"; }

  private async signIn(page: Page, returnTo: string) {
    await page.context().clearCookies();
    await page.goto(`/login?return_to=${encodeURIComponent(returnTo)}&reason=none`);
    await page.getByLabel("Username").fill(this.username);
    await page.getByLabel("Password", { exact: true }).fill(this.password);
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect(page).not.toHaveURL(/\/login/, { timeout: 15_000 });
  }
  private async toggleStaffing(page: Page, on: boolean) {
    await page.goto("/demo");
    const sw = page.getByRole("switch", { name: "Demo: simulate staff on shift" });
    await expect(sw).toBeEnabled({ timeout: 15_000 });
    if ((await sw.isChecked()) !== on) await sw.setChecked(on);
    await expect(sw).toBeChecked({ checked: on });
    await expect(sw).toBeEnabled();
  }
  async signInAs(page: Page, role: Role, path: string, opts: EnterOpts = {}) {
    if (opts.scenario) test.skip(true, SKIP_SCENARIO(opts.scenario));
    await this.signIn(page, "/");
    if (opts.staffing) await this.toggleStaffing(page, opts.staffing === "on");
    if (role !== "customer") {
      await page.goto("/");
      await page.getByRole("radiogroup", { name: "Acting as" }).first().getByRole("radio", { name: ROLE_RADIO[role] }).click();
      await expect(page).toHaveURL(new RegExp(HOME[role].replace(/\//g, "\\/")));
    }
    if (new URL(page.url()).pathname !== path.split("?")[0]) await page.goto(path);
  }
  async visitSignedOut(page: Page, path: string) {
    await page.context().clearCookies();
    await page.goto(path);
  }
  async applyScenario(_page: Page, sc: ScenarioRef) { test.skip(true, SKIP_SCENARIO(sc.id)); }
  async setStaffing(page: Page, on: boolean) {
    const back = page.url();
    await this.toggleStaffing(page, on);
    await page.goto(back);
  }
  async reset(page: Page) {
    await page.goto("/demo");
    await page.getByRole("button", { name: "Reset the demo" }).click();
    const dialog = page.getByRole("dialog", { name: "Reset the demo?" });
    await dialog.getByRole("button", { name: "Reset the demo" }).click();
    await expect(dialog).toBeHidden({ timeout: 15_000 });
  }
}

export function createState(target: Target = TARGET): E2EState {
  return target === "real" ? new RealState() : new MockState();
}
export const state: E2EState = createState();

/** True when the app's own route (ignoring host and query) is `p`. */
export const atPath = (page: Page, p: string) => new URL(page.url()).pathname === p;
