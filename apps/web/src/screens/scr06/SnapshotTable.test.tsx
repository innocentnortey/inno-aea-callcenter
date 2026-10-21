import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SnapshotTable } from "./SnapshotTable";
import { SourceCard } from "./SourceCard";
import { defaultCase } from "./case.fixtures";

const AS_OF = "2026-10-16T14:20:00-05:00";
describe("SnapshotTable", () => {
  it("table with th scope and a changed row", () => {
    render(<SnapshotTable snapshot={{ tier: "Basic", seats: 2 }} current={{ tier: "Comfort Plus", seats: 2 }} asOf={AS_OF} unavailable={false} />);
    const t = screen.getByRole("table");
    expect(within(t).getAllByRole("columnheader").some((h) => h.getAttribute("scope") === "col")).toBe(true);
    expect(within(t).getByRole("rowheader", { name: "Tier" }).getAttribute("scope")).toBe("row");
    expect(within(t).getByText("Changed since")).toBeTruthy();
    expect(within(t).getByText(/Now · 2:20 pm/)).toBeTruthy();
    expect(within(t).getAllByText("Changed since")).toHaveLength(1);
  });
  it("KB passage renders as a blockquote", () => {
    const { container } = render(<SnapshotTable snapshot={{ passage: "The $89 diagnostic is credited." }} current={null} asOf={AS_OF} unavailable />);
    expect(container.querySelector("blockquote")?.textContent).toBe("The $89 diagnostic is credited.");
  });
  it("unavailable shows the sentence and the snapshot alone", () => {
    const faq = defaultCase().sources.find((s) => s.source_id === "src-faq")!;
    render(<SourceCard source={faq} asOf={AS_OF} highlighted={false} />);
    expect(screen.getByText("This record can't be read right now; the snapshot is shown alone.")).toBeTruthy();
    expect(screen.queryByText(/^Now/)).toBeNull();
  });
  it("changed source card shows both values in the status line", () => {
    const m = defaultCase().sources.find((s) => s.source_id === "src-membership")!;
    render(<SourceCard source={m} asOf={AS_OF} highlighted={false} />);
    expect(screen.getByText("Changed since the AI saw it: was Basic, now Comfort Plus")).toBeTruthy();
  });
});
