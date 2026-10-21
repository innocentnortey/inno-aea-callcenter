import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { CallContext } from "@/api/transport";
import { jsonResponse } from "@/test/fakeTransport";
import { renderWithProviders } from "@/test/render";
import { opsTransport, type OpHandler } from "../reads/test/opsTransport";
import { mockDesktop } from "../reads/test/mockDesktop";
import { specExample } from "../reads/test/specExample";
import { AssignDialog } from "./AssignDialog";

const row = specExample("getOversight", "SEEDED").lanes.unowned.rows[1]!;
function setup(applyCaseAction?: OpHandler) {
  const calls: CallContext[] = [];
  const onDone = vi.fn(async () => undefined);
  const onClose = vi.fn();
  const handlers: Record<string, OpHandler> = { getCase: () => jsonResponse(200, specExample("getCase", "DEFAULT")) };
  if (applyCaseAction) handlers.applyCaseAction = applyCaseAction;
  renderWithProviders(<AssignDialog row={row} onClose={onClose} onDone={onDone} />, {
    route: "/staff/oversight", role: "supervisor", transport: opsTransport("supervisor", handlers, calls),
  });
  return { calls, onDone, onClose };
}
const submitBtn = (name: string) => screen.getByRole("button", { name }) as HTMLButtonElement;
const type = (text: string) => fireEvent.change(screen.getByRole("textbox", { name: /Reason/ }), { target: { value: text } });

beforeEach(() => mockDesktop());

describe("AssignDialog", () => {
  it("Assign stays disabled until a reason is typed", async () => {
    setup();
    await waitFor(() => expect(screen.queryByText(/Loading the case/)).toBeNull());
    expect(submitBtn("Assign").disabled).toBe(true);
    expect(screen.getByRole("textbox", { name: /Reason/ }).getAttribute("aria-required")).toBe("true");
    type("Billing dispute, Riley has the context");
    expect(submitBtn("Assign").disabled).toBe(false);
  });

  it("Assign stays disabled until getCase resolves", async () => {
    const calls: CallContext[] = [];
    renderWithProviders(<AssignDialog row={row} onClose={() => undefined} onDone={async () => undefined} />, {
      role: "supervisor", transport: opsTransport("supervisor", { getCase: () => new Promise<Response>(() => undefined) }, calls),
    });
    type("A reason");
    expect(submitBtn("Assign").disabled).toBe(true);
    expect(screen.getByText(/Loading the case/)).toBeTruthy();
  });

  it("assign sends the exact body and refetches", async () => {
    const { calls, onDone, onClose } = setup(() => jsonResponse(200, specExample("applyCaseAction", "ASSIGNED")));
    await waitFor(() => expect(screen.queryByText(/Loading the case/)).toBeNull());
    type("Billing dispute, Riley has the context");
    fireEvent.click(submitBtn("Assign"));
    await waitFor(() => expect(onDone).toHaveBeenCalledWith("Assigned MHC-C-0007 to Riley (demo)."));
    const call = calls.find((c) => c.op === "applyCaseAction")!;
    expect(call.path).toBe("/api/staff/cases/MHC-C-0007/actions");
    expect(call.body).toEqual({ action: "assign", expected_version: 3, assignee: "riley", reason: "Billing dispute, Riley has the context" });
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it("change priority sends the exact body", async () => {
    const { calls, onDone } = setup(() => jsonResponse(200, specExample("applyCaseAction", "PRIORITY_CHANGED")));
    await waitFor(() => expect(screen.queryByText(/Loading the case/)).toBeNull());
    fireEvent.click(screen.getByRole("radio", { name: "Change priority" }));
    fireEvent.click(screen.getByRole("radio", { name: "P2 · Time-sensitive" }));
    type("Customer reports a second invoice");
    fireEvent.click(submitBtn("Change priority"));
    await waitFor(() => expect(onDone).toHaveBeenCalledWith("Priority of MHC-C-0007 changed to P2 · Time-sensitive."));
    expect(calls.find((c) => c.op === "applyCaseAction")!.body).toEqual({
      action: "change_priority", expected_version: 3, priority: "P2", reason: "Customer reports a second invoice",
    });
  });

  it("422 REASON_REQUIRED shows the sentence", async () => {
    const { onClose } = setup(() => jsonResponse(422, {
      error: { code: "REASON_REQUIRED", field: "reason", constraint: "required for release, assign and change_priority", details: null }, request_id: "req_8f2a41",
    }));
    await waitFor(() => expect(screen.queryByText(/Loading the case/)).toBeNull());
    type("x");
    fireEvent.click(submitBtn("Assign"));
    await screen.findByText("Add a reason to assign this case.");
    expect(onClose).not.toHaveBeenCalled();
  });

  it("409 VERSION_CONFLICT shows who changed it and offers Reload", async () => {
    const { calls } = setup(() => jsonResponse(409, {
      error: { code: "VERSION_CONFLICT", details: { changed_by: "Demo supervisor", changed_at: "2026-10-16T14:31:00-05:00", current_version: 4 } }, request_id: "req_1",
    }));
    await waitFor(() => expect(screen.queryByText(/Loading the case/)).toBeNull());
    type("x");
    fireEvent.click(submitBtn("Assign"));
    await screen.findByText(/This case changed since you opened it \(Demo supervisor at Fri 2:31 pm\)\. Reload to see it\./);
    const before = calls.filter((c) => c.op === "getCase").length;
    fireEvent.click(screen.getByRole("button", { name: "Reload" }));
    await waitFor(() => expect(calls.filter((c) => c.op === "getCase").length).toBe(before + 1));
  });
});
