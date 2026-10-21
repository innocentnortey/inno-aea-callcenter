import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { atPath, state } from "./support/state";

type Role = "customer" | "representative" | "supervisor" | "owner";
const SCREENS: { id: string; path: string; role: Role | null }[] = [
  { id: "SCR-1", path: "/", role: "customer" },
  { id: "SCR-2", path: "/demo/inbox", role: "customer" },
  { id: "SCR-3", path: "/demo", role: "customer" },
  { id: "SCR-4", path: "/role", role: "customer" },
  { id: "SCR-5", path: "/staff/queue", role: "representative" },
  { id: "SCR-6", path: "/staff/cases/MHC-C-0007", role: "representative" },
  { id: "SCR-7", path: "/staff/oversight", role: "supervisor" },
  { id: "SCR-8", path: "/staff/flags", role: "representative" },
  { id: "SCR-9", path: "/staff/owner", role: "owner" },
  { id: "SCR-10", path: "/monitoring", role: "customer" },
  { id: "SCR-11", path: "/eval", role: "customer" },
  { id: "SCR-12", path: "/login", role: null },
];

function watch(page: Page) {
  const problems: string[] = [];
  page.on("console", (m) => { if (m.text().includes("[contract drift]")) problems.push("drift: " + m.text()); });
  page.on("pageerror", (e) => problems.push("pageerror: " + e.message));
  return problems;
}

for (const s of SCREENS) {
  test(`${s.id} ${s.path}`, async ({ page }) => {
    const problems = watch(page);
    if (s.role) await state.signInAs(page, s.role, s.path);
    else await state.visitSignedOut(page, s.path);
    const h1 = page.locator("h1");
    await expect(h1).toHaveCount(1);
    // Real screens replace the stub heading (it carried "SCR-n"); where a screen marks itself, the mark must name it.
    const mark = await page.locator("[data-screen]").first().getAttribute("data-screen", { timeout: 1000 }).catch(() => null);
    if (mark) expect(mark).toBe(s.id);
    else if (/SCR-\d+/.test(await page.title())) expect(await page.title()).toContain(s.id);
    if (s.id !== "SCR-12") await expect(page.getByRole("radiogroup", { name: "Acting as" }).first()).toBeVisible();
    const results = await new AxeBuilder({ page }).exclude("#mhc-dev-panel-root").analyze();
    expect(results.violations.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
    expect(problems).toEqual([]);
  });
}

test("a signed-out visit to the queue lands on the login with return_to", async ({ page }) => {
  await state.visitSignedOut(page, "/staff/queue");
  await expect(page).toHaveURL(/\/login\?.*return_to=%2Fstaff%2Fqueue.*reason=none/);
});

test("the role switch moves Customer to Representative and back", async ({ page }) => {
  await state.signInAs(page, "customer", "/");
  await page.getByRole("radiogroup", { name: "Acting as" }).first().getByRole("radio", { name: /Riley/ }).click();
  await expect(page).toHaveURL(/\/staff\/queue/);
  await page.getByRole("radiogroup", { name: "Acting as" }).first().getByRole("radio", { name: /Customer/ }).click();
  await expect.poll(() => atPath(page, "/")).toBe(true);
});
