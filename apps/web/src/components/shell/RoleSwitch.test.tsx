import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/render";
import { makeFakeTransport, jsonResponse } from "@/test/fakeTransport";
import { SESSION_REPRESENTATIVE } from "@/test/fixtures";
import { RoleSwitch } from "./RoleSwitch";

describe("RoleSwitch", () => {
  it("is a radiogroup named Acting as with four radios in order, current marked", async () => {
    renderWithProviders(<RoleSwitch />, { role: "representative" });
    const group = await screen.findByRole("radiogroup", { name: "Acting as" });
    await waitFor(() => expect(screen.getAllByRole("radio").some((r) => r.getAttribute("aria-checked") === "true")).toBe(true));
    const radios = screen.getAllByRole("radio");
    expect(group).toBeTruthy();
    expect(radios.map((r) => r.getAttribute("aria-label"))).toEqual([
      "Customer (demo)", "Riley, demo representative, current", "Demo supervisor", "Demo business owner",
    ]);
    expect(radios[1].getAttribute("aria-checked")).toBe("true");
  });

  it("disables all four while switching and shows Switching", async () => {
    let release: (r: Response) => void = () => undefined;
    const t = makeFakeTransport((ctx) => {
      if (ctx.op === "getSession") return jsonResponse(200, SESSION_REPRESENTATIVE);
      if (ctx.op === "switchRole") return new Promise<Response>((res) => { release = res; });
      return jsonResponse(200, {});
    });
    renderWithProviders(<RoleSwitch />, { transport: t });
    await waitFor(() => expect(screen.getByRole("radio", { name: /current/ })).toBeTruthy());
    await userEvent.click(screen.getByRole("radio", { name: "Demo supervisor" }));
    await waitFor(() => expect(screen.getAllByRole("radio").every((r) => r.hasAttribute("disabled"))).toBe(true));
    expect(screen.getByText(/Switching/)).toBeTruthy();
    release(jsonResponse(200, SESSION_REPRESENTATIVE));
  });

  it("shows the error line when the switch fails", async () => {
    const t = makeFakeTransport((ctx) => {
      if (ctx.op === "getSession") return jsonResponse(200, SESSION_REPRESENTATIVE);
      return jsonResponse(503, { error: { code: "RESET_IN_PROGRESS" } });
    });
    renderWithProviders(<RoleSwitch />, { transport: t });
    await waitFor(() => expect(screen.getByRole("radio", { name: /current/ })).toBeTruthy());
    await userEvent.click(screen.getByRole("radio", { name: "Demo supervisor" }));
    expect(await screen.findByText("Couldn't switch role. Try again.")).toBeTruthy();
  });
});
