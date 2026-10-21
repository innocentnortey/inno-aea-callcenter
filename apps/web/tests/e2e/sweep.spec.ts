// Browser QA sweep: every registered dev scenario x (light, both viewports) + (dark, desktop only), plus 4 flow tests.
// The scenario list comes from tests/e2e/.gen/scenarios.json, written by `npx vite-node tests/e2e/list-scenarios.ts`
// (it is regenerated automatically below if missing). Optional env SWEEP_GREP limits ids by regex.
// Per-scenario results are appended to tests/e2e/.gen/results-<project>.jsonl for the report table.
import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { appendFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { execSync } from "node:child_process";
import path from "node:path";
import { atPath, state } from "./support/state";
import { fileURLToPath } from "node:url";
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const GEN = path.join(__dirname, ".gen");
const JSON_PATH = path.join(GEN, "scenarios.json");
if (!existsSync(JSON_PATH)) execSync("npx vite-node tests/e2e/list-scenarios.ts", { cwd: path.join(__dirname, "../.."), stdio: "ignore" });
type Sc = { id: string; screen: string; route: string; state: string; hang: boolean; notes: string };
const ALL: Sc[] = JSON.parse(readFileSync(JSON_PATH, "utf8"));
const FILTER = process.env.SWEEP_GREP ? new RegExp(process.env.SWEEP_GREP) : null;
const SHOTS = path.join(__dirname, "../../../../docs/ux/04-prototype/screenshots");
mkdirSync(SHOTS, { recursive: true });
mkdirSync(GEN, { recursive: true });

// Scenarios skipped because the state cannot be judged from a URL load alone. Everything timed is still loaded
// (the initial state is asserted); only the later state is not waited for.
const SKIP: Record<string, string> = {};

// Expected browser-side network noise: Chrome logs "Failed to load resource ... 4xx/5xx" for every forced error
// response. Allowed only for scenarios whose matrix state is not default/success/empty/loading (error, stale,
// disabled, partial), because those are the ones that force 4xx/5xx examples.
const NETWORK_LINE = /^Failed to load resource: the server responded with a status of (4\d\d|5\d\d)\b/;
const NETWORK_OK_STATES = new Set(["error", "stale", "disabled", "partial"]);

// One representative scenario per screen (12), screenshots in light, desktop and phone.
const SHOT_IDS = new Set([
  "scr01-core.default", "scr02.default", "scr03.default", "scr04.default", "scr05.default", "scr06.default",
  "scr07.default", "scr08.default", "scr09.default", "scr10.default", "scr11.default", "scr12.default",
]);

function watch(page: Page, sc: Sc) {
  const problems: string[] = [];
  const allowed: string[] = [];
  page.on("response", (r) => { if (r.status() >= 400) allowed.push(`${r.status()} ${r.request().method()} ${new URL(r.url()).pathname}`); });
  page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
  page.on("console", (m) => {
    const t = m.text();
    if (t.includes("[contract drift]")) problems.push("drift: " + t);
    else if (m.type() === "error") {
      // SCR-12 (sign-in) probes GET /api/session while signed out; the 401 is the designed answer, not a defect.
      if (sc.screen === "SCR-12" && /status of 401/.test(t)) allowed.push("login 401");
      else if (NETWORK_LINE.test(t) && NETWORK_OK_STATES.has(sc.state)) allowed.push(t);
      else problems.push("console.error: " + t + (m.location().url ? " @ " + m.location().url : ""));
    }
  });
  return { problems, allowed };
}

async function settle(page: Page) {
  await page.waitForLoadState("load");
  await page.locator("h1").first().waitFor({ state: "attached", timeout: 8000 }).catch(() => undefined);
  await page.waitForLoadState("networkidle", { timeout: 5000 }).catch(() => undefined);
  await page.waitForTimeout(500);
}

const list = ALL.filter((s) => !FILTER || FILTER.test(s.id));
for (const sc of list) {
  for (const theme of ["light", "dark"] as const) {
    test(`sweep ${sc.id} [${theme}]`, async ({ page }, info) => {
      test.skip(theme === "dark" && info.project.name !== "chrome-desktop", "dark runs on desktop only");
      test.skip(sc.id in SKIP, SKIP[sc.id] ?? "");
      const { problems, allowed } = watch(page, sc);
      const fails: string[] = [];
      const record = () => appendFileSync(path.join(GEN, `results-${info.project.name}.jsonl`), JSON.stringify({ id: sc.id, theme, fails, problems, http: allowed }) + "\n");
      await state.applyScenario(page, sc, { dark: theme === "dark" });
      await settle(page);
      if (theme === "dark") expect(await page.locator("html").getAttribute("data-theme")).toBe("dark");
      const h1 = await page.locator("h1").count();
      if (h1 !== 1) fails.push(`h1 count ${h1}`);
      const overflow = await page.evaluate(() => ({ s: document.documentElement.scrollWidth, c: document.documentElement.clientWidth }));
      if (overflow.s > overflow.c) fails.push(`horizontal scroll ${overflow.s} > ${overflow.c}`);
      const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).exclude("#mhc-dev-panel-root").analyze();
      for (const v of axe.violations) fails.push(`axe ${v.id} (${v.nodes.length}): ${v.nodes[0]?.target.join(" ")} :: ${v.help}`);
      if (theme === "light" && SHOT_IDS.has(sc.id)) {
        await page.screenshot({ path: path.join(SHOTS, `${sc.id}--${info.project.name === "chrome-phone" ? "phone" : "desktop"}--light.png`), fullPage: false });
      }
      fails.push(...problems);
      record();
      expect(fails).toEqual([]);
    });
  }
}

