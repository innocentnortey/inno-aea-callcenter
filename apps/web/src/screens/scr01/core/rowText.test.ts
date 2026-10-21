import { describe, expect, it } from "vitest";
import type { Entry } from "./model";
import { customerRowText } from "./rowText";

const entries: Entry[] = [{
  kind: "reply", id: "r", live: true,
  blocks: [{ block_id: "b", type: "quick_checks", card_id: "qc-1", options: [{ option: "skip_and_book", label: "Skip and book", disabled: false, reason: null }] } as unknown as Extract<Entry, { kind: "reply" }>["blocks"][number]],
}];
describe("customerRowText", () => {
  it("applies the five rules and never echoes code or form values", () => {
    expect(customerRowText({ kind: "text", text: "  hello " }, [])).toBe("hello");
    expect(customerRowText({ kind: "choice", cardId: "qc-1", option: "skip_and_book" }, entries)).toBe("Skip and book");
    expect(customerRowText({ kind: "choice", cardId: "zzz", option: "x" }, entries)).toBe("Choice sent");
    expect(customerRowText({ kind: "code", cardId: "code-1", code: "123456" }, [])).toBe("Code entered");
    expect(customerRowText({ kind: "form", cardId: "loc-1", values: { phone: "555" } }, [])).toBe("Details sent");
    expect(customerRowText({ kind: "person" }, [])).toBe("Talk to a person");
  });
});
