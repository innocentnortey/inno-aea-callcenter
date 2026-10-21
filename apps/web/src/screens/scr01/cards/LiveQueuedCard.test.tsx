import { beforeEach, describe, expect, it } from "vitest";
import { screen } from "@testing-library/react";
import { LiveQueuedCard } from "./LiveQueuedCard";
import { makeProps, renderCard } from "./testing/props";
import { resetCardState } from "./testing/resets";
import { blockOf, turnExample } from "./testing/examples";

beforeEach(resetCardState);

describe("LiveQueuedCard", () => {
  it("three steps, the second is current", () => {
    const res = turnExample("LIVE_QUEUED");
    renderCard(<LiveQueuedCard {...makeProps(blockOf(res, "live_queued"))} />);
    const steps = screen.getAllByRole("listitem");
    expect(steps).toHaveLength(3);
    expect(steps[1].getAttribute("aria-current")).toBe("step");
  });
  it("a human replying makes the second step done", () => {
    const res = turnExample("LIVE_QUEUED");
    const settled = { ...res.settled, replying: { kind: "human" as const, display_name: "Riley" } };
    renderCard(<LiveQueuedCard {...makeProps(blockOf(res, "live_queued"), { settled })} />);
    const steps = screen.getAllByRole("listitem");
    expect(steps[1].getAttribute("aria-current")).toBeNull();
    expect(steps[2].getAttribute("aria-current")).toBe("step");
  });
});
