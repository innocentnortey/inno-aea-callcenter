import type { Reaction } from "../scenarios/types";
import { withExtraFlag, withReviewed } from "../scenarios/g5-transforms";

let armed = false;

export const reactions: Reaction[] = [
  {
    when: { op: "reviewFlag", example: "REVIEWED" },
    then(ctx) {
      const b = ctx.response?.body as { flag_id: string; reviewed_by: string | null; reviewed_note: string | null } | undefined;
      if (b) ctx.setForce("listFlags", { example: "THREE", transform: withReviewed(b.flag_id, { by: b.reviewed_by, note: b.reviewed_note }) });
    },
  },
  {
    when: { op: "listFlags", example: "THREE" },
    then(ctx) {
      if (ctx.world.scenarioId !== "scr08.stale-new-flag" || armed) return;
      armed = true;
      setTimeout(() => {
        armed = false;
        ctx.setForce("listFlags", { example: "THREE", transform: withExtraFlag });
      }, 3000);
    },
  },
];
