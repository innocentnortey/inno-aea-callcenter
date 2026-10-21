import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { expectNo24HourTimes } from "@/test/no24h";
import { cancelledWithWrite } from "@/dev/scenarios/scr01-cards.fixtures";
import { AppointmentCard, CancelledCard, ConfirmationCard } from "./VisitCards";
import { makeProps, renderCard } from "./testing/props";
import { resetCardState } from "./testing/resets";
import { blockOf, turnExample } from "./testing/examples";

beforeEach(resetCardState);

describe("ConfirmationCard", () => {
  it("BOOKED: hero window, sentence, Booked tag, timeline and landing", () => {
    const res = turnExample("BOOKED");
    const props = makeProps(blockOf(res, "confirmation"), { settled: res.settled });
    const { container } = renderCard(<ConfirmationCard {...props} />);
    const times = Array.from(container.querySelectorAll("time")).map((t) => t.textContent);
    expect(times).toContain("8:00 am");
    expect(times).toContain("12:00 pm");
    expect(screen.getByText("Wednesday, October 21, 2026 · arrives between 8:00 am and 12:00 pm")).toBeTruthy();
    expect(container.querySelector("[data-tone]")?.textContent).toBe("Booked");
    const steps = screen.getAllByRole("listitem");
    expect(steps).toHaveLength(3);
    expect(steps[1].getAttribute("aria-current")).toBe("step");
    expect(props.landed).toHaveBeenCalledTimes(1);
    expect(props.landed).toHaveBeenCalledWith("visit");
    expectNo24HourTimes(container);
  });
  it("no booked write: no Booked tag", () => {
    const res = turnExample("BOOKED");
    const { container } = renderCard(<ConfirmationCard {...makeProps(blockOf(res, "confirmation"), { settled: { ...res.settled, actions: [] } })} />);
    // the "Booked" tag is gated on the write; the timeline's own first step is contract text
    expect(container.querySelector("[data-tone]")).toBeNull();
  });
  it("without settled it still reads the window from the label", () => {
    const res = turnExample("BOOKED");
    const { container } = renderCard(<ConfirmationCard {...makeProps(blockOf(res, "confirmation"))} />);
    expect(Array.from(container.querySelectorAll("time")).map((t) => t.getAttribute("datetime"))).toContain("2026-10-21T08:00:00-05:00");
  });
});

describe("AppointmentCard", () => {
  it("uses the block label and has no timeline", () => {
    const res = turnExample("APPOINTMENT");
    renderCard(<AppointmentCard {...makeProps(blockOf(res, "appointment"), { settled: res.settled })} />);
    expect(screen.getByText("Your booked visit")).toBeTruthy();
    expect(screen.queryByRole("list")).toBeNull();
  });
});

describe("CancelledCard", () => {
  it("says cancelled only with a cancelled write", () => {
    const res = cancelledWithWrite(turnExample("CANCELLED"));
    const props = makeProps(blockOf(res, "cancelled"), { settled: res.settled });
    renderCard(<CancelledCard {...props} />);
    expect(screen.getByText("Your visit on Wed Oct 21 is cancelled.")).toBeTruthy();
    expect(screen.getByText("There's no fee.")).toBeTruthy();
    expect(props.landed).toHaveBeenCalledWith("visit");
  });
  it("without the write only the fee line shows", () => {
    const res = turnExample("CANCELLED");
    const props = makeProps(blockOf(res, "cancelled"), { settled: res.settled });
    const { container } = renderCard(<CancelledCard {...props} />);
    expect(container.textContent).toBe("There's no fee.");
    expect(props.landed).not.toHaveBeenCalled();
  });
});
