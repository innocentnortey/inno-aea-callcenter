import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { OptionTile } from "./OptionTile";

describe("OptionTile", () => {
  it("selected shows a check and aria-pressed", () => {
    const { container } = render(<OptionTile label="8:00 am" selected onClick={vi.fn()} />);
    expect(screen.getByRole("button", { name: "8:00 am" }).getAttribute("aria-pressed")).toBe("true");
    expect(container.querySelector("svg")).not.toBeNull();
  });
  it("taken is disabled, struck through and says Taken", () => {
    const { container } = render(<OptionTile label="8:00 am" taken onClick={vi.fn()} />);
    const b = screen.getByRole("button") as HTMLButtonElement;
    expect(b.disabled).toBe(true);
    expect(container.textContent).toContain("Taken");
    expect(container.querySelector(".line-through")).not.toBeNull();
  });
  it("keeps the 44 px target class", () => {
    render(<OptionTile label="x" onClick={vi.fn()} />);
    expect(screen.getByRole("button").className).toContain("min-h-[var(--target-min)]");
  });
});
