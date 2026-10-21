import type { Reaction } from "../scenarios/types";
import { rebaseMonitoring } from "../scenarios/g5-transforms";

export const reactions: Reaction[] = [
  {
    // So /monitoring opened without a scenario is fresh too. `?ex=getMonitoring:DEFAULT` bypasses this and reads as days old.
    when: { op: "getSession" },
    then(ctx) {
      if (!ctx.world.forces.getMonitoring) ctx.setForce("getMonitoring", { example: "DEFAULT", transform: rebaseMonitoring(0) });
    },
  },
];
