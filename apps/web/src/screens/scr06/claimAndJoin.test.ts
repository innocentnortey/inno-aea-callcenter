import { afterEach, describe, expect, it } from "vitest";
import { defaultCase, claimedResponse, joinedResponse, apiErrorBody, fakeApi, ok } from "./case.fixtures";
import { setTransport, defaultTransport } from "@/api/transport";
import { ClaimedNotJoinedError, claimAndJoin } from "./claimAndJoin";

afterEach(() => setTransport(defaultTransport));
const install = (h: Parameters<typeof fakeApi>[1]) => { const api = fakeApi("representative", h); setTransport(api.transport); return api; };

describe("claimAndJoin", () => {
  it("claims with the case version then joins", async () => {
    const { calls } = install((ctx) => ctx.op === "getCase" ? ok(defaultCase()) : ctx.op === "applyCaseAction" ? ok(claimedResponse()) : ctx.op === "liveChatAction" ? ok(joinedResponse()) : undefined);
    const r = await claimAndJoin("MHC-C-0012");
    expect(calls.map((c) => c.op)).toEqual(["getCase", "applyCaseAction", "liveChatAction"]);
    expect(calls[1].body).toEqual({ action: "claim", expected_version: 3 });
    expect(calls[2].body).toEqual({ action: "join" });
    expect(r.join.live.state).toBe("joined");
  });
  it("does not join when the claim fails", async () => {
    const { calls } = install((ctx) => ctx.op === "applyCaseAction" ? ok(apiErrorBody("applyCaseAction", "409", "CASE_ALREADY_CLAIMED"), 409) : undefined);
    await expect(claimAndJoin("MHC-C-0012", 3)).rejects.toMatchObject({ code: "CASE_ALREADY_CLAIMED" });
    expect(calls.map((c) => c.op)).toEqual(["applyCaseAction"]);
  });
  it("a failed join after a good claim throws ClaimedNotJoinedError carrying the claim", async () => {
    install((ctx) => ctx.op === "applyCaseAction" ? ok(claimedResponse()) : ctx.op === "liveChatAction" ? ok(apiErrorBody("liveChatAction", "409", "NOT_LIVE"), 409) : undefined);
    const err = await claimAndJoin("MHC-C-0012", 3).catch((e) => e);
    expect(err).toBeInstanceOf(ClaimedNotJoinedError);
    expect(err.claim.case.version).toBe(4);
    expect(err.joinError).toMatchObject({ code: "NOT_LIVE" });
  });
  it("uses the known version without calling getCase", async () => {
    const { calls } = install((ctx) => ctx.op === "applyCaseAction" ? ok(claimedResponse()) : ctx.op === "liveChatAction" ? ok(joinedResponse()) : undefined);
    await claimAndJoin("MHC-C-0012", 7);
    expect(calls[0].body).toEqual({ action: "claim", expected_version: 7 });
    expect(calls.some((c) => c.op === "getCase")).toBe(false);
  });
});
