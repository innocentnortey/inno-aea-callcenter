import { describe, expect, it } from "vitest";
import { screen, within } from "@testing-library/react";
import { jsonResponse } from "@/test/fakeTransport";
import { expectNo24HourTimes } from "@/test/no24h";
import { renderWithProviders } from "@/test/render";
import { opsTransport, type OpHandler } from "../reads/test/opsTransport";
import { specExample } from "../reads/test/specExample";
import Scr11 from "./Scr11";

function setup(handler: OpHandler | string = "BOTH_SPLITS") {
  const h: OpHandler = typeof handler === "string" ? () => jsonResponse(200, specExample("getLatestEval", handler)) : handler;
  return renderWithProviders(<Scr11 />, { route: "/eval", role: "customer", transport: opsTransport("customer", { getLatestEval: h }) });
}
const section = (name: string) => within(screen.getByRole("region", { name }));
const DEV_LABEL = "Dev (we read and fixed these, so it overstates)";

describe("Scr11", () => {
  it("headline", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Headline" });
    const h = section("Headline");
    expect(h.getByText("65%")).toBeTruthy();
    expect(h.getByText("26 of 40 held-out cases")).toBeTruthy();
    expect(h.getByText("Held-out split: scored only, never tuned against.")).toBeTruthy();
    expect(h.getByText("run-2026-10-20-h")).toBeTruthy();
    expect(h.getByText("Range over repeats: 60% – 68%")).toBeTruthy();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
  });

  it("run identity", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Run identity" });
    const r = section("Run identity");
    expect(r.getByText(/run-2026-10-20-h/).textContent).toContain("40 cases");
    expect(r.getByText(/run-2026-10-19-d/).textContent).toContain("120 cases");
    expect(r.getAllByText("8 transcript-derived and 4 labelled synthetic cases in the mix").length).toBe(2);
  });

  it("caption names the run", async () => {
    setup();
    await screen.findByText("Measures: held-out run run-2026-10-20-h; dev run run-2026-10-19-d");
  });

  it("measures table has col and row headers and n of N", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Measures" });
    const m = section("Measures");
    expect(m.getAllByRole("columnheader").map((c) => c.textContent)).toEqual(["Measure", "Held-out", `Dev${DEV_LABEL}`]);
    expect(m.getByRole("rowheader", { name: "Accuracy on handled drivers" })).toBeTruthy();
    expect(m.getByText("22 of 25 held-out cases")).toBeTruthy();
    expect(m.getByText("96 of 120 dev cases")).toBeTruthy();
    expect(m.getAllByText("Not in this run").length).toBeGreaterThan(0);
  });

  it("dev column carries the dev label", async () => {
    setup();
    await screen.findByText(DEV_LABEL);
  });

  it("no Target column when no measure has a target", async () => {
    setup();
    await screen.findByRole("heading", { level: 2, name: "Measures" });
    expect(screen.queryByRole("columnheader", { name: "Target" })).toBeNull();
  });

  it("a target renders only in a column headed Target", async () => {
    const b = specExample("getLatestEval", "BOTH_SPLITS");
    b.splits.held_out!.measures[0]!.target = "Target text";
    setup(() => jsonResponse(200, b));
    await screen.findByRole("columnheader", { name: "Target" });
    const cell = screen.getByText("Target text");
    const idx = Array.from(cell.closest("tr")!.children).indexOf(cell.closest("td")!);
    const heads = Array.from(cell.closest("table")!.querySelectorAll("thead th"));
    expect(heads[idx]!.textContent).toBe("Target");
    expect(screen.getAllByText("Target text")).toHaveLength(1);
  });

  it("empty (NO_RUN) shows the sentence and no number", async () => {
    const { container } = setup("NO_RUN");
    await screen.findByText("No evaluation run yet.");
    expect(screen.getByText("When one runs, its results appear here with their test set. No number is shown before then.")).toBeTruthy();
    expect(container.textContent).not.toMatch(/\d+%/);
  });

  it("partial (DEV_ONLY) says no held-out run yet and labels dev", async () => {
    setup("DEV_ONLY");
    await screen.findByText("No held-out run yet.");
    expect(screen.getAllByText(new RegExp(DEV_LABEL.replace(/[()]/g, "\\$&"))).length).toBeGreaterThan(0);
    expect(screen.queryByText(/Held-out split: scored only/)).toBeNull();
  });

  it("stale run version", async () => {
    setup("STALE_RUN");
    await screen.findByText("This run used an earlier version of the agent (agent-0.4.0+kb-2026-10-10); the deployed version is agent-0.4.2+kb-2026-10-14.");
  });

  it("dev failures come from the dev split only", async () => {
    const b = specExample("getLatestEval", "BOTH_SPLITS");
    b.splits.held_out!.dev_failures = [{ case_id: "held-001", redacted_summary: "Should never show." }];
    setup(() => jsonResponse(200, b));
    await screen.findByText("dev-031");
    expect(screen.getByText(/Quoted the stale fee for after-hours dispatch\./)).toBeTruthy();
    expect(screen.queryByText("held-001")).toBeNull();
  });

  it("error shows the sentence", async () => {
    setup(() => jsonResponse(500, { error: { code: "X" } }));
    await screen.findByText("The evaluation report didn't load. Try again.");
  });

  it("resetting shows the reset sentence", async () => {
    setup(() => jsonResponse(503, { error: { code: "RESET_IN_PROGRESS", details: null }, request_id: "r" }));
    await screen.findByText("The demo is resetting. Try again in a few seconds.");
  });

  it("no 24-hour times", async () => {
    const { container } = setup();
    await screen.findByRole("heading", { level: 2, name: "Headline" });
    expectNo24HourTimes(container);
  });
});
