import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { AccountCard } from "./AccountCard";
import { makeProps, renderCard } from "./testing/props";
import { blockOf, turnExample } from "./testing/examples";

describe("AccountCard", () => {
  it("invoice: lines as billed, total, balance caption, no verdict", () => {
    const block = blockOf(turnExample("VERIFIED_ACCOUNT_INVOICE"), "account_card");
    const { container } = renderCard(<AccountCard {...makeProps(block)} />);
    for (const l of block.invoice!.lines) {
      expect(container.textContent).toContain(l.description);
      expect(screen.getAllByText(l.amount.display).length).toBeGreaterThan(0);
    }
    expect(screen.getAllByText("$478.00").length).toBeGreaterThanOrEqual(2); // total and balance
    expect(screen.getByText("Balance · unpaid · due Nov 1, 2026")).toBeTruthy();
    expect(screen.getAllByText("Source").length).toBeGreaterThan(0);
    expect(container.textContent).not.toMatch(/overcharg|wrong|should|error/i);
  });
  it("membership", () => {
    renderCard(<AccountCard {...makeProps(blockOf(turnExample("ACCOUNT_MEMBERSHIP"), "account_card"))} />);
    expect(screen.getByText("Comfort Plus")).toBeTruthy();
    expect(screen.getByText("Mar 14, 2027")).toBeTruthy();
  });
  it("warranty", () => {
    const block = blockOf(turnExample("ACCOUNT_WARRANTY"), "account_card");
    renderCard(<AccountCard {...makeProps(block)} />);
    expect(screen.getByText(block.warranty!.sentence)).toBeTruthy();
  });
});
