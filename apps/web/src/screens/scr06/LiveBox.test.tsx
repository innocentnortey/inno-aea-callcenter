import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LiveBox } from "./LiveBox";

const props = { ownerName: "Riley", onSend: async () => true, onHandBack: () => {}, onClose: () => {}, endedByReset: false, busy: false };
describe("LiveBox", () => {
  it("active shows the reply label with the owner name", () => {
    render(<LiveBox {...props} mode="active" />);
    expect(screen.getByText("You are replying as Riley (demo representative). The assistant is paused.")).toBeTruthy();
    expect(screen.getByLabelText("Reply")).toBeTruthy();
  });
  it("send posts text and clears the field", async () => {
    const onSend = vi.fn().mockResolvedValue(true);
    render(<LiveBox {...props} mode="active" onSend={onSend} />);
    fireEvent.change(screen.getByLabelText("Reply"), { target: { value: "Hello Omar" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    expect(onSend).toHaveBeenCalledWith("Hello Omar");
    await waitFor(() => expect((screen.getByLabelText("Reply") as HTMLTextAreaElement).value).toBe(""));
  });
  it("disabled after hand back", () => {
    render(<LiveBox {...props} mode="disabled" />);
    expect(screen.getByText("This chat is no longer live.")).toBeTruthy();
    expect((screen.getByRole("button", { name: "Send" }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: "Hand back to the assistant" }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByRole("button", { name: "Close the chat" }) as HTMLButtonElement).disabled).toBe(true);
  });
  it("reset message replaces the field", () => {
    render(<LiveBox {...props} mode="active" endedByReset />);
    expect(screen.getByText("This chat ended because the demo was reset.")).toBeTruthy();
    expect(screen.queryByLabelText("Reply")).toBeNull();
  });
});
