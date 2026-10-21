import { describe, expect, it } from "vitest";
import { ApiError } from "@/api/errors";
import { describe as describeError, MSG } from "./errors";

const api = (status: number, code: string) => new ApiError(status, code, null);
describe("describe()", () => {
  it("any ctx: 404 SESSION_NOT_FOUND and 410 mean the chat is gone", () => {
    for (const ctx of ["start", "turn", "person", "followup"] as const) {
      expect(describeError(api(404, "SESSION_NOT_FOUND"), ctx)).toEqual({ message: MSG.ended, retryable: false, ended: "gone" });
      expect(describeError(api(410, "SESSION_ENDED"), ctx).ended).toBe("gone");
    }
  });
  it("start", () => {
    expect(describeError(api(503, "RESET_IN_PROGRESS"), "start")).toMatchObject({ message: MSG.reset, retryable: true });
    expect(describeError(api(429, "REQUEST_RATE_LIMITED"), "start").message).toBe("Try again in a moment.");
    expect(describeError(new ApiError(0, "NETWORK", null), "start").message).toBe("The chat didn't start. Try again.");
  });
  it("turn", () => {
    expect(describeError(api(503, "RESET_IN_PROGRESS"), "turn").message).toBe(MSG.reset);
    expect(describeError(api(429, "REQUEST_RATE_LIMITED"), "turn").message).toBe("Try again in a moment.");
    for (const e of [new ApiError(0, "NETWORK", null), api(500, "HTTP_500"), api(400, "VALIDATION_ERROR"), api(401, "UNAUTHENTICATED"), api(200, "CONTRACT_DRIFT"), new Error("x")]) {
      expect(describeError(e, "turn")).toEqual({ message: "That didn't send. Your message is still here.", retryable: true, ended: null });
    }
  });
  it("person and followup", () => {
    expect(describeError(api(503, "HANDOFF_FAILED"), "person").message).toBe(MSG.personFailed);
    expect(describeError(api(409, "NOT_ALLOWED_IN_STATE"), "followup")).toEqual({ message: "There's no open request to attach this to.", retryable: false, ended: null });
    expect(describeError(api(500, "HTTP_500"), "followup").message).toBe(MSG.followUpFailed);
  });
});