// ---- interaction flows against the real mock ----
// In flows, 4xx responses that the app itself triggers on a fresh session (404 "no chat yet", 401 before login)
// are expected; they are listed as annotations (visible in the report) instead of failing. Other errors still fail.
function watchFlow(page: Page, info: { annotations: { type: string; description?: string }[] }) {
  const problems: string[] = [];
  page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
  page.on("console", (m) => {
    const t = m.text();
    if (t.includes("[contract drift]")) problems.push("drift: " + t);
    else if (m.type() === "error" && !NETWORK_LINE.test(t)) problems.push("console.error: " + t);
  });
  page.on("response", (r) => { if (r.status() >= 400 && r.url().includes("/api/")) info.annotations.push({ type: "http", description: `${r.status()} ${r.request().method()} ${new URL(r.url()).pathname}` }); });
  return problems;
}
const radios = (page: Page) => page.getByRole("radiogroup", { name: "Acting as" }).first();

test("flow: customer sends a chat message and sees a reply", async ({ page }, info) => {
  const problems = watchFlow(page, info);
  await state.signInAs(page, "customer", "/");
  const box = page.getByRole("textbox", { name: "Message" });
  await expect(box).toBeVisible({ timeout: 10_000 });
  // Finding F-3: on the 390 px phone, pressing Enter in the Message box does not send (Send button does); the flow
  // therefore clicks Send, which works at both viewports.
  await box.fill("My AC is making a rattling noise");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(box).toHaveValue("");
  await expect(page.getByText("My AC is making a rattling noise")).toBeVisible();
  if (state.target === "mock") {
    // The mock's scripted reply to this turn (the turn director picks the fee example).
    await expect(page.getByText(/after-hours dispatch fee is \$149/i)).toBeVisible({ timeout: 15_000 });
  } else {
    // Real backend (G-12): the scripted model's wording is not ours to assert; a reply entry must follow the customer's.
    await expect(page.getByRole("log", { name: "Conversation" }).locator("[data-entry]")).toHaveCount(2, { timeout: 30_000 });
  }
  expect(problems).toEqual([]);
});

test("flow: representative claims a case from the queue and lands on the case view", async ({ page }, info) => {
  const problems = watchFlow(page, info);
  await state.signInAs(page, "representative", "/staff/queue", { staffing: "on", scenario: "scr05.live-queued" });
  const claim = page.getByRole("button", { name: /^Claim and join MHC-C-/ }).first();
  await expect(claim).toBeVisible({ timeout: 10_000 });
  await claim.click();
  await expect(page).toHaveURL(/\/staff\/cases\/MHC-C-\d+/);
  await expect(page.locator("h1")).toHaveCount(1);
  expect(problems).toEqual([]);
});

test("flow: role switch round trip", async ({ page }) => {
  await state.signInAs(page, "customer", "/");
  await radios(page).getByRole("radio", { name: /Riley/ }).click();
  await expect(page).toHaveURL(/\/staff\/queue/);
  await expect(page.locator("h1")).toHaveCount(1);
  await radios(page).getByRole("radio", { name: /Customer/ }).click();
  await expect.poll(() => atPath(page, "/")).toBe(true);
  await expect(page.locator("h1")).toHaveCount(1);
});

test("flow: demo login returns to return_to", async ({ page }, info) => {
  const problems = watchFlow(page, info);
  await state.visitSignedOut(page, "/staff/queue");
  await expect(page).toHaveURL(/\/login\?.*return_to=%2Fstaff%2Fqueue/);
  await page.getByLabel("Username").fill("demo");
  await page.getByLabel("Password", { exact: true }).fill("demo");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/staff\/queue/, { timeout: 10_000 });
  expect(problems).toEqual([]);
});
