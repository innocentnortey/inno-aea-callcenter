import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LocatePromptCard } from "./LocatePromptCard";
import { makeProps, renderCard } from "./testing/props";
import { blockOf, turnExample } from "./testing/examples";

describe("LocatePromptCard", () => {
  const block = blockOf(turnExample("LOCATE_PROMPT"), "locate_prompt");
  it("starts with name and phone and the demo hint", () => {
    renderCard(<LocatePromptCard {...makeProps(block)} />);
    expect(screen.getByLabelText("Name on the account")).toBeTruthy();
    expect((screen.getByLabelText("Phone") as HTMLInputElement).type).toBe("tel");
    expect(screen.getByRole("button", { name: "Send the code" })).toBeTruthy();
    expect(screen.getByText(/never a real phone/)).toBeTruthy();
  });
  it("missing fields show an error", async () => {
    const props = makeProps(block);
    renderCard(<LocatePromptCard {...props} />);
    await userEvent.setup().click(screen.getByRole("button", { name: "Send the code" }));
    expect(screen.getByText("Fill in every field above.")).toBeTruthy();
    expect(props.dispatch).not.toHaveBeenCalled();
  });
  it("switching to the customer ID set posts only customer_id", async () => {
    const props = makeProps(block);
    renderCard(<LocatePromptCard {...props} />);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Name on the account"), "Omar Patel");
    await user.click(screen.getByRole("button", { name: "Use my customer ID instead" }));
    await user.type(screen.getByLabelText("Customer ID"), "C-1001");
    await user.click(screen.getByRole("button", { name: "Send the code" }));
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "form", cardId: block.card_id, values: { customer_id: "C-1001" } });
  });
});
