import type { Reaction } from "../scenarios/types";
import { withoutRow } from "../scenarios/g5-transforms";

let armed = false;

export const reactions: Reaction[] = [
  {
    // Keeps the mock honest when no scenario forced a response for Assign (the UI builds its lines from the request).
    when: { op: "getOversight", status: 200 },
    then(ctx) {
      if (!ctx.world.forces.applyCaseAction) ctx.setForce("applyCaseAction", { example: "ASSIGNED" });
    },
  },
  {
    when: { op: "advanceDemoClock", example: "NEXT_MORNING" },
    then(ctx) {
      ctx.setForce("getDemoClock", { example: "ADVANCED" });
      ctx.setForce("getOversight", { example: "AFTER_ADVANCE" });
      ctx.refetch();
    },
  },
  {
    when: { op: "setStaffing", example: "TURNED_OFF_WITH_WAITING" },
    then(ctx) {
      ctx.setForce("getOversight", { example: "SHIFT_ENDED_WITH_WAITING" });
      ctx.refetch();
    },
  },
  {
    // The Prism ASSIGNED body always names MHC-C-0007 (mock artefact).
    when: { op: "applyCaseAction", example: "ASSIGNED" },
    then(ctx) {
      const ref = (ctx.response?.body as { case?: { reference?: string } } | undefined)?.case?.reference;
      if (ref) ctx.setForce("getOversight", { example: "SEEDED", transform: withoutRow(ref) });
      ctx.refetch();
    },
  },
  {
    when: { op: "getOversight", example: "SEEDED" },
    then(ctx) {
      if (ctx.world.scenarioId !== "scr07.stale-lanes-updated" || armed) return;
      armed = true;
      setTimeout(() => {
        armed = false;
        ctx.setForce("getOversight", { example: "AFTER_ADVANCE" });
      }, 11_000);
    },
  },
];
