import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { expectNo24HourTimes } from "@/test/no24h";
import { changeRequestCancel, changeRequestStaffed } from "@/dev/scenarios/scr01-cards.fixtures";
import { ChangeRequestCard } from "./ChangeRequestCard";
import { makeProps, renderCard } from "./testing/props";
import { resetCardState } from "./testing/resets";
import { blockOf, turnExample } from "./testing/examples";

beforeEach(resetCardState);

describe("ChangeRequestCard", () => {
  it("WP-4: CHANGE_REQUEST shows fee, original-stays and cannot-guarantee once each, and never says charged or sent", () => {
    const res = turnExample("CHANGE_REQUEST");
    const block = blockOf(res, "change_request");
    const { container } = renderCard(<ChangeRequestCard {...makeProps(block, { settled: res.settled })} />);
    for (const sentence of [block.fee_line, block.original_stays_line, block.cant_guarantee_line as string]) {
      expect(screen.getAllByText(sentence, { exact: false }).filter((el) => el.tagName !== "BODY" && el.children.length === 0)).toHaveLength(1);
    }
    expect(container.textContent).not.toMatch(/\bcharged\b|\bsent\b/i);
    expect(container.querySelector("button[type=button]:not([aria-label^='Copy reference'])")).toBeNull();
    expect(screen.getByText("Due")).toBeTruthy();
    expect(screen.getByText("Sat Oct 17 · 12:00 pm")).toBeTruthy();
    expectNo24HourTimes(container);
  });
  it("staffed fixture: no Due row, phone line once", () => {
    const block = blockOf(changeRequestStaffed(turnExample("CHANGE_REQUEST")), "change_request");
    renderCard(<ChangeRequestCard {...makeProps(block)} />);
    expect(screen.queryByText("Due")).toBeNull();
    expect(screen.getAllByText("Phone support is open until 7:00 pm today if you'd like to call.")).toHaveLength(1);
  });
  it("cancel fixture uses the same markup and lands the request", () => {
    const block = blockOf(changeRequestCancel(turnExample("CHANGE_REQUEST")), "change_request");
    const props = makeProps(block);
    renderCard(<ChangeRequestCard {...props} />);
    expect(screen.getByText(block.wanted_text)).toBeTruthy();
    expect(props.landed).toHaveBeenCalledWith("request");
  });
});
