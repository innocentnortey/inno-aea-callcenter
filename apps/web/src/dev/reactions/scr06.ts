import type { Reaction } from "../scenarios/types";
import { resetCaseStore } from "../directors/case-store";

// Reset restores the seeded cases (FLOW-12); the shared reaction already resets the world, role and refetch.
export const reactions: Reaction[] = [{ when: { op: "resetDemo", status: 200 }, then: () => resetCaseStore() }];
