import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { turnExample } from "../testing/examples";
import { PersonKey, hasWrite, choiceKept } from "./CardParts";

describe("CardParts", () => {
  it("PersonKey is enabled and dispatches person", async () => {
    const dispatch = vi.fn().mockResolvedValue(undefined);
    render(<PersonKey dispatch={dispatch} />);
    const b = screen.getByRole("button", { name: "Talk to a person" }) as HTMLButtonElement;
    expect(b.disabled).toBe(false);
    await userEvent.setup().click(b);
    expect(dispatch).toHaveBeenCalledWith({ kind: "person" });
  });
  it("hasWrite reads settled.actions", () => {
    const s = turnExample("BOOKED").settled;
    expect(hasWrite(s, "booked")).toBe(true);
    expect(hasWrite(s, "cancelled")).toBe(false);
    expect(hasWrite(null, "booked")).toBe(false);
  });
  it("choiceKept is true from either source", () => {
    expect(choiceKept({ answered: null }, { answered: false })).toBe(false);
    expect(choiceKept({ answered: "no" }, { answered: false })).toBe(true);
    expect(choiceKept({ answered: null }, { answered: true })).toBe(true);
  });
});
