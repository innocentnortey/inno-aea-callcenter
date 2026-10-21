import type { OperationId } from "@/api/client";
import { OPS } from "@/api/client";
import type { World } from "./world";

export type DefaultMap = (op: OperationId, world: World) => string | undefined;

/** The example Prism should answer with when nothing forces one. Group files never edit this; they use forces and reactions. */
export const defaultExample: DefaultMap = (op, world) => {
  const on = world.staffing === "simulated_on_shift";
  switch (op) {
    case "getStaffing": return on ? "ON" : "OFF";
    case "startChatSession": return on ? "SIMULATION_ON" : "STARTED";
    case "getDemoClock": return "START";
    case "listDemoRoles": return "ROLES";
    case "requestPerson": return on ? "LIVE_QUEUED" : first2xx(op);
    case "getQueue": return on ? "STAFFED_WITH_WAITING" : "SEEDED";
    default: return first2xx(op);
  }
};

function first2xx(op: OperationId): string | undefined {
  const first = OPS[op].responses.find((r) => r.status >= 200 && r.status < 300 && r.examples.length > 0);
  return first?.examples[0]; // Prism's own default
}
