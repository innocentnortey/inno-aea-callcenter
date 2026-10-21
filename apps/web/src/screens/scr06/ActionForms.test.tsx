import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AssignForm, CloseForm, ContactForm, FlagForm, PriorityForm, ReleaseForm, ResolveForm, WaitForm, type FormProps } from "./ActionForms";

const mk = () => ({ onSubmit: vi.fn(), onCancel: vi.fn(), busy: false, version: 3 }) satisfies FormProps;
const type = (label: string, value: string) => fireEvent.change(screen.getByLabelText(label), { target: { value } });

describe("ActionForms", () => {
  it("Release posts the reason", () => {
    const p = mk(); render(<ReleaseForm {...p} />);
    type("Reason", "Not my area");
    fireEvent.click(screen.getByRole("button", { name: "Release" }));
    expect(p.onSubmit).toHaveBeenCalledWith({ kind: "case", body: { action: "release", expected_version: 3, reason: "Not my area" } });
  });
  it("Resolve and Close post their fields", () => {
    const a = mk(); const { unmount } = render(<ResolveForm {...a} />);
    type("Outcome", "Credit recorded");
    fireEvent.click(screen.getByRole("button", { name: "Resolve" }));
    expect(a.onSubmit).toHaveBeenCalledWith({ kind: "case", body: { action: "resolve", expected_version: 3, outcome: "Credit recorded" } });
    unmount();
    const b = mk(); render(<CloseForm {...b} />);
    type("Reason", "Duplicate");
    fireEvent.click(screen.getByRole("button", { name: "Close unresolved" }));
    expect(b.onSubmit).toHaveBeenCalledWith({ kind: "case", body: { action: "close_unresolved", expected_version: 3, reason: "Duplicate" } });
  });
  it("Wait posts a Chicago wake-up time and omits it when the time is empty", () => {
    const p = mk(); render(<WaitForm {...p} nowIso="2026-10-16T14:20:00-05:00" />);
    type("Wake-up date", "2026-10-19");
    fireEvent.click(screen.getByRole("button", { name: "Set waiting" }));
    expect(p.onSubmit).toHaveBeenLastCalledWith({ kind: "case", body: { action: "wait", expected_version: 3 } });
    type("Wake-up time", "09:00");
    type("Reason (optional)", "Customer asked");
    fireEvent.click(screen.getByRole("button", { name: "Set waiting" }));
    expect(p.onSubmit).toHaveBeenLastCalledWith({ kind: "case", body: { action: "wait", expected_version: 3, wake_up_at: "2026-10-19T09:00:00-05:00", reason: "Customer asked" } });
  });
  it("Contact posts kind, outcome, note and version", () => {
    const p = mk(); render(<ContactForm {...p} kind="call" />);
    fireEvent.click(screen.getByLabelText("Reached the customer"));
    type("Note", "Explained the credit review");
    fireEvent.click(screen.getByRole("button", { name: "Record" }));
    expect(p.onSubmit).toHaveBeenCalledWith({ kind: "contact", body: { kind: "call", outcome: "reached", note: "Explained the credit review", expected_version: 3 } });
    expect(screen.getByText("Demo: recorded, not sent. No call is placed.")).toBeTruthy();
  });
  it("Flag posts the case reference, target and the last assistant message", () => {
    const p = mk(); render(<FlagForm {...p} reference="MHC-C-0007" lastAssistantMessageId="m-2" />);
    fireEvent.click(screen.getByLabelText("An answer was wrong"));
    type("Note", "Quoted $144");
    fireEvent.click(screen.getByRole("button", { name: "Add to review list" }));
    expect(p.onSubmit).toHaveBeenCalledWith({ kind: "flag", body: { case_ref: "MHC-C-0007", target: "answer", reason: "Quoted $144", message_id: "m-2" } });
  });
  it("Assign and Priority post their fields", () => {
    const a = mk(); const { unmount } = render(<AssignForm {...a} />);
    type("Reason", "Has the context");
    fireEvent.click(screen.getByRole("button", { name: "Assign" }));
    expect(a.onSubmit).toHaveBeenCalledWith({ kind: "case", body: { action: "assign", expected_version: 3, assignee: "riley", reason: "Has the context" } });
    unmount();
    const b = mk(); render(<PriorityForm {...b} />);
    type("Priority", "P2");
    type("Reason", "Second invoice");
    fireEvent.click(screen.getByRole("button", { name: "Change priority" }));
    expect(b.onSubmit).toHaveBeenCalledWith({ kind: "case", body: { action: "change_priority", expected_version: 3, priority: "P2", reason: "Second invoice" } });
  });
  it("Escape cancels", () => {
    const p = mk(); render(<ReleaseForm {...p} />);
    fireEvent.keyDown(screen.getByLabelText("Reason"), { key: "Escape" });
    expect(p.onCancel).toHaveBeenCalled();
  });
  it("first field is focused", () => {
    render(<ReleaseForm {...mk()} />);
    expect(document.activeElement).toBe(screen.getByLabelText("Reason"));
  });
});
