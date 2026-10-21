import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expectNo24HourTimes } from "@/test/no24h";
import { handoffGeneralOnly, handoffRefund } from "@/dev/scenarios/scr01-cards.fixtures";
import { HandoffCard } from "./HandoffCard";
import { makeProps, renderCard } from "./testing/props";
import { resetCardState } from "./testing/resets";
import { blockOf, followUpExample, turnExample } from "./testing/examples";

beforeEach(resetCardState);

describe("HandoffCard", () => {
  it("HANDOFF: joined promise, Due, Status tag, reference chip, no countdown", () => {
    const block = blockOf(turnExample("HANDOFF"), "handoff");
    const props = makeProps(block);
    const { container } = renderCard(<HandoffCard {...props} />);
    expect(screen.getByText("No representative is online right now. A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm. Your reference is MHC-C-0007.")).toBeTruthy();
    expect(screen.getByText("Mon Oct 19 · 7:00 pm")).toBeTruthy();
    expect(screen.getByText("Waiting for a representative")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Copy reference MHC-C-0007" })).toBeTruthy();
    expect(container.textContent).not.toMatch(/shortly|queue position|charged|\bsent\b/i);
    expect(props.landed).toHaveBeenCalledWith("request");
    expectNo24HourTimes(container);
  });
  it("HANDOFF_STAFFED: no Due row, no time", () => {
    const { container } = renderCard(<HandoffCard {...makeProps(blockOf(turnExample("HANDOFF_STAFFED"), "handoff"))} />);
    expect(screen.queryByText("Due")).toBeNull();
    expect(container.querySelector("time")).toBeNull();
  });
  it("refund variant reads as one sentence run", () => {
    renderCard(<HandoffCard {...makeProps(blockOf(handoffRefund(turnExample("HANDOFF")), "handoff"))} />);
    expect(screen.getByText("A representative will get to your refund request within 2 business days. I can't promise an outcome. Your reference is MHC-C-0007.")).toBeTruthy();
    expect(screen.queryByText("Due")).toBeNull();
  });
  it("default Save posts email on record, any time", async () => {
    const props = makeProps(blockOf(turnExample("HANDOFF"), "handoff"));
    renderCard(<HandoffCard {...props} />);
    await userEvent.setup().click(screen.getByRole("button", { name: "Save my choice" }));
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "followUp", channel: "email", destination: "on_record", window: "any" });
    expect(props.announce).toHaveBeenCalledWith("Follow-up saved");
  });
  it("phone call asks for a best time and posts it", async () => {
    const block = blockOf(turnExample("HANDOFF"), "handoff");
    const props = makeProps(block);
    renderCard(<HandoffCard {...props} />);
    const user = userEvent.setup();
    expect(screen.queryByText("Best time to call")).toBeNull();
    const phone = block.followup_chooser.channels.find((c) => c.channel === "phone")!;
    await user.click(screen.getByLabelText(phone.label));
    expect(screen.getByText("Best time to call")).toBeTruthy();
    const morn = block.followup_chooser.windows.find((w) => w.window === "morning")!;
    await user.click(screen.getByLabelText(morn.label));
    await user.click(screen.getByRole("button", { name: "Save my choice" }));
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "followUp", channel: "phone", destination: "on_record", window: "morning" });
  });
  it("general_only sends destination general", async () => {
    const props = makeProps(blockOf(handoffGeneralOnly(turnExample("HANDOFF")), "handoff"));
    renderCard(<HandoffCard {...props} />);
    await userEvent.setup().click(screen.getByRole("button", { name: "Save my choice" }));
    expect(props.dispatch).toHaveBeenCalledWith({ kind: "followUp", channel: "email", destination: "general", window: "any" });
  });
  it("saved follow-up shows only the saved line, no radios", () => {
    const saved = followUpExample("PHONE_MORNINGS");
    const props = makeProps(blockOf(turnExample("HANDOFF"), "handoff"), { settled: saved.settled });
    const { container } = renderCard(<HandoffCard {...props} />);
    expect(screen.getByText("Follow-up saved: phone call, the number ending in 02, mornings.")).toBeTruthy();
    expect(container.querySelector("input[type=radio]")).toBeNull();
    expect(screen.queryByRole("button", { name: "Save my choice" })).toBeNull();
  });
});
