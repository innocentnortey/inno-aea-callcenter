// G-03: the cross-flow journey of INTEGRATION_HANDOFF section 4.7, `journey.customer-booking-then-person`
// (backend ids J-3, J-6, J-7, J-8), two browser contexts (customer, staff).
//
//   customer: chat -> start a booking -> SLOT_TAKEN -> fresh windows -> Talk to a person
//   staff:    SCR-5 queue -> Claim and join -> SCR-6 -> send a message -> hand back (or close)
//   customer: sees the representative's message, then the assistant back (or the ended chat)
//
// Two modes, one set of steps (E2E_TARGET picks, see support/state.ts):
//
//   mock  -> "[MOCK-ONLY rehearsal]". Every selector exists, nothing here counts as REAL-BACKEND evidence.
//            The dev layer is per browser page (an in-memory world), so the two contexts share NOTHING. Where the real
//            system would carry state or events from one context to the other, the rehearsal replays the same thing
//            by hand on the receiving side; each such place says "MOCK:" in a comment. They are:
//              M1  SLOT_TAKEN comes from the chat director (first pick of slot 57 is "taken"), not from a second customer.
//              M2  The customer's "Talk to a person" is forced to LIVE_QUEUED by scenario scr01-cards.live-queued.
//                  The card shows MHC-C-0007 while the staff queue's seeded live row is MHC-C-0012: the mock cannot
//                  make the two contexts agree on one case, so staff claims the seeded row.
//              M3  Staff actions never reach the customer tab. The chat stream events (representative_joined,
//                  ai_paused, staff_message, ai_resumed, chat_closed) are pushed into the customer tab with the dev
//                  layer's scripted stream hook window.__mhcDev.emit, carrying the text the staff tab really sent.
//                  So this proves the customer screen renders those events, NOT that the server delivers them (SSE
//                  delivery across two contexts, event ids and Last-Event-ID replay are what G-04 / the real run test).
//              M4  The case brief is the fixed mock one: it does not show the booking attempt or SLOT_TAKEN.
//              M5  No persisted-state assertions (case row, messages after a reload): the mock keeps none.
//
//   real  -> "[REAL-BACKEND — not yet run]". No dev parameter, no emit, no forced example. Needs a backend whose chat
//            has a booking path and a second customer who can take a window (scripted model of AEA-57, seeded identity
//            via E2E_CUSTOMER_NAME / E2E_CUSTOMER_PHONE). Skips with a message when GET /api/healthz is unreachable.
//            Written against the contract and the mock's selectors, never run: expect selector fixes on first contact.
import { expect, test, type Browser, type BrowserContext, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { state } from "./support/state";

const REAL = state.target === "real";
const TAG = REAL ? "[REAL-BACKEND — not yet run]" : "[MOCK-ONLY rehearsal]";
const WINDOW = "12:00 pm – 4:00 pm"; // in the mock this is slot 57, the one the chat director calls taken (M1)
const MOCK_QUEUE_REF = "MHC-C-0012"; // M2

test.beforeEach(async ({ request }) => {
  if (!REAL) return;
  let why = "";
  let ok = false;
  try {
    const r = await request.get("/api/healthz", { timeout: 5_000 });
    ok = r.ok();
    why = `HTTP ${r.status()}`;
  } catch (e) {
    why = (e as Error).message.split("\n")[0];
  }
  test.skip(!ok, `E2E_TARGET=real: GET /api/healthz is unreachable (${why}). Start the backend on :8000 and a dev server (npm run dev) whose /api proxies to it, then set E2E_BASE_URL if it is not http://127.0.0.1:5184.`);
});

function watch(page: Page, who: string, problems: string[]) {
  page.on("pageerror", (e) => problems.push(`${who} pageerror: ${e.message}`));
  page.on("console", (m) => {
    const t = m.text();
    if (t.includes("[contract drift]")) problems.push(`${who} drift: ${t}`);
    // Chrome logs every 4xx/5xx as a console error; the app triggers some by design (404 "no chat yet", 401 before login).
    else if (m.type() === "error" && !/^Failed to load resource: the server responded with a status of (4\d\d|5\d\d)\b/.test(t)) problems.push(`${who} console.error: ${t}`);
  });
}
async function axe(page: Page, where: string) {
  const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).exclude("#mhc-dev-panel-root").analyze();
  expect(r.violations.map((v) => `${where} ${v.id}: ${v.nodes[0]?.target.join(" ")}`)).toEqual([]);
}
const conversation = (page: Page) => page.getByRole("log", { name: "Conversation" });
const entries = (page: Page) => conversation(page).locator("[data-entry]");
const send = async (page: Page, text: string) => {
  // The composer can re-mount while the chat is still starting and drop the draft, so fill-then-click is retried as a unit.
  await expect(async () => {
    await page.getByRole("textbox", { name: "Message" }).fill(text);
    await page.getByRole("button", { name: "Send", exact: true }).click({ timeout: 2_000 }); // Enter does not send on the phone (finding F-3)
  }).toPass({ timeout: 15_000 });
};
/** The windows tile (aria name "<window>, open") on the LAST slot card in the thread, i.e. the freshest one. */
const lastOpenTile = (page: Page, label: string) => page.getByRole("button", { name: `${label}, open` }).last();
const lastDay = async (page: Page) => { // the freshest card may open on a day with no open window; pick the tab that has one
  const tabs = page.getByRole("tab").filter({ hasText: /open/ });
  if (await tabs.count()) await tabs.last().click();
};

