import { beforeEach, describe, expect, it } from "vitest";
import type { OperationId } from "@/api/client";
import type { Role } from "@/lib/roles";
import { casePicker } from "./case-actions";
import { getOverride, resetCaseStore } from "./case-store";
import type { World } from "../world";
import { addNeedsRow, claimedByMe, emptyHeadings, moveLiveToNeeds, queueChange, shiftEndedPromise, stuckWaiting } from "../scenarios/case-transforms";
import { specExample } from "@/screens/scr06/specExample";

beforeEach(resetCaseStore);
const world = (role: Role = "representative", staffing: World["staffing"] = "nobody_online"): World =>
  ({ signedIn: true, role, sessionBody: null, staffing, expireNext: false, refuseNextLogin: false, roleResetPending: false, delayMs: 0, forces: {}, scenarioId: null });
const pick = (op: OperationId, reference: string | null, body: unknown, role: Role = "representative") => casePicker({ op, reference, body, world: world(role) });
const act = (n: string) => specExample<any>("/api/staff/cases/{reference}/actions", "post", "200", n); // eslint-disable-line @typescript-eslint/no-explicit-any
const getCase = (n: string) => specExample<any>("/api/staff/cases/{reference}", "get", "200", n); // eslint-disable-line @typescript-eslint/no-explicit-any
const REF = "MHC-C-0007";

