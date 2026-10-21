import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LiveRow } from "./LiveRow";
import { staffedQueue } from "./queue.fixtures";

const row = () => staffedQueue().live[0];
const wrap = (ui: React.ReactElement) => render(<ul>{ui}</ul>);

describe("LiveRow", () => {
  it("accessible name is the visible text and ends with waiting since 2:14 pm (WCAG 2.5.3)", () => {
    wrap(<LiveRow row={row()} onOpen={() => {}} />);
    const btn = screen.getByRole("button", { name: /^.*MHC-C-0012.*Waiting since 2:14 pm$/ });
    expect(btn.hasAttribute("aria-label")).toBe(false);
    expect(btn.textContent).toMatch(/^Asked for a person/i);
  });
  it("shows no duration or estimate text", () => {
    const { container } = wrap(<LiveRow row={row()} onOpen={() => {}} />);
    expect(container.textContent).toContain("Waiting since 2:14 pm");
    expect(container.textContent).not.toMatch(/\d+\s?(min|minutes|h|hours)\b|estimate|about/i);
  });
  it("Claim and join calls the handler and shows loading", () => {
    const onClaim = vi.fn();
    const { rerender } = wrap(<LiveRow row={row()} onOpen={() => {}} onClaimAndJoin={onClaim} />);
    fireEvent.click(screen.getByRole("button", { name: "Claim and join MHC-C-0012" }));
    expect(onClaim).toHaveBeenCalledWith("MHC-C-0012");
    rerender(<ul><LiveRow row={row()} onOpen={() => {}} onClaimAndJoin={onClaim} pending /></ul>);
    expect(screen.getByRole("button", { name: "Claim and join MHC-C-0012" }).getAttribute("aria-busy")).toBe("true");
  });
  it("compact omits the button", () => {
    wrap(<LiveRow row={row()} onOpen={() => {}} compact />);
    expect(screen.queryByText("Claim and join")).toBeNull();
  });
});
