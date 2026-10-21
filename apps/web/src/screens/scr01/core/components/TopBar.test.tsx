import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import { TopBar } from "./TopBar";

const show = (props: Parameters<typeof TopBar>[0]) => render(<MemoryRouter><TopBar {...props} /></MemoryRouter>);
describe("TopBar", () => {
  it("shows the assistant line and the Demo guide link", () => {
    show({ replying: { kind: "ai", display_name: null }, reference: null });
    expect(screen.getByRole("heading", { level: 1, name: "Meridian Home Comfort" })).toBeTruthy();
    expect(screen.getByText(/Meridian assistant · automated/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Demo guide" }).getAttribute("href")).toBe("/demo");
  });
  it("adds the reference once a case exists", () => {
    show({ replying: { kind: "ai", display_name: null }, reference: "MHC-C-0007" });
    expect(screen.getByText("MHC-C-0007")).toBeTruthy();
  });
  it("names the representative while the assistant is paused", () => {
    show({ replying: { kind: "human", display_name: "Riley" }, reference: "MHC-C-0007" });
    expect(screen.getByText("Riley (demo representative). Assistant paused.")).toBeTruthy();
    expect(screen.queryByText(/automated/)).toBeNull();
  });
});
