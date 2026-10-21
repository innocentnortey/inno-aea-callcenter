import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import type { CallContext } from "@/api/transport";
import type { Role } from "@/lib/roles";
import { jsonResponse } from "@/test/fakeTransport";
import { expectNo24HourTimes } from "@/test/no24h";
import { renderWithProviders } from "@/test/render";
import { mockDesktop } from "../reads/test/mockDesktop";
import { opsTransport, type OpHandler } from "../reads/test/opsTransport";
import { specExample } from "../reads/test/specExample";
import Scr08 from "./Scr08";

function setup(handlers: Record<string, OpHandler> = {}, role: Role = "supervisor") {
  const calls: CallContext[] = [];
  const transport = opsTransport(role, { listFlags: () => jsonResponse(200, specExample("listFlags", "THREE")), ...handlers }, calls);
  const view = renderWithProviders(<Scr08 />, { route: "/staff/flags", transport, role });
  return { ...view, calls };
}
const markBtn = () => screen.findByRole("button", { name: "Mark reviewed, flag on MHC-C-0007" });
beforeEach(() => mockDesktop());

describe("Scr08", () => {
  it("statement is shown", async () => {
    setup();
    await screen.findByText("Nothing on this list changes the knowledge base, prompts or tests. People decide each fix.");
  });

  it("renders the flag row with all columns", async () => {
    setup();
    await screen.findByText("Quoted $144 as the after-hours fee");
    expect(screen.getByText("Answer")).toBeTruthy();
    expect(screen.getByText("Note: Quoted $144 as the fee")).toBeTruthy();
    expect(screen.getByRole("link", { name: "MHC-C-0007" }).getAttribute("href")).toBe("/staff/cases/MHC-C-0007");
    expect(screen.getByRole("link", { name: "Open the message" }).getAttribute("href")).toBe("/staff/cases/MHC-C-0007?tab=conversation&message=m-2");
    expect(screen.getByText("Riley (demo)")).toBeTruthy();
    expect(screen.getByText("New")).toBeTruthy();
    expect(document.querySelectorAll('th[scope="col"]').length).toBe(6);
  });

  it("empty list sentence", async () => {
    setup({ listFlags: () => jsonResponse(200, specExample("listFlags", "EMPTY")) });
    await screen.findByText("No flags yet.");
    expect(screen.getByText(/Staff flag a wrong answer, a brief that left something out, or an escalation that wasn't needed, from any case\./)).toBeTruthy();
  });

  it("loading shows skeletons", async () => {
    setup({ listFlags: () => new Promise<Response>(() => undefined) });
    await screen.findByText(/Nothing on this list changes/);
    expect(document.querySelectorAll("[data-skeleton]").length).toBe(1);
  });

  it("load failure shows the sentence", async () => {
    setup({ listFlags: () => jsonResponse(500, { error: { code: "BOOM" } }) });
    await screen.findByText("The review list didn't load. Try again.");
  });

  it("representative sees disabled buttons and the hint", async () => {
    setup({}, "representative");
    const btn = (await markBtn()) as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
    expect(screen.getByText("Supervisors mark flags reviewed.")).toBeTruthy();
  });

  it("owner can list but not review", async () => {
    setup({}, "owner");
    expect(((await markBtn()) as HTMLButtonElement).disabled).toBe(true);
  });

  it("mark reviewed with a note", async () => {
    const { calls } = setup({ reviewFlag: () => jsonResponse(200, specExample("reviewFlag", "REVIEWED")) });
    fireEvent.click(await markBtn());
    fireEvent.change(screen.getByRole("textbox", { name: /Note/ }), { target: { value: "Fee schedule is right; answer fixed in review" } });
    fireEvent.click(await markBtn());
    await screen.findAllByText("Marked reviewed.");
    const call = calls.find((c) => c.op === "reviewFlag")!;
    expect(call.path).toBe("/api/staff/flags/flg-3");
    expect(call.method).toBe("PATCH");
    expect(call.body).toEqual({ status: "reviewed", note: "Fee schedule is right; answer fixed in review" });
    expect(screen.getByText("Reviewed")).toBeTruthy();
  });

  it("an empty note is sent as null", async () => {
    const { calls } = setup({ reviewFlag: () => jsonResponse(200, specExample("reviewFlag", "REVIEWED")) });
    fireEvent.click(await markBtn());
    fireEvent.click(await markBtn());
    await waitFor(() => expect(calls.find((c) => c.op === "reviewFlag")).toBeTruthy());
    expect(calls.find((c) => c.op === "reviewFlag")!.body).toEqual({ status: "reviewed", note: null });
  });

  it("403 from reviewFlag shows Supervisors mark flags reviewed.", async () => {
    setup({ reviewFlag: () => jsonResponse(403, { error: { code: "ROLE_NOT_ALLOWED", details: null }, request_id: "r" }) });
    fireEvent.click(await markBtn());
    fireEvent.click(await markBtn());
    await screen.findByText("Supervisors mark flags reviewed.");
  });

  it("a flag added by a later read is held back with Show it", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      let n = 0;
      setup({
        listFlags: () => {
          const b = specExample("listFlags", "THREE");
          if (++n > 1) b.flags.push({ ...b.flags[0]!, flag_id: "flg-4", case_ref: "MHC-C-0008", message_id: null });
          return jsonResponse(200, b);
        },
      });
      await screen.findByText("Quoted $144 as the after-hours fee");
      await act(async () => { await vi.advanceTimersByTimeAsync(15_100); });
      await screen.findByText("1 new flag since you opened this page.");
      expect(screen.queryByRole("link", { name: "MHC-C-0008" })).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: "Show it" }));
      await screen.findByRole("link", { name: "MHC-C-0008" });
    } finally {
      vi.useRealTimers();
    }
  });

  it("no automation words", async () => {
    const { container } = setup();
    await screen.findByText("Quoted $144 as the after-hours fee");
    expect(container.textContent).not.toMatch(/learn|updated the model|fixed automatically/i);
  });

  it("no 24-hour times", async () => {
    const { container } = setup();
    await screen.findByText("Quoted $144 as the after-hours fee");
    expectNo24HourTimes(container);
  });
});
