import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CodePromptCard } from "./CodePromptCard";
import { makeProps, renderCard } from "./testing/props";
import { resetCardState } from "./testing/resets";
import { blockOf, turnExample } from "./testing/examples";

beforeEach(resetCardState);
const sent = () => blockOf(turnExample("CODE_SENT"), "code_prompt");

describe("CodePromptCard", () => {
  it("CODE_SENT: labelled numeric one-time-code field and the inbox link", () => {
    const block = sent();
    renderCard(<CodePromptCard {...makeProps(block)} />);
    const input = screen.getByLabelText("6-digit code") as HTMLInputElement;
    expect(input.getAttribute("inputmode")).toBe("numeric");
    expect(input.getAttribute("autocomplete")).toBe("one-time-code");
    const link = screen.getByRole("link", { name: /Open the demo inbox/ });
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("href")).toBe(block.inbox_link);
    expect(screen.getByText(/never a real phone/)).toBeTruthy();
  });
  it("typing six digits posts the code and clears the field", async () => {
    const block = sent();
    const props = makeProps(block);
    renderCard(<CodePromptCard {...props} />);
    const user = userEvent.setup();
    const input = screen.getByLabelText("6-digit code") as HTMLInputElement;
    await user.type(input, "482913");
    await user.click(screen.getByRole("button", { name: "Verify" }));
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "code", cardId: block.card_id, code: "482913" });
    expect(input.value).toBe("");
  });
  it("five digits show an inline error and post nothing", async () => {
    const props = makeProps(sent());
    renderCard(<CodePromptCard {...props} />);
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("6-digit code"), "48291");
    await user.click(screen.getByRole("button", { name: "Verify" }));
    expect(screen.getByText("Enter the 6-digit code.")).toBeTruthy();
    expect(props.dispatch).not.toHaveBeenCalled();
  });
  it("CODE_WRONG: field is invalid and takes focus once", () => {
    const block = blockOf(turnExample("CODE_WRONG"), "code_prompt");
    renderCard(<CodePromptCard {...makeProps(block)} />);
    const input = screen.getByLabelText("6-digit code");
    expect(input.getAttribute("aria-invalid")).toBe("true");
    expect(document.activeElement).toBe(input);
  });
  it("CODE_EXPIRED: Send a new code resends, no Verify, field disabled", async () => {
    const block = blockOf(turnExample("CODE_EXPIRED"), "code_prompt");
    const props = makeProps(block);
    renderCard(<CodePromptCard {...props} />);
    expect(screen.queryByRole("button", { name: "Verify" })).toBeNull();
    expect((screen.getByLabelText("6-digit code") as HTMLInputElement).disabled).toBe(true);
    await userEvent.setup().click(screen.getByRole("button", { name: "Send a new code" }));
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "choice", cardId: block.card_id, option: "resend" });
  });
  it("expired without resend offered has no resend button", () => {
    const block = { ...blockOf(turnExample("CODE_EXPIRED"), "code_prompt"), resend_offered: false };
    renderCard(<CodePromptCard {...makeProps(block)} />);
    expect(screen.queryByRole("button", { name: /new code/i })).toBeNull();
  });
  it("locked: field disabled, no Verify, no resend, no inbox link", () => {
    renderCard(<CodePromptCard {...makeProps({ ...sent(), state: "locked" })} />);
    expect((screen.getByLabelText("6-digit code") as HTMLInputElement).disabled).toBe(true);
    expect(screen.queryByRole("button", { name: "Verify" })).toBeNull();
    expect(screen.queryByRole("link")).toBeNull();
  });
});