/** M3: the dev layer's scripted-stream hook. In real mode there is no such thing and this throws. */
async function mockStream(page: Page, event: Record<string, unknown>) {
  expect(REAL, "mockStream is mock-only").toBe(false);
  await page.evaluate((ev) => (window as unknown as { __mhcDev: { emit(t: string, e: unknown): void } }).__mhcDev.emit("*", ev), { event_id: 0, ...event });
}
const RILEY = { kind: "representative", display_name: "Riley" };
const SYSTEM = { kind: "event", display_name: null };

/** Real only: a second customer takes the window first, so the first customer's stale card hits SLOT_TAKEN. */
async function holdWindowAsSecondCustomer(browser: Browser, label: string): Promise<BrowserContext> {
  const ctx = await browser.newContext({ baseURL: test.info().project.use.baseURL, viewport: test.info().project.use.viewport });
  const p = await ctx.newPage();
  await state.signInAs(p, "customer", "/");
  await send(p, "I'd like to book a technician visit");
  await p.getByRole("button", { name: "Skip and book" }).click();
  await p.getByLabel("ZIP code or city").fill("78701");
  await p.getByRole("button", { name: "Show windows" }).click();
  await lastDay(p);
  await lastOpenTile(p, label).click();
  await p.getByRole("button", { name: "Continue with this window" }).click();
  // Booking writes the account, so the chat asks to verify first (seeded identity, simulated inbox).
  await p.getByLabel("Name on the account").fill(process.env.E2E_CUSTOMER_NAME ?? "Omar Patel");
  await p.getByLabel("Phone").fill(process.env.E2E_CUSTOMER_PHONE ?? "5125550102");
  await p.getByRole("button", { name: "Send the code" }).click();
  await expect(p.getByLabel("6-digit code")).toBeVisible({ timeout: 20_000 });
  await p.goto("/demo/inbox");
  const code = /\b(\d{6})\b/.exec(await p.locator("main").innerText())?.[1];
  expect(code, "a six-digit code in the simulated inbox").toBeTruthy();
  await p.goto("/");
  await p.getByLabel("6-digit code").fill(code!);
  await p.getByRole("button", { name: "Verify", exact: true }).click();
  await expect(conversation(p)).toContainText(/booked|confirmed|appointment/i, { timeout: 30_000 });
  return ctx;
}

