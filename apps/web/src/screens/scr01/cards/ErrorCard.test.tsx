import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { ErrorCard } from "./ErrorCard";
import { makeProps, renderCard } from "./testing/props";
import { blockOf, turnExample } from "./testing/examples";

const err = (name: string) => blockOf(turnExample(name), "error");

describe("ErrorCard", () => {
  it("SLOT_TAKEN: the sentence and a fresh slot card", () => {
    const block = err("SLOT_TAKEN");
    renderCard(<ErrorCard {...makeProps(block)} />);
    expect(screen.getByText("Sorry, that window just went. Here are the next open ones.")).toBeTruthy();
    expect(screen.getByText("Choose a window")).toBeTruthy();
    expect(screen.getAllByRole("button", { name: /, open$/ }).length).toBeGreaterThan(0);
  });
  it("OUT_OF_AREA: sentence and a person key", () => {
    const block = err("OUT_OF_AREA");
    renderCard(<ErrorCard {...makeProps(block)} />);
    expect(screen.getByText(block.text)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Talk to a person" })).toBeTruthy();
  });
  it("CODE_WRONG is announced as an alert, with no person key", () => {
    const block = err("CODE_WRONG");
    renderCard(<ErrorCard {...makeProps(block)} />);
    expect(screen.getByRole("alert").textContent).toContain(block.text);
    expect(screen.queryByRole("button")).toBeNull();
  });
  it("NOT_VERIFIED, CODE_LOCKED and CODE_CAP_REACHED render identical markup", () => {
    const html = ["NOT_VERIFIED", "CODE_LOCKED", "CODE_CAP_REACHED"].map((n) => {
      const { container, unmount } = renderCard(<ErrorCard {...makeProps(err(n))} />);
      const out = container.innerHTML;
      unmount();
      return out;
    });
    expect(html[0]).toBe(html[1]);
    expect(html[1]).toBe(html[2]);
  });
});
