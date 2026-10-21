import { resetLanded } from "./parts/landed";
import { resetAlerted } from "./SafetyCard";

/** Clears the module-level once-per-block memory so a new chat or a demo reset can announce its cards again. */
export function resetCardMemory(): void {
  resetLanded();
  resetAlerted();
}
