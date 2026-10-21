import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { SCREENS } from "@/routes";
import { renderApp } from "@/test/render";
import type { Role } from "@/lib/roles";

const ROLE_FOR: Record<string, Role> = { "SCR-5": "representative", "SCR-6": "representative", "SCR-7": "supervisor", "SCR-8": "representative", "SCR-9": "owner" };

describe("screen stubs", () => {
  it.each(SCREENS.map((s) => [s.id, s.path] as const))("%s renders exactly one h1", async (id, path) => {
    const role = id === "SCR-12" ? null : (ROLE_FOR[id] ?? "customer");
    renderApp({ route: path.replace(":reference", "MHC-C-0007"), role });
    await waitFor(() => expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1), { timeout: 5000 });
    // Real screens replace the stub heading; where a screen marks itself, the mark must name this screen.
    const mark = document.querySelector("[data-screen]")?.getAttribute("data-screen");
    if (mark) expect(mark).toBe(id);
    else if (/SCR-\d+/.test(document.title)) expect(document.title).toContain(id);
  });

  it("SCR-5 as customer shows the role-gate sentence and never reads the queue", async () => {
    const seen: string[] = [];
    renderApp({ route: "/staff/queue", role: "customer", seen });
    await screen.findByText("You're acting as the customer. Switch to a staff role to see this.");
    expect(seen).not.toContain("getQueue");
    expect(screen.getAllByRole("radiogroup", { name: "Acting as" }).length).toBeGreaterThan(0);
  });

  it("a signed-out visit lands on the login with return_to", async () => {
    const { router } = renderApp({ route: "/staff/queue", role: null });
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    expect(router.state.location.search).toBe("?return_to=%2Fstaff%2Fqueue&reason=none");
  });

  it("unknown paths show Page not found", async () => {
    renderApp({ route: "/nope", role: "customer" });
    expect(await screen.findByRole("heading", { name: "Page not found" })).toBeTruthy();
  });
});
