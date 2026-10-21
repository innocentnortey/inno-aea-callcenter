import { describe, expect, it } from "vitest";
import { turnExample, blockOf } from "../testing/examples";
import { joinPromise } from "./promise";

describe("joinPromise", () => {
  it("HANDOFF reads as one sentence run (UXR-19)", () => {
    expect(joinPromise(blockOf(turnExample("HANDOFF"), "handoff"))).toBe(
      "No representative is online right now. A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm. Your reference is MHC-C-0007.",
    );
  });
  it("HANDOFF_STAFFED carries no time", () => {
    expect(joinPromise(blockOf(turnExample("HANDOFF_STAFFED"), "handoff"))).toBe(
      "A representative will join this chat when available. You can keep chatting with me while you wait, if you like. Your reference is MHC-C-0007.",
    );
  });
  it("CHANGE_REQUEST drops the line shown elsewhere", () => {
    const b = blockOf(turnExample("CHANGE_REQUEST"), "change_request");
    expect(joinPromise(b, [b.cant_guarantee_line])).toBe(
      "No representative is online right now. A representative will get back to you within 1 business day, by Saturday, October 17, 12:00 pm. Your reference is MHC-C-0009.",
    );
  });
  it("refund variant without a due label", () => {
    expect(joinPromise({
      promise_text: "A representative will get to your refund request within 2 business days.",
      due_label: null,
      extra_lines: ["I can't promise an outcome.", "Your reference is MHC-C-0007."],
    })).toBe("A representative will get to your refund request within 2 business days. I can't promise an outcome. Your reference is MHC-C-0007.");
  });
});
