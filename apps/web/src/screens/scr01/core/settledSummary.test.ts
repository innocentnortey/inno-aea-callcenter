import { describe, expect, it } from "vitest";
import { expectNo24HourTimes } from "@/test/no24h";
import type { Settled } from "../contract";
import type { Write } from "./model";
import { followUpLabel, identityLine, landingsFromWrites, landingText, promiseSentence, stripLine } from "./settledSummary";
import { startExample, turnExample } from "./testFixtures";

const base = (): Settled => startExample().settled;
const visit: NonNullable<Settled["visit"]> = {
  appointment_id: 1, date: "2026-10-21", window: "08:00-12:00", window_label: "8:00 am – 12:00 pm", technician: "Jun Park", service_type: "x", fee_line: "$0", status: "booked", change_request: null,
};
const request: NonNullable<Settled["request"]> = {
  reference: "MHC-C-0007", promise_text: "A representative will get back to you within 1 business day", due_at: "2026-10-19T19:00:00-05:00",
  due_label: "by Monday, October 19, 7:00 pm", extra_lines: [], live_queued: false, followup: null,
};
const w = (kind: Write["kind"]): Write => ({ kind, summary: "s", turn_id: "t", at: "2026-10-16T14:20:00-05:00" });

describe("stripLine", () => {
  it("covers nothing, visit, request, both and danger", () => {
    expect(stripLine(null, false)).toBe("Nothing yet");
    expect(stripLine(base(), false)).toBe("Nothing yet");
    expect(stripLine({ ...base(), visit }, false)).toBe("Wed Oct 21 · 8:00 am – 12:00 pm");
    expect(stripLine({ ...base(), request: { ...request, due_at: null } }, false)).toBe("MHC-C-0007");
    expect(stripLine({ ...base(), request }, false)).toBe("MHC-C-0007 · due Mon 7:00 pm");
    expect(stripLine({ ...base(), visit, request }, false)).toBe("Wed Oct 21 · 8:00 am – 12:00 pm · MHC-C-0007 · due Mon 7:00 pm");
    expect(stripLine({ ...base(), visit }, true)).toBe("DANGER · Leave the home immediately");
  });
});
describe("promiseSentence", () => {
  it("joins the label, and treats empty and null as absent", () => {
    expect(promiseSentence(request)).toBe("A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm.");
    expect(promiseSentence({ ...request, due_label: "" })).toBe("A representative will get back to you within 1 business day.");
    expect(promiseSentence({ ...request, due_label: null })).toBe("A representative will get back to you within 1 business day.");
  });
});
describe("labels", () => {
  const f = (channel: "email" | "phone", window: "morning" | "afternoon" | "any") => ({ channel, window, destination_label: "x", on_record: true, saved_line: "" });
  it("follow-up", () => {
    expect(followUpLabel(f("phone", "morning"))).toBe("Phone · mornings");
    expect(followUpLabel(f("phone", "afternoon"))).toBe("Phone · afternoons");
    expect(followUpLabel(f("phone", "any"))).toBe("Phone · any time");
    expect(followUpLabel(f("email", "morning"))).toBe("Email");
  });
  it("identity, all five statuses", () => {
    const hint = "the phone ending in 02";
    expect(identityLine({ status: "not_checked", hint: null })).toBe("Not checked. Only needed for private details.");
    expect(identityLine({ status: "code_sent", hint })).toBe("Code sent to the phone ending in 02");
    expect(identityLine({ status: "verified", hint })).toBe("Verified for this chat · the phone ending in 02");
    expect(identityLine({ status: "not_verified", hint: null })).toBe("I can't confirm your account here. A representative will help.");
    expect(identityLine({ status: "locked", hint: null })).toBe("I can't confirm your account here. A representative will help.");
  });
  it("landing text uses 12-hour times", () => {
    const text = landingText("visit", { ...base(), visit });
    expect(text).toBe("Your visit: Wednesday, October 21, 8:00 am to 12:00 pm");
    const el = document.createElement("div");
    el.textContent = text;
    expectNo24HourTimes(el);
  });
  it("landing for the BOOKED example", () => {
    const res = turnExample("BOOKED");
    expect(landingsFromWrites(res.writes)).toContain("visit");
  });
});
describe("landingsFromWrites", () => {
  it("maps kinds, collapses duplicates, keeps first-appearance order", () => {
    expect(landingsFromWrites([w("booked")])).toEqual(["visit"]);
    expect(landingsFromWrites([w("change_request_sent")])).toEqual(["visit", "request"]);
    expect(landingsFromWrites([w("verified")])).toEqual(["identity"]);
    expect(landingsFromWrites([w("case_opened"), w("followup_saved"), w("moved"), w("cancelled")])).toEqual(["request", "visit"]);
  });
});
