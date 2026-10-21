import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BriefView } from "./BriefView";
import { briefPendingCase, defaultCase, trimmedCase } from "./case.fixtures";

const view = (d = defaultCase(), onJump = vi.fn()) => render(<BriefView brief={d.brief} sources={d.sources} onJump={onJump} />);

describe("BriefView", () => {
  it("renders eight headings in order with exact titles", () => {
    const d = defaultCase();
    view(d);
    const hs = screen.getAllByRole("heading", { level: 3 });
    expect(hs.map((h) => h.textContent)).toEqual(d.brief.headings.map((h) => h.title));
    expect(hs).toHaveLength(8);
  });
  it("claims card has the Customer says tag and no chips", () => {
    view();
    const card = screen.getByRole("heading", { name: "What the customer says (not checked)" }).closest("section")!;
    expect(within(card).getByText(/Customer says/)).toBeTruthy();
    expect(within(card).queryAllByRole("button")).toHaveLength(0);
  });
  it("facts show one chip per source id and changed adds the word", () => {
    const d = defaultCase();
    d.brief.headings[2].items = [{ text: "Plan is Basic.", kind: "fact", source_ids: ["src-membership", "src-invoice"], changed: true }];
    view(d);
    const card = screen.getByRole("heading", { name: d.brief.headings[2].title }).closest("section")!;
    const chips = within(card).getAllByRole("button");
    expect(chips).toHaveLength(2);
    expect(chips[0].textContent).toContain("changed");
  });
  it("clicking a chip jumps to its source", () => {
    const onJump = vi.fn();
    view(defaultCase(), onJump);
    fireEvent.click(screen.getAllByRole("button", { name: /Invoice INV-204411/ })[0]);
    expect(onJump).toHaveBeenCalledWith("src-invoice");
  });
  it("trimmed section shows the note", () => {
    view(trimmedCase());
    expect(screen.getAllByText(/Something here didn't match the record and was removed\.|removed/).length).toBeGreaterThan(0);
  });
  it("being written shows only the sentence", () => {
    view(briefPendingCase());
    expect(screen.getByText("The brief is being written. The conversation is complete.")).toBeTruthy();
    expect(screen.queryAllByRole("heading")).toHaveLength(0);
  });
  it("empty items read Nothing recorded.", () => {
    const d = defaultCase();
    d.brief.headings[4].items = [];
    view(d);
    expect(screen.getByText("Nothing recorded.")).toBeTruthy();
  });
  it("index chip focuses its section", () => {
    const d = defaultCase();
    view(d);
    fireEvent.click(screen.getByRole("button", { name: `${d.brief.headings[3].number}, ${d.brief.headings[3].title}` }));
    expect(document.activeElement?.id).toBe("brief-4");
  });
});
