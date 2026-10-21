import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { expectNo24HourTimes } from "@/test/no24h";
import { ConditionalSafetyCard, SafetyCard } from "./SafetyCard";
import { makeProps, renderCard } from "./testing/props";
import { resetCardState } from "./testing/resets";
import { blockOf, turnExample } from "./testing/examples";

beforeEach(resetCardState);

describe("SafetyCard", () => {
  it("WP-5: the SAFETY example renders Meridian's two instructions verbatim and no follow-up time", () => {
    const block = blockOf(turnExample("SAFETY"), "safety");
    const { container } = renderCard(<SafetyCard {...makeProps(block)} />);
    const sheet = screen.getByLabelText("Danger: safety instruction");
    expect(Array.from(sheet.querySelectorAll("li")).map((li) => li.textContent)).toEqual(block.steps);
    expect(block.steps).toHaveLength(2);
    const link = screen.getByRole("link", { name: block.call_key.label });
    expect(link.getAttribute("href")).toBe("tel:911");
    expect(screen.getByText(block.contact_line)).toBeTruthy();
    expect(container.textContent).not.toMatch(/business day|within|due|reference|MHC-C-/i);
    expectNo24HourTimes(container);
    expect(sheet.querySelector("button, input, textarea")).toBeNull();
  });
  it("announces once even when rendered twice", () => {
    const block = blockOf(turnExample("SAFETY"), "safety");
    renderCard(<SafetyCard {...makeProps(block)} />);
    renderCard(<SafetyCard {...makeProps(block)} />);
    expect(document.querySelectorAll("[role=alert]")).toHaveLength(1);
  });
  it("CONDITIONAL_SAFETY shows WARNING and the emergency-number line, no 911 button", () => {
    const block = blockOf(turnExample("CONDITIONAL_SAFETY"), "conditional_safety");
    renderCard(<ConditionalSafetyCard {...makeProps(block)} />);
    expect(screen.getByText(block.level)).toBeTruthy();
    expect(screen.getByText(block.emergency_line)).toBeTruthy();
    expect(screen.queryByRole("link")).toBeNull();
    expect(screen.getByLabelText("Warning: safety instruction")).toBeTruthy();
  });
});
