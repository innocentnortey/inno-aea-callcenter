import { useState } from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useRowKeys } from "./useRowKeys";

function Harness({ initial, onOpen }: { initial: string[]; onOpen(r: string): void }) {
  const [refs, setRefs] = useState(initial);
  const { cursor } = useRowKeys(refs, { onOpen, enabled: true });
  return (
    <div>
      <p data-testid="cursor">{cursor ?? "none"}</p>
      <input aria-label="typing" />
      <button onClick={() => setRefs(["c", "a", "b"])}>reorder</button>
      <button>focusable</button>
    </div>
  );
}
const cursor = () => screen.getByTestId("cursor").textContent;

describe("useRowKeys", () => {
  it("j and k move the cursor and clamp", () => {
    render(<Harness initial={["a", "b", "c"]} onOpen={() => {}} />);
    fireEvent.keyDown(document.body, { key: "j" });
    expect(cursor()).toBe("a");
    fireEvent.keyDown(document.body, { key: "j" });
    fireEvent.keyDown(document.body, { key: "j" });
    fireEvent.keyDown(document.body, { key: "j" });
    expect(cursor()).toBe("c");
    fireEvent.keyDown(document.body, { key: "k" });
    fireEvent.keyDown(document.body, { key: "k" });
    fireEvent.keyDown(document.body, { key: "k" });
    expect(cursor()).toBe("a");
  });
  it("ignores keys typed in an input", () => {
    render(<Harness initial={["a", "b"]} onOpen={() => {}} />);
    fireEvent.keyDown(screen.getByLabelText("typing"), { key: "j" });
    expect(cursor()).toBe("none");
  });
  it("Enter opens the cursor row when nothing is focused", () => {
    const onOpen = vi.fn();
    render(<Harness initial={["a", "b"]} onOpen={onOpen} />);
    fireEvent.keyDown(document.body, { key: "j" });
    fireEvent.keyDown(document.body, { key: "Enter" });
    expect(onOpen).toHaveBeenCalledWith("a");
  });
  it("Enter does not open when a row button is focused", () => {
    const onOpen = vi.fn();
    render(<Harness initial={["a", "b"]} onOpen={onOpen} />);
    fireEvent.keyDown(document.body, { key: "j" });
    act(() => screen.getByText("focusable").focus());
    fireEvent.keyDown(screen.getByText("focusable"), { key: "Enter" });
    expect(onOpen).not.toHaveBeenCalled();
  });
  it("cursor stays on its reference when rows reorder", () => {
    render(<Harness initial={["a", "b", "c"]} onOpen={() => {}} />);
    fireEvent.keyDown(document.body, { key: "j" });
    fireEvent.keyDown(document.body, { key: "j" });
    expect(cursor()).toBe("b");
    fireEvent.click(screen.getByText("reorder"));
    expect(cursor()).toBe("b");
  });
});
