import { describe, expect, it } from "vitest";
import { act, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders, shellTransport } from "@/test/render";
import { RoleSwitch } from "@/components/shell/RoleSwitch";
import { SignOutButton } from "@/components/shell/chrome";
import { useSession } from "./session";
import { jsonResponse } from "@/test/fakeTransport";
import { makeFakeTransport } from "@/test/fakeTransport";
import { SESSION_BY_ROLE, SESSION_REPRESENTATIVE } from "@/test/fixtures";
import type { Role } from "@/lib/roles";

function Probe() {
  const { role, status } = useSession();
  return <p data-testid="probe">{status}:{role ?? "none"}</p>;
}
const tree = (<><Probe /><RoleSwitch /><SignOutButton /></>);

async function switchTo(label: RegExp) {
  await waitFor(() => expect(screen.getByTestId("probe").textContent).toMatch(/^ready/));
  await userEvent.click(screen.getByRole("radio", { name: label }));
}

describe("session", () => {
  it.each([
    ["Riley, demo representative", "/staff/queue", "representative"],
    ["Demo supervisor", "/staff/oversight", "supervisor"],
    ["Demo business owner", "/staff/owner", "owner"],
  ] as const)("switching to %s lands on %s", async (label, path, role) => {
    const { router } = renderWithProviders(tree, { route: "/x", role: "customer" });
    await switchTo(new RegExp(label));
    await waitFor(() => expect(router.state.location.pathname).toBe(path));
    expect(screen.getByTestId("probe").textContent).toBe(`ready:${role}`);
  });

  it("switching to customer lands on /", async () => {
    const { router } = renderWithProviders(tree, { route: "/x", role: "representative" });
    await switchTo(/Customer \(demo\)/);
    await waitFor(() => expect(router.state.location.pathname).toBe("/"));
  });

  it.each(["/demo", "/demo/inbox", "/monitoring", "/eval"])("stays on %s when the role changes", async (path) => {
    const { router } = renderWithProviders(tree, { route: path, role: "customer" });
    await switchTo(/Demo supervisor/);
    await waitFor(() => expect(screen.getByTestId("probe").textContent).toBe("ready:supervisor"));
    expect(router.state.location.pathname).toBe(path);
  });

  it("a 401 on getSession goes to the login with return_to", async () => {
    const { router } = renderWithProviders(tree, { route: "/staff/queue", role: undefined, transport: shellTransport(null) });
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    expect(router.state.location.search).toBe("?return_to=%2Fstaff%2Fqueue&reason=none");
  });

  it("signOut calls logout then goes to /login", async () => {
    const seen: string[] = [];
    const { router } = renderWithProviders(tree, { route: "/staff/queue", transport: shellTransport("representative", undefined, seen) });
    await waitFor(() => expect(screen.getByTestId("probe").textContent).toBe("ready:representative"));
    await userEvent.click(screen.getByRole("button", { name: /Sign out/ }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    expect(seen).toContain("logout");
  });

  it("shows the error line when the switch fails", async () => {
    const t = makeFakeTransport((ctx) => {
      if (ctx.op === "getSession") return jsonResponse(200, SESSION_REPRESENTATIVE);
      if (ctx.op === "switchRole") return jsonResponse(503, { error: { code: "RESET_IN_PROGRESS" } });
      return jsonResponse(200, {});
    });
    renderWithProviders(tree, { route: "/x", transport: t });
    await waitFor(() => expect(screen.getByTestId("probe").textContent).toBe("ready:representative"));
    await act(async () => { await userEvent.click(screen.getByRole("radio", { name: /Demo supervisor/ })); });
    expect(await screen.findByText("Couldn't switch role. Try again.")).toBeTruthy();
    void SESSION_BY_ROLE; void (null as Role | null);
  });
});
