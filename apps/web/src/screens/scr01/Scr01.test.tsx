import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/api/errors";
import { chatEvents } from "@/dev/stream/events";
import { renderWithProviders } from "@/test/render";
import { THREAD_KEY } from "./core/storage";
import { followUpExample, handoffExample, startExample, threadExample, turnExample } from "./core/testFixtures";
import Scr01 from "./Scr01";

const gw = vi.hoisted(() => ({
  start: vi.fn(), resume: vi.fn(), submit: vi.fn(), requestPerson: vi.fn(), saveFollowUp: vi.fn(),
}));
vi.mock("./core/gateway", () => ({ apiGateway: gw }));
const stream = vi.hoisted(() => ({ status: "open", cb: null as ((d: unknown, id: number | null, t: string) => void) | null }));
vi.mock("@/api/useEventStream", () => ({
  useEventStream: (_s: unknown, cb: (d: unknown, id: number | null, t: string) => void) => { stream.cb = cb; return { status: stream.status, lastEventId: null }; },
}));

beforeEach(() => {
  sessionStorage.clear();
  stream.status = "open";
  gw.start.mockReset().mockResolvedValue(startExample());
  gw.resume.mockReset().mockResolvedValue(threadExample("OPEN"));
  gw.submit.mockReset().mockResolvedValue(turnExample("ANSWER_WITH_SOURCE"));
  gw.requestPerson.mockReset().mockResolvedValue(handoffExample("CASE_CREATED"));
  gw.saveFollowUp.mockReset().mockResolvedValue(followUpExample());
});
const open = async () => {
  const view = renderWithProviders(<Scr01 />, { route: "/" });
  await screen.findByRole("log");
  return view;
};
const type = async (text: string) => {
  await userEvent.type(screen.getByRole("textbox"), text);
  await userEvent.click(screen.getByRole("button", { name: "Send" }));
};

