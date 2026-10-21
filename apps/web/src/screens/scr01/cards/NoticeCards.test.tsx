import { describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FailureOfferCard, NoInfoCard, NoticeCard } from "./NoticeCards";
import { makeProps, renderCard } from "./testing/props";
import { blockOf, turnExample } from "./testing/examples";

const notice = (name: string) => blockOf(turnExample(name), "notice");
const person = () => screen.getByRole("button", { name: "Talk to a person" }) as HTMLButtonElement;

describe("NoticeCards", () => {
  for (const name of ["RATE_LIMITED", "BOOKING_CAP", "SPEND_CAP_REACHED"]) {
    it(`${name}: exact sentence, Talk to a person, no primary`, () => {
      const block = notice(name);
      const { container } = renderCard(<NoticeCard {...makeProps(block)} />);
      expect(screen.getByText(block.text)).toBeTruthy();
      expect(person()).toBeTruthy();
      expect(container.querySelector("button[class*='btn-primary']")).toBeNull();
      expect(container.textContent).not.toMatch(/\bcharged\b/);
    });
  }
  it("TURN_TIMEOUT: heading, Try again retries once while pending", async () => {
    const block = notice("TURN_TIMEOUT");
    let release: () => void = () => {};
    const props = makeProps(block);
    props.dispatch.mockImplementation(() => new Promise<void>((r) => { release = r; }));
    renderCard(<NoticeCard {...props} />);
    expect(screen.getByRole("heading", { name: block.text })).toBeTruthy();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Try again" }));
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(props.dispatch).toHaveBeenCalledTimes(1);
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "retry", turnId: "" });
    release();
  });
  it("BUSY: plain sentence, no heading", () => {
    const block = notice("BUSY");
    renderCard(<NoticeCard {...makeProps(block)} />);
    expect(screen.getByText(block.text)).toBeTruthy();
    expect(screen.queryByRole("heading")).toBeNull();
    expect(person()).toBeTruthy();
  });
  it("AI_PAUSED: one plain line", () => {
    const block = notice("AI_PAUSED");
    renderCard(<NoticeCard {...makeProps(block)} />);
    expect(screen.getByText(block.text)).toBeTruthy();
  });
  it("FAILURE_OFFER and NO_INFO offer a person", () => {
    const f = blockOf(turnExample("FAILURE_OFFER"), "failure_offer");
    renderCard(<FailureOfferCard {...makeProps(f)} />);
    expect(screen.getByText(f.text)).toBeTruthy();
    expect(person()).toBeTruthy();
    const n = blockOf(turnExample("NO_INFO"), "no_info");
    renderCard(<NoInfoCard {...makeProps(n)} />);
    expect(screen.getByText("I don't have that information.")).toBeTruthy();
  });
  it("Talk to a person stays enabled when props.disabled is true, in every card", () => {
    for (const name of ["RATE_LIMITED", "BOOKING_CAP", "SPEND_CAP_REACHED", "TURN_TIMEOUT", "BUSY"]) {
      const { unmount } = renderCard(<NoticeCard {...makeProps(notice(name), { disabled: true, answered: true })} />);
      expect(person().disabled, name).toBe(false);
      unmount();
    }
    const f = renderCard(<FailureOfferCard {...makeProps(blockOf(turnExample("FAILURE_OFFER"), "failure_offer"), { disabled: true })} />);
    expect(person().disabled).toBe(false);
    f.unmount();
    renderCard(<NoInfoCard {...makeProps(blockOf(turnExample("NO_INFO"), "no_info"), { disabled: true })} />);
    expect(person().disabled).toBe(false);
  });
});
