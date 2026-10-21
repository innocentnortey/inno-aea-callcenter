import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SpendBar } from "./SpendBar";

describe("SpendBar", () => {
  it("612 of 3000 shows $6.12 of $30.00 and no Cap reached", () => {
    render(<SpendBar todayCents={612} capCents={3000} />);
    expect(screen.getByText("$6.12 of $30.00 daily cap")).toBeTruthy();
    expect(screen.queryByText("Cap reached")).toBeNull();
  });
  it("3012 of 3000 clamps the bar to 100% and shows Cap reached", () => {
    render(<SpendBar todayCents={3012} capCents={3000} />);
    expect(screen.getByText("Cap reached")).toBeTruthy();
    expect(screen.getByTestId("spend-fill").style.width).toBe("100%");
  });
  it("fill width is the rounded percent", () => {
    render(<SpendBar todayCents={612} capCents={3000} />);
    expect(screen.getByTestId("spend-fill").style.width).toBe("20%");
    expect(screen.getByText("Spend today $6.12 of the $30.00 daily cap, 20 percent.")).toBeTruthy();
  });
});
