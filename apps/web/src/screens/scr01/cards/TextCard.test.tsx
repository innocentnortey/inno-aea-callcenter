import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expectNo24HourTimes } from "@/test/no24h";
import { partialReply } from "@/dev/scenarios/scr01-cards.fixtures";
import { NoInfoCard } from "./NoticeCards";
import { SourceChipCard, TextCard } from "./TextCard";
import { makeProps, renderCard } from "./testing/props";
import { resetCardState } from "./testing/resets";
import { blockOf, turnExample } from "./testing/examples";

beforeEach(resetCardState);
const CHIP = "Source: policies/fee_schedule_2026.pdf, After-hours dispatch, Effective Jan 1, 2026";

describe("TextCard", () => {
  it("renders one chip for ANSWER_WITH_SOURCE and opens the passage", async () => {
    const res = turnExample("ANSWER_WITH_SOURCE");
    const { container } = renderCard(<><TextCard {...makeProps(blockOf(res, "text"))} /><SourceChipCard {...makeProps(blockOf(res, "source_chip"))} /></>);
    expect(screen.getAllByLabelText(CHIP)).toHaveLength(1);
    await userEvent.setup().click(screen.getByLabelText(CHIP));
    expect(screen.getByText("Where this comes from")).toBeTruthy();
    expect(screen.getByText("After-hours dispatch: $149.")).toBeTruthy();
    expect(container.textContent).not.toContain("2026-01-01");
    expectNo24HourTimes(container);
  });
  it("WP-1: a partial answer keeps its source and then says it has no information", () => {
    const res = partialReply(turnExample("ANSWER_WITH_SOURCE"));
    const props = makeProps(blockOf(res, "no_info"));
    const { container } = renderCard(<><TextCard {...makeProps(blockOf(res, "text"))} /><NoInfoCard {...props} /></>);
    expect(screen.getByText("The after-hours dispatch fee is $149.")).toBeTruthy();
    expect(screen.getByText("I don't have that information.")).toBeTruthy();
    expect((screen.getByRole("button", { name: "Talk to a person" }) as HTMLButtonElement).disabled).toBe(false);
    expectNo24HourTimes(container);
  });
});
