import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { startExample } from "../testFixtures";
import { Composer, type ComposerProps } from "./Composer";

const original = window.matchMedia;
afterEach(() => { window.matchMedia = original; });
const laptop = (on: boolean) => { window.matchMedia = ((q: string) => ({ matches: on && q.includes("pointer"), media: q, addEventListener: () => {}, removeEventListener: () => {} })) as unknown as typeof window.matchMedia; };
const make = (over: Partial<ComposerProps> = {}) => {
  const dispatch = vi.fn(async () => undefined);
  const props: ComposerProps = { lock: null, pending: false, replying: { kind: "ai", display_name: null }, limits: startExample().limits, dispatch, ...over };
  render(<Composer {...props} />);
  return dispatch;
};
const field = () => screen.getByRole("textbox") as HTMLTextAreaElement;
const person = () => screen.getByRole("button", { name: "Talk to a person" }) as HTMLButtonElement;
const send = () => screen.getByRole("button", { name: "Send" }) as HTMLButtonElement;

describe("Composer", () => {
  it("Send is disabled until there is text, and while a reply is pending; the field stays editable", async () => {
    make({ pending: true });
    expect(send().disabled).toBe(true);
    await userEvent.type(field(), "hello");
    expect(field().disabled).toBe(false);
    expect(send().disabled).toBe(true);
  });
  it("sends text and clears the field", async () => {
    const dispatch = make();
    expect(send().disabled).toBe(true);
    await userEvent.type(field(), "hello");
    await userEvent.click(send());
    expect(dispatch).toHaveBeenCalledWith({ kind: "text", text: "hello" });
    expect(field().value).toBe("");
  });
  it("keeps the typed text when the chat refuses the send", async () => {
    const dispatch = make({ canSend: () => false });
    await userEvent.type(field(), "hello");
    await userEvent.click(send());
    expect(dispatch).not.toHaveBeenCalled();
    expect(field().value).toBe("hello");
  });
  it("Talk to a person is enabled in every non-ended state and comes first in the tab order", async () => {
    for (const lock of [null, { reason: "rate" as const, hint: "limit" }, { reason: "spend" as const, hint: "cap" }, { reason: "starting" as const, hint: "" }]) {
      const { unmount } = render(<Composer lock={lock} pending replying={{ kind: "ai", display_name: null }} limits={null} dispatch={vi.fn(async () => undefined)} />);
      expect((screen.getByRole("button", { name: "Talk to a person" }) as HTMLButtonElement).disabled).toBe(false);
      unmount();
    }
    make();
    await userEvent.tab();
    expect(document.activeElement).toBe(person());
    await userEvent.tab();
    expect(document.activeElement).toBe(field());
  });
  it("rate lock disables the field and shows the sentence, key stays", () => {
    make({ lock: { reason: "rate", hint: "I can't take more messages in this chat right now." } });
    expect(field().disabled).toBe(true);
    expect(screen.getByText("I can't take more messages in this chat right now.")).toBeTruthy();
    expect(person().disabled).toBe(false);
  });
  it("ended swaps the key for Start a new chat and disables the field", async () => {
    const dispatch = make({ lock: { reason: "ended", hint: "This chat has ended." } });
    expect(screen.queryByRole("button", { name: "Talk to a person" })).toBeNull();
    expect(field().disabled).toBe(true);
    expect(screen.getByText("This chat has ended.")).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Start a new chat" }));
    expect(dispatch).toHaveBeenCalledWith({ kind: "newChat" });
  });
  it("takes max length from the limits and the placeholder from who is replying", () => {
    make({ replying: { kind: "human", display_name: "Riley" } });
    expect(field().maxLength).toBe(2000);
    expect(field().placeholder).toBe("Message Riley");
    expect(screen.getByLabelText("Message to Riley")).toBe(field());
  });
  it("Enter sends only on a laptop; on a phone it adds a newline", () => {
    laptop(true);
    const dispatch = make();
    fireEvent.change(field(), { target: { value: "hi" } });
    fireEvent.keyDown(field(), { key: "Enter" });
    expect(dispatch).toHaveBeenCalledWith({ kind: "text", text: "hi" });
    fireEvent.change(field(), { target: { value: "a" } });
    fireEvent.keyDown(field(), { key: "Enter", shiftKey: true });
    expect(dispatch).toHaveBeenCalledTimes(1);
  });
  it("Enter does not send on a phone", () => {
    laptop(false);
    const dispatch = make();
    fireEvent.change(field(), { target: { value: "hi" } });
    fireEvent.keyDown(field(), { key: "Enter" });
    expect(dispatch).not.toHaveBeenCalled();
  });
  it("focuses the field on a laptop and not on a phone", () => {
    laptop(true);
    make();
    expect(document.activeElement).toBe(field());
  });
  it("does not focus the field on a phone", () => {
    laptop(false);
    make();
    expect(document.activeElement).not.toBe(field());
  });
});