/** Steps 1 to 6. Returns the open pages; the caller finishes with a hand back or a close. */
async function runUntilStaffMessage(browser: Browser, problems: string[]) {
  const customerCtx = await browser.newContext({ baseURL: test.info().project.use.baseURL, viewport: test.info().project.use.viewport });
  const staffCtx = await browser.newContext({ baseURL: test.info().project.use.baseURL, viewport: test.info().project.use.viewport });
  const customer = await customerCtx.newPage();
  const staff = await staffCtx.newPage();
  watch(customer, "customer", problems);
  watch(staff, "staff", problems);

  // 1. Staff context: signed in as the representative, staffing on, SCR-5 open (real: the role switch and SCR-3 do this).
  await state.signInAs(staff, "representative", "/staff/queue", { staffing: "on" });
  await expect(staff.getByRole("heading", { level: 1, name: "Representative queue" })).toBeVisible();

  // 2. Customer: chat, start a booking, see windows.
  // M2: mock forces "Talk to a person" to LIVE_QUEUED here; real has no scenario.
  await state.signInAs(customer, "customer", "/", { staffing: "on", scenario: REAL ? undefined : "scr01-cards.live-queued" });
  await expect(customer.getByRole("textbox", { name: "Message" })).toBeVisible({ timeout: 15_000 });
  await send(customer, "I'd like to book a technician visit");
  await customer.getByRole("button", { name: "Skip and book" }).click(); // the optional quick checks are skipped
  await customer.getByLabel("ZIP code or city").fill("78701");
  await customer.getByRole("button", { name: "Show windows" }).click();
  await expect(customer.getByRole("heading", { name: "Choose a window" }).last()).toBeVisible({ timeout: 15_000 });
  await lastDay(customer);
  await expect(lastOpenTile(customer, WINDOW)).toBeVisible();

  // 3. SLOT_TAKEN. Real: a second customer holds the window first. Mock (M1): the director calls slot 57 taken once.
  let second: BrowserContext | null = null;
  if (REAL) second = await holdWindowAsSecondCustomer(browser, WINDOW);
  await lastOpenTile(customer, WINDOW).click();
  await customer.getByRole("button", { name: "Continue with this window" }).last().click();
  await expect(customer.getByText(/that window just went/i)).toBeVisible({ timeout: 15_000 });
  await axe(customer, "step 3 (slot taken, fresh windows)");
  // ... and picks from the fresh windows (the newest card).
  const before = await entries(customer).count();
  await lastDay(customer);
  await lastOpenTile(customer, WINDOW).click();
  await customer.getByRole("button", { name: "Continue with this window" }).last().click();
  await expect.poll(() => entries(customer).count(), { timeout: 15_000 }).toBeGreaterThan(before + 1);
  if (!REAL) await expect(customer.getByText("Prove it's your account")).toBeVisible(); // the mock's reply after a fresh pick
  await second?.close();

  // 4. Customer asks for a person and gets a live-queued card with a case reference.
  await customer.getByRole("button", { name: "Talk to a person" }).click();
  const card = conversation(customer).getByText(/MHC-C-\d+/).last();
  await expect(card).toBeVisible({ timeout: 15_000 });
  const reference = /MHC-C-\d+/.exec(await card.innerText())![0];
  if (REAL) { // persisted: the case survives a reload of the customer tab
    await customer.reload();
    await expect(conversation(customer).getByText(reference).first()).toBeVisible({ timeout: 15_000 });
  }

  // 5. Staff: the live row is on SCR-5 (real: arrives by poll or stream, no reload), Claim and join, case view.
  const claimRef = REAL ? reference : MOCK_QUEUE_REF; // M2
  const claim = staff.getByRole("button", { name: `Claim and join ${claimRef}` });
  await expect(claim).toBeVisible({ timeout: 30_000 });
  await claim.click();
  await expect(staff).toHaveURL(new RegExp(`/staff/cases/${claimRef}`), { timeout: 15_000 });
  // On the 390 px phone the case view opens on "Brief" and the live reply box sits under "Evidence" (finding: joining
  // does not move the phone to it), so the representative taps Evidence first. On desktop there is no such tab.
  const evidenceTab = staff.getByRole("tab", { name: "Evidence" });
  await staff.getByText(/You are replying as Riley/).or(evidenceTab).first().waitFor({ timeout: 15_000 });
  if (await evidenceTab.isVisible()) await evidenceTab.click();
  await expect(staff.getByText(/You are replying as Riley/)).toBeVisible({ timeout: 15_000 });
  if (REAL) {
    // The brief carries the booking attempt and its SLOT_TAKEN outcome (a real-backend fact; M4 in the mock).
    await expect.soft(staff.locator("main"), "case brief mentions the taken window").toContainText(/that window just went|SLOT_TAKEN|window/i);
  } else {
    // M3: the chat stream tells the customer tab that a person joined and the assistant paused.
    await mockStream(customer, { type: "representative_joined", at: "2026-10-16T14:22:00-05:00", speaker: RILEY, display_name: "Riley", line: "Riley (demo representative) has joined." });
    await mockStream(customer, { type: "ai_paused", at: "2026-10-16T14:22:01-05:00", speaker: SYSTEM, line: "The assistant is paused while Riley is here." });
  }
  await expect(customer.locator("header")).toContainText(/Riley/, { timeout: 20_000 });
  await axe(staff, "step 5 (case view, live)");

  // 6. Staff sends a message; the customer sees it.
  const text = `Hi, this is Riley. I can see your window was taken (${reference}).`;
  await staff.getByLabel("Reply", { exact: true }).fill(text);
  await staff.getByRole("button", { name: "Send", exact: true }).click();
  await expect(staff.getByText(text).first()).toBeVisible({ timeout: 15_000 });
  if (!REAL) await mockStream(customer, { type: "staff_message", at: "2026-10-16T14:22:40-05:00", speaker: RILEY, message_id: "m-journey-1", text }); // M3
  await expect(conversation(customer).getByText(text)).toBeVisible({ timeout: 20_000 });
  if (REAL) { // persisted + replay: a reload of the customer tab still shows the representative's message
    await customer.reload();
    await expect(conversation(customer).getByText(text)).toBeVisible({ timeout: 15_000 });
  }
  return { customer, staff, customerCtx, staffCtx };
}

