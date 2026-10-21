import { describe, expect, it } from "vitest";
import { renderHook } from "@testing-library/react";
import { act } from "react";
import type { components } from "@/api/types.gen";
import { useShownFlags } from "./useShownFlags";

type Flag = components["schemas"]["Flag"];
const flag = (id: string, status: Flag["status"] = "new"): Flag => ({
  flag_id: id, target: "answer", reason: null, case_ref: "MHC-C-0007", message_id: null, note: null, flagged_by: "Riley (demo)",
  at: "2026-10-16T14:41:00-05:00", status, reviewed_by: null, reviewed_note: null,
});

describe("useShownFlags", () => {
  it("first read is shown, nothing is new", () => {
    const { result } = renderHook(() => useShownFlags([flag("a")]));
    expect(result.current.shown.map((f) => f.flag_id)).toEqual(["a"]);
    expect(result.current.newCount).toBe(0);
  });
  it("a later added flag is counted, not shown", () => {
    const { result, rerender } = renderHook(({ f }) => useShownFlags(f), { initialProps: { f: [flag("a")] } });
    rerender({ f: [flag("a"), flag("b")] });
    expect(result.current.shown.map((f) => f.flag_id)).toEqual(["a"]);
    expect(result.current.newCount).toBe(1);
  });
  it("showNew reveals it", () => {
    const { result, rerender } = renderHook(({ f }) => useShownFlags(f), { initialProps: { f: [flag("a")] } });
    rerender({ f: [flag("a"), flag("b")] });
    act(() => result.current.showNew());
    expect(result.current.shown.map((f) => f.flag_id)).toEqual(["a", "b"]);
    expect(result.current.newCount).toBe(0);
  });
  it("a status change on a shown flag appears without showNew", () => {
    const { result, rerender } = renderHook(({ f }) => useShownFlags(f), { initialProps: { f: [flag("a")] } });
    rerender({ f: [flag("a", "reviewed")] });
    expect(result.current.shown[0]!.status).toBe("reviewed");
  });
  it("a removed flag disappears", () => {
    const { result, rerender } = renderHook(({ f }) => useShownFlags(f), { initialProps: { f: [flag("a"), flag("b")] } });
    rerender({ f: [flag("b")] });
    expect(result.current.shown.map((f) => f.flag_id)).toEqual(["b"]);
  });
});
