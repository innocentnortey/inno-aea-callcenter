import { defineConfig } from "@playwright/test";

// E2E_TARGET=mock (default): starts Prism (:4019) and `vite --mode mock` (:5184); states come from the dev layer.
// E2E_TARGET=real: starts nothing. E2E_BASE_URL (default http://127.0.0.1:5184) must already be a `npm run dev` server
// whose /api proxies to the real backend (API_PORT, default 8000). See tests/e2e/support/state.ts and
// docs/ux/04-prototype/INTEGRATION_HANDOFF.md "E2E status".
const real = process.env.E2E_TARGET === "real";
const baseURL = real ? (process.env.E2E_BASE_URL ?? "http://127.0.0.1:5184") : "http://127.0.0.1:5184";

export default defineConfig({
  testDir: "tests/e2e",
  timeout: real ? 60_000 : 30_000,
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  webServer: real
    ? undefined
    : [
        { command: "npm run mock", port: 4019, reuseExistingServer: false, timeout: 60_000 },
        { command: "npm run dev:mock", port: 5184, reuseExistingServer: false, timeout: 60_000 },
      ],
  use: { baseURL, locale: "en-US", timezoneId: "America/Chicago", reducedMotion: "reduce" },
  projects: [
    { name: "chrome-desktop", use: { channel: "chrome", viewport: { width: 1280, height: 800 } } },
    { name: "chrome-phone", use: { channel: "chrome", viewport: { width: 390, height: 844 } } },
  ],
});