test.describe(`journey.customer-booking-then-person ${TAG}`, () => {
  test(`${TAG} chat, booking, SLOT_TAKEN, person, claim, reply, hand back`, async ({ browser }) => {
    test.setTimeout(REAL ? 180_000 : 60_000);
    const problems: string[] = [];
    const { customer, staff, customerCtx, staffCtx } = await runUntilStaffMessage(browser, problems);

    // 7. Staff hands back; the customer sees the assistant return.
    await staff.getByRole("button", { name: "Hand back to the assistant" }).click();
    await expect(staff.getByText("This chat is no longer live.")).toBeVisible({ timeout: 15_000 });
    if (!REAL) await mockStream(customer, { type: "ai_resumed", at: "2026-10-16T14:30:00-05:00", speaker: SYSTEM, line: "The assistant is back." }); // M3
    await expect(conversation(customer).getByText("The assistant is back.")).toBeVisible({ timeout: 20_000 });
    await expect(customer.locator("header")).toContainText(/Meridian assistant/);
    await axe(customer, "step 7 (handed back)");
    expect(problems).toEqual([]);
    await customerCtx.close();
    await staffCtx.close();
  });

  test(`${TAG} chat, booking, SLOT_TAKEN, person, claim, reply, close`, async ({ browser }) => {
    test.setTimeout(REAL ? 180_000 : 60_000);
    const problems: string[] = [];
    const { customer, staff, customerCtx, staffCtx } = await runUntilStaffMessage(browser, problems);

    // 7b. Staff closes the chat (only possible while joined, so this is the alternative to handing back).
    await staff.getByRole("button", { name: "Close the chat" }).click();
    await expect(staff.getByText("This chat is no longer live.")).toBeVisible({ timeout: 15_000 });
    if (!REAL) await mockStream(customer, { type: "chat_closed", at: "2026-10-16T14:24:00-05:00", speaker: SYSTEM, line: "Riley closed this chat.", composer_disabled: true }); // M3
    await expect(conversation(customer).getByText("Riley closed this chat.")).toBeVisible({ timeout: 20_000 });
    await expect(customer.getByRole("button", { name: "Start a new chat" })).toBeVisible();
    await expect(customer.getByRole("textbox", { name: "Message" })).toBeDisabled();
    expect(problems).toEqual([]);
    await customerCtx.close();
    await staffCtx.close();
  });
});

