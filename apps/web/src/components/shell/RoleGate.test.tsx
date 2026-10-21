import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/render";
import { RoleGate } from "./RoleGate";

describe("RoleGate", () => {
  it("shows the customer sentence and renders no children for a staff screen", async () => {
    const child = vi.fn(() => <p>staff data</p>);
    const Child = () => child();
    renderWithProviders(<RoleGate allow={["representative", "supervisor"]}><Child /></RoleGate>, { role: "customer" });
    expect(await screen.findByText("You're acting as the customer. Switch to a staff role to see this.")).toBeTruthy();
    expect(child).not.toHaveBeenCalled();
    expect(screen.getByRole("radiogroup", { name: "Acting as" })).toBeTruthy();
  });
  it("renders children when allowed", async () => {
    renderWithProviders(<RoleGate allow={["representative"]}><p>staff data</p></RoleGate>, { role: "representative" });
    expect(await screen.findByText("staff data")).toBeTruthy();
  });
  it("words the panel for another staff role", async () => {
    renderWithProviders(<RoleGate allow={["supervisor"]}><p>x</p></RoleGate>, { role: "owner" });
    expect(await screen.findByText("You're acting as Demo business owner. Switch to Demo supervisor to see this.")).toBeTruthy();
  });
});
