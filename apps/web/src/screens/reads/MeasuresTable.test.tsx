import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import type { components } from "@/api/types.gen";
import { MeasuresTable } from "./MeasuresTable";

type Measure = components["schemas"]["Measure"];
const m = (over: Partial<Measure>): Measure => ({
  id: "M-1", label: "Resolved by the AI", numerator: 9, denominator: 17, unit: "count", value: 0.529, null_reason: null, kind: "measured", case_refs: ["MHC-C-0001"], ...over,
} as Measure);

describe("MeasuresTable", () => {
  const props = { caption: "Outcomes", firstColumn: "Outcome", noun: "conversations", openKey: null, onOpen: () => undefined, panelId: "p" };
  it("rows use th scope=row and the columns use th scope=col", () => {
    const { container } = render(<MeasuresTable {...props} rows={[m({})]} />);
    expect(container.querySelectorAll('th[scope="col"]').length).toBe(4);
    expect(container.querySelector('th[scope="row"]')?.textContent).toBe("Resolved by the AI");
  });
  it("count is n of N and share is rounded", () => {
    render(<MeasuresTable {...props} rows={[m({})]} />);
    expect(screen.getByText("9 of 17 conversations")).toBeTruthy();
    expect(screen.getByText("53%")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Open the cases for Resolved by the AI" })).toBeTruthy();
  });
  it("a row with no case refs says No cases to open.", () => {
    render(<MeasuresTable {...props} rows={[m({ case_refs: [] })]} />);
    expect(screen.getByText("No cases to open.")).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });
});
