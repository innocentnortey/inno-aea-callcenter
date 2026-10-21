import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { expectNo24HourTimes } from "@/test/no24h";
import { emergencyLineStaffed } from "@/dev/scenarios/scr01-cards.fixtures";
import { EmergencyLineCard } from "./EmergencyLineCard";
import { makeProps, renderCard } from "./testing/props";
import { blockOf, turnExample } from "./testing/examples";

describe("EmergencyLineCard", () => {
  it("shows the tel link and the separate line after a divider", () => {
    const block = blockOf(turnExample("EMERGENCY_LINE"), "emergency_line");
    const { container } = renderCard(<EmergencyLineCard {...makeProps(block)} />);
    const link = screen.getByRole("link");
    expect(link.getAttribute("href")).toBe("tel:5125550199");
    expect(container.querySelector("hr")).not.toBeNull();
    expect(screen.getByText(block.separate_line as string)).toBeTruthy();
    expectNo24HourTimes(container);
  });
  it("staffed: no divider and no business-day line", () => {
    const block = blockOf(emergencyLineStaffed(turnExample("EMERGENCY_LINE")), "emergency_line");
    const { container } = renderCard(<EmergencyLineCard {...makeProps(block)} />);
    expect(container.querySelector("hr")).toBeNull();
    expect(container.textContent).not.toContain("1 business day");
    expectNo24HourTimes(container);
  });
});
