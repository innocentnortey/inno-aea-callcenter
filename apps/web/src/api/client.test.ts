import { afterEach, beforeEach, describe, expect, expectTypeOf, it, vi } from "vitest";
import { callOp, OPS, type OkBody, type ReqBody, type PathParams } from "./client";
import { ApiError } from "./errors";
import { defaultTransport, setTransport } from "./transport";
import { onAuthLost } from "./refetch";
import { jsonResponse, makeFakeTransport } from "@/test/fakeTransport";
import type { components } from "./types.gen";

afterEach(() => setTransport(defaultTransport));

describe("callOp", () => {
  it("encodes path params", async () => {
    const urls: string[] = [];
    setTransport(makeFakeTransport((_c, url) => { urls.push(url); return jsonResponse(200, {}); }));
    await callOp("getCase", { path: { reference: "MHC-C-0007" } });
    await callOp("getCase", { path: { reference: "a/b c" } });
    expect(urls).toEqual(["/api/staff/cases/MHC-C-0007", "/api/staff/cases/a%2Fb%20c"]);
  });
  it("rejects a missing path param before any request", async () => {
    const fetchSpy = vi.fn();
    setTransport(makeFakeTransport((...a) => { fetchSpy(...a); return jsonResponse(200, {}); }));
    await expect(callOp("getCase", { path: { reference: "" } })).rejects.toMatchObject({ code: "MISSING_PARAM" });
    expect(fetchSpy).not.toHaveBeenCalled();
  });
  it("returns undefined on 204", async () => {
    setTransport(makeFakeTransport(() => jsonResponse(204)));
    await expect(callOp("logout")).resolves.toBeUndefined();
  });
  it("returns the 201 body", async () => {
    setTransport(makeFakeTransport(() => jsonResponse(201, { thread_id: "t1" })));
    await expect(callOp("startChatSession")).resolves.toEqual({ thread_id: "t1" });
  });
  it("sends the body as JSON with credentials", async () => {
    let seen: { init?: RequestInit } = {};
    setTransport(makeFakeTransport((_c, _u, init) => { seen = { init }; return jsonResponse(200, {}); }));
    await callOp("switchRole", { body: { role: "owner" } });
    expect(seen.init?.method).toBe("PUT");
    expect(seen.init?.credentials).toBe("include");
    expect(seen.init?.body).toBe('{"role":"owner"}');
    expect((seen.init?.headers as Record<string, string>)["Content-Type"]).toBe("application/json");
  });
  it("throws a typed ApiError on a named error", async () => {
    setTransport(makeFakeTransport(() => jsonResponse(404, { error: { code: "CASE_NOT_FOUND" }, request_id: "r1" })));
    const err = await callOp("getCase", { path: { reference: "x" } }).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ status: 404, code: "CASE_NOT_FOUND", requestId: "r1" });
  });
  it("emits auth lost on 401 UNAUTHENTICATED with the expired reason, not for login", async () => {
    const seen: string[] = [];
    const off = onAuthLost((r) => seen.push(r));
    setTransport(makeFakeTransport(() => jsonResponse(401, { error: { code: "UNAUTHENTICATED", details: { reason: "expired" } } })));
    await expect(callOp("getSession")).rejects.toMatchObject({ isUnauthenticated: true });
    setTransport(makeFakeTransport(() => jsonResponse(401, { error: { code: "UNAUTHENTICATED" } })));
    await expect(callOp("getSession")).rejects.toBeInstanceOf(ApiError);
    setTransport(makeFakeTransport(() => jsonResponse(401, { error: { code: "UNAUTHENTICATED" } })));
    await expect(callOp("login", { body: { username: "a", password: "b" } })).rejects.toBeInstanceOf(ApiError);
    off();
    expect(seen).toEqual(["expired", "none"]);
  });
  it("maps a network failure to ApiError(0, NETWORK)", async () => {
    setTransport(makeFakeTransport(() => { throw new TypeError("Failed to fetch"); }));
    await expect(callOp("getSession")).rejects.toMatchObject({ status: 0, code: "NETWORK" });
  });
  it("returns a composed error (HTTP 200) instead of throwing", async () => {
    const body = { blocks: [{ type: "error", code: "SLOT_TAKEN" }] };
    setTransport(makeFakeTransport(() => jsonResponse(200, body)));
    await expect(callOp("getChatThread", { path: { thread_id: "t" } })).resolves.toEqual(body);
  });
  it("carries the operation metadata", () => {
    expect(OPS.getQueue.roles).toEqual(["representative", "supervisor"]);
    expect(OPS.reviewFlag.method).toBe("PATCH");
    expect(Object.keys(OPS)).toHaveLength(30);
  });
});

describe("types", () => {
  beforeEach(() => undefined);
  it("types request and response bodies per operation", () => {
    expectTypeOf<OkBody<"getQueue">>().toEqualTypeOf<components["schemas"]["QueueResponse"]>();
    expectTypeOf<ReqBody<"submitTurn">>().toEqualTypeOf<components["schemas"]["TurnRequest"]>();
    expectTypeOf<PathParams<"getCase">>().toHaveProperty("reference");
    expectTypeOf<OkBody<"logout">>().toEqualTypeOf<undefined>();
  });
});
