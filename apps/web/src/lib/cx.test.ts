import { describe, expect, it } from "vitest";
import { cn } from "./cx";

describe("cn", () => {
  it("keeps a colour and a type-scale size together", () => {
    expect(cn("text-[color:var(--btn-primary-text)]", "text-body")).toBe("text-[color:var(--btn-primary-text)] text-body");
    expect(cn("text-text", "text-small")).toBe("text-text text-small");
  });
  it("still resolves real conflicts", () => {
    expect(cn("text-body", "text-small")).toBe("text-small");
    expect(cn("text-text", "text-text-muted")).toBe("text-text-muted");
  });
});
