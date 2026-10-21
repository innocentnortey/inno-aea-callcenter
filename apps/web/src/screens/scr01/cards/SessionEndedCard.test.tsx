import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { BlockOf } from "../contract";
import { SessionEndedCard } from "./SessionEndedCard";
import { makeProps, renderCard } from "./testing/props";
import { chatThreadExample } from "./testing/examples";

describe("SessionEndedCard", () => {
  const thread = chatThreadExample("ENDED_BLOCK");
  const found = JSON.stringify(thread).includes("session_ended");
  const block = (JSON.parse(JSON.stringify(thread)) as { turns: Array<{ blocks?: Array<{ type: string }> }> }).turns
    .flatMap((t) => t.blocks ?? []).find((b) => b.type === "session_ended") as BlockOf<"session_ended"> | undefined;

  it("the ENDED_BLOCK example carries a session_ended block", () => {
    expect(found).toBe(true);
    expect(block).toBeTruthy();
  });
  it("shows the sentence and starts a new chat, even when disabled", async () => {
    const props = makeProps(block!, { disabled: true });
    renderCard(<SessionEndedCard {...props} />);
    expect(screen.getByText(block!.text)).toBeTruthy();
    const b = screen.getByRole("button", { name: block!.new_chat_action }) as HTMLButtonElement;
    expect(b.disabled).toBe(false);
    await userEvent.setup().click(b);
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "newChat" });
  });
});
