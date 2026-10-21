import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { quickChecksShown } from "@/dev/scenarios/scr01-cards.fixtures";
import { BurningCheckCard, QuickChecksCard, UrgencyQuestionsCard } from "./ChoiceCards";
import { makeProps, renderCard } from "./testing/props";
import { blockOf, turnExample } from "./testing/examples";

describe("BurningCheckCard", () => {
  const block = blockOf(turnExample("BURNING_CHECK"), "burning_check");
  it("offers Yes, No and Not sure and posts the choice", async () => {
    const props = makeProps(block);
    renderCard(<BurningCheckCard {...props} />);
    for (const n of ["Yes", "No", "Not sure"]) expect(screen.getByRole("button", { name: n })).toBeTruthy();
    await userEvent.setup().click(screen.getByRole("button", { name: "No" }));
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "choice", cardId: block.card_id, option: "no" });
  });
  it("answered: all disabled and the choice stays marked", () => {
    renderCard(<BurningCheckCard {...makeProps({ ...block, answered: "no" }, { answered: true })} />);
    for (const b of screen.getAllByRole("button")) expect((b as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByRole("button", { name: "No" }).getAttribute("aria-pressed")).toBe("true");
  });
});

describe("QuickChecksCard", () => {
  it("has exactly one primary button and no list by default", () => {
    const block = blockOf(turnExample("QUICK_CHECKS"), "quick_checks");
    renderCard(<QuickChecksCard {...makeProps(block)} />);
    expect(screen.getByRole("button", { name: "Skip and book" }).className).toContain("btn-primary");
    expect(screen.getByRole("button", { name: "Show the checks" }).className).not.toContain("btn-primary");
    expect(screen.queryByRole("list")).toBeNull();
  });
  it("shown fixture lists two checks, each with a Source chip", () => {
    const block = blockOf(quickChecksShown(turnExample("QUICK_CHECKS")), "quick_checks");
    renderCard(<QuickChecksCard {...makeProps(block)} />);
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(screen.getAllByText("Source")).toHaveLength(2);
  });
});

describe("UrgencyQuestionsCard", () => {
  const block = blockOf(turnExample("URGENCY_QUESTIONS"), "urgency_questions");
  it("posts one turn once every question is answered", async () => {
    const props = makeProps(block);
    renderCard(<UrgencyQuestionsCard {...props} />);
    const user = userEvent.setup();
    const groups = screen.getAllByRole("group");
    expect(groups).toHaveLength(3);
    const pick = async (g: number, name: string) => user.click(Array.from(groups[g].querySelectorAll("button")).find((b) => b.textContent === name)!);
    await pick(0, "Yes");
    await pick(1, "No");
    expect(props.dispatch).not.toHaveBeenCalled();
    await pick(2, "Skip");
    expect(props.dispatch).toHaveBeenCalledTimes(1);
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "choice", cardId: block.card_id, option: "temp:yes;water:no;risk:skip" });
  });
  it("Skip posts skip", async () => {
    const props = makeProps(block);
    renderCard(<UrgencyQuestionsCard {...props} />);
    const skip = block.options.find((o) => o.option === "skip")!;
    // the card-level Skip is the one outside every question group (last in the DOM)
    await userEvent.setup().click(screen.getAllByRole("button", { name: skip.label }).at(-1)!);
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "choice", cardId: block.card_id, option: "skip" });
  });
});
