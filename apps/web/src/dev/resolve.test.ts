import { beforeEach, describe, expect, it } from "vitest";
import { OPS, type OperationId } from "@/api/client";
import type { CallContext } from "@/api/transport";
import { defaultExample } from "./defaults";
import { detectDrift } from "./transport";
import { resolveCall, type Resolution } from "./resolve";
import type { OpForce } from "./scenarios/types";
import { parseParams, resetWorld, setWorld, getWorld, takeSequenceStep, type World } from "./world";

const ctx = (op: OperationId, body?: unknown): CallContext => ({ op, method: OPS[op].method, path: OPS[op].path, body });
const resolve = (op: OperationId, body?: unknown): Resolution => resolveCall(ctx(op, body), OPS[op], getWorld(), defaultExample, takeSequenceStep);
const prefer = (r: Resolution) => (r.kind === "prism" ? r.prefer : r.kind);
const signedIn = (p: Partial<World> = {}) => setWorld({ signedIn: true, ...p });

beforeEach(() => { sessionStorage.clear(); resetWorld(); });

describe("resolveCall precedence", () => {
  it("signed out beats a force", () => {
    setWorld({ forces: { getQueue: { example: "SEEDED" } }, role: "representative" });
    expect(prefer(resolve("getQueue"))).toBe("code=401, example=UNAUTHENTICATED");
  });
  it("a force beats role emulation", () => {
    signedIn({ role: "customer", forces: { getQueue: { example: "SEEDED" } } });
    expect(prefer(resolve("getQueue"))).toBe("code=200, example=SEEDED");
  });
  it("expireNext answers UNAUTHENTICATED_EXPIRED once and signs out", () => {
    signedIn({ expireNext: true });
    const r = resolve("getStaffing");
    expect(prefer(r)).toBe("code=401, example=UNAUTHENTICATED_EXPIRED");
    expect(r.effects).toEqual({ signedIn: false, expireNext: false });
  });
  it("login is never blocked by sign-in; refuseNextLogin gives LOGIN_FAILED once", () => {
    expect(prefer(resolve("login"))).toBe("code=200, example=LOGGED_IN");
    setWorld({ refuseNextLogin: true });
    const r = resolve("login");
    expect(prefer(r)).toBe("code=401, example=LOGIN_FAILED");
    expect(r.effects).toEqual({ refuseNextLogin: false });
  });
  it("sequence cursor advances and repeats the last", () => {
    const seq: OpForce = { sequence: [{ example: "SEEDED" }, { example: "ALL_CAUGHT_UP" }] };
    signedIn({ role: "representative", forces: { getQueue: seq } });
    expect([prefer(resolve("getQueue")), prefer(resolve("getQueue")), prefer(resolve("getQueue"))]).toEqual([
      "code=200, example=SEEDED", "code=200, example=ALL_CAUGHT_UP", "code=200, example=ALL_CAUGHT_UP",
    ]);
  });
  it("hang and network failure", () => {
    signedIn({ forces: { getStaffing: { hang: true }, getDemoClock: { fail: "network", delayMs: 5 } } });
    expect(resolve("getStaffing").kind).toBe("hang");
    expect(resolve("getDemoClock")).toMatchObject({ kind: "network-fail", delayMs: 5 });
  });
});

describe("role emulation from x-roles", () => {
  it("customer on getQueue is 403", () => {
    signedIn({ role: "customer" });
    expect(prefer(resolve("getQueue"))).toBe("code=403, example=ROLE_NOT_ALLOWED");
  });
  it("owner on getCase is allowed", () => {
    signedIn({ role: "owner" });
    expect(prefer(resolve("getCase"))).not.toContain("403");
  });
  it("representative on advanceDemoClock is 403", () => {
    signedIn({ role: "representative" });
    expect(prefer(resolve("advanceDemoClock", { to: "next_business_morning" }))).toBe("code=403, example=ROLE_NOT_ALLOWED");
  });
  it("a pending role reset uses the reset example once", () => {
    signedIn({ role: "customer", roleResetPending: true });
    const r = resolve("getQueue");
    expect(prefer(r)).toBe("code=403, example=ROLE_NOT_ALLOWED_ROLE_RESET");
    expect(r.effects).toEqual({ roleResetPending: false });
  });
});

