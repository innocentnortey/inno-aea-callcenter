import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { WherePromptCard } from "./WherePromptCard";
import { makeProps, renderCard } from "./testing/props";
import { blockOf, turnExample } from "./testing/examples";

describe("WherePromptCard", () => {
  const block = blockOf(turnExample("WHERE_PROMPT"), "where_prompt");
  it("posts the trimmed value as a form", async () => {
    const props = makeProps(block);
    renderCard(<WherePromptCard {...props} />);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(block.label), "  78701 {enter}");
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "form", cardId: block.card_id, values: { zip_or_city: "78701" } });
  });
  it("empty value shows an inline error and posts nothing", async () => {
    const props = makeProps(block);
    renderCard(<WherePromptCard {...props} />);
    await userEvent.setup().click(screen.getByRole("button", { name: block.submit_label }));
    expect(screen.getByText("Enter a ZIP code or city.")).toBeTruthy();
    expect(props.dispatch).not.toHaveBeenCalled();
  });
});
