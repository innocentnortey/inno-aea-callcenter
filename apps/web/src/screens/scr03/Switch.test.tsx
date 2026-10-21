import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Switch } from "./Switch";

describe("Switch", () => {
  it("has role switch and a visible label", () => {
    render(<Switch checked={false} onCheckedChange={() => undefined} label="Demo: simulate staff on shift" />);
    expect(screen.getByRole("switch", { name: "Demo: simulate staff on shift" })).toBeTruthy();
    expect(screen.getByText("Demo: simulate staff on shift")).toBeTruthy();
  });
  it("toggles on click and Space", async () => {
    const fn = vi.fn();
    render(<Switch checked={false} onCheckedChange={fn} label="L" />);
    await userEvent.click(screen.getByRole("switch"));
    expect(fn).toHaveBeenLastCalledWith(true);
    screen.getByRole("switch").focus();
    await userEvent.keyboard(" ");
    expect(fn).toHaveBeenCalledTimes(2);
  });
  it("disabled blocks toggling", async () => {
    const fn = vi.fn();
    render(<Switch checked={false} onCheckedChange={fn} label="L" disabled />);
    await userEvent.click(screen.getByRole("switch"));
    expect(fn).not.toHaveBeenCalled();
  });
  it("hint is described-by", () => {
    render(<Switch checked label="L" hint="The hint" onCheckedChange={() => undefined} />);
    expect(screen.getByRole("switch", { description: "The hint" })).toBeTruthy();
  });
});
