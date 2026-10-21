import { describe, expect, it, vi } from "vitest";
import { useState } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Dialog } from "./Dialog";

function Harness({ onClose }: { onClose?: () => void }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button onClick={() => setOpen(true)}>Open</button>
      <Dialog open={open} onClose={() => { setOpen(false); onClose?.(); }} title="Example">
        <button>Inside</button>
      </Dialog>
    </>
  );
}

describe("Dialog", () => {
  it("calls showModal when opened", async () => {
    const spy = vi.spyOn(HTMLDialogElement.prototype, "showModal");
    render(<Harness />);
    await userEvent.click(screen.getByText("Open"));
    expect(spy).toHaveBeenCalled();
  });
  it("closes on the native close event (Escape) and returns focus to the opener", async () => {
    const onClose = vi.fn();
    const { container } = render(<Harness onClose={onClose} />);
    const opener = screen.getByText("Open");
    opener.focus();
    await userEvent.click(opener);
    const dialog = container.querySelector("dialog") as HTMLDialogElement;
    expect(dialog.hasAttribute("open")).toBe(true);
    fireEvent(dialog, new Event("close"));
    expect(onClose).toHaveBeenCalled();
    expect(document.activeElement).toBe(opener);
  });
  it("has the title as its accessible name", async () => {
    const { container } = render(<Harness />);
    await userEvent.click(screen.getByText("Open"));
    const d = container.querySelector("dialog")!;
    expect(document.getElementById(d.getAttribute("aria-labelledby")!)?.textContent).toBe("Example");
  });
});