describe("casePicker", () => {
  it("release without reason picks REASON_REQUIRED 422", () => {
    expect(pick("applyCaseAction", REF, { action: "release", expected_version: 3, reason: "" })).toMatchObject({ example: "REASON_REQUIRED", status: 422 });
  });
  it("wait without a time and resolve without an outcome pick their 422s", () => {
    expect(pick("applyCaseAction", REF, { action: "wait", expected_version: 3 })).toMatchObject({ example: "WAKE_UP_REQUIRED" });
    expect(pick("applyCaseAction", REF, { action: "resolve", expected_version: 3 })).toMatchObject({ example: "OUTCOME_REQUIRED" });
  });
  it("claim twice picks CASE_ALREADY_CLAIMED", () => {
    const first = pick("applyCaseAction", REF, { action: "claim", expected_version: 3 })!;
    first.transform!(act("CLAIMED"));
    expect(pick("applyCaseAction", REF, { action: "claim", expected_version: 4 })).toMatchObject({ example: "CASE_ALREADY_CLAIMED", status: 409 });
  });
  it("an action not allowed in the state picks NOT_ALLOWED_IN_STATE", () => {
    pick("applyCaseAction", REF, { action: "claim", expected_version: 3 })!.transform!(act("CLAIMED"));
    pick("applyCaseAction", REF, { action: "wait", expected_version: 4, wake_up_at: "2026-10-19T09:00:00-05:00" })!.transform!(act("WAITING"));
    expect(pick("applyCaseAction", REF, { action: "resolve", expected_version: 6, outcome: "x" })).toMatchObject({ example: "NOT_ALLOWED_IN_STATE" });
  });
  it("unknown reference picks CASE_NOT_FOUND with the reference in details", () => {
    const p = pick("getCase", "MHC-C-0099", null)!;
    expect(p).toMatchObject({ example: "CASE_NOT_FOUND", status: 404 });
    expect(p.transform!({ error: { code: "CASE_NOT_FOUND", details: null } }).error.details).toEqual({ reference: "MHC-C-0099" });
  });
  it("getCase picks the named example per reference", () => {
    expect(pick("getCase", "MHC-C-0008", null)!.example).toBe("SAFETY_CASE");
    expect(pick("getCase", "MHC-C-0009", null)!.example).toBe("FEE_BEARING_CHANGE");
    expect(pick("getCase", REF, null)!.example).toBe("DEFAULT");
  });
  it("getCase for the owner recomputes allowed_actions to []", () => {
    const body = pick("getCase", REF, null, "owner")!.transform!(getCase("DEFAULT"));
    expect(body.case.allowed_actions).toEqual([]);
    expect(pick("getCase", REF, null, "supervisor")!.transform!(getCase("DEFAULT")).case.allowed_actions).toContain("assign");
  });
  it("getCase re-skins a reference without a named example", () => {
    const body = pick("getCase", "MHC-C-0012", null)!.transform!(getCase("DEFAULT"));
    expect(body.case.reference).toBe("MHC-C-0012");
    expect(body.case.lifecycle).toBe("live_queued");
    expect(body.live.state).toBe("queued");
    expect(body.case.allowed_actions).toEqual(["claim_and_join", "claim", "flag"]);
    expect(body.sources).toEqual([]);
    expect(body.promise.text).toContain("MHC-C-0012");
  });
  it("claim by a supervisor sets owner Demo supervisor", () => {
    const p = pick("applyCaseAction", REF, { action: "claim", expected_version: 3 }, "supervisor")!;
    const body = p.transform!(act("CLAIMED"));
    expect(body.case.owner).toBe("Demo supervisor");
    expect(body.result_line).toBe("Claimed · Demo supervisor");
  });
  it("wait result line uses the request time", () => {
    pick("applyCaseAction", REF, { action: "claim", expected_version: 3 })!.transform!(act("CLAIMED"));
    const body = pick("applyCaseAction", REF, { action: "wait", expected_version: 4, wake_up_at: "2026-10-20T09:00:00-05:00" })!.transform!(act("WAITING"));
    expect(body.result_line).toBe("Waiting until Tue Oct 20 · 9:00 am");
    expect(body.case.wake_up_at).toBe("2026-10-20T09:00:00-05:00");
  });
  it("resolve reports the reference and marks the promise", () => {
    pick("applyCaseAction", REF, { action: "claim", expected_version: 3 })!.transform!(act("CLAIMED"));
    const body = pick("applyCaseAction", REF, { action: "resolve", expected_version: 4, outcome: "done" })!.transform!(act("RESOLVED"));
    expect(body.result_line).toBe("MHC-C-0007 resolved.");
    expect(body.case.lifecycle).toBe("resolved");
    expect(body.case.promise_status).toBe("kept");
  });
  it("transform writes the store only when called", () => {
    pick("applyCaseAction", REF, { action: "claim", expected_version: 3 });
    expect(getOverride(REF)).toBeUndefined();
    pick("applyCaseAction", REF, { action: "claim", expected_version: 3 })!.transform!(act("CLAIMED"));
    expect(getOverride(REF)?.lifecycle).toBe("claimed");
  });
  it("the queue drops resolved rows and shows owners after actions", () => {
    pick("applyCaseAction", REF, { action: "claim", expected_version: 3 })!.transform!(act("CLAIMED"));
    const q = specExample<any>("/api/staff/queue", "get", "200", "SEEDED"); // eslint-disable-line @typescript-eslint/no-explicit-any
    const claimed = pick("getQueue", null, null)!.transform!(structuredClone(q));
    expect(claimed.needs_my_action.find((r: any) => r.reference === REF).owner).toBe("Riley"); // eslint-disable-line @typescript-eslint/no-explicit-any
    pick("applyCaseAction", REF, { action: "resolve", expected_version: 4, outcome: "done" })!.transform!(act("RESOLVED"));
    const after = pick("getQueue", null, null)!.transform!(structuredClone(q));
    expect(after.needs_my_action.map((r: any) => r.reference)).not.toContain(REF); // eslint-disable-line @typescript-eslint/no-explicit-any
    expect(pick("getQueue", null, null)!.example).toBe("SEEDED");
    expect(casePicker({ op: "getQueue", reference: null, body: null, world: world("representative", "simulated_on_shift") })!.example).toBe("STAFFED_WITH_WAITING");
  });
  it("join needs a claim; send, hand back and close follow the live state", () => {
    pick("applyCaseAction", "MHC-C-0012", { action: "claim", expected_version: 3 })!.transform!(act("CLAIMED"));
    const join = pick("liveChatAction", "MHC-C-0012", { action: "join" })!;
    expect(join.example).toBe("JOINED");
    join.transform!(specExample("/api/staff/cases/{reference}/live", "post", "200", "JOINED"));
    const send = pick("liveChatAction", "MHC-C-0012", { action: "send", text: "Hello" })!;
    const sent = send.transform!(specExample<any>("/api/staff/cases/{reference}/live", "post", "200", "SENT")); // eslint-disable-line @typescript-eslint/no-explicit-any
    expect(sent.message.text).toBe("Hello");
    expect(pick("liveChatAction", "MHC-C-0012", { action: "send", text: "" })).toMatchObject({ example: "VALIDATION_ERROR", status: 400 });
    pick("liveChatAction", "MHC-C-0012", { action: "hand_back" })!.transform!(specExample("/api/staff/cases/{reference}/live", "post", "200", "HANDED_BACK"));
    expect(pick("liveChatAction", "MHC-C-0012", { action: "send", text: "again" })).toMatchObject({ example: "NOT_LIVE" });
  });
  it("join on an unclaimed case picks NOT_CLAIMED_BY_YOU", () => {
    pick("getCase", REF, null)!.transform!(getCase("DEFAULT"));
    pick("applyCaseAction", REF, { action: "release", expected_version: 3, reason: "x" })?.transform?.(act("CLAIMED"));
    expect(pick("liveChatAction", REF, { action: "join" })).toMatchObject({ example: "NOT_CLAIMED_BY_YOU", status: 403 });
  });
  it("contacts get unique ids and are refused before the claim", () => {
    pick("applyCaseAction", REF, { action: "claim", expected_version: 3 })!.transform!(act("CLAIMED"));
    const call = specExample<any>("/api/staff/cases/{reference}/activities", "post", "201", "CALL_REACHED"); // eslint-disable-line @typescript-eslint/no-explicit-any
    const a = pick("recordContactActivity", REF, { kind: "call", outcome: "no_answer", note: "n", expected_version: 4 })!.transform!(structuredClone(call));
    const b = pick("recordContactActivity", REF, { kind: "email", outcome: "reached", expected_version: 4 })!;
    expect(b.example).toBe("EMAIL_LEFT_MESSAGE");
    expect(a.activity.outcome).toBe("no_answer");
    expect(b.transform!(structuredClone(call)).activity.activity_id).not.toBe(a.activity.activity_id);
    resetCaseStore();
    pick("applyCaseAction", REF, { action: "claim", expected_version: 3 })!.transform!(act("CLAIMED"));
    pick("applyCaseAction", REF, { action: "release", expected_version: 4, reason: "r" })!.transform!(act("CLAIMED"));
    expect(pick("recordContactActivity", REF, { kind: "call", outcome: "reached", expected_version: 5 })).toMatchObject({ example: "NOT_ALLOWED_IN_STATE" });
  });
  it("other ops fall through", () => {
    expect(pick("getSession", null, null)).toBeUndefined();
  });
});

