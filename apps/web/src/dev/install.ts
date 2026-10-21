import { createElement } from "react";
import { createRoot } from "react-dom/client";
import type { RouteObject } from "react-router";
import { defaultTransport, setTransport } from "@/api/transport";
import { setTheme } from "@/state/theme";
import { calls } from "./calllog";
import { applyScenario, syncUrl } from "./apply";
import { patchHistory } from "./nav";
import { allScenarios } from "./scenarios";
import { applyRole, setSessionCookie } from "./session-fake";
import { emitToStream } from "./stream/dev-stream";
import { wrapTransport } from "./transport";
import { getWorld, parseParams, setWorld } from "./world";
import { Kit } from "./Kit";
import { Panel } from "./Panel";

export const __MHC_DEV_LAYER__ = "mhc-dev-layer";

declare global {
  interface Window { __mhcDev?: unknown; __mhcDevRoutes?: RouteObject[] }
}

/** Mock mode only: swaps the transport, seeds the fake world, mounts the panel in its own React root. */
export async function installDev(): Promise<void> {
  patchHistory();
  const parsed = parseParams(window.location.search);
  setWorld(parsed.patch);
  setTransport(wrapTransport(defaultTransport));
  setSessionCookie(); // Prism checks the cookie; "signed out" is emulated by resolve.ts
  if (parsed.theme) setTheme(parsed.theme);

  const w = getWorld();
  if (w.role !== "customer" && !w.sessionBody) await applyRole(defaultTransport, w.role);

  window.__mhcDevRoutes = [{ path: "/__kit", element: createElement(Kit) }];
  window.__mhcDev = {
    world: getWorld,
    calls,
    scenarios: () => allScenarios().map((s) => s.id),
    apply: applyScenario,
    emit: emitToStream,
  };

  if (parsed.scenario) await applyScenario(parsed.scenario);
  else syncUrl();

  const host = document.createElement("div");
  host.id = "mhc-dev-panel-root";
  document.body.appendChild(host);
  createRoot(host).render(createElement(Panel));
}
