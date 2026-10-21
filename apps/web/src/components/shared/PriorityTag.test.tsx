import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { PriorityTag } from "./PriorityTag";

describe("PriorityTag", () => {
  it("P0 is strong with the word", () => {
    const { container } = render(<PriorityTag priority={{ level: "P0", word: "Safety" }} />);
    expect(container.textContent).toBe("P0 · Safety");
    expect(container.querySelector("[data-tone=strong]")).toBeTruthy();
    expect(container.querySelector("svg")).toBeTruthy();
  });
  it("P1 is strong", () => {
    const { container } = render(<PriorityTag priority={{ level: "P1", word: "Danger" }} />);
    expect(container.textContent).toBe("P1 · Danger");
    expect(container.querySelector("[data-tone=strong]")).toBeTruthy();
  });
  it("P3 is plain with no icon", () => {
    const { container } = render(<PriorityTag priority={{ level: "P3", word: "Standard" }} />);
    expect(container.textContent).toBe("P3 · Standard");
    expect(container.querySelector("[data-tone=plain]")).toBeTruthy();
    expect(container.querySelector("svg")).toBeNull();
  });
});
