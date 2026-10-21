import { afterEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import { useOp } from "./useOp";
import { refetchAll } from "./refetch";
import { defaultTransport, setTransport } from "./transport";
import { jsonResponse, makeFakeTransport } from "@/test/fakeTransport";
import { STAFFING_OFF } from "@/test/fixtures";

afterEach(() => setTransport(defaultTransport));

function Probe({ enabled = true }: { enabled?: boolean }) {
  const { data, status } = useOp("getStaffing", enabled ? {} : null);
  return <p>{status}:{data?.label ?? "none"}</p>;
}

describe("useOp", () => {
  it("goes loading to success", async () => {
    setTransport(makeFakeTransport(() => jsonResponse(200, STAFFING_OFF)));
    render(<Probe />);
    expect(screen.getByText("loading:none")).toBeTruthy();
    await waitFor(() => expect(screen.getByText("success:Nobody online")).toBeTruthy());
  });
  it("refetches on refetchAll", async () => {
    const h = vi.fn(() => jsonResponse(200, STAFFING_OFF));
    setTransport(makeFakeTransport(h));
    render(<Probe />);
    await waitFor(() => expect(h).toHaveBeenCalledTimes(1));
    act(() => refetchAll());
    await waitFor(() => expect(h).toHaveBeenCalledTimes(2));
  });
  it("makes no call when args is null", async () => {
    const h = vi.fn(() => jsonResponse(200, STAFFING_OFF));
    setTransport(makeFakeTransport(h));
    render(<Probe enabled={false} />);
    await new Promise((r) => setTimeout(r, 20));
    expect(h).not.toHaveBeenCalled();
    expect(screen.getByText("idle:none")).toBeTruthy();
  });
  it("aborts the in-flight request on unmount", async () => {
    let signal: AbortSignal | undefined;
    setTransport(makeFakeTransport((_c, _u, init) => { signal = init.signal ?? undefined; return new Promise<Response>(() => {}); }));
    const { unmount } = render(<Probe />);
    await waitFor(() => expect(signal).toBeDefined());
    unmount();
    expect(signal?.aborted).toBe(true);
  });
  it("does not expose the previous key's data while the new key loads", async () => {
    let release!: () => void;
    const gate = new Promise<void>((r) => { release = r; });
    setTransport(makeFakeTransport(async (ctx) => {
      const ref = ctx.path.split("/").at(-1);
      if (ref === "B") await gate;
      return jsonResponse(200, { case: { reference: ref } });
    }));
    function CaseProbe({ r }: { r: string }) {
      const { data, status } = useOp("getCase", { path: { reference: r } });
      return <p>{status}:{(data as { case: { reference: string } } | undefined)?.case.reference ?? "none"}</p>;
    }
    const { rerender } = render(<CaseProbe r="A" />);
    await waitFor(() => expect(screen.getByText("success:A")).toBeTruthy());
    rerender(<CaseProbe r="B" />);
    expect(screen.getByText("loading:none")).toBeTruthy();
    release();
    await waitFor(() => expect(screen.getByText("success:B")).toBeTruthy());
  });
});