describe("case-transforms", () => {
  const queue = () => specExample<any>("/api/staff/queue", "get", "200", "STAFFED_WITH_WAITING"); // eslint-disable-line @typescript-eslint/no-explicit-any
  it("claimedByMe, emptyHeadings, stuckWaiting, shiftEndedPromise", () => {
    expect(claimedByMe(getCase("DEFAULT")).case).toMatchObject({ lifecycle: "claimed", owner: "Riley", version: 4 });
    expect(emptyHeadings([5, 7])(getCase("DEFAULT")).brief.headings.filter((h: any) => h.items.length === 0).map((h: any) => h.number)).toEqual([5, 7]); // eslint-disable-line @typescript-eslint/no-explicit-any
    expect(stuckWaiting("2026-10-16T14:00:00-05:00")(getCase("WAITING")).case.wake_up_at).toBe("2026-10-16T14:00:00-05:00");
    expect(shiftEndedPromise()(getCase("DEFAULT")).promise.status).toBe("changed");
  });
  it("queueChange, moveLiveToNeeds and addNeedsRow", () => {
    const q = queue();
    expect(queueChange({ "MHC-C-0006": { owner: "X" } })(q).needs_my_action.find((r: any) => r.reference === "MHC-C-0006").owner).toBe("X"); // eslint-disable-line @typescript-eslint/no-explicit-any
    const moved = moveLiveToNeeds()(queue());
    expect(moved.live).toEqual([]);
    expect(moved.staffing.mode).toBe("nobody_online");
    const row = moved.needs_my_action.at(-1);
    expect(row).toMatchObject({ reference: "MHC-C-0012", lifecycle: "unassigned", queued_at: null, created_at: "2026-10-16T14:14:00-05:00" });
    expect(addNeedsRow(row)({ ...q, needs_my_action: [] }).needs_my_action).toHaveLength(1);
  });
});