describe("Scr01", () => {
  it("has the landmarks, one h1, the screen marker and the document title", async () => {
    const { container } = await open();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Meridian Home Comfort");
    expect(screen.getByRole("banner")).toBeTruthy();
    expect(screen.getByRole("complementary", { name: "What's settled" })).toBeTruthy();
    expect(screen.getByRole("main")).toBeTruthy();
    expect(screen.getByRole("form", { name: "Send a message" })).toBeTruthy();
    expect(container.querySelector('[data-screen="SCR-1"]')).not.toBeNull();
    expect(document.title).toBe("SCR-1 · Customer chat · Meridian");
    expect(screen.getByText(startExample().greeting.text)).toBeTruthy();
  });
  it("keeps the role switch while starting, failed, and ended", async () => {
    let release!: () => void;
    gw.start.mockImplementationOnce(() => new Promise((r) => { release = () => r(startExample()); }));
    renderWithProviders(<Scr01 />, { route: "/" });
    expect(await screen.findByRole("radiogroup", { name: "Acting as" })).toBeTruthy();
    expect(screen.queryByRole("log")).toBeNull();
    await act(async () => { release(); });
    await screen.findByRole("log");
    expect(screen.getByRole("radiogroup", { name: "Acting as" })).toBeTruthy();
  });
  it("start failure shows the retry and still the role switch", async () => {
    gw.start.mockRejectedValueOnce(new ApiError(0, "NETWORK", null));
    renderWithProviders(<Scr01 />, { route: "/" });
    expect(await screen.findByText("The chat didn't start. Try again.")).toBeTruthy();
    expect(screen.getByRole("radiogroup", { name: "Acting as" })).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByRole("log");
  });
  it("an ended thread shows the ended composer and still the role switch", async () => {
    sessionStorage.setItem(THREAD_KEY, JSON.stringify({ threadId: "old", limits: startExample().limits }));
    gw.resume.mockRejectedValueOnce(new ApiError(410, "SESSION_ENDED", null));
    renderWithProviders(<Scr01 />, { route: "/" });
    expect(await screen.findByRole("button", { name: "Start a new chat" })).toBeTruthy();
    expect(screen.getByText("This chat has ended.")).toBeTruthy();
    expect(screen.getByRole("radiogroup", { name: "Acting as" })).toBeTruthy();
    expect((screen.getByRole("textbox") as HTMLTextAreaElement).disabled).toBe(true);
  });
  it("shows the reconnecting line while the stream is reconnecting", async () => {
    stream.status = "reconnecting";
    await open();
    expect(screen.getByText(/Reconnecting… Staffing and messages may be out of date\./)).toBeTruthy();
  });
  it("a staffing_changed event shows the banner and the event line", async () => {
    await open();
    expect(screen.queryByText(/Simulated staffing \(demo\)/)).toBeNull();
    act(() => { stream.cb?.({ ...chatEvents.staffing_changed(), event_id: 41 }, 41, "staffing_changed"); });
    expect(await screen.findByText("Simulated staffing (demo). No Meridian employee is online.")).toBeTruthy();
    expect(within(screen.getByRole("log")).getByText(/Simulated staffing is on \(demo\)\./)).toBeTruthy();
  });
  it("a representative joining changes the top bar and the placeholder", async () => {
    await open();
    act(() => { stream.cb?.({ ...chatEvents.representative_joined(), event_id: 41 }, 41, "representative_joined"); });
    expect(await screen.findByText("Riley (demo representative). Assistant paused.")).toBeTruthy();
    expect((screen.getByRole("textbox") as HTMLTextAreaElement).placeholder).toBe("Message Riley");
  });
  it("pins the safety card outside the log and mounts it once", async () => {
    gw.submit.mockResolvedValueOnce(turnExample("SAFETY"));
    await open();
    await type("gas");
    await screen.findByRole("alert");
    const pinned = document.querySelector("[data-pinned-safety]")!;
    const card = pinned.firstElementChild;
    expect(card).not.toBeNull();
    expect(within(screen.getByRole("log")).queryByText(/Leave the home immediately/i)).toBeNull();
    expect(screen.getAllByText(/DANGER/).length).toBeGreaterThan(0);
    await type("one");
    await waitFor(() => expect(gw.submit).toHaveBeenCalledTimes(2));
    await type("two");
    await waitFor(() => expect(gw.submit).toHaveBeenCalledTimes(3));
    expect(document.querySelector("[data-pinned-safety]")!.firstElementChild).toBe(card);
    expect(screen.getAllByRole("alert")).toHaveLength(1);
    expect((screen.getByRole("textbox") as HTMLTextAreaElement).disabled).toBe(false);
    expect(document.activeElement).not.toBe(screen.getByRole("textbox"));
  });
  it("settled follows the server: a booked visit appears in the panel", async () => {
    gw.submit.mockResolvedValueOnce(turnExample("BOOKED"));
    await open();
    await type("book");
    const aside = screen.getByRole("complementary", { name: "What's settled" });
    await waitFor(() => expect(within(aside).queryByTestId("strip-line")?.textContent ?? "").not.toBe("Nothing yet"));
  });
  it("never prints the words the screen must not print", async () => {
    gw.submit.mockResolvedValueOnce(turnExample("HANDOFF"));
    const { container } = await open();
    await type("refund");
    await screen.findAllByText(/MHC-C-0007/);
    expect(container.textContent).not.toMatch(/\bcharged\b|\bshortly\b|queue position/i);
  });
  it("Talk to a person while the first reply is pending still works", async () => {
    let release!: () => void;
    gw.submit.mockImplementationOnce(() => new Promise((r) => { release = () => r(turnExample("ANSWER_WITH_SOURCE")); }));
    await open();
    await type("hello");
    await userEvent.click(screen.getByRole("button", { name: "Talk to a person" }));
    await waitFor(() => expect(gw.requestPerson).toHaveBeenCalledTimes(1));
    await act(async () => { release(); });
  });
});
