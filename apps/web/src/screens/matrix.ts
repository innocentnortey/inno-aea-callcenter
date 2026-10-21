// The 12 x 8 state matrix from SCREEN_SPECS "State matrix" (96 cells: 82 real, 14 n/a).
// Lives outside src/dev so the production stubs can list their real states; src/dev/scenarios/matrix.ts re-exports it.
import type { ScreenId } from "@/routes";

export type StandardState = "default" | "empty" | "loading" | "partial" | "error" | "stale" | "success" | "disabled";
export const STANDARD_STATES: readonly StandardState[] = ["default", "empty", "loading", "partial", "error", "stale", "success", "disabled"];
export type MatrixCell = { real: true } | { real: false; reason: string };

const NA: Partial<Record<ScreenId, Partial<Record<StandardState, string>>>> = {
  "SCR-2": { partial: "n/a: each message is delivered whole; there is nothing to show half of" },
  "SCR-3": {
    empty: "n/a: the guide is static content and always has something to show",
    partial: "n/a: the only live data is staffing and the clock; if either fails it is the error state for that control while the static guide still shows",
  },
  "SCR-4": { empty: "n/a: the four roles are fixed", partial: "n/a: a switch either changes the role or it doesn't" },
  "SCR-7": { partial: "n/a: one oversight read returns every lane together (CON-17); there is no half-loaded lane to show" },
  "SCR-8": { partial: "n/a: each flag is stored whole with its case and message references" },
  "SCR-9": { success: "n/a: the page is read-only; opening cases is navigation, not an action with a result" },
  "SCR-10": { success: "n/a: read-only page with no actions", disabled: "n/a: no controls on this page" },
  "SCR-11": { success: "n/a: read-only page", disabled: "n/a: no controls" },
  "SCR-12": { empty: "n/a: nothing is listed; the empty form is the default state", partial: "n/a: a login is accepted or refused; there is no half-signed-in state" },
};
const IDS: ScreenId[] = ["SCR-1", "SCR-2", "SCR-3", "SCR-4", "SCR-5", "SCR-6", "SCR-7", "SCR-8", "SCR-9", "SCR-10", "SCR-11", "SCR-12"];

export const MATRIX = Object.fromEntries(
  IDS.map((id) => [id, Object.fromEntries(STANDARD_STATES.map((s) => {
    const reason = NA[id]?.[s];
    return [s, reason ? { real: false, reason } : { real: true }];
  }))]),
) as Record<ScreenId, Record<StandardState, MatrixCell>>;

export function realStates(id: ScreenId): StandardState[] {
  return STANDARD_STATES.filter((s) => MATRIX[id][s].real);
}
