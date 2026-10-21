import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expectNo24HourTimes } from "@/test/no24h";
import { slotCardUrgent } from "@/dev/scenarios/scr01-cards.fixtures";
import { SlotCard } from "./SlotCard";
import { makeProps, renderCard } from "./testing/props";
import { blockOf, turnExample } from "./testing/examples";

const slots = () => blockOf(turnExample("SLOT_CARD"), "slot_card");

describe("SlotCard", () => {
  it("opens on the first day with windows and offers them as open tiles", () => {
    const { container } = renderCard(<SlotCard {...makeProps(slots())} />);
    expect(screen.getByRole("tab", { selected: true }).textContent).toContain("Wed 21");
    expect(screen.getByRole("button", { name: "8:00 am – 12:00 pm, open" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "12:00 pm – 4:00 pm, open" })).toBeTruthy();
    expect(screen.getByText("Windows are shown, not held.")).toBeTruthy();
    expect((screen.getByRole("button", { name: "Continue with this window" }) as HTMLButtonElement).disabled).toBe(true);
    expectNo24HourTimes(container);
  });
  it("a Full day shows struck-through, disabled Taken tiles", async () => {
    renderCard(<SlotCard {...makeProps(slots())} />);
    await userEvent.setup().click(screen.getByRole("tab", { name: /Mon 19/ }));
    const taken = screen.getAllByRole("button", { name: /taken/ })[0] as HTMLButtonElement;
    expect(taken.disabled).toBe(true);
    expect(taken.textContent).toContain("Taken");
    expect(taken.querySelector(".line-through")).not.toBeNull();
  });
  it("picking a window enables Continue and posts the slot id", async () => {
    const block = slots();
    const props = makeProps(block);
    renderCard(<SlotCard {...props} />);
    const user = userEvent.setup();
    const first = block.days.find((d) => d.open_count > 0)!.windows.find((w) => !w.taken)!;
    const tile = screen.getByRole("button", { name: `${first.window_label}, open` });
    await user.click(tile);
    expect(tile.getAttribute("aria-pressed")).toBe("true");
    const go = screen.getByRole("button", { name: "Continue with this window" });
    expect((go as HTMLButtonElement).disabled).toBe(false);
    await user.click(go);
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "choice", cardId: block.card_id, option: first.slot_id });
  });
  it("answered keeps the chosen tile and disables Continue", () => {
    const base = slots();
    const id = base.days.flatMap((d) => d.windows).find((w) => !w.taken)!.slot_id;
    renderCard(<SlotCard {...makeProps({ ...base, answered: id }, { answered: true })} />);
    expect(screen.getAllByRole("button", { pressed: true })).toHaveLength(1);
    expect((screen.getByRole("button", { name: "Continue with this window" }) as HTMLButtonElement).disabled).toBe(true);
  });
  it("SLOT_CARD_MEMBER tags member-only windows", () => {
    const block = blockOf(turnExample("SLOT_CARD_MEMBER"), "slot_card");
    renderCard(<SlotCard {...makeProps(block)} />);
    expect(screen.getAllByText("Members").length).toBeGreaterThan(0);
    expect(block.members_note).toBeNull();
  });
  it("urgent fixture shows an Urgent tag", () => {
    renderCard(<SlotCard {...makeProps(blockOf(slotCardUrgent(turnExample("SLOT_CARD")), "slot_card"))} />);
    expect(screen.getByText("Urgent")).toBeTruthy();
  });
  it("every tile keeps the 44 px target", () => {
    renderCard(<SlotCard {...makeProps(slots())} />);
    for (const b of screen.getAllByRole("button")) expect(b.className).toContain("min-h-[var(--target-min)]");
  });
});
