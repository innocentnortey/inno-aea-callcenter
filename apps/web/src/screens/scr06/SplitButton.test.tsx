import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { PlanItem, MenuKey } from "./actionPlan";
import { SplitButton } from "./SplitButton";

const menu: PlanItem<MenuKey>[] = [
  { key: "release", label: "Release", enabled: true },
  { key: "wait", label: "Set waiting", enabled: false, reason: "Claim the case first." },
];
describe("SplitButton", () => {
  it("main segment calls onPrimary", () => {
    const onPrimary = vi.fn();
    render(<SplitButton primary={{ kind: "claim", label: "Claim" }} menu={menu} onPrimary={onPrimary} onMenu={() => {}} busy={false} />);
    fireEvent.click(screen.getByRole("button", { name: "Claim" }));
    expect(onPrimary).toHaveBeenCalled();
  });
  it("menu lists items and disabled items show their reason", async () => {
    const onMenu = vi.fn();
    render(<SplitButton primary={{ kind: "claim", label: "Claim" }} menu={menu} onPrimary={() => {}} onMenu={onMenu} busy={false} />);
    await userEvent.click(screen.getByRole("button", { name: "More actions" }));
    expect(await screen.findByRole("menuitem", { name: "Release" })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: /Set waiting/ }).getAttribute("aria-disabled")).toBe("true");
    expect(screen.getByText("Claim the case first.")).toBeTruthy();
    await userEvent.click(screen.getByRole("menuitem", { name: "Release" }));
    expect(onMenu).toHaveBeenCalledWith("release");
  });
  it("no primary renders More actions", () => {
    render(<SplitButton primary={null} menu={menu} onPrimary={() => {}} onMenu={() => {}} busy={false} />);
    expect(screen.getByRole("button", { name: "More actions" })).toBeTruthy();
  });
  it("renders nothing when nothing is enabled", () => {
    const { container } = render(<SplitButton primary={null} menu={[menu[1]]} onPrimary={() => {}} onMenu={() => {}} busy={false} />);
    expect(container.textContent).toBe("");
  });
  it("keyboard opens the menu", async () => {
    render(<SplitButton primary={{ kind: "claim", label: "Claim" }} menu={menu} onPrimary={() => {}} onMenu={() => {}} busy={false} />);
    screen.getByRole("button", { name: "More actions" }).focus();
    await userEvent.keyboard("{Enter}");
    expect(await screen.findByRole("menu")).toBeTruthy();
  });
});
