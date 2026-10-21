import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MetricTile, type MetricTileProps } from "./MetricTile";

const base: MetricTileProps = {
  heading: "Handoffs", value: "29%", denominatorLine: "5 of 17 conversations", caseRefs: ["MHC-C-0007"], denominator: 17,
  open: false, onToggle: () => undefined, panelId: "panel",
};

describe("MetricTile", () => {
  it("renders the figure, the denominator line and an Open the cases button", () => {
    const onToggle = vi.fn();
    render(<MetricTile {...base} onToggle={onToggle} />);
    expect(screen.getByRole("heading", { level: 2, name: "Handoffs" })).toBeTruthy();
    expect(screen.getByText("29%")).toBeTruthy();
    expect(screen.getByText("5 of 17 conversations")).toBeTruthy();
    const btn = screen.getByRole("button", { name: "Open the cases" });
    expect(btn.getAttribute("aria-expanded")).toBe("false");
    btn.click();
    expect(onToggle).toHaveBeenCalled();
  });
  it("a zero denominator renders No cases to open. and no button", () => {
    render(<MetricTile {...base} denominator={0} value={"—"} />);
    expect(screen.getByText("No cases to open.")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });
  it("a null value shows the reason", () => {
    render(<MetricTile {...base} value={"—"} reason="No promises are due yet." caseRefs={[]} denominator={0} />);
    expect(screen.getByText("No promises are due yet.")).toBeTruthy();
  });
});
