import type { OperationId, Role } from "@/api/client";
import type { components } from "@/api/types.gen";
import type { ScreenId } from "@/routes";
import type { StandardState } from "@/screens/matrix";
import type { StreamScript } from "../stream/types";
import type { World } from "../world";

export type { StandardState };
export type OpForce =
  | { example: string; status?: number; delayMs?: number; transform?: (body: any) => any } // eslint-disable-line @typescript-eslint/no-explicit-any -- status only to disambiguate a name under two statuses
  | { fail: "network"; delayMs?: number } // fetch rejects -> ApiError(0,"NETWORK")
  | { hang: true } // never resolves (loading state, 65 s give-up)
  | { sequence: OpForce[] }; // consumed one per call; the last entry repeats

export interface Scenario {
  id: string; // `${slug}.${kebab}` e.g. "scr05.empty"; unique
  screen: ScreenId | "*"; // "*" only for the shared.* scenarios that work on any screen
  state: StandardState; // which cell of the 12x8 matrix this shows
  flowState?: string; // exact first-column text of the SCREEN_SPECS flow-state table, when it is one
  label: string; // shown in the panel
  route: string; // concrete path, e.g. "/staff/cases/MHC-C-0007"
  role?: Role; // default: first role in the screen's `roles`
  signedIn?: boolean; // default true, except screen "SCR-12" (login) where it is false; applyScenario (src/dev/apply.ts) must read it
  staffing?: "nobody_online" | "simulated_on_shift";
  ops?: Partial<Record<OperationId, OpForce>>;
  stream?: StreamScript;
  notes?: string; // how it is reached when it is not a pure forced response
}
export interface ScreenScenarios { complete?: boolean; scenarios: Scenario[] } // each scenarios/<slug>.ts: `export const screenScenarios: ScreenScenarios`

export interface Reaction {
  when: { op: OperationId; status?: number; example?: string };
  then(ctx: DevCtx): void;
}
export interface DevCtx {
  world: World; // read-only snapshot
  setForce(op: OperationId, force: OpForce | null): void;
  setRole(role: Role): void;
  setStaffing(mode: "nobody_online" | "simulated_on_shift"): void;
  emit(thread: string, event: unknown): void; // push a typed chat/case event into the scripted stream
  refetch(): void; // refetchAll()
  response?: { status: number; body: unknown }; // the response that triggered the reaction
  request?: unknown; // the request body
}
export interface ChatDirectorCtx { world: World }
/** Returns a submitTurn example name, or undefined to let the next rule decide. */
export type DirectorRule = (req: components["schemas"]["TurnRequest"], ctx: ChatDirectorCtx) => string | undefined;