describe("getSession and defaults", () => {
  it("answers from the stored body for a supervisor without Prism", () => {
    const body = { authenticated: true as const, role: "supervisor" as const, display_name: "Demo supervisor", sees: [] as string[], signed_in_at: "2026-10-16T14:00:00-05:00" };
    signedIn({ role: "supervisor", sessionBody: body });
    expect(resolve("getSession")).toMatchObject({ kind: "short-circuit", response: { status: 200, body } });
  });
  it("falls back to Prism CUSTOMER when no body is stored", () => {
    signedIn();
    expect(prefer(resolve("getSession"))).toBe("code=200, example=CUSTOMER");
  });
  it("switchRole uses the TO_ example for the asked role", () => {
    signedIn({ role: "customer" });
    expect(prefer(resolve("switchRole", { role: "supervisor" }))).toBe("code=200, example=TO_SUPERVISOR");
  });
  it("submitTurn defaults to ANSWER_WITH_SOURCE", () => {
    signedIn();
    expect(prefer(resolve("submitTurn", { turn_id: "x", payload: { kind: "text", text: "hi" } }))).toBe("code=200, example=ANSWER_WITH_SOURCE");
  });
  it("staffing decides the staffing, chat-start and queue defaults", () => {
    signedIn({ role: "supervisor", staffing: "simulated_on_shift" });
    expect(prefer(resolve("getStaffing"))).toBe("code=200, example=ON");
    expect(prefer(resolve("startChatSession"))).toBe("code=201, example=SIMULATION_ON");
    expect(prefer(resolve("getQueue"))).toBe("code=200, example=STAFFED_WITH_WAITING");
    setWorld({ staffing: "nobody_online" });
    expect(prefer(resolve("getQueue"))).toBe("code=200, example=SEEDED");
  });
  it("setStaffing answers with the example for the mode in the request body", () => {
    signedIn({ role: "supervisor" });
    expect(prefer(resolve("setStaffing", { mode: "simulated_on_shift" }))).toBe("code=200, example=TURNED_ON");
    expect(prefer(resolve("setStaffing", { mode: "nobody_online" }))).toBe("code=200, example=TURNED_OFF_WITH_WAITING");
  });
  it("an explicit setStaffing force still beats the body-keyed answer", () => {
    signedIn({ role: "supervisor", forces: { setStaffing: { example: "TURNED_ON" } } });
    expect(prefer(resolve("setStaffing", { mode: "nobody_online" }))).toBe("code=200, example=TURNED_ON");
  });
  it("any other op uses its first 2xx example", () => {
    signedIn({ role: "supervisor" });
    expect(prefer(resolve("getOversight"))).toMatch(/^code=200, example=/);
  });
  it("a Prefer names both code and example so a 4xx is selectable", () => {
    signedIn({ role: "representative", forces: { applyCaseAction: { example: "VERSION_CONFLICT" } } });
    expect(prefer(resolve("applyCaseAction", { action: "claim", expected_version: 1 }))).toMatch(/^code=409, example=VERSION_CONFLICT$/);
  });
  it("the force status disambiguates a name under two statuses", () => {
    signedIn({ role: "supervisor", forces: { resetDemo: { example: "RESET_IN_PROGRESS", status: 409 } } });
    expect(prefer(resolve("resetDemo", { confirm: true }))).toBe("code=409, example=RESET_IN_PROGRESS");
  });
});

describe("delay precedence", () => {
  it("the force's delay wins over the world's", () => {
    signedIn({ delayMs: 1500, forces: { getStaffing: { example: "OFF", delayMs: 40 } } });
    expect(resolve("getStaffing")).toMatchObject({ delayMs: 40 });
    expect(resolve("getDemoClock")).toMatchObject({ delayMs: 1500 });
  });
  it("hang as the global delay hangs everything", () => {
    signedIn({ delayMs: "hang" });
    expect(resolve("getDemoClock").kind).toBe("hang");
  });
});

describe("URL params", () => {
  it("parses signedin, role, staffing, delay, theme and scenario", () => {
    const p = parseParams("?signedin=1&role=supervisor&staffing=on&delay=4000&theme=dark&scenario=scr05.empty");
    expect(p.patch).toMatchObject({ signedIn: true, role: "supervisor", staffing: "simulated_on_shift", delayMs: 4000 });
    expect(p.theme).toBe("dark");
    expect(p.scenario).toBe("scr05.empty");
    expect(parseParams("?delay=hang").patch.delayMs).toBe("hang");
  });
  it("parses ?ex lists, with and without a status", () => {
    expect(parseParams("?ex=getQueue:SEEDED,getStaffing:ON").patch.forces).toEqual({ getQueue: { example: "SEEDED" }, getStaffing: { example: "ON" } });
    expect(parseParams("?ex=applyCaseAction:409/NOT_ALLOWED_IN_STATE").patch.forces).toEqual({ applyCaseAction: { example: "NOT_ALLOWED_IN_STATE", status: 409 } });
  });
  it("ignores an unknown role", () => {
    expect(parseParams("?role=admin").patch.role).toBeUndefined();
  });
});

describe("drift detection", () => {
  it("flags an Error severity violation header", () => {
    const res = new Response("{}", { headers: { "sl-violations": '[{"severity":"Error","message":"x"}]' } });
    expect(detectDrift(res, {})).toContain("Error");
  });
  it("flags a Prism problem body and ignores clean responses", () => {
    expect(detectDrift(new Response("{}"), { type: "https://stoplight.io/prism/errors#UNPROCESSABLE_ENTITY", detail: "bad" })).toContain("UNPROCESSABLE_ENTITY");
    expect(detectDrift(new Response("{}"), { ok: true })).toBeNull();
    expect(detectDrift(new Response("{}", { headers: { "sl-violations": '[{"severity":"Warning"}]' } }), {})).toBeNull();
  });
});

describe("case-aware picking hook (FR-1)", () => {
  it("pickCaseCall resolves to undefined while no casePicker is registered, and the defaults table answers", () => {
    signedIn({ role: "representative" });
    expect(prefer(resolve("getQueue"))).not.toBe("");
  });
  it("parses the reference path parameter from the concrete URL, decoded", async () => {
    const { referenceOf } = await import("./resolve");
    signedIn({ role: "representative" });
    const c: CallContext = { op: "getCase", method: "GET", path: "/api/staff/cases/MHC-C-0007", body: undefined };
    expect(referenceOf(c, OPS.getCase)).toBe("MHC-C-0007");
    expect(referenceOf({ ...c, path: "/api/staff/cases/MHC%2FX?x=1" }, OPS.getCase)).toBe("MHC/X");
    expect(referenceOf({ ...c, op: "getQueue", path: "/api/staff/queue" }, OPS.getQueue)).toBeNull();
  });
});
