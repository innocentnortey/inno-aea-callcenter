import { resetLandedForTests } from "../parts/landed";
import { resetDedupeForTests } from "../sourceDedupe";
import { resetAlertedForTests } from "../SafetyCard";
import { resetFocusedForTests } from "../CodePromptCard";

export function resetCardState(): void {
  resetLandedForTests();
  resetDedupeForTests();
  resetAlertedForTests();
  resetFocusedForTests();
}
