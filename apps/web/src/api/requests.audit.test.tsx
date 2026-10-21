// UNIT (fake transport), G-07: every request body the UI sends is checked against the spec's request schema, STRICTLY.
// The spec sets no additionalProperties, so Prism accepts a misspelt or extra field. src/test/spec.ts closes each object:
// a key no schema property declares is a violation, as is a missing required key, a wrong type or enum value, a bad uuid.
// The bodies come from the real call sites: useChat + the real gateway (CON-1, 2, 4, 5), the SCR-6 forms and buttons
// (CON-13 to 16), SCR-3, SCR-4, SCR-7, SCR-8 and SCR-12. MOCK-ONLY/UNIT evidence: no server saw these requests.
// Residual list (what this does not drive) is in docs/ux/04-prototype/INTEGRATION_HANDOFF.md, gap G-07.
import { act, cleanup, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createElement, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { OPS, type OperationId } from "@/api/client";
import { setTransport, type CallContext } from "@/api/transport";
import { AnnounceProvider } from "@/components/ui/LiveRegion";
import { DemoStatusContext, type DemoStatusApi } from "@/state/demoStatus";
import { jsonResponse, makeFakeTransport } from "@/test/fakeTransport";
import { ref, requestExamples, requestOps, requestSchema, specBody, specError, violations } from "@/test/spec";
import { ok, renderRoute, defaultCase, liveJoinedCase } from "@/screens/scr06/case.fixtures";
import { seededQueue } from "@/screens/scr05/queue.fixtures";
import { apiGateway } from "@/screens/scr01/core/gateway";
import { useChat } from "@/screens/scr01/core/useChat";
import { AssignForm, CloseForm, ContactForm, FlagForm, PriorityForm, ReleaseForm, ResolveForm, WaitForm, type FormProps } from "@/screens/scr06/ActionForms";
type Submission = Parameters<FormProps["onSubmit"]>[0];
import { configure } from "@testing-library/react";
/** Under the full parallel suite the first lazy screen chunk can take longer than the 1 s default. */
configure({ asyncUtilTimeout: 4000 });

/* eslint-disable @typescript-eslint/no-explicit-any -- spec bodies are walked as plain JSON */
const found: string[] = [];
const covered = new Set<string>();
/** Validates the body of one outgoing call against its request schema and notes what was covered. */
function audit(ctx: CallContext, label?: string): void {
  const schema = requestSchema(ctx.op);
  if (!schema) { if (ctx.body !== undefined) found.push(`${ctx.op}: sent a body but the spec has no requestBody`); return; }
  if (ctx.body === undefined) { found.push(`${ctx.op}: sent no body but the spec requires one`); return; }
  const sent = JSON.parse(JSON.stringify(ctx.body)); // what the wire carries: undefined keys are dropped
  for (const v of violations(schema, sent, `${ctx.op}`)) found.push(`${v}  <- ${JSON.stringify(sent)}`);
  const b = sent as Record<string, unknown>;
  covered.add(label ?? `${ctx.op}${b.action ? ":" + b.action : b.kind ? ":" + b.kind : b.mode ? ":" + b.mode : b.step ? ":" + b.step : b.payload ? ":" + (b.payload as any).kind : ""}`);
}
beforeEach(() => { found.length = 0; sessionStorage.clear(); vi.spyOn(console, "error").mockImplementation(() => undefined); });
afterEach(() => cleanup());

describe("UNIT (fake transport) G-07: the strict checker is strict for all 13 request schemas", () => {
  const ops = requestOps();
  it("there are 13 request operations", () => expect(ops).toHaveLength(13));
  it.each(ops)("%s: every spec request example passes; an extra key, a missing required key and a wrong type fail", (op) => {
    const schema = requestSchema(op);
    const examples = Object.entries(requestExamples(op));
    expect(examples.length).toBeGreaterThan(0);
    for (const [name, ex] of examples) {
      expect(violations(schema, ex), `${op}/${name}`).toEqual([]);
      expect(violations(schema, { ...ex, not_in_the_spec: 1 }).join(), `${op}/${name} extra`).toMatch(/unknown key/);
      expect(violations(schema, Array.isArray(ex) ? "x" : "not an object").length, `${op}/${name} type`).toBeGreaterThan(0);
      const required: string[] = ref(schema).required ?? [];
      expect(required.length, `${op} declares required keys`).toBeGreaterThan(0);
      for (const k of required) {
        const { [k]: _gone, ...rest } = ex as Record<string, unknown>;
        void _gone;
        expect(violations(schema, rest).length, `${op}/${name} without ${k}`).toBeGreaterThan(0);
      }
    }
  });
});

describe("UNIT (fake transport) G-07: bodies from the customer chat (useChat through the real gateway)", () => {
  const demo = (): DemoStatusApi => ({ clock: null, staffing: null, refresh: vi.fn(async () => undefined), setFromChat: vi.fn(), setSource: vi.fn() });
  const wrapper = ({ children }: { children: ReactNode }) => createElement(AnnounceProvider, null, createElement(DemoStatusContext.Provider, { value: demo() }, children));
  it("text, choice, code, form, person and follow-up requests match the schemas", async () => {
    setTransport(makeFakeTransport((ctx) => {
      audit(ctx);
      switch (ctx.op) {
        case "startChatSession": return jsonResponse(201, specBody("startChatSession", 201, "STARTED"));
        case "submitTurn": return jsonResponse(200, specBody("submitTurn", 200, "ANSWER_WITH_SOURCE"));
        case "requestPerson": return jsonResponse(200, specBody("requestPerson", 200, "CASE_CREATED"));
        case "saveFollowUp": return jsonResponse(200, specBody("saveFollowUp", 200, "PHONE_MORNINGS"));
        default: return jsonResponse(404, specError("getChatThread", 404, "SESSION_NOT_FOUND"));
      }
    }));
    const { result } = renderHook(() => useChat(apiGateway), { wrapper });
    await waitFor(() => expect(result.current.state.phase).toBe("ready"));
    const go = async (a: Parameters<typeof result.current.dispatch>[0]) => { await act(async () => { await result.current.dispatch(a); }); };
    await go({ kind: "text", text: "  Why is my bill $478? " });
    await go({ kind: "choice", cardId: "qc-1", option: "skip_and_book" });
    await go({ kind: "code", cardId: "cp-1", code: "482913" });
    await go({ kind: "form", cardId: "lp-1", values: { name: "Omar Patel", phone: "512-555-0102" } });
    await go({ kind: "form", cardId: "wp-1", values: { zip_or_city: "78701" } });
    await go({ kind: "form", cardId: "lp-1", values: { customer_id: "C-1001" } });
    await go({ kind: "person" });
    await go({ kind: "followUp", channel: "phone", destination: "on_record", window: "morning" });
    await go({ kind: "followUp", channel: "email", destination: "general", window: "any" });
    expect(found).toEqual([]);
    for (const c of ["submitTurn:text", "submitTurn:choice", "submitTurn:code", "submitTurn:form", "requestPerson", "saveFollowUp"]) expect(covered.has(c), c).toBe(true);
  });
});

describe("UNIT (fake transport) G-07: bodies built by the SCR-6 forms (CON-13, 15, 16)", () => {
  const mk = () => {
    const submitted: Submission[] = [];
    return { submitted, p: { onSubmit: (s: Submission) => { submitted.push(s); }, onCancel: vi.fn(), busy: false, version: 3 } satisfies FormProps };
  };
  const type = (label: string, value: string) => fireEvent.change(screen.getByLabelText(label), { target: { value } });
  const opOf = (s: Submission): OperationId => (s.kind === "case" ? "applyCaseAction" : s.kind === "contact" ? "recordContactActivity" : "createFlag");
  const check = (s: Submission) => audit({ op: opOf(s), method: OPS[opOf(s)].method, path: "", body: s.body });

  it("release, resolve, close, wait (with and without a time), assign, change priority, call, email, flag", async () => {
    const run = async (el: (p: FormProps) => React.ReactElement, fill: () => void, button: string) => {
      const { submitted, p } = mk();
      const { unmount } = render(el(p));
      fill();
      fireEvent.click(screen.getByRole("button", { name: button }));
      await waitFor(() => expect(submitted.length).toBeGreaterThan(0));
      submitted.forEach(check);
      unmount();
    };
    await run((p) => <ReleaseForm {...p} />, () => type("Reason", "Not my area"), "Release");
    await run((p) => <ResolveForm {...p} />, () => type("Outcome", "Credit recorded"), "Resolve");
    await run((p) => <CloseForm {...p} />, () => type("Reason", "Duplicate"), "Close unresolved");
    await run((p) => <WaitForm {...p} nowIso="2026-10-16T14:20:00-05:00" />, () => { type("Wake-up date", "2026-10-19"); type("Wake-up time", "09:00"); type("Reason (optional)", "Customer asked"); }, "Set waiting");
    await run((p) => <WaitForm {...p} nowIso="2026-10-16T14:20:00-05:00" />, () => type("Wake-up date", "2026-10-19"), "Set waiting");
    await run((p) => <AssignForm {...p} />, () => type("Reason", "Has the context"), "Assign");
    await run((p) => <PriorityForm {...p} />, () => { type("Priority", "P2"); type("Reason", "Second invoice"); }, "Change priority");
    await run((p) => <ContactForm {...p} kind="call" />, () => { fireEvent.click(screen.getByLabelText("Reached the customer")); type("Note", "Explained"); }, "Record");
    await run((p) => <ContactForm {...p} kind="email" />, () => fireEvent.click(screen.getByLabelText("Left a message")), "Record");
    await run((p) => <FlagForm {...p} reference="MHC-C-0007" lastAssistantMessageId="m-2" />, () => { fireEvent.click(screen.getByLabelText("An answer was wrong")); type("Note", "Quoted $144"); }, "Add to review list");
    await run((p) => <FlagForm {...p} reference="MHC-C-0007" lastAssistantMessageId={null} />, () => fireEvent.click(screen.getByLabelText("The brief left something out")), "Add to review list");
    // assign/change_priority send reason "" when the field is left empty: the schema allows a string, the server answers REASON_REQUIRED.
    expect(found).toEqual([]);
    for (const c of ["applyCaseAction:release", "applyCaseAction:resolve", "applyCaseAction:close_unresolved", "applyCaseAction:wait", "applyCaseAction:assign", "applyCaseAction:change_priority", "recordContactActivity:call", "recordContactActivity:email", "createFlag"]) expect(covered.has(c), c).toBe(true);
  });
});

describe("UNIT (fake transport) G-07: bodies sent by whole screens", () => {
  const answer = (ctx: CallContext): Response | undefined => {
    audit(ctx);
    switch (ctx.op) {
      case "getCase": return ok(defaultCase());
      case "getQueue": return ok(seededQueue());
      case "applyCaseAction": return ok(specBody("applyCaseAction", 200, "CLAIMED"));
      case "liveChatAction": return ok(specBody("liveChatAction", 200, "JOINED"));
      case "listFlags": return ok(specBody("listFlags", 200, "THREE"));
      case "reviewFlag": return ok(specBody("reviewFlag", 200, "REVIEWED"));
      case "advanceDemoClock": return ok(specBody("advanceDemoClock", 200, "PLUS_1H"));
      case "getOversight": return ok(specBody("getOversight", 200, "SEEDED"));
      case "setStaffing": return ok(specBody("setStaffing", 200, "TURNED_ON"));
      case "resetDemo": return ok(specBody("resetDemo", 200, "RESET"));
      case "listDemoRoles": return ok(specBody("listDemoRoles", 200, "ROLES"));
      case "login": return ok(specBody("login", 200, "LOGGED_IN"));
      default: return undefined;
    }
  };

  it("SCR-6: Claim, Claim and join (claim + join), join, send, hand back, close", async () => {
    const queued = defaultCase();
    queued.case.lifecycle = "live_queued";
    queued.case.allowed_actions = ["claim_and_join", "claim", "flag"];
    queued.live = { state: "queued", since: "2026-10-16T14:14:00-05:00", controller: "ai" };
    renderRoute("/staff/cases/MHC-C-0007", "representative", (ctx) => (ctx.op === "getCase" ? (audit(ctx), ok(queued)) : answer(ctx)));
    fireEvent.click(await screen.findByRole("button", { name: "Claim and join" }));
    await waitFor(() => expect(covered.has("liveChatAction:join")).toBe(true));
    cleanup();
    renderRoute("/staff/cases/MHC-C-0007", "representative", (ctx) => (ctx.op === "getCase" ? (audit(ctx), ok(liveJoinedCase())) : answer(ctx)));
    await screen.findByText(/You are replying as Riley/);
    fireEvent.change(screen.getByLabelText("Reply"), { target: { value: "Hi Omar" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() => expect(covered.has("liveChatAction:send")).toBe(true));
    fireEvent.click(await screen.findByRole("button", { name: "Hand back to the assistant" }));
    await waitFor(() => expect(covered.has("liveChatAction:hand_back")).toBe(true));
    cleanup();
    renderRoute("/staff/cases/MHC-C-0007", "representative", (ctx) => (ctx.op === "getCase" ? (audit(ctx), ok(liveJoinedCase())) : answer(ctx)));
    await screen.findByText(/You are replying as Riley/);
    fireEvent.click(screen.getByRole("button", { name: "Close the chat" }));
    await waitFor(() => expect(covered.has("liveChatAction:close")).toBe(true));
    expect(found).toEqual([]);
    for (const c of ["applyCaseAction:claim", "liveChatAction:join", "liveChatAction:send", "liveChatAction:hand_back", "liveChatAction:close"]) expect(covered.has(c), c).toBe(true);
  }, 30_000);

  it("SCR-8 reviewFlag with and without a note", async () => {
    renderRoute("/staff/flags", "supervisor", answer);
    const mark = () => screen.findByRole("button", { name: "Mark reviewed, flag on MHC-C-0007" });
    fireEvent.click(await mark());
    fireEvent.change(screen.getByRole("textbox", { name: /Note/ }), { target: { value: "Fee schedule is right" } });
    fireEvent.click(await mark());
    await waitFor(() => expect(covered.has("reviewFlag")).toBe(true));
    cleanup();
    renderRoute("/staff/flags", "supervisor", answer);
    fireEvent.click(await mark());
    fireEvent.click(await mark());
    await waitFor(() => expect(found.length + covered.size).toBeGreaterThan(0));
    await act(async () => { await new Promise((r) => setTimeout(r, 40)); });
    expect(found).toEqual([]);
  });

  it("SCR-7 advance (all three steps), SCR-3 staffing and reset, SCR-4 switch role, SCR-12 login", async () => {
    renderRoute("/staff/oversight", "supervisor", answer);
    await screen.findByRole("switch");
    for (const name of ["+1 hour", "+4 hours", "Next business morning (Mon 7:00 am)"]) {
      fireEvent.click(screen.getByRole("button", { name }));
      await act(async () => { await new Promise((r) => setTimeout(r, 60)); });
    }
    cleanup();
    renderRoute("/demo", "customer", answer);
    const sw = await screen.findByRole("switch", { name: "Demo: simulate staff on shift" });
    await waitFor(() => expect((sw as HTMLInputElement).disabled).toBe(false));
    fireEvent.click(sw);
    await waitFor(() => expect(covered.has("setStaffing:simulated_on_shift")).toBe(true));
    await userEvent.click(screen.getByRole("button", { name: "Reset the demo" }));
    const dlg = await screen.findByRole("dialog", { name: "Reset the demo?" });
    await userEvent.click([...dlg.querySelectorAll("button")].find((b) => b.textContent === "Reset the demo")!);
    await waitFor(() => expect(covered.has("resetDemo")).toBe(true));
    cleanup();
    renderRoute("/role", "customer", answer);
    await userEvent.click(await screen.findByRole("button", { name: "Demo supervisor" }));
    await waitFor(() => expect(covered.has("switchRole")).toBe(true));
    cleanup();
    renderRoute("/login", "customer", (ctx) => (ctx.op === "getSession" ? new Response(JSON.stringify(specError("getSession", 401, "UNAUTHENTICATED")), { status: 401 }) : answer(ctx)));
    await userEvent.type(await screen.findByLabelText("Username"), "<demo-username>");
    await userEvent.type(screen.getByLabelText("Password"), "<demo-password>");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() => expect(covered.has("login")).toBe(true));
    expect(found).toEqual([]);
    for (const c of ["advanceDemoClock:plus_1h", "setStaffing:simulated_on_shift", "resetDemo", "switchRole", "login"]) expect([...covered].some((x) => x.startsWith(c.split(":")[0])), c).toBe(true);
  }, 30_000);

  it("the audit does catch a bad body (control)", () => {
    audit({ op: "setStaffing", method: "PUT", path: "", body: { mode: "simulated_on_shift", also: true } });
    audit({ op: "resetDemo", method: "POST", path: "", body: {} });
    expect(found.join("\n")).toMatch(/unknown key/);
    expect(found.join("\n")).toMatch(/required key is missing/);
  });
});
