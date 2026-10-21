import { describe, expect, it } from "vitest";
import { ApiError } from "@/api/errors";
import { errorText } from "./errorCopy";

const e = (code: string, details: Record<string, unknown> | null = null) => new ApiError(409, code, null, details);
describe("errorText", () => {
  it("REASON_REQUIRED by action", () => {
    expect(errorText(e("REASON_REQUIRED"), "release", "representative").text).toBe("Add a reason to release this case.");
    expect(errorText(e("REASON_REQUIRED"), "assign", "supervisor").text).toBe("Add a reason to assign this case.");
    expect(errorText(e("REASON_REQUIRED"), "change_priority", "supervisor").text).toBe("Add a reason to change the priority.");
    expect(errorText(e("REASON_REQUIRED"), "close_unresolved", "representative").text).toBe("Add a reason to close this case.");
    expect(errorText(e("REASON_REQUIRED"), "wait", "representative").text).toBe("Add a reason.");
  });
  it("wake-up and outcome", () => {
    expect(errorText(e("WAKE_UP_REQUIRED"), "wait", "representative")).toEqual({ text: "Waiting needs a wake-up time.", offerReload: false });
    expect(errorText(e("OUTCOME_REQUIRED"), "resolve", "representative").text).toBe("Resolving needs an outcome.");
  });
  it("NOT_ALLOWED_IN_STATE and NOT_CLAIMED_BY_YOU", () => {
    expect(errorText(e("NOT_ALLOWED_IN_STATE", { state: "unassigned", needs: "claimed" }), "wait", "representative")).toEqual({ text: "Claim the case first.", offerReload: false });
    expect(errorText(e("NOT_ALLOWED_IN_STATE", { state: "waiting" }), "wait", "representative")).toEqual({ text: "That isn't possible in the case's current state.", offerReload: true });
    expect(errorText(e("NOT_CLAIMED_BY_YOU", { owner: "x" }), "join", "representative").text).toBe("Claim the case first.");
  });
  it("VERSION_CONFLICT with and without details", () => {
    const full = errorText(e("VERSION_CONFLICT", { changed_by: "Demo supervisor", changed_at: "2026-10-16T14:31:00-05:00", current_version: 4 }), "claim", "representative");
    expect(full).toEqual({ text: "This case changed since you opened it (Demo supervisor at 2:31 pm). Reload to see it.", offerReload: true });
    expect(errorText(e("VERSION_CONFLICT"), "claim", "representative").text).toBe("This case changed since you opened it. Reload to see it.");
  });
  it("CASE_ALREADY_CLAIMED", () => {
    expect(errorText(e("CASE_ALREADY_CLAIMED", { claimed_by: "Demo supervisor", claimed_at: "2026-10-16T14:31:00-05:00" }), "claim", "representative"))
      .toEqual({ text: "Already claimed by Demo supervisor at 2:31 pm. Reload.", offerReload: true });
    expect(errorText(e("CASE_ALREADY_CLAIMED", { claimed_by: "Demo supervisor" }), "claim", "representative").text).toBe("Already claimed by Demo supervisor. Reload.");
  });
  it("NOT_LIVE, ROLE_NOT_ALLOWED, CASE_NOT_FOUND and the fallback", () => {
    expect(errorText(e("NOT_LIVE", { reason: "demo_reset" }), "send", "representative").text).toBe("This chat ended because the demo was reset.");
    expect(errorText(e("NOT_LIVE", { reason: "closed" }), "send", "representative").text).toBe("This chat has ended.");
    expect(errorText(e("ROLE_NOT_ALLOWED"), "claim", "owner").text).toBe("You can't do that as Demo business owner.");
    expect(errorText(e("CASE_NOT_FOUND", { reference: "MHC-C-0099" }), "claim", "representative").text).toBe("No case MHC-C-0099. It may have been cleared by a demo reset.");
    expect(errorText(new ApiError(0, "NETWORK", null), "claim", "representative")).toEqual({ text: "That didn't go through. Try again.", offerReload: false });
  });
});
