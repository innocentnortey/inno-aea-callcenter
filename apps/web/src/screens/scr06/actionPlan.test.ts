import { describe, expect, it } from "vitest";
import type { Role } from "@/lib/roles";
import { planActions } from "./actionPlan";
import { allowedFor } from "@/dev/directors/case-store";
import { defaultCase, liveJoinedCase, waitingCase } from "./case.fixtures";
import type { CaseDetail } from "./caseText";

const with_ = (d: CaseDetail, lifecycle: CaseDetail["case"]["lifecycle"], role: Role, live: CaseDetail["live"]["state"] = "not_live"): CaseDetail => ({
  ...d, case: { ...d.case, lifecycle, allowed_actions: allowedFor(lifecycle, role, live) }, live: { ...d.live, state: live },
});
const labels = (xs: { label: string; enabled: boolean }[]) => xs.filter((x) => x.enabled).map((x) => x.label);

describe("planActions", () => {
  it("unassigned / representative: Claim, locked menu and bar", () => {
    const p = planActions(defaultCase(), "representative");
    expect(p.primary).toEqual({ kind: "claim", label: "Claim" });
    expect(labels(p.menu)).toEqual([]);
    expect(p.menu.find((m) => m.key === "wait")!.reason).toBe("Claim the case first.");
    expect(p.bar.find((b) => b.key === "join_chat")!.reason).toBe("Join chat works only while the customer is waiting in a live chat.");
    expect(labels(p.bar)).toEqual(["Flag"]);
    expect(p.bar.some((b) => b.key === "assign")).toBe(false);
  });
  it("live_queued / representative: Claim and join", () => {
    const p = planActions(with_(defaultCase(), "live_queued", "representative", "queued"), "representative");
    expect(p.primary?.label).toBe("Claim and join");
  });
  it("claimed / representative: Resolve primary, menu holds Release, Set waiting, Close unresolved, Pick it back up", () => {
    const p = planActions(with_(defaultCase(), "claimed", "representative"), "representative");
    expect(p.primary).toEqual({ kind: "resolve", label: "Resolve" });
    expect(labels(p.menu)).toEqual(["Release", "Set waiting", "Close unresolved", "Pick it back up"]);
    expect(labels(p.bar)).toEqual(["Log a call", "Log an email", "Flag"]);
  });
  it("joined / representative: no primary, live box active, menu is More actions", () => {
    const p = planActions(liveJoinedCase(), "representative");
    expect(p.primary).toBeNull();
    expect(p.liveBox).toBe("active");
    expect(labels(p.menu)).toContain("Resolve");
  });
  it("handed back disables the live box", () => {
    expect(planActions(with_(liveJoinedCase(), "in_progress", "representative", "handed_back"), "representative").liveBox).toBe("disabled");
  });
  it("waiting / representative: Pick it back up", () => {
    const p = planActions(waitingCase(), "representative");
    expect(p.primary).toEqual({ kind: "start", label: "Pick it back up" });
    expect(p.menu.find((m) => m.key === "wait")!.reason).toBe("Pick the case back up first.");
  });
  it("resolved / representative: nothing but Flag", () => {
    const p = planActions(with_(defaultCase(), "resolved", "representative"), "representative");
    expect(p.primary).toBeNull();
    expect(labels(p.menu)).toEqual([]);
    expect(p.menu[0].reason).toBe("This case is closed.");
  });
  it("unassigned / supervisor: Assign visible, Reassign when owned", () => {
    const p = planActions(with_(defaultCase(), "unassigned", "supervisor"), "supervisor");
    expect(p.bar.map((b) => b.label)).toEqual(expect.arrayContaining(["Assign", "Change priority"]));
    expect(p.bar.some((b) => b.key === "join_chat")).toBe(false);
    const owned = with_(waitingCase(), "waiting", "supervisor");
    expect(planActions(owned, "supervisor").bar.find((b) => b.key === "assign")!.label).toBe("Reassign");
  });
  it("owner: read-only, nothing offered", () => {
    expect(planActions(liveJoinedCase(), "owner")).toEqual({ readOnly: true, primary: null, menu: [], bar: [], liveBox: "hidden" });
  });
  it("an item is enabled only if its key is in allowed_actions", () => {
    const lifecycles = ["unassigned", "live_queued", "claimed", "in_progress", "waiting", "resolved", "closed_unresolved"] as const;
    for (const role of ["representative", "supervisor"] as const) {
      for (const lc of lifecycles) {
        for (const live of ["not_live", "queued", "joined", "handed_back", "closed"] as const) {
          const d = with_(defaultCase(), lc, role, live);
          const allowed = d.case.allowed_actions as string[];
          const p = planActions(d, role);
          for (const m of [...p.menu, ...p.bar]) if (m.enabled) expect(allowed).toContain(m.key);
          if (p.primary) {
            const need = { claim: "claim", claim_and_join: "claim_and_join", resolve: "resolve", start: "start" }[p.primary.kind];
            expect(allowed).toContain(need);
          }
        }
      }
    }
  });
});
