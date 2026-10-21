// Test-only: queue bodies quoted from the OpenAPI getQueue examples.
import type { components } from "@/api/types.gen";
import { specExample } from "../scr06/specExample";

type Q = components["schemas"]["QueueResponse"];
const q = (name: string) => specExample<Q>("/api/staff/queue", "get", "200", name);
export const seededQueue = () => q("SEEDED");
export const staffedQueue = () => q("STAFFED_WITH_WAITING");
export const caughtUpQueue = () => q("ALL_CAUGHT_UP");
export const pendingBriefQueue = () => q("BRIEF_BEING_WRITTEN");
